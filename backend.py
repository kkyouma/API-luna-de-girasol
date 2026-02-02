import logging

from models import (
    InventoryItem,
)
from sqlmodel import Sequence, Session, select

logger = logging.getLogger(__name__)


def get_all_inventory(session: Session) -> Sequence[InventoryItem]:
    """Get all the inventory items."""
    statement = select(InventoryItem).order_by(InventoryItem.variant_name)
    items = session.exec(statement).all()
    logger.debug(f"Obtenidas {len(items)} flores del inventario")
    return items
