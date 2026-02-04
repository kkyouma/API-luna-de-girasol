import logging

from backend import get_all_inventory
from database import get_session
from fastapi import Depends, FastAPI
from models import (
    InventoryItemRead,
    ProductCatalog,
    ProductCatalogCreate,
    ProductCatalogRead,
)
from sqlmodel import Session

logger = logging.getLogger(__name__)

app = FastAPI(title="Luna de Girasol API")


@app.get("/", tags=["Health"])
def root() -> dict[str, str]:
    """Health check endpoint."""
    return {
        "message": "Luna de Girasol API",
        "status": "active",
    }


@app.get("/inventory", response_model=list[InventoryItemRead], tags=["Inventory"])
def get_inventory(session: Session = Depends(get_session)) -> list[InventoryItemRead]:
    """Get all inventory."""
    inventory = get_all_inventory(session)
    return [
        InventoryItemRead(
            id=i.id,
            variant_name=i.variant_name,
            current_stock=i.current_stock,
            unit_price=i.unit_price,
        )
        for i in inventory
    ]


@app.post("/catalog", response_model=ProductCatalogRead, tags=["Catalog"])
def add_catalog(
    product: ProductCatalogCreate,
    session: Session = Depends(get_session),
):
    """Add a product to the catalog."""
    db_product = ProductCatalog.model_validate(product)
    session.add(db_product)
    session.commit()
    session.refresh(db_product)
    logger.info(f"Added {product.name} to catalog")
    return db_product
