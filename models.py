from datetime import datetime
from enum import StrEnum

from sqlmodel import Field, Relationship, SQLModel

# =============== ENUMS ================


class PurchaseOrderStatus(StrEnum):
    PENDING = "pending"
    DELIVERED = "delivered"
    CANCELLED = "cancelled"


class SaleOrderType(StrEnum):
    WALK_IN = "walk-in"
    ONLINE = "online"
    PHONE = "phone"


class SaleOrderStatus(StrEnum):
    PENDING = "pending"
    COMPLETED = "completed"
    CANCELLED = "cancelled"


class StockMovementType(StrEnum):
    IN = "in"
    OUT = "out"


class StockReferenceType(StrEnum):
    PURCHASE = "purchase"
    SALE = "sale"
    ADJUSTMENT = "adjustment"
    WASTE = "waste"
    PRODUCTION = "production"


# =============== PRODUCT CATALOG ================


class ProductCatalogBase(SQLModel):
    name: str = Field(max_length=100)
    category: str = Field(max_length=50)
    description: str | None = Field(default=None, max_length=500)
    care_instructions: str | None = Field(default=None, max_length=500)


class ProductCatalog(ProductCatalogBase, table=True):
    __tablename__ = "product_catalog"

    id: int | None = Field(default=None, primary_key=True)
    created_at: datetime | None = Field(
        default=None, sa_column_kwargs={"server_default": "current_timestamp"}
    )

    inventory_items: list["InventoryItem"] = Relationship(back_populates="product")


class ProductCatalogCreate(ProductCatalogBase):
    pass


class ProductCatalogRead(ProductCatalogBase):
    id: int
    created_at: datetime | None = None


class ProductCatalogReadWithInventory(ProductCatalogRead):
    inventory_items: list["InventoryItemRead"] = []


# =============== INVENTORY ITEM ================


class InventoryItemBase(SQLModel):
    variant_name: str
    sku: str | None = None
    unit_cost: int
    unit_price: int
    current_stock: int = 0
    reorder_level: int = 10
    shelf_life_days: int | None = None
    is_active: bool = True


class InventoryItem(InventoryItemBase, table=True):
    __tablename__ = "inventory_item"

    id: int | None = Field(default=None, primary_key=True)
    product_id: int = Field(foreign_key="product_catalog.id")
    sku: str | None = Field(default=None, unique=True)
    created_at: datetime | None = Field(
        default=None,
        sa_column_kwargs={"server_default": "current_timestamp"},
    )
    updated_at: datetime | None = Field(
        default=None,
        sa_column_kwargs={"server_default": "current_timestamp"},
    )

    product: ProductCatalog = Relationship(back_populates="inventory_items")


class InventoryItemCreate(InventoryItemBase):
    product_id: int


class InventoryItemRead(InventoryItemBase):
    id: int
    product_id: int
    created_at: datetime | None = None
    updated_at: datetime | None = None


class InventoryItemUpdate(SQLModel):
    variant_name: str | None = None
    sku: str | None = None
    unit_cost: int | None = None
    unit_price: int | None = None
    current_stock: int | None = None
    reorder_level: int | None = None
    shelf_life_days: int | None = None
    is_active: bool | None = None


# =============== SUPPLIER ================


class SupplierBase(SQLModel):
    name: str
    contact_person: str | None = None
    phone: str | None = None
    email: str | None = None
    address: str | None = None
    payment_terms: str | None = None
    rating: int = Field(default=3, ge=1, le=5)
    notes: str | None = None


class Supplier(SupplierBase, table=True):
    __tablename__ = "supplier"

    id: int | None = Field(default=None, primary_key=True)
    created_at: datetime | None = Field(
        default=None, sa_column_kwargs={"server_default": "current_timestamp"}
    )

    purchase_orders: list["PurchaseOrder"] = Relationship(back_populates="supplier")


class SupplierCreate(SupplierBase):
    pass


class SupplierRead(SupplierBase):
    id: int
    created_at: datetime


class SupplierUpdate(SQLModel):
    name: str | None = None
    contact_person: str | None = None
    phone: str | None = None
    email: str | None = None
    address: str | None = None
    payment_terms: str | None = None
    rating: int | None = Field(default=None, ge=1, le=5)
    notes: str | None = None


# =============== PURCHASE ORDER ================


class PurchaseOrderBase(SQLModel):
    order_date: datetime
    delivery_date: datetime | None = None
    total_cost: float
    status: PurchaseOrderStatus = PurchaseOrderStatus.PENDING
    notes: str | None = None


class PurchaseOrder(PurchaseOrderBase, table=True):
    __tablename__ = "purchase_order"

    id: int | None = Field(default=None, primary_key=True)
    supplier_id: int = Field(foreign_key="supplier.id")
    created_at: datetime | None = Field(
        default=None, sa_column_kwargs={"server_default": "current_timestamp"}
    )

    supplier: Supplier = Relationship(back_populates="purchase_orders")
    items: list["PurchaseOrderItem"] = Relationship(back_populates="purchase_order")


class PurchaseOrderCreate(PurchaseOrderBase):
    supplier_id: int
    items: list["PurchaseOrderItemCreate"] = []


class PurchaseOrderRead(PurchaseOrderBase):
    id: int
    supplier_id: int
    created_at: datetime


class PurchaseOrderReadWithDetails(PurchaseOrderRead):
    supplier: SupplierRead
    items: list["PurchaseOrderItemRead"] = []


# =============== PURCHASE ORDER ITEM ================


class PurchaseOrderItemBase(SQLModel):
    quantity: int
    unit_cost: float
    subtotal: float


class PurchaseOrderItem(PurchaseOrderItemBase, table=True):
    __tablename__ = "purchase_order_item"

    id: int | None = Field(default=None, primary_key=True)
    purchase_order_id: int = Field(foreign_key="purchase_order.id")
    inventory_item_id: int = Field(foreign_key="inventory_item.id")

    purchase_order: PurchaseOrder = Relationship(back_populates="items")


class PurchaseOrderItemCreate(PurchaseOrderItemBase):
    inventory_item_id: int


class PurchaseOrderItemRead(PurchaseOrderItemBase):
    id: int
    purchase_order_id: int
    inventory_item_id: int


# =============== CUSTOMER ================


class CustomerBase(SQLModel):
    name: str | None = None
    phone: str | None = None
    email: str | None = None
    address: str | None = None
    birth_date: datetime | None = None
    notes: str | None = None


class Customer(CustomerBase, table=True):
    __tablename__ = "customer"

    id: int | None = Field(default=None, primary_key=True)
    total_purchases: int = Field(default=0)
    total_spent: float = Field(default=0)
    created_at: datetime | None = Field(
        default=None, sa_column_kwargs={"server_default": "current_timestamp"}
    )


class CustomerCreate(CustomerBase):
    pass


class CustomerRead(CustomerBase):
    id: int
    total_purchases: int
    total_spent: float
    created_at: datetime


class CustomerUpdate(SQLModel):
    name: str | None = None
    phone: str | None = None
    email: str | None = None
    address: str | None = None
    birth_date: datetime | None = None
    notes: str | None = None


# =============== OCCASION ================


class OccasionBase(SQLModel):
    name: str
    description: str | None = None
    seasonal_peak_months: str | None = None


class Occasion(OccasionBase, table=True):
    __tablename__ = "occasion"

    id: int | None = Field(default=None, primary_key=True)
    name: str = Field(unique=True)


class OccasionCreate(OccasionBase):
    pass


class OccasionRead(OccasionBase):
    id: int


# =============== BOUQUET TEMPLATE ================


class BouquetTemplateBase(SQLModel):
    name: str
    description: str | None = None
    labor_cost: float = 0
    base_price: float
    is_active: bool = True


class BouquetTemplate(BouquetTemplateBase, table=True):
    __tablename__ = "bouquet_template"

    id: int | None = Field(default=None, primary_key=True)
    occasion_id: int | None = Field(foreign_key="occasion.id")
    created_at: datetime | None = Field(
        default=None, sa_column_kwargs={"server_default": "current_timestamp"}
    )

    items: list["BouquetTemplateItem"] = Relationship(back_populates="bouquet")


class BouquetTemplateCreate(BouquetTemplateBase):
    occasion_id: int | None = None
    items: list["BouquetTemplateItemCreate"] = []


class BouquetTemplateRead(BouquetTemplateBase):
    id: int
    occasion_id: int | None
    created_at: datetime


class BouquetTemplateReadWithItems(BouquetTemplateRead):
    items: list["BouquetTemplateItemRead"] = []


# =============== BOUQUET TEMPLATE ITEM ================


class BouquetTemplateItemBase(SQLModel):
    quantity: int


class BouquetTemplateItem(BouquetTemplateItemBase, table=True):
    __tablename__ = "bouquet_template_item"

    id: int | None = Field(default=None, primary_key=True)
    bouquet_template_id: int = Field(foreign_key="bouquet_template.id")
    inventory_item_id: int = Field(foreign_key="inventory_item.id")

    bouquet: BouquetTemplate = Relationship(back_populates="items")


class BouquetTemplateItemCreate(BouquetTemplateItemBase):
    inventory_item_id: int


class BouquetTemplateItemRead(BouquetTemplateItemBase):
    id: int
    bouquet_template_id: int
    inventory_item_id: int


# =============== SALE ORDER ================


class SaleOrderBase(SQLModel):
    order_date: datetime
    order_type: str = SaleOrderType.WALK_IN.value
    subtotal: float
    discount_percent: float = 0
    discount_amount: float = 0
    packaging_fee: float = 0
    total: float
    status: str = SaleOrderStatus.COMPLETED.value
    notes: str | None = None


class SaleOrder(SaleOrderBase, table=True):
    __tablename__ = "sale_order"

    id: int | None = Field(default=None, primary_key=True)
    customer_id: int | None = Field(foreign_key="customer.id")
    occasion_id: int | None = Field(foreign_key="occasion.id")
    created_at: datetime | None = Field(
        default=None,
        sa_column_kwargs={"server_default": "current_timestamp"},
    )

    items: list["SaleOrderItem"] = Relationship(back_populates="sale_order")


class SaleOrderCreate(SaleOrderBase):
    order_type: SaleOrderType = SaleOrderType.WALK_IN
    status: SaleOrderStatus = SaleOrderStatus.COMPLETED
    customer_id: int | None = None
    occasion_id: int | None = None
    items: list["SaleOrderItemCreate"] = []


class SaleOrderRead(SaleOrderBase):
    id: int
    customer_id: int | None
    occasion_id: int | None
    created_at: datetime


class SaleOrderReadWithDetails(SaleOrderRead):
    items: list["SaleOrderItemRead"] = []


# =============== SALE ORDER ITEM ================


class SaleOrderItemBase(SQLModel):
    quantity: int
    unit_price: float | None = Field(default=None, ge=0)
    subtotal: float | None = None
    description: str | None = None


class SaleOrderItem(SaleOrderItemBase, table=True):
    __tablename__ = "sale_order_item"

    id: int | None = Field(default=None, primary_key=True)
    sale_order_id: int = Field(foreign_key="sale_order.id")
    inventory_item_id: int | None = Field(foreign_key="inventory_item.id")
    bouquet_template_id: int | None = Field(foreign_key="bouquet_template.id")

    sale_order: SaleOrder = Relationship(back_populates="items")


class SaleOrderItemCreate(SaleOrderItemBase):
    inventory_item_id: int | None = None
    bouquet_template_id: int | None = None


class SaleOrderItemRead(SaleOrderItemBase):
    id: int
    sale_order_id: int
    inventory_item_id: int | None
    bouquet_template_id: int | None


# =============== STOCK MOVEMENT ================


class StockMovementBase(SQLModel):
    movement_type: str = StockMovementType.IN.value
    quantity: int = Field(gt=0)
    reference_type: str = StockReferenceType.SALE.value
    reference_id: int | None = None
    notes: str | None = None


class StockMovement(StockMovementBase, table=True):
    __tablename__ = "stock_movement"

    id: int | None = Field(default=None, primary_key=True)
    inventory_item_id: int = Field(foreign_key="inventory_item.id")
    created_at: datetime | None = Field(
        default=None,
        sa_column_kwargs={"server_default": "current_timestamp"},
    )


class StockMovementCreate(StockMovementBase):
    movement_type: StockMovementType = StockMovementType.IN
    reference_type: StockReferenceType = StockReferenceType.SALE
    inventory_item_id: int


class StockMovementRead(StockMovementBase):
    id: int
    inventory_item_id: int
    created_at: datetime
