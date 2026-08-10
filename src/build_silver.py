from pathlib import Path

import duckdb


PROJECT_ROOT = Path(__file__).resolve().parents[1]

DATABASE_FILE = (
    PROJECT_ROOT
    / "data"
    / "warehouse"
    / "customer_value_radar.duckdb"
)

REFERENCE_FILE = (
    PROJECT_ROOT
    / "data"
    / "reference"
    / "stockcode_categories.csv"
)


connection = duckdb.connect(
    str(DATABASE_FILE)
)


# Table de référence des StockCode spéciaux

connection.execute(
    """
    CREATE OR REPLACE TABLE stockcode_categories AS
    SELECT *
    FROM read_csv_auto(?)
    """,
    [str(REFERENCE_FILE)]
)


# Création de la couche Silver

connection.execute(
    """
    CREATE OR REPLACE TABLE silver_transactions AS

    SELECT
        b.*,

        CASE
            WHEN b.Invoice LIKE 'C%' THEN TRUE
            ELSE FALSE
        END AS is_cancellation,

        CASE
            WHEN b.Quantity < 0 THEN TRUE
            ELSE FALSE
        END AS is_negative_quantity,

        CASE
            WHEN b.Price = 0 THEN TRUE
            ELSE FALSE
        END AS is_zero_price,

        CASE
            WHEN b.Price < 0 THEN TRUE
            ELSE FALSE
        END AS is_negative_price,

        CASE
            WHEN b."Customer ID" IS NULL THEN TRUE
            ELSE FALSE
        END AS is_missing_customer,

        CASE
            WHEN b.Description IS NULL THEN TRUE
            ELSE FALSE
        END AS is_missing_description,
        
        CASE
            WHEN r.stock_code IS NOT NULL THEN TRUE
            ELSE FALSE
        END AS is_special_stockcode,

        CASE
            WHEN COUNT(*) OVER (
                PARTITION BY
                    b.Invoice,
                    b.StockCode,
                    b.Description,
                    b.Quantity,
                    b.InvoiceDate,
                    b.Price,
                    b."Customer ID",
                    b.Country,
                    b.SourcePeriod
            ) > 1 THEN TRUE
            ELSE FALSE
        END AS is_repeated_row,

        COALESCE(
            r.category,
            'product'
        ) AS line_category,

        b.Quantity * b.Price AS raw_line_value

    FROM bronze_transactions AS b

    LEFT JOIN stockcode_categories AS r
        ON b.StockCode = r.stock_code
    """
)


row_count = connection.execute(
    """
    SELECT COUNT(*)
    FROM silver_transactions
    """
).fetchone()[0]

column_count = connection.execute(
    """
    SELECT COUNT(*)
    FROM pragma_table_info('silver_transactions')
    """
).fetchone()[0]


print("Table créée : silver_transactions")
print("Nombre de lignes :", row_count)
print("Nombre de colonnes :", column_count)

# Vérification des règles Silver

silver_check = connection.execute(
    """
    SELECT
        SUM(CASE WHEN is_cancellation THEN 1 ELSE 0 END),
        SUM(CASE WHEN is_negative_quantity THEN 1 ELSE 0 END),
        SUM(CASE WHEN is_zero_price THEN 1 ELSE 0 END),
        SUM(CASE WHEN is_negative_price THEN 1 ELSE 0 END),
        SUM(CASE WHEN is_missing_customer THEN 1 ELSE 0 END),
        SUM(CASE WHEN is_missing_description THEN 1 ELSE 0 END)
    FROM silver_transactions
    """
).fetchone()

print()
print("Vérification Silver")
print("Annulations C :", silver_check[0])
print("Quantités négatives :", silver_check[1])
print("Prix nuls :", silver_check[2])
print("Prix négatifs :", silver_check[3])
print("Customer ID manquants :", silver_check[4])
print("Descriptions manquantes :", silver_check[5])

# Vérification des catégories de lignes

category_check = connection.execute(
    """
    SELECT
        COUNT(
            CASE
                WHEN r.stock_code IS NOT NULL THEN 1
            END
        ) AS special_rows,

        COUNT(
            DISTINCT CASE
                WHEN r.stock_code IS NOT NULL THEN s.StockCode
            END
        ) AS special_codes,

        COUNT(
            CASE
                WHEN s.line_category IS NULL THEN 1
            END
        ) AS missing_categories

    FROM silver_transactions AS s

    LEFT JOIN stockcode_categories AS r
        ON s.StockCode = r.stock_code
    """
).fetchone()


print()
print("Vérification des StockCode spéciaux")
print("Lignes avec StockCode spécial :", category_check[0])
print("StockCode spéciaux distincts :", category_check[1])
print("Catégories manquantes :", category_check[2])

# Répartition des lignes par catégorie

category_counts = connection.execute(
    """
    SELECT
        line_category,
        COUNT(*) AS rows
    FROM silver_transactions
    GROUP BY line_category
    ORDER BY rows DESC
    """
).fetchall()


print()
print("Répartition des lignes par catégorie")

for category, rows in category_counts:
    print(category, ":", rows)

# Vérification des flags qualité

quality_flags_check = connection.execute(
    """
    SELECT
        SUM(
            CASE
                WHEN is_special_stockcode THEN 1
                ELSE 0
            END
        ),
        SUM(
            CASE
                WHEN is_repeated_row THEN 1
                ELSE 0
            END
        )
    FROM silver_transactions
    """
).fetchone()

print()
print("Vérification des flags qualité")
print("Lignes avec StockCode spécial :", quality_flags_check[0])
print("Lignes appartenant à un groupe répété :", quality_flags_check[1])

connection.close()