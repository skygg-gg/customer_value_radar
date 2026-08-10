from pathlib import Path

import duckdb


PROJECT_ROOT = Path(__file__).resolve().parents[1]

PARQUET_FILE = (
    PROJECT_ROOT
    / "data"
    / "interim"
    / "transactions_consolidated.parquet"
)

WAREHOUSE_DIR = PROJECT_ROOT / "data" / "warehouse"

DATABASE_FILE = (
    WAREHOUSE_DIR
    / "customer_value_radar.duckdb"
)


WAREHOUSE_DIR.mkdir(
    parents=True,
    exist_ok=True
)

connection = duckdb.connect(
    str(DATABASE_FILE)
)

connection.execute(
    """
    CREATE OR REPLACE TABLE bronze_transactions AS
    SELECT *
    FROM read_parquet(?)
    """,
    [str(PARQUET_FILE)]
)

row_count = connection.execute(
    """
    SELECT COUNT(*)
    FROM bronze_transactions
    """
).fetchone()[0]

column_count = connection.execute(
    """
    SELECT COUNT(*)
    FROM pragma_table_info('bronze_transactions')
    """
).fetchone()[0]

print("DuckDB créé :", DATABASE_FILE.name)
print("Table créée : bronze_transactions")
print("Nombre de lignes :", row_count)
print("Nombre de colonnes :", column_count)


# Vérification Parquet vs Bronze

parquet_check = connection.execute(
    """
    SELECT
        COUNT(*) AS rows,
        SUM(Quantity) AS total_quantity,
        SUM(Price) AS total_price,
        SUM(
            CASE
                WHEN "Customer ID" IS NULL THEN 1
                ELSE 0
            END
        ) AS missing_customer,
        MIN(InvoiceDate) AS min_date,
        MAX(InvoiceDate) AS max_date
    FROM read_parquet(?)
    """,
    [str(PARQUET_FILE)]
).fetchone()

bronze_check = connection.execute(
    """
    SELECT
        COUNT(*) AS rows,
        SUM(Quantity) AS total_quantity,
        SUM(Price) AS total_price,
        SUM(
            CASE
                WHEN "Customer ID" IS NULL THEN 1
                ELSE 0
            END
        ) AS missing_customer,
        MIN(InvoiceDate) AS min_date,
        MAX(InvoiceDate) AS max_date
    FROM bronze_transactions
    """
).fetchone()

print()
print("Vérification Parquet / Bronze")
print("Parquet :", parquet_check)
print("Bronze  :", bronze_check)
# Comparaison avec tolérance pour les nombres décimaux

same_rows = parquet_check[0] == bronze_check[0]
same_quantity = parquet_check[1] == bronze_check[1]

same_price = abs(
    parquet_check[2] - bronze_check[2]
) < 0.01

same_missing_customer = parquet_check[3] == bronze_check[3]
same_min_date = parquet_check[4] == bronze_check[4]
same_max_date = parquet_check[5] == bronze_check[5]

bronze_is_valid = (
    same_rows
    and same_quantity
    and same_price
    and same_missing_customer
    and same_min_date
    and same_max_date
)

print("Bronze valide :", bronze_is_valid)
connection.close()