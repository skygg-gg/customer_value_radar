from pathlib import Path

import duckdb


PROJECT_ROOT = Path(__file__).resolve().parents[1]

DATABASE_FILE = (
    PROJECT_ROOT
    / "data"
    / "warehouse"
    / "customer_value_radar.duckdb"
)


connection = duckdb.connect(
    str(DATABASE_FILE)
)


# Création de fact_order_lines

connection.execute(
    """
    CREATE OR REPLACE TABLE fact_order_lines AS

    SELECT
        Invoice,
        StockCode,
        Description,
        Quantity,
        InvoiceDate,
        Price,
        "Customer ID",
        Country,
        SourcePeriod,

        line_category,

        is_cancellation,
        is_negative_quantity,
        is_zero_price,
        is_negative_price,
        is_missing_customer,
        is_missing_description,
        is_special_stockcode,
        is_repeated_row,

        raw_line_value,

        CASE
            WHEN line_category = 'product'
                AND is_cancellation = FALSE
                AND Quantity > 0
                AND Price > 0
            THEN TRUE
            ELSE FALSE
        END AS is_product_sale,

        CASE
            WHEN line_category = 'product'
                AND is_cancellation = TRUE
                AND Quantity < 0
                AND Price > 0
            THEN TRUE
            ELSE FALSE
        END AS is_product_cancellation,

        CASE
            WHEN line_category = 'product'
                AND is_cancellation = FALSE
                AND Quantity > 0
                AND Price > 0
            THEN raw_line_value
            ELSE 0
        END AS gross_product_sales_value,

        CASE
            WHEN line_category = 'product'
                AND is_cancellation = TRUE
                AND Quantity < 0
                AND Price > 0
            THEN raw_line_value
            ELSE 0
        END AS product_cancellation_value,

        CASE
            WHEN (
                line_category = 'product'
                AND is_cancellation = FALSE
                AND Quantity > 0
                AND Price > 0
            )
            OR (
                line_category = 'product'
                AND is_cancellation = TRUE
                AND Quantity < 0
                AND Price > 0
            )
            THEN raw_line_value
            ELSE 0
        END AS net_product_sales_value

    FROM silver_transactions
    """
)


# Vérification

fact_check = connection.execute(
    """
    SELECT
        COUNT(*) AS rows,

        SUM(
            CASE
                WHEN is_product_sale THEN 1
                ELSE 0
            END
        ) AS product_sale_rows,

        SUM(
            CASE
                WHEN is_product_cancellation THEN 1
                ELSE 0
            END
        ) AS product_cancellation_rows,

        ROUND(
            SUM(gross_product_sales_value),
            2
        ) AS gross_product_sales,

        ROUND(
            SUM(product_cancellation_value),
            2
        ) AS product_cancellations,

        ROUND(
            SUM(net_product_sales_value),
            2
        ) AS net_product_sales

    FROM fact_order_lines
    """
).fetchone()


print("Table créée : fact_order_lines")
print("Nombre de lignes :", fact_check[0])
print("Lignes de ventes produit :", fact_check[1])
print("Lignes d'annulation produit :", fact_check[2])
print("Valeur brute des ventes produit :", fact_check[3])
print("Valeur des annulations produit :", fact_check[4])
print("Valeur nette des ventes produit :", fact_check[5])

# Création de fact_orders

connection.execute(
    """
    CREATE OR REPLACE TABLE fact_orders AS

    SELECT
        Invoice,

        MIN(InvoiceDate) AS order_datetime,
        MAX(InvoiceDate) AS last_line_datetime,

        MAX("Customer ID") AS customer_id,
        MAX(Country) AS country,
        MIN(SourcePeriod) AS source_period,

        COUNT(*) AS line_count,
        COUNT(DISTINCT StockCode) AS distinct_stockcodes,

        SUM(Quantity) AS total_quantity,
        SUM(raw_line_value) AS raw_order_value,

        SUM(
            CASE
                WHEN is_product_sale THEN Quantity
                ELSE 0
            END
        ) AS product_sale_quantity,

        SUM(
            CASE
                WHEN is_product_cancellation THEN Quantity
                ELSE 0
            END
        ) AS product_cancellation_quantity,

        SUM(gross_product_sales_value)
            AS gross_product_sales_value,

        SUM(product_cancellation_value)
            AS product_cancellation_value,

        SUM(net_product_sales_value)
            AS net_product_sales_value,

        BOOL_OR(is_cancellation)
            AS is_cancellation,

        BOOL_OR(is_product_sale)
            AS has_product_sale,

        BOOL_OR(is_product_cancellation)
            AS has_product_cancellation

    FROM fact_order_lines

    GROUP BY Invoice
    """
)

# Vérification de fact_orders

orders_check = connection.execute(
    """
    SELECT
        COUNT(*) AS orders,
        ROUND(
            SUM(gross_product_sales_value),
            2
        ) AS gross_product_sales,
        ROUND(
            SUM(product_cancellation_value),
            2
        ) AS product_cancellations,
        ROUND(
            SUM(net_product_sales_value),
            2
        ) AS net_product_sales
    FROM fact_orders
    """
).fetchone()


expected_orders = connection.execute(
    """
    SELECT COUNT(DISTINCT Invoice)
    FROM fact_order_lines
    """
).fetchone()[0]


print()
print("Table créée : fact_orders")
print("Nombre de factures :", orders_check[0])
print("Nombre attendu :", expected_orders)
print(
    "Grain Invoice valide :",
    orders_check[0] == expected_orders
)

print(
    "Valeur brute des ventes produit :",
    orders_check[1]
)

print(
    "Valeur des annulations produit :",
    orders_check[2]
)

print(
    "Valeur nette des ventes produit :",
    orders_check[3]
)

# Création de dim_customers

connection.execute(
    """
    CREATE OR REPLACE TABLE dim_customers AS

    SELECT
        customer_id,

        MIN(order_datetime)
            AS first_activity_datetime,

        MAX(order_datetime)
            AS last_activity_datetime,

        COUNT(*)
            AS invoice_count,

        COUNT(
            DISTINCT country
        ) AS distinct_countries,

        CASE
            WHEN COUNT(DISTINCT country) > 1
            THEN TRUE
            ELSE FALSE
        END AS is_multi_country,

        ARG_MAX(
            country,
            order_datetime
        ) AS latest_country

    FROM fact_orders

    WHERE customer_id IS NOT NULL

    GROUP BY customer_id
    """
)

# Vérification de dim_customers

customers_check = connection.execute(
    """
    SELECT
        COUNT(*) AS customers,
        COUNT(DISTINCT customer_id)
            AS distinct_customers,
        SUM(
            CASE
                WHEN is_multi_country THEN 1
                ELSE 0
            END
        ) AS multi_country_customers,
        MIN(first_activity_datetime)
            AS first_activity,
        MAX(last_activity_datetime)
            AS last_activity
    FROM dim_customers
    """
).fetchone()


print()
print("Table créée : dim_customers")
print("Nombre de clients :", customers_check[0])
print(
    "Customer ID distincts :",
    customers_check[1]
)
print(
    "Grain customer valide :",
    customers_check[0] == customers_check[1]
)
print(
    "Clients observés dans plusieurs pays :",
    customers_check[2]
)
print(
    "Première activité :",
    customers_check[3]
)
print(
    "Dernière activité :",
    customers_check[4]
)

connection.close()