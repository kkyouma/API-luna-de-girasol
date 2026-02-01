"""Centralized SQL queries for the florist database."""

# =============== ORDERS ===============

GET_PENDING_ORDERS = """
    SELECT id, order_date, total, notes 
    FROM sale_order 
    WHERE status = 'pending' 
    ORDER BY order_date ASC
"""

GET_ORDER_BY_ID = """
    SELECT id, customer_id, order_date, subtotal, total, status, notes 
    FROM sale_order 
    WHERE id = ?
"""

GET_ORDER_ITEMS = """
    SELECT
        soi.flower_id,
        f.name,
        f.color,
        soi.quantity,
        soi.unit_price,
        soi.subtotal
    FROM sale_order_item AS soi
    JOIN flower AS f ON soi.flower_id = f.id
    WHERE soi.sale_order_id = ?
"""

INSERT_ORDER = """
    INSERT INTO sale_order (customer_id, occasion_id, order_date, subtotal, total, status, notes)
    VALUES (?, ?, DATETIME('now'), ?, ?, 'pending', ?)
"""

INSERT_ORDER_ITEM = """
    INSERT INTO sale_order_item (sale_order_id, flower_id, quantity, unit_price, subtotal)
    VALUES (?, ?, ?, ?, ?)
"""

UPDATE_ORDER_STATUS = """
    UPDATE sale_order 
    SET status = ? 
    WHERE id = ?
"""

# =============== INVENTORY ===============
GET_ALL_CATALOG = """
    SELECT id, name, category, description
    FROM product_catalog
    ORDER BY name
"""

INSERT_CATALOG = """
    INSERT INTO product_catalog (name, category, description, care_instructions)
    VALUES (?, ?, ?, ?)
"""

GET_ALL_INVENTORY = """
    SELECT id, name, color, current_stock, unit_price
    FROM inventory_item 
    ORDER BY name
"""

GET_FLOWER_BY_ID = """
    SELECT id, name, color, current_stock, price 
    FROM flower 
    WHERE id = ?
"""

GET_INVENTORY_DETAILS = """
    SELECT iventory_id, product_name, variant_name, category, unit_price, current_stock
    FROM view_inventory_details 
    WHERE category = ?
"""

GET_AVAILABLE_STOCK = """
    SELECT 
        f.id,
        f.current_stock - COALESCE(
            (
                SELECT SUM(soi.quantity)
                FROM sale_order_item soi
                JOIN sale_order so ON soi.sale_order_id = so.id
                WHERE soi.flower_id = f.id AND so.status = 'pending'
            ), 0
        ) as available_stock
    FROM flower f
"""

UPDATE_STOCK_DEDUCT = """
    UPDATE flower 
    SET inventory_item = inventory_item - ? 
    WHERE id = ?
"""

UPDATE_STOCK_ADD = """
    UPDATE flower 
    SET inventory_item = inventory_item + ? 
    WHERE id = ?
"""

# =============== STOCK MOVEMENTS ===============

INSERT_STOCK_MOVEMENT = """
    INSERT INTO stock_movement (flower_id, movement_type, quantity, reference_id, reference_type, notes)
    VALUES (?, ?, ?, ?, ?, ?)
"""


GET_STOCK_MOVEMENTS = """
    SELECT id, flower_id, movement_type, quantity, reference_type, reference_id, notes, created_at
    FROM stock_movement
    ORDER BY created_at DESC
    LIMIT ?
"""

GET_STOCK_HISTORY = """
    WITH MovimientosDiarios AS (
        SELECT
            flower_id,
            DATE(created_at) as fecha,
            SUM(CASE
                WHEN movement_type IN ('in') THEN quantity
                WHEN movement_type IN ('out') THEN -quantity
                ELSE 0
            END) as cambio_diario
        FROM stock_movement
        GROUP BY flower_id, DATE(created_at)
    )
    SELECT
        f.name,
        md.fecha,
        SUM(md.cambio_diario) OVER (
            PARTITION BY md.flower_id
            ORDER BY md.fecha
        ) as stock_al_cierre
    FROM MovimientosDiarios md
    JOIN flowers f ON md.flower_id = f.id
    ORDER BY f.name, md.fecha;
"""

# =============== CUSTOMERS ===============

GET_ALL_CUSTOMERS = """
    SELECT id, name, phone, email 
    FROM customer 
    ORDER BY name
"""

GET_CUSTOMER_BY_ID = """
    SELECT id, name, phone, email 
    FROM customer 
    WHERE id = ?
"""

INSERT_CUSTOMER = """
    INSERT INTO customer (name, phone, email) 
    VALUES (?, ?, ?)
"""

UPDATE_CUSTOMER = """
    UPDATE customer 
    SET name = ?, phone = ?, email = ? 
    WHERE id = ?
"""

# =============== OCCASIONS ===============

GET_ALL_OCCASIONS = """
    SELECT id, name, description 
    FROM occasion 
    ORDER BY name
"""

GET_OCCASION_BY_ID = """
    SELECT id, name, description 
    FROM occasion 
    WHERE id = ?
"""

INSERT_OCCASION = """
    INSERT INTO occasion (name, description) 
    VALUES (?, ?)
"""

# =============== REPORTS ===============

GET_SALES_BY_DATE_RANGE = """
    SELECT 
        DATE(order_date) as date,
        COUNT(*) as total_orders,
        SUM(total) as total_sales
    FROM sale_order
    WHERE order_date BETWEEN ? AND ?
    GROUP BY DATE(order_date)
    ORDER BY date DESC
"""

GET_TOP_SELLING_FLOWERS = """
    SELECT 
        f.id,
        f.name,
        f.color,
        SUM(soi.quantity) as total_sold,
        SUM(soi.subtotal) as total_revenue
    FROM sale_order_item soi
    JOIN flower f ON soi.flower_id = f.id
    JOIN sale_order so ON soi.sale_order_id = so.id
    WHERE so.status = 'completed'
        AND so.order_date >= ?
    GROUP BY f.id, f.name, f.color
    ORDER BY total_sold DESC
    LIMIT ?
"""
