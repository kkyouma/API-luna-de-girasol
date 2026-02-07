import logging

from database import get_session
from fastapi import Depends, FastAPI, HTTPException
from models import (
    InventoryItem,
    InventoryItemCreate,
    InventoryItemRead,
    InventoryItemUpdate,
    ProductCatalog,
    ProductCatalogCreate,
    ProductCatalogRead,
    ProductCatalogReadWithInventory,
    SaleOrder,
    SaleOrderCreate,
    SaleOrderItem,
    SaleOrderRead,
    SaleOrderReadWithDetails,
    StockMovement,
    StockMovementType,
    StockReferenceType,
)
from sqlmodel import Session, select

logger = logging.getLogger(__name__)

app = FastAPI(title="Luna de Girasol API")


@app.get("/", tags=["Health"])
def root() -> dict[str, str]:
    """Health check endpoint."""
    return {
        "message": "Luna de Girasol API",
        "status": "active",
    }


# =============== PRODUCT CATALOG ENDPOINTS ===============


@app.get("/catalog", response_model=list[ProductCatalogRead], tags=["Catalog"])
def get_catalog(session: Session = Depends(get_session)) -> list[ProductCatalogRead]:
    """Get all products from catalog."""
    statement = select(ProductCatalog).order_by(ProductCatalog.name)
    products = session.exec(statement).all()
    return [ProductCatalogRead.model_validate(p) for p in products]


@app.get(
    "/catalog/{product_id}",
    response_model=ProductCatalogReadWithInventory,
    tags=["Catalog"],
)
def get_product(
    product_id: int,
    session: Session = Depends(get_session),
) -> ProductCatalogReadWithInventory:
    """Get a specific product with its inventory items."""
    product = session.get(ProductCatalog, product_id)
    if not product:
        raise HTTPException(status_code=404, detail="Product not found")
    # Convert inventory items to read models
    inventory_reads = [
        InventoryItemRead.model_validate(item) for item in product.inventory_items
    ]

    product_data = {
        "id": product.id,
        "name": product.name,
        "category": product.category,
        "description": product.description,
        "care_instructions": product.care_instructions,
        "created_at": product.created_at,
        "inventory_items": inventory_reads,
    }
    return ProductCatalogReadWithInventory(**product_data)


@app.post("/catalog", response_model=ProductCatalogRead, tags=["Catalog"])
def create_product(
    product: ProductCatalogCreate,
    session: Session = Depends(get_session),
) -> ProductCatalog:
    """Add a new product to the catalog."""
    db_product = ProductCatalog.model_validate(product)
    session.add(db_product)
    session.commit()
    session.refresh(db_product)
    logger.info(f"Added {product.name} to catalog")
    return db_product


@app.delete("/catalog/{product_id}", tags=["Catalog"])
def delete_product(
    product_id: int,
    session: Session = Depends(get_session),
) -> dict[str, str]:
    """Delete a product from catalog."""
    product = session.get(ProductCatalog, product_id)
    if not product:
        raise HTTPException(status_code=404, detail="Product not found")
    session.delete(product)
    session.commit()
    return {"message": f"Product {product_id} deleted successfully"}


# =============== INVENTORY ENDPOINTS ===============


# NOTE: Low-stock route MUST be defined before /{item_id} to avoid path matching issues
@app.get(
    "/inventory/low-stock",
    response_model=list[InventoryItemRead],
    tags=["Inventory"],
)
def get_low_stock_items(
    session: Session = Depends(get_session),
) -> list[InventoryItem]:
    """Get inventory items below reorder level."""
    statement = select(InventoryItem).where(
        InventoryItem.current_stock <= InventoryItem.reorder_level,
    )
    items = list(session.exec(statement).all())
    return items


@app.get("/inventory", response_model=list[InventoryItemRead], tags=["Inventory"])
def get_inventory(session: Session = Depends(get_session)) -> list[InventoryItemRead]:
    """Get all inventory items."""
    statement = select(InventoryItem).order_by(InventoryItem.variant_name)
    items = session.exec(statement).all()
    return [InventoryItemRead.model_validate(i) for i in items]


@app.get("/inventory/{item_id}", response_model=InventoryItemRead, tags=["Inventory"])
def get_inventory_item(
    item_id: int,
    session: Session = Depends(get_session),
) -> InventoryItem:
    """Get a specific inventory item."""
    item = session.get(InventoryItem, item_id)
    if not item:
        raise HTTPException(status_code=404, detail="Inventory item not found")
    return item


@app.post("/inventory", response_model=InventoryItemRead, tags=["Inventory"])
def create_inventory_item(
    item: InventoryItemCreate,
    session: Session = Depends(get_session),
) -> InventoryItem:
    """Add a new inventory item."""
    # Verify product exists
    product = session.get(ProductCatalog, item.product_id)
    if not product:
        raise HTTPException(status_code=404, detail="Product not found")

    db_item = InventoryItem.model_validate(item)
    session.add(db_item)
    session.commit()
    session.refresh(db_item)
    logger.info(f"Added inventory item for product {item.product_id}")
    return db_item


@app.put("/inventory/{item_id}", response_model=InventoryItemRead, tags=["Inventory"])
def update_inventory_item(
    item_id: int,
    item_update: InventoryItemUpdate,
    session: Session = Depends(get_session),
) -> InventoryItem:
    """Update an inventory item."""
    db_item = session.get(InventoryItem, item_id)
    if not db_item:
        raise HTTPException(status_code=404, detail="Inventory item not found")

    # Update only provided fields
    item_data = item_update.model_dump(exclude_unset=True)
    for key, value in item_data.items():
        setattr(db_item, key, value)

    db_item.updated_at = None  # Will be set to current timestamp by database
    session.commit()
    session.refresh(db_item)
    return db_item


@app.delete("/inventory/{item_id}", tags=["Inventory"])
def delete_inventory_item(
    item_id: int,
    session: Session = Depends(get_session),
) -> dict[str, str]:
    """Delete an inventory item."""
    item = session.get(InventoryItem, item_id)
    if not item:
        raise HTTPException(status_code=404, detail="Inventory item not found")
    session.delete(item)
    session.commit()
    return {"message": f"Inventory item {item_id} deleted successfully"}


# =============== SALES ENDPOINTS ===============


@app.get("/sales", response_model=list[SaleOrderRead], tags=["Sales"])
def get_sales(session: Session = Depends(get_session)):
    statement = select(SaleOrder).order_by(SaleOrder.created_at)  # ty:ignore[invalid-argument-type]
    orders = session.exec(statement).all()
    return orders


@app.post("/sales", response_model=SaleOrderReadWithDetails, tags=["Sales"])
def create_sale_order(
    sale_order: SaleOrderCreate,
    session: Session = Depends(get_session),
) -> SaleOrderReadWithDetails:

    sale_dict = sale_order.model_dump(exclude={"items"})
    db_sale = SaleOrder.model_validate(sale_dict)

    db_sale.subtotal = 0
    db_sale.total = 0

    session.add(db_sale)
    session.flush()

    running_subtotal = 0.0

    for item_data in db_sale.items:
        # STOCK DEDUCTION
        inventory_item = session.get(InventoryItem, item_data.inventory_item_id)
        if not inventory_item:
            raise HTTPException(
                status_code=404,
                detail=f"Item {item_data.inventory_item_id} not found",
            )

        if inventory_item.current_stock < item_data.quantity:
            raise HTTPException(
                status_code=400,
                detail=f"Insufficient stock for item {item_data.inventory_item_id}",
            )

        # Deduct Stock
        inventory_item.current_stock -= item_data.quantity
        session.add(inventory_item)

        # Log movement
        movement = StockMovement(
            movement_type=StockMovementType.OUT,
            quantity=item_data.quantity,
            reference_type=StockReferenceType.SALE,
            reference_id=db_sale.id,
            inventory_item_id=inventory_item.id,
            notes=f"Sale #{db_sale.id}",
        )
        session.add(movement)

        db_item = SaleOrderItem(
            sale_order_id=db_sale.id,
            quantity=item_data.quantity,
            unit_price=item_data.unit_price,
            subtotal=item_data.quantity * item_data.unit_price,
            description=item_data.description,
            inventory_item_id=item_data.inventory_item_id,
            bouquet_template_id=item_data.bouquet_template_id,
        )
        session.add(db_item)
        running_subtotal += db_item.subtotal

    db_sale.subtotal = running_subtotal
    discount_val = (
        running_subtotal * (db_sale.discount_percent / 100) + db_sale.discount_amount
    )
    db_sale.total = max(0, running_subtotal - discount_val + db_sale.packaging_fee)

    session.add(db_sale)
    session.commit()
    session.refresh(db_sale)

    return db_sale  # ty:ignore[invalid-return-type]
