"""
Centralized SQL queries for the florist database
"""

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
    VALUES (?, ?, DATE('now'), ?, ?, 'pending', ?)
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

# =============== FLOWERS ===============

GET_ALL_FLOWERS = """
    SELECT id, name, color, current_stock, price 
    FROM flower 
    ORDER BY name
"""

GET_FLOWER_BY_ID = """
    SELECT id, name, color, current_stock, price 
    FROM flower 
    WHERE id = ?
"""

GET_FLOWER_STOCK = """
    SELECT current_stock 
    FROM flower 
    WHERE id = ?
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
    SET current_stock = current_stock - ? 
    WHERE id = ?
"""

UPDATE_STOCK_ADD = """
    UPDATE flower 
    SET current_stock = current_stock + ? 
    WHERE id = ?
"""

# =============== STOCK MOVEMENTS ===============

INSERT_STOCK_MOVEMENT = """
    INSERT INTO stock_movement (flower_id, movement_type, quantity, reference_id, reference_type, notes)
    VALUES (?, ?, ?, ?, ?, ?)
"""

GET_STOCK_MOVEMENTS = """
    SELECT id, flower_id, movement_type, quantity, movement_date, reference_id, reference_type, notes
    FROM stock_movement
    WHERE flower_id = ?
    ORDER BY movement_date DESC
    LIMIT ?
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
