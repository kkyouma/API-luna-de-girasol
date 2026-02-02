import logging

from backend import get_all_inventory
from database import get_session
from fastapi import Depends, FastAPI
from models import InventoryResponse
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
def get_inventory(session: Session = Depends(get_session)):
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
