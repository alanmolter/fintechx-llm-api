import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from app.core.security import validate_sql_guardrails


class TestSQLGuardrails:
    """Testes para validação dos guardrails de segurança SQL."""

    def test_valid_select_query(self):
        sql = "SELECT ProductName, UnitPrice FROM products ORDER BY UnitPrice DESC"
        assert validate_sql_guardrails(sql) is True

    def test_valid_select_with_join(self):
        sql = """
            SELECT c.CompanyName, COUNT(o.OrderID) AS TotalPedidos
            FROM customers c
            JOIN orders o ON c.CustomerID = o.CustomerID
            GROUP BY c.CompanyName
        """
        assert validate_sql_guardrails(sql) is True

    def test_valid_cte_query(self):
        sql = """
            WITH vendas AS (
                SELECT OrderID, SUM(UnitPrice * Quantity) AS Total
                FROM `order details`
                GROUP BY OrderID
            )
            SELECT AVG(Total) AS TicketMedio FROM vendas
        """
        assert validate_sql_guardrails(sql) is True

    def test_valid_order_details_table(self):
        sql = "SELECT * FROM `order details` LIMIT 10"
        assert validate_sql_guardrails(sql) is True

    def test_valid_categories_table(self):
        sql = "SELECT CategoryName FROM categories"
        assert validate_sql_guardrails(sql) is True

    def test_valid_suppliers_table(self):
        sql = "SELECT CompanyName FROM suppliers"
        assert validate_sql_guardrails(sql) is True

    def test_block_drop_table(self):
        sql = "DROP TABLE customers"
        assert validate_sql_guardrails(sql) is False

    def test_block_delete(self):
        sql = "DELETE FROM orders WHERE OrderID = 1"
        assert validate_sql_guardrails(sql) is False

    def test_block_update(self):
        sql = "UPDATE products SET UnitPrice = 0"
        assert validate_sql_guardrails(sql) is False

    def test_block_insert(self):
        sql = "INSERT INTO customers (CompanyName) VALUES ('Hacker')"
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
