start project
python3 -m venv venv
source venv/bin/activate
uvicorn app.main:app --reload


post products sample
{
  "name": "Arabica Coffee Beans 1kg",
  "sku": "CFB-001",
  "category": "Coffee Beans",
  "supplier": "BeanCraft Roasters",
  "price": 18.99,
  "reorder_level": 10,
  "in_stock": 50,
  "description": "Premium roasted Arabica coffee beans",
  "movements": [
    { "movement_date": "2025-10-25", "type": "IN", "quantity": 50 },
    { "movement_date": "2025-10-26", "type": "OUT", "quantity": 5 }
  ]
}
# InventoryBackend
