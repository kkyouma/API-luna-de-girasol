import logging

from backend import add_to_catalog, get_all_inventory
from database import get_session
from fastapi import Depends, FastAPI
from schemas import InventoryResponse, ProductCatalogResponse
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


@app.get("/inventory", response_model=list[InventoryResponse], tags=["Inventory"])
def get_inventory(session: Session = Depends(get_session)) -> list[InventoryResponse]:
    """Get all inventory."""
    inventory = get_all_inventory(session)
    return [
        InventoryResponse(
            id=i.id,
            variant_name=i.variant_name,
            current_stock=i.current_stock,
            unit_price=i.unit_price,
        )
        for i in inventory
    ]


@app.post("/catalog", response_model=ProductCatalogResponse)
def add_catalog(
    name: str,
    category: str,
    description: str | None = None,
    care_instructions: str | None = None,
    session: Session = Depends(get_session),
) -> ProductCatalogResponse:
    product = add_to_catalog(
        session,
        name,
        category,
        description,
        care_instructions,
    )
    return ProductCatalogResponse(
        id=product.id,
        name=product.name,
        category=product.category,
        description=product.description,
        care_instructions=product.care_instructions,
    )
