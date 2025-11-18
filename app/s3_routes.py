"""
Simplified FastAPI routes for S3 file operations
Handles file upload and listing only
"""

from fastapi import APIRouter, File, UploadFile, HTTPException, Depends, status
from fastapi.responses import Response, StreamingResponse
from typing import List
from io import BytesIO
from .auth import get_current_user
from .utils import ok, bad
from .s3.service import BulkDataService

router = APIRouter(prefix="/s3", tags=["S3 Files"])

# Initialize service
try:
    file_service = BulkDataService()
except Exception as e:

    file_service = None


@router.get("/")
def get_s3_info(current=Depends(get_current_user)):
    """Get S3 service information"""
    if not file_service:
        return bad(503, "SERVICE_UNAVAILABLE", "S3 service not configured")
    
    return ok("S3 file service information", {
        "supported_file_types": file_service.get_supported_file_types(),
        "note": "Upload files directly to S3 bucket root",
        "max_file_size": "100MB (recommended)"
    })


@router.post("/upload")
async def upload_file(
    file: UploadFile = File(...),
    current=Depends(get_current_user)
):
    """
    Upload file to S3
    
    Supported file types: CSV, JSON, XLSX, TXT
    """
    if not file_service:
        return bad(503, "SERVICE_UNAVAILABLE", "S3 service not configured")
    
    try:
        # Validate file
        if not file.filename:
            return bad(400, "INVALID_FILE", "No filename provided")
        
        if not file_service.validate_file_type(file.filename):
            supported = ", ".join(file_service.get_supported_file_types())
            return bad(400, "INVALID_FILE_TYPE", f"File type not supported. Allowed: {supported}")
        
        # Read file content
        file_content = await file.read()
        if len(file_content) == 0:
            return bad(400, "EMPTY_FILE", "File is empty")
        
        # Upload to S3
        result = file_service.upload_bulk_file(file_content, file.filename)
        
        if not result or not result.get('success'):
            error_msg = result.get('error', 'Unknown upload error') if result else 'Upload service failed'
            return bad(500, "UPLOAD_FAILED", error_msg)
        
        return ok("File uploaded successfully", {
            "file_key": result['file_key'],
            "original_filename": result['original_filename'],
            "size_bytes": result['size_bytes'],
            "uploaded_at": result['uploaded_at']
        })
        
    except Exception as e:
        return bad(500, "UPLOAD_ERROR", "Failed to upload file", str(e))


@router.get("/files")
def list_files(current=Depends(get_current_user)):
    """
    List all files in S3 bucket
    """
    if not file_service:
        return bad(503, "SERVICE_UNAVAILABLE", "S3 service not configured")
    
    try:
        files = file_service.list_files()
        
        return ok("Files retrieved successfully", {
            "files": files,
            "total_count": len(files)
        })
        
    except Exception as e:
        return bad(500, "LIST_ERROR", "Failed to list files", str(e))


@router.get("/download/{file_key:path}")
def download_file(file_key: str, current=Depends(get_current_user)):
    """
    Download file from S3
    """
    if not file_service:
        return bad(503, "SERVICE_UNAVAILABLE", "S3 service not configured")
    
    try:
        result = file_service.download_bulk_file(file_key)
        
        if not result or not result.get('success'):
            error_msg = result.get('error', 'File not found') if result else 'Download service failed'
            return bad(404, "DOWNLOAD_FAILED", error_msg)
        
        file_content = result['content']
        
        # Determine filename for download
        original_filename = file_key
        if '_' in file_key:
            parts = file_key.split('_', 2)
            if len(parts) >= 3:
                original_filename = parts[2]
        
        # Return file as streaming response
        return StreamingResponse(
            BytesIO(file_content),
            media_type='application/octet-stream',
            headers={"Content-Disposition": f"attachment; filename={original_filename}"}
        )
        
    except Exception as e:
        return bad(500, "DOWNLOAD_ERROR", "Failed to download file", str(e))


@router.delete("/files/{file_key:path}")
def delete_file(file_key: str, current=Depends(get_current_user)):
    """
    Delete file from S3
    """
    if not file_service:
        return bad(503, "SERVICE_UNAVAILABLE", "S3 service not configured")
    
    try:
        result = file_service.delete_bulk_file(file_key)
        
        if not result or not result.get('success'):
            error_msg = result.get('error', 'Delete failed') if result else 'Delete service failed'
            return bad(500, "DELETE_FAILED", error_msg)
        
        return ok("File deleted successfully", {
            "file_key": file_key,
            "deleted_at": result['deleted_at']
        })
        
    except Exception as e:
        return bad(500, "DELETE_ERROR", "Failed to delete file", str(e))