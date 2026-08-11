from pathlib import Path
import duckdb

ROOT = Path(__file__).resolve().parents[1]

DATABASE = (
    ROOT
    / "data"
    / "warehouse"
    / "customer_value_radar.duckdb"
)

OUTPUT = ROOT / "data" / "tableau"
OUTPUT.mkdir(parents=True, exist_ok=True)

con = duckdb.connect(
    str(DATABASE),
    read_only=True
)


# Commandes 
# (une ligne par facture)

con.execute(
    f"""
    COPY (
        SELECT
            Invoice AS invoice,
            order_datetime,
            customer_id,
            country,
            line_count,
            distinct_stockcodes,
            product_sale_quantity,
            product_cancellation_quantity,
            gross_product_sales_value,
            product_cancellation_value,
            net_product_sales_value,
            is_cancellation,
            has_product_sale,
            has_product_cancellation
        FROM fact_orders
        ORDER BY order_datetime
    )
    TO '{OUTPUT / "tableau_orders.csv"}'
    (HEADER, DELIMITER ',')
    """
)


# Clients : Customer Value / RFM
# (une ligne par client)


con.execute(
    f"""
    COPY (
        SELECT
            customer_id,
            last_purchase_datetime,
            recency,
            CAST(frequency AS BIGINT) AS frequency,
            monetary,
            r_score,
            f_score,
            m_score,
            rfm_code,
            rfm_total_score,
            segment,
            rfm_reference_date
        FROM customer_rfm
        ORDER BY customer_id
    )
    TO '{OUTPUT / "tableau_rfm.csv"}'
    (HEADER, DELIMITER ',')
    """
)



# Produits : Sales & Cancellations
# (mois x pays x produit)


con.execute(
    f"""
    COPY (
        SELECT
            DATE_TRUNC('month', fol.InvoiceDate) AS month,
            fol.Country AS country,
            fol.StockCode AS stock_code,
            dp.product_description,

            SUM(fol.gross_product_sales_value)
                AS gross_product_sales_value,

            SUM(fol.product_cancellation_value)
                AS product_cancellation_value,

            SUM(fol.net_product_sales_value)
                AS net_product_sales_value,

            SUM(
                CASE
                    WHEN fol.is_product_sale = TRUE
                    THEN fol.Quantity
                    ELSE 0
                END
            ) AS product_sale_quantity,

            SUM(
                CASE
                    WHEN fol.is_product_cancellation = TRUE
                    THEN fol.Quantity
                    ELSE 0
                END
            ) AS product_cancellation_quantity,

            COUNT(
                DISTINCT CASE
                    WHEN fol.is_product_sale = TRUE
                    THEN fol.Invoice
                END
            ) AS purchase_invoices,

            COUNT(
                DISTINCT CASE
                    WHEN fol.is_product_cancellation = TRUE
                    THEN fol.Invoice
                END
            ) AS cancellation_invoices

        FROM fact_order_lines fol

        LEFT JOIN dim_products dp
            ON fol.StockCode = dp.stock_code

        WHERE fol.line_category = 'product'

        GROUP BY
            1, 2, 3, 4

        ORDER BY
            1, 2, 3
    )
    TO '{OUTPUT / "tableau_products_monthly.csv"}'
    (HEADER, DELIMITER ',')
    """
)


con.close()

print("Exports Tableau créés :")
print("- tableau_orders.csv")
print("- tableau_rfm.csv")
print("- tableau_products_monthly.csv")