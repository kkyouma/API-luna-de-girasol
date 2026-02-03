import logging

from models import (
    InventoryItem,
    ProductCatalog,
)
from sqlmodel import Sequence, Session, select

logger = logging.getLogger(__name__)


def get_all_inventory(session: Session) -> Sequence[InventoryItem]:
    """Get all the inventory items."""
    statement = select(InventoryItem).order_by(InventoryItem.variant_name)
    items = session.exec(statement).all()
    logger.debug(f"Get {len(items)} items from the inventory")
    return items


def add_to_catalog(
    session: Session,
    name: str,
    category: str,
    description: str | None = None,
    care_instructions: str | None = None,
) -> ProductCatalog:
    """Add a new product to the catalog."""
    product = ProductCatalog(
        name=name,
        category=category,
        description=description,
        care_instructions=care_instructions,
    )
    session.add(product)
    session.commit()
    session.refresh(product)
    logger.info(f"Added {product.name} to catalog")
    return product
