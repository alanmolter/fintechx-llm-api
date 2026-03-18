from app.core.security import validate_sql_guardrails


class TestSQLGuardrails:
    """Testes para validação dos guardrails de segurança SQL."""

    def test_valid_select_query(self):
        sql = "SELECT product_name, list_price FROM products ORDER BY list_price DESC"
        assert validate_sql_guardrails(sql) is True

    def test_valid_select_with_join(self):
        sql = """
            SELECT c.company, COUNT(o.id) AS TotalPedidos
            FROM customers c
            JOIN orders o ON c.id = o.customer_id
            GROUP BY c.company
        """
        assert validate_sql_guardrails(sql) is True

    def test_valid_cte_query(self):
        sql = """
            WITH vendas AS (
                SELECT order_id, SUM(unit_price * quantity) AS Total
                FROM order_details
                GROUP BY order_id
            )
            SELECT AVG(Total) AS TicketMedio FROM vendas
        """
        assert validate_sql_guardrails(sql) is True

    def test_valid_order_details_table(self):
        sql = "SELECT * FROM order_details LIMIT 10"
        assert validate_sql_guardrails(sql) is True

    def test_valid_invoices_table(self):
        sql = "SELECT id, amount_due FROM invoices"
        assert validate_sql_guardrails(sql) is True

    def test_valid_suppliers_table(self):
        sql = "SELECT company FROM suppliers"
        assert validate_sql_guardrails(sql) is True

    def test_valid_purchase_orders_table(self):
        sql = "SELECT id, supplier_id FROM purchase_orders"
        assert validate_sql_guardrails(sql) is True

    def test_block_drop_table(self):
        sql = "DROP TABLE customers"
        assert validate_sql_guardrails(sql) is False

    def test_block_delete(self):
        sql = "DELETE FROM orders WHERE id = 1"
        assert validate_sql_guardrails(sql) is False

    def test_block_update(self):
        sql = "UPDATE products SET list_price = 0"
        assert validate_sql_guardrails(sql) is False

    def test_block_insert(self):
        sql = "INSERT INTO customers (company) VALUES ('Hacker')"
        assert validate_sql_guardrails(sql) is False

    def test_block_alter(self):
        sql = "ALTER TABLE orders ADD COLUMN hack VARCHAR(255)"
        assert validate_sql_guardrails(sql) is False

    def test_block_truncate(self):
        sql = "TRUNCATE TABLE products"
        assert validate_sql_guardrails(sql) is False

    def test_block_query_without_allowed_tables(self):
        sql = "SELECT * FROM secret_table"
        assert validate_sql_guardrails(sql) is False

    def test_block_empty_query(self):
        assert validate_sql_guardrails("") is False
        assert validate_sql_guardrails(None) is False

    def test_block_non_select_start(self):
        sql = "SHOW TABLES"
        assert validate_sql_guardrails(sql) is False
