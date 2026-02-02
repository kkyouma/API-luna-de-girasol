from datetime import datetime
from enum import Enum

from sqlmodel import Field, Relationship, SQLModel

# =============== ENUMS (Reemplazo de Literal) ================


class PurchaseOrderStatus(str, Enum):
    PENDING = "pending"
    DELIVERED = "delivered"
    CANCELLED = "cancelled"


class SaleOrderType(str, Enum):
    WALK_IN = "walk-in"
    ONLINE = "online"
    PHONE = "phone"


class SaleOrderStatus(str, Enum):
    PENDING = "pending"
    COMPLETED = "completed"
    CANCELLED = "cancelled"


class StockMovementType(str, Enum):
    IN = "in"
    OUT = "out"


class StockReferenceType(str, Enum):
    PURCHASE = "purchase"
    SALE = "sale"
    ADJUSTMENT = "adjustment"
    WASTE = "waste"
    PRODUCTION = "production"


# =============== MAIN TABLES ================


class ProductCatalog(SQLModel, table=True):
    __tablename__ = "product_catalog"

    id: int | None = Field(default=None, primary_key=True)
    name: str = Field(max_length=100, nullable=False)
    category: str = Field(max_length=50, nullable=False)
    description: str | None = Field(default=None, max_length=500)
    care_instructions: str | None = Field(default=None, max_length=500)
    created_at: datetime | None = Field(default=None)

    inventory_items: list["InventoryItem"] = Relationship(back_populates="product")


class InventoryItem(SQLModel, table=True):
    __tablename__ = "inventory_item"

    id: int | None = Field(default=None, primary_key=True)
    product_id: int = Field(foreign_key="product_catalog.id", nullable=False)

    variant_name: str = Field(nullable=False)
    sku: str | None = Field(default=None, unique=True)
    unit_cost: int = Field(nullable=False)
    unit_price: int = Field(nullable=False)

    current_stock: int = Field(default=0)
    reorder_level: int = Field(default=10)
    shelf_life_days: int | None = None
    is_active: bool = Field(default=True)

    created_at: datetime | None = Field(default=None)
    updated_at: datetime | None = Field(default=None)

    product: ProductCatalog = Relationship(back_populates="inventory_items")


class Supplier(SQLModel, table=True):
    __tablename__ = "supplier"

    id: int = Field(default=None, primary_key=True)
    name: str = Field(nullable=False)
    contact_person: str | None = None
    phone: str | None = None
    email: str | None = None
    address: str | None = None
    payment_terms: str | None = None
    rating: int = Field(default=3, ge=1, le=5)
    notes: str | None = None
    created_at: datetime | None = Field(default=None)

    purchase_orders: list["PurchaseOrder"] = Relationship(back_populates="supplier")


class PurchaseOrder(SQLModel, table=True):
    __tablename__ = "purchase_order"

    id: int | None = Field(default=None, primary_key=True)
    supplier_id: int = Field(foreign_key="supplier.id", nullable=False)

    order_date: datetime
    delivery_date: datetime | None = None
    total_cost: float
    status: PurchaseOrderStatus = Field(default=PurchaseOrderStatus.PENDING)
    notes: str | None = None
    created_at: datetime | None = Field(default=None)

    supplier: Supplier = Relationship(back_populates="purchase_orders")
    items: list["PurchaseOrderItem"] = Relationship(back_populates="purchase_order")


class PurchaseOrderItem(SQLModel, table=True):
    __tablename__ = "purchase_order_item"

    id: int | None = Field(default=None, primary_key=True)
    purchase_order_id: int = Field(foreign_key="purchase_order.id")
    inventory_item_id: int = Field(foreign_key="inventory_item.id")

    quantity: int
    unit_cost: float
    subtotal: float

    purchase_order: PurchaseOrder = Relationship(back_populates="items")


class Customer(SQLModel, table=True):
    __tablename__ = "customer"

    id: int | None = Field(default=None, primary_key=True)
    name: str | None = None
    phone: str | None = None
    email: str | None = None
    address: str | None = None
    birth_date: datetime | None = None

    total_purchases: int = Field(default=0)
    total_spent: float = Field(default=0)
    notes: str | None = None
    created_at: datetime | None = Field(default=None)


class Occasion(SQLModel, table=True):
    __tablename__ = "occasion"

    id: int | None = Field(default=None, primary_key=True)
    name: str = Field(nullable=False, unique=True)
    description: str | None = None
    seasonal_peak_months: str | None = None


class BouquetTemplate(SQLModel, table=True):
    __tablename__ = "bouquet_template"

    id: int | None = Field(default=None, primary_key=True)
    name: str = Field(nullable=False)
    description: str | None = None
    labor_cost: float = Field(default=0)
    base_price: float
    occasion_id: str | None = Field(foreign_key="occasion.id")
    is_active: bool = Field(default=True)
    created_at: datetime | None = Field(default=None)

    items: list["BouquetTemplateItem"] = Relationship(back_populates="bouquet")


class BouquetTemplateItem(SQLModel, table=True):
    __tablename__ = "bouquet_template_item"

    id: str | None = Field(default=None, primary_key=True)
    bouquet_template_id: int = Field(foreign_key="bouquet_template.id")
    inventory_item_id: int = Field(foreign_key="inventory_item.id")
    quantity: int

    bouquet: BouquetTemplate = Relationship(back_populates="items")


class SaleOrder(SQLModel, table=True):
    __tablename__ = "sale_order"

    id: int | None = Field(default=None, primary_key=True)
    customer_id: int | None = Field(foreign_key="customer.id")
    order_date: datetime
    order_type: SaleOrderType = Field(default=SaleOrderType.WALK_IN)
    occasion_id: int | None = Field(foreign_key="occasion.id")

    subtotal: float
    discount_percent: float = Field(default=0)
    discount_amount: float = Field(default=0)
    packaging_fee: float = Field(default=0)
    total: float

    status: SaleOrderStatus = Field(default=SaleOrderStatus.COMPLETED)
    notes: str | None = None
    created_at: datetime | None = Field(default=None)

    items: list["SaleOrderItem"] = Relationship(back_populates="sale_order")


class SaleOrderItem(SQLModel, table=True):
    __tablename__ = "sale_order_item"

    id: int | None = Field(default=None, primary_key=True)
    sale_order_id: int = Field(foreign_key="sale_order.id")

    inventory_item_id: int | None = Field(foreign_key="inventory_item.id")
    bouquet_template_id: int | None = Field(foreign_key="bouquet_template.id")

    quantity: int
    unit_price: float = Field(ge=0)
    subtotal: float
    description: str | None = None

    sale_order: SaleOrder = Relationship(back_populates="items")


class StockMovement(SQLModel, table=True):
    __tablename__ = "stock_movement"

    id: int | None = Field(default=None, primary_key=True)
    inventory_item_id: int = Field(foreign_key="inventory_item.id")

    movement_type: StockMovementType
    quantity: int = Field(gt=0)
    reference_type: StockReferenceType
    reference_id: int | None = None
    notes: str | None = None
    created_at: datetime = Field(default=None)


# ============= API MODELS =================


class InventoryItemBase(SQLModel):
    variant_name: str
    current_stock: int
    unit_price: int


class InventoryResponse(InventoryItemBase):
    id: int
