"""Tests for Luna de Girasol API endpoints."""

import pytest
from fastapi.testclient import TestClient
from models import InventoryItem, ProductCatalog
from sqlmodel import Session


class TestHealthCheck:
    """Tests for the health check endpoint."""

    def test_root_returns_api_status(self, client: TestClient) -> None:
        """Verify health check endpoint returns correct status."""
        response = client.get("/")
        assert response.status_code == 200
        data = response.json()
        assert data["message"] == "Luna de Girasol API"
        assert data["status"] == "active"


class TestCatalogEndpoints:
    """Tests for the Product Catalog CRUD endpoints."""

    def test_get_catalog_empty(self, client: TestClient) -> None:
        """Get catalog when database is empty."""
        response = client.get("/catalog")
        assert response.status_code == 200
        assert response.json() == []

    def test_get_catalog_with_products(
        self,
        client: TestClient,
        sample_product: ProductCatalog,
    ) -> None:
        """Get catalog with existing products."""
        response = client.get("/catalog")
        assert response.status_code == 200
        data = response.json()
        assert len(data) == 1
        assert data[0]["name"] == "Red Rose"
        assert data[0]["category"] == "Flowers"

    def test_get_catalog_ordered_by_name(
        self,
        client: TestClient,
        session: Session,
    ) -> None:
        """Verify catalog returns products ordered by name."""
        from datetime import datetime

        # Create products in non-alphabetical order
        products = [
            ProductCatalog(
                name="Sunflower",
                category="Flowers",
                created_at=datetime.now(),
            ),
            ProductCatalog(
                name="Carnation",
                category="Flowers",
                created_at=datetime.now(),
            ),
            ProductCatalog(
                name="Lily",
                category="Flowers",
                created_at=datetime.now(),
            ),
        ]
        for product in products:
            session.add(product)
        session.commit()

        response = client.get("/catalog")
        data = response.json()
        names = [p["name"] for p in data]
        assert names == ["Carnation", "Lily", "Sunflower"]

    def test_get_product_by_id(
        self,
        client: TestClient,
        sample_product: ProductCatalog,
    ) -> None:
        """Get a single product by ID."""
        response = client.get(f"/catalog/{sample_product.id}")
        assert response.status_code == 200
        data = response.json()
        assert data["name"] == "Red Rose"
        assert data["category"] == "Flowers"
        assert data["description"] == "Beautiful red rose"
        assert "inventory_items" in data

    def test_get_product_not_found(self, client: TestClient) -> None:
        """Get a non-existent product returns 404."""
        response = client.get("/catalog/9999")
        assert response.status_code == 404
        assert response.json()["detail"] == "Product not found"

    def test_get_product_with_inventory(
        self,
        client: TestClient,
        sample_product: ProductCatalog,
        sample_inventory_item: InventoryItem,
    ) -> None:
        """Get product includes its inventory items."""
        response = client.get(f"/catalog/{sample_product.id}")
        assert response.status_code == 200
        data = response.json()
        assert len(data["inventory_items"]) == 1
        assert data["inventory_items"][0]["variant_name"] == "Large Red Rose"

    def test_create_product(self, client: TestClient) -> None:
        """Create a new product."""
        product_data = {
            "name": "White Lily",
            "category": "Flowers",
            "description": "Elegant white lily",
            "care_instructions": "Change water daily",
        }
        response = client.post("/catalog", json=product_data)
        assert response.status_code == 200
        data = response.json()
        assert data["name"] == "White Lily"
        assert data["category"] == "Flowers"
        assert data["id"] is not None

    def test_create_product_minimal(self, client: TestClient) -> None:
        """Create a product with only required fields."""
        product_data = {
            "name": "Simple Flower",
            "category": "Basics",
        }
        response = client.post("/catalog", json=product_data)
        assert response.status_code == 200
        data = response.json()
        assert data["name"] == "Simple Flower"
        assert data["description"] is None

    def test_create_product_missing_required_fields(
        self,
        client: TestClient,
    ) -> None:
        """Create product without required fields fails."""
        product_data = {"name": "Missing Category"}
        response = client.post("/catalog", json=product_data)
        assert response.status_code == 422  # Validation error

    def test_delete_product(
        self,
        client: TestClient,
        sample_product: ProductCatalog,
    ) -> None:
        """Delete an existing product."""
        response = client.delete(f"/catalog/{sample_product.id}")
        assert response.status_code == 200
        assert "deleted successfully" in response.json()["message"]

        # Verify product is deleted
        response = client.get(f"/catalog/{sample_product.id}")
        assert response.status_code == 404

    def test_delete_product_not_found(self, client: TestClient) -> None:
        """Delete a non-existent product returns 404."""
        response = client.delete("/catalog/9999")
        assert response.status_code == 404
        assert response.json()["detail"] == "Product not found"


class TestInventoryEndpoints:
    """Tests for the Inventory CRUD endpoints."""

    def test_get_inventory_empty(self, client: TestClient) -> None:
        """Get inventory when database is empty."""
        response = client.get("/inventory")
        assert response.status_code == 200
        assert response.json() == []

    def test_get_inventory_with_items(
        self,
        client: TestClient,
        sample_inventory_item: InventoryItem,
    ) -> None:
        """Get inventory with existing items."""
        response = client.get("/inventory")
        assert response.status_code == 200
        data = response.json()
        assert len(data) == 1
        assert data[0]["variant_name"] == "Large Red Rose"
        assert data[0]["sku"] == "ROSE-RED-L"

    def test_get_inventory_item_by_id(
        self,
        client: TestClient,
        sample_inventory_item: InventoryItem,
    ) -> None:
        """Get a single inventory item by ID."""
        response = client.get(f"/inventory/{sample_inventory_item.id}")
        assert response.status_code == 200
        data = response.json()
        assert data["variant_name"] == "Large Red Rose"
        assert data["unit_cost"] == 500
        assert data["unit_price"] == 1000
        assert data["current_stock"] == 50

    def test_get_inventory_item_not_found(self, client: TestClient) -> None:
        """Get a non-existent inventory item returns 404."""
        response = client.get("/inventory/9999")
        assert response.status_code == 404
        assert response.json()["detail"] == "Inventory item not found"

    def test_create_inventory_item(
        self,
        client: TestClient,
        sample_product: ProductCatalog,
    ) -> None:
        """Create a new inventory item."""
        item_data = {
            "product_id": sample_product.id,
            "variant_name": "Medium Rose",
            "sku": "ROSE-RED-M",
            "unit_cost": 400,
            "unit_price": 800,
            "current_stock": 25,
            "reorder_level": 10,
            "shelf_life_days": 7,
            "is_active": True,
        }
        response = client.post("/inventory", json=item_data)
        assert response.status_code == 200
        data = response.json()
        assert data["variant_name"] == "Medium Rose"
        assert data["sku"] == "ROSE-RED-M"
        assert data["id"] is not None

    def test_create_inventory_item_invalid_product(
        self,
        client: TestClient,
    ) -> None:
        """Create inventory item with non-existent product fails."""
        item_data = {
            "product_id": 9999,
            "variant_name": "Ghost Item",
            "unit_cost": 100,
            "unit_price": 200,
        }
        response = client.post("/inventory", json=item_data)
        assert response.status_code == 404
        assert response.json()["detail"] == "Product not found"

    def test_create_inventory_item_missing_required_fields(
        self,
        client: TestClient,
        sample_product: ProductCatalog,
    ) -> None:
        """Create inventory item without required fields fails."""
        item_data = {
            "product_id": sample_product.id,
            "variant_name": "Incomplete Item",
            # Missing unit_cost and unit_price
        }
        response = client.post("/inventory", json=item_data)
        assert response.status_code == 422  # Validation error

    def test_update_inventory_item(
        self,
        client: TestClient,
        sample_inventory_item: InventoryItem,
    ) -> None:
        """Update an existing inventory item."""
        update_data = {
            "current_stock": 100,
            "unit_price": 1200,
        }
        response = client.put(
            f"/inventory/{sample_inventory_item.id}",
            json=update_data,
        )
        assert response.status_code == 200
        data = response.json()
        assert data["current_stock"] == 100
        assert data["unit_price"] == 1200
        # Unchanged fields should remain
        assert data["variant_name"] == "Large Red Rose"

    def test_update_inventory_item_partial(
        self,
        client: TestClient,
        sample_inventory_item: InventoryItem,
    ) -> None:
        """Partial update only changes specified fields."""
        update_data = {"is_active": False}
        response = client.put(
            f"/inventory/{sample_inventory_item.id}",
            json=update_data,
        )
        assert response.status_code == 200
        data = response.json()
        assert data["is_active"] is False
        assert data["current_stock"] == 50  # Unchanged

    def test_update_inventory_item_not_found(
        self,
        client: TestClient,
    ) -> None:
        """Update a non-existent inventory item returns 404."""
        update_data = {"current_stock": 999}
        response = client.put("/inventory/9999", json=update_data)
        assert response.status_code == 404
        assert response.json()["detail"] == "Inventory item not found"

    def test_delete_inventory_item(
        self,
        client: TestClient,
        sample_inventory_item: InventoryItem,
    ) -> None:
        """Delete an existing inventory item."""
        response = client.delete(f"/inventory/{sample_inventory_item.id}")
        assert response.status_code == 200
        assert "deleted successfully" in response.json()["message"]

        # Verify item is deleted
        response = client.get(f"/inventory/{sample_inventory_item.id}")
        assert response.status_code == 404

    def test_delete_inventory_item_not_found(self, client: TestClient) -> None:
        """Delete a non-existent inventory item returns 404."""
        response = client.delete("/inventory/9999")
        assert response.status_code == 404
        assert response.json()["detail"] == "Inventory item not found"


class TestLowStockEndpoint:
    """Tests for the low-stock inventory endpoint."""

    def test_get_low_stock_empty(self, client: TestClient) -> None:
        """Get low-stock items when database is empty."""
        response = client.get("/inventory/low-stock")
        assert response.status_code == 200
        assert response.json() == []

    def test_get_low_stock_no_low_stock(
        self,
        client: TestClient,
        sample_inventory_item: InventoryItem,
    ) -> None:
        """No items returned when all stock is above reorder level."""
        # sample_inventory_item has stock=50, reorder=10
        response = client.get("/inventory/low-stock")
        assert response.status_code == 200
        assert response.json() == []

    def test_get_low_stock_with_low_items(
        self,
        client: TestClient,
        sample_inventory_item: InventoryItem,
        low_stock_item: InventoryItem,
    ) -> None:
        """Returns only items below reorder level."""
        response = client.get("/inventory/low-stock")
        assert response.status_code == 200
        data = response.json()
        assert len(data) == 1
        assert data[0]["variant_name"] == "Small Red Rose"
        assert data[0]["current_stock"] == 5

    def test_get_low_stock_at_reorder_level(
        self,
        client: TestClient,
        session: Session,
        sample_product: ProductCatalog,
    ) -> None:
        """Items at exactly the reorder level are included."""
        from datetime import datetime

        item = InventoryItem(
            product_id=sample_product.id,
            variant_name="At Threshold",
            unit_cost=100,
            unit_price=200,
            current_stock=10,  # Equal to reorder_level
            reorder_level=10,
            created_at=datetime.now(),
            updated_at=datetime.now(),
        )
        session.add(item)
        session.commit()

        response = client.get("/inventory/low-stock")
        assert response.status_code == 200
        data = response.json()
        assert len(data) == 1
        assert data[0]["variant_name"] == "At Threshold"


class TestValidation:
    """Tests for input validation."""

    def test_product_name_max_length(self, client: TestClient) -> None:
        """Product name exceeding max length fails."""
        product_data = {
            "name": "A" * 101,  # Max is 100
            "category": "Flowers",
        }
        response = client.post("/catalog", json=product_data)
        assert response.status_code == 422

    def test_product_category_max_length(self, client: TestClient) -> None:
        """Product category exceeding max length fails."""
        product_data = {
            "name": "Valid Name",
            "category": "A" * 51,  # Max is 50
        }
        response = client.post("/catalog", json=product_data)
        assert response.status_code == 422

    @pytest.mark.parametrize(
        ("field", "value"),
        [
            ("unit_cost", "not_a_number"),
            ("unit_price", "invalid"),
            ("current_stock", 3.14),
            ("reorder_level", "ten"),
        ],
    )
    def test_inventory_item_invalid_types(
        self,
        client: TestClient,
        sample_product: ProductCatalog,
        field: str,
        value: str | float,
    ) -> None:
        """Inventory item with invalid field types fails."""
        item_data = {
            "product_id": sample_product.id,
            "variant_name": "Test Item",
            "unit_cost": 100,
            "unit_price": 200,
            field: value,
        }
        response = client.post("/inventory", json=item_data)
        assert response.status_code == 422
