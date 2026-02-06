# Luna de Girasol API

A simple FastAPI backend for managing product catalogs and inventory.

## Getting Started

### Prerequisites

- Python 3.13+
- `uv` package manager

## API Endpoints

### Health Check

- `GET /` - API status

### Product Catalog

- `GET /catalog` - List all products
- `GET /catalog/{product_id}` - Get product details with inventory
- `POST /catalog` - Create new product
- `PUT /catalog/{product_id}` - Update product
- `DELETE /catalog/{product_id}` - Delete product

### Inventory

- `GET /inventory` - List all inventory items
- `POST /inventory` - Add inventory item
- `PUT /inventory/{item_id}` - Update inventory item
- `DELETE /inventory/{item_id}` - Delete inventory item

