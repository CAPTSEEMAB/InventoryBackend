"""
Bulk Data Service for handling large dataset uploads to S3
Supports various file formats like CSV, JSON, Excel for bulk operations
Does NOT store metadata in database - pure S3 file operations
"""

import os
import csv
import json
import uuid
from datetime import datetime
from typing import List, Dict, Optional, Union
from io import StringIO, BytesIO
from .s3_client import S3Client


class BulkDataService:
    """Service for handling bulk data file operations with S3"""
    
    def __init__(self):
        """Initialize the bulk data service"""
        self.s3_client = S3Client()
        self.allowed_file_types = {
            'csv': 'text/csv',
            'json': 'application/json',
            'xlsx': 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
            'txt': 'text/plain'
        }
        
        # Simple file storage - no categorization needed
        

    
    def generate_file_key(self, original_filename: str) -> str:
        """
        Generate unique S3 file key for bucket root
        
        Args:
            original_filename: Original uploaded filename
            
        Returns:
            str: S3 file key for bucket root
        """
        # Create unique filename with timestamp
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        unique_id = str(uuid.uuid4())[:8]
        
        # Format: timestamp_uniqueid_originalname.ext
        filename = f"{timestamp}_{unique_id}_{original_filename}"
        return filename
    
    def validate_file_type(self, filename: str) -> bool:
        """
        Validate if file type is allowed for bulk operations
        
        Args:
            filename: Name of the file to validate
            
        Returns:
            bool: True if file type is allowed
        """
        file_extension = filename.split('.')[-1].lower()
        return file_extension in self.allowed_file_types
    
    def get_content_type(self, filename: str) -> str:
        """
        Get appropriate content type for file
        
        Args:
            filename: Name of the file
            
        Returns:
            str: MIME content type
        """
        file_extension = filename.split('.')[-1].lower()
        return self.allowed_file_types.get(file_extension, 'application/octet-stream')
    
    def upload_bulk_file(self, file_content: bytes, filename: str) -> Optional[Dict]:
        """
        Upload file to S3
        
        Args:
            file_content: File content as bytes
            filename: Original filename
            
        Returns:
            Dict: Upload result with file metadata
        """
        try:
            # Validate file type
            if not self.validate_file_type(filename):
                return {
                    'success': False,
                    'error': f'File type not allowed. Supported: {", ".join(self.allowed_file_types.keys())}'
                }
            
            # Generate unique S3 key
            file_key = self.generate_file_key(filename)
            content_type = self.get_content_type(filename)
            
            # Upload to S3
            success = self.s3_client.upload_file(file_content, file_key, content_type)
            
            if success:
                return {
                    'success': True,
                    'file_key': file_key,
                    'original_filename': filename,
                    'size_bytes': len(file_content),
                    'content_type': content_type,
                    'uploaded_at': datetime.now().isoformat()
                }
            else:
                return {
                    'success': False,
                    'error': 'Failed to upload file to S3'
                }
                
        except Exception as e:
            return {
                'success': False,
                'error': f'Upload failed: {str(e)}'
            }
    
    def download_bulk_file(self, file_key: str) -> Optional[Dict]:
        """
        Download bulk data file from S3
        
        Args:
            file_key: S3 object key
            
        Returns:
            Dict: Download result with file content
        """
        try:
            file_content = self.s3_client.download_file(file_key)
            
            if file_content:
                return {
                    'success': True,
                    'file_key': file_key,
                    'content': file_content,
                    'size_bytes': len(file_content),
                    'downloaded_at': datetime.now().isoformat()
                }
            else:
                return {
                    'success': False,
                    'error': 'File not found or download failed'
                }
                
        except Exception as e:
            return {
                'success': False,
                'error': f'Download failed: {str(e)}'
            }
    
    def list_files(self) -> List[Dict]:
        """
        List all files in S3 bucket
        
        Returns:
            List[Dict]: List of file metadata
        """
        try:
            # Get all files from bucket root
            files = self.s3_client.list_files("")
            
            # Add parsed metadata
            enriched_files = []
            for file_info in files:
                enriched_file = file_info.copy()
                
                # Extract original filename from S3 key
                filename = file_info['key']
                if '_' in filename:
                    # Format: YYYYMMDD_HHMMSS_uniqueid_originalname.ext
                    # Split on underscore, skip first 3 parts (date, time, uniqueid)
                    parts = filename.split('_', 3)
                    if len(parts) == 4:
                        # The fourth part contains the original filename
                        enriched_file['original_filename'] = parts[3]
                    else:
                        enriched_file['original_filename'] = filename
                else:
                    enriched_file['original_filename'] = filename
                    
                enriched_files.append(enriched_file)
            
            return enriched_files
            
        except Exception as e:
            return []
    
    def delete_bulk_file(self, file_key: str) -> Dict:
        """
        Delete bulk data file from S3
        
        Args:
            file_key: S3 object key
            
        Returns:
            Dict: Deletion result
        """
        try:
            success = self.s3_client.delete_file(file_key)
            
            if success:
                return {
                    'success': True,
                    'message': f'File deleted successfully: {file_key}',
                    'deleted_at': datetime.now().isoformat()
                }
            else:
                return {
                    'success': False,
                    'error': 'Failed to delete file from S3'
                }
                
        except Exception as e:
            return {
                'success': False,
                'error': f'Delete failed: {str(e)}'
            }
    
    def get_download_url(self, file_key: str, expiration: int = 3600) -> Optional[str]:
        """
        Generate pre-signed download URL for bulk file
        
        Args:
            file_key: S3 object key
            expiration: URL expiration in seconds
            
        Returns:
            str: Pre-signed download URL
        """
        return self.s3_client.get_file_url(file_key, expiration)
    
    def preview_csv_content(self, file_key: str, max_rows: int = 10) -> Optional[Dict]:
        """
        Preview CSV file content without full download
        
        Args:
            file_key: S3 object key for CSV file
            max_rows: Maximum rows to preview
            
        Returns:
            Dict: Preview data with headers and sample rows
        """
        try:
            if not file_key.lower().endswith('.csv'):
                return {
                    'success': False,
                    'error': 'File is not a CSV file'
                }
            
            # Download file content
            file_content = self.s3_client.download_file(file_key)
            if not file_content:
                return {
                    'success': False,
                    'error': 'Failed to download file for preview'
                }
            
            # Parse CSV content
            csv_text = file_content.decode('utf-8')
            csv_reader = csv.reader(StringIO(csv_text))
            
            rows = list(csv_reader)
            if not rows:
                return {
                    'success': False,
                    'error': 'CSV file is empty'
                }
            
            headers = rows[0] if rows else []
            sample_rows = rows[1:max_rows+1] if len(rows) > 1 else []
            
            return {
                'success': True,
                'file_key': file_key,
                'total_rows': len(rows) - 1,  # Exclude header
                'headers': headers,
                'sample_rows': sample_rows,
                'preview_rows': len(sample_rows)
            }
            
        except Exception as e:
            return {
                'success': False,
                'error': f'Preview failed: {str(e)}'
            }
    
    def get_supported_file_types(self) -> List[str]:
        """Get list of supported file extensions"""
        return list(self.allowed_file_types.keys())
    
    def get_supported_file_types(self) -> List[str]:
        """Get list of supported file extensions"""
        return list(self.allowed_file_types.keys())