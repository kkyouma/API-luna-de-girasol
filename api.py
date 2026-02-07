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
def create_sale(
    sale_order_data: SaleOrderCreate,
    session: Session = Depends(get_session),
) -> SaleOrder:
    """Create a new sale."""
    logger.info("START create_sale")
    logger.debug("Incoming payload: %s", sale_order_data.model_dump())

    # 1. Prepare the Sale Order object
    logger.info("Creating SaleOrder DB object")
    db_sale = SaleOrder(
        order_date=sale_order_data.order_date,
        order_type=sale_order_data.order_type.value,
        customer_id=sale_order_data.customer_id,
        occasion_id=sale_order_data.occasion_id,
        subtotal=0,
        total=0,
        status=sale_order_data.status.value,
        notes=sale_order_data.notes,
    )

    session.add(db_sale)
    session.flush()
    logger.debug("SaleOrder flushed with ID=%s", db_sale.id)

    running_subtotal = 0.0

    # 2. Process each item
    for idx, item_data in enumerate(sale_order_data.items, start=1):
        logger.info("Processing item #%d", idx)
        logger.debug("Item payload: %s", item_data.model_dump())

        # Validation
        if item_data.inventory_item_id and item_data.bouquet_template_id:
            logger.error("Item has both inventory and bouquet IDs: %s", item_data)
            raise HTTPException(400, "Item cannot be both inventory and bouquet")

        if not item_data.inventory_item_id and not item_data.bouquet_template_id:
            logger.error("Item has no inventory or bouquet ID: %s", item_data)
            raise HTTPException(400, "Item must target inventory or bouquet")

        inventory_item = session.get(InventoryItem, item_data.inventory_item_id)
        if not inventory_item:
            logger.error("Inventory item not found: id=%s", item_data.inventory_item_id)
            raise HTTPException(404, f"Item {item_data.inventory_item_id} not found")

        unit_price = (
            item_data.unit_price
            if hasattr(item_data, "unit_price_override")
            and item_data.unit_price_override is not None
            else inventory_item.unit_price
        )

        # Create SaleOrderItem
        db_item = SaleOrderItem(
            sale_order_id=db_sale.id,
            quantity=item_data.quantity,
            unit_price=unit_price,
            subtotal=item_data.quantity * unit_price,
            description=item_data.description,
            inventory_item_id=item_data.inventory_item_id,
            bouquet_template_id=item_data.bouquet_template_id,
        )

        session.add(db_item)
        running_subtotal += db_item.subtotal
        logger.debug(
            "Added SaleOrderItem: inventory_id=%s qty=%s subtotal=%s running_subtotal=%s",
            item_data.inventory_item_id,
            item_data.quantity,
            db_item.subtotal,
            running_subtotal,
        )

        logger.debug(
            "Stock before deduction: item=%s stock=%s",
            inventory_item.id,
            inventory_item.current_stock,
        )

        if inventory_item.current_stock < item_data.quantity:
            logger.warning(
                "Insufficient stock: item=%s required=%s available=%s",
                inventory_item.id,
                item_data.quantity,
                inventory_item.current_stock,
            )
            raise HTTPException(
                400,
                f"Insufficient stock for '{inventory_item.variant_name}'. "
                f"Required: {item_data.quantity}, Available: {inventory_item.current_stock}",
            )

        # === STOCK DEDUCTION ===
        # Deduct stock
        inventory_item.current_stock -= item_data.quantity
        session.add(inventory_item)
        logger.debug(
            "Stock deducted: item=%s new_stock=%s",
            inventory_item.id,
            inventory_item.current_stock,
        )

        # Stock movement
        movement = StockMovement(
            movement_type=StockMovementType.OUT.value,
            quantity=item_data.quantity,
            reference_type=StockReferenceType.SALE.value,
            reference_id=db_sale.id,
            inventory_item_id=inventory_item.id,
            notes=f"Sale #{db_sale.id} (Direct)",
        )
        session.add(movement)
        logger.debug("StockMovement created: %s", movement)

    # 3. Finalize totals
    db_sale.subtotal = running_subtotal
    discount_val = (
        running_subtotal * (sale_order_data.discount_percent / 100)
    ) + sale_order_data.discount_amount

    db_sale.total = running_subtotal - discount_val + sale_order_data.packaging_fee

    logger.info(
        "Totals calculated: subtotal=%s discount=%s packaging=%s total=%s",
        running_subtotal,
        discount_val,
        sale_order_data.packaging_fee,
        db_sale.total,
    )

    # 4. Commit
    logger.info("Committing transaction for sale_id=%s", db_sale.id)
    logger.info(f"SALE:\n{db_sale.model_dump_json()}")
    logger.info(f"MOVEMENT:\n{movement.model_dump_json()}")
    session.commit()
    session.refresh(db_sale)

    logger.info("END create_sale sale_id=%s", db_sale.id)
    return db_sale
