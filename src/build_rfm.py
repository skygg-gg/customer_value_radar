from pathlib import Path

import duckdb
import pandas as pd


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


# Date de référence RFM

last_purchase_date = connection.execute(
    """
    SELECT
        MAX(CAST(order_datetime AS DATE))
    FROM fact_orders
    WHERE has_product_sale = TRUE
    """
).fetchone()[0]

reference_date = (
    pd.Timestamp(last_purchase_date)
    + pd.Timedelta(days=1)
)


# Métriques RFM 

rfm = connection.execute(
    """
    SELECT
        customer_id,

        MAX(
            CASE
                WHEN has_product_sale = TRUE
                THEN order_datetime
            END
        ) AS last_purchase_datetime,

        SUM(
            CASE
                WHEN has_product_sale = TRUE
                THEN 1
                ELSE 0
            END
        ) AS frequency,

        ROUND(
            SUM(net_product_sales_value),
            2
        ) AS monetary

    FROM fact_orders

    WHERE customer_id IS NOT NULL

    GROUP BY customer_id

    HAVING SUM(
        CASE
            WHEN has_product_sale = TRUE
            THEN 1
            ELSE 0
        END
    ) > 0

    ORDER BY customer_id
    """
).df()


# Recency

rfm["last_purchase_datetime"] = pd.to_datetime(
    rfm["last_purchase_datetime"]
)

rfm["last_purchase_date"] = (
    rfm["last_purchase_datetime"]
    .dt.normalize()
)

rfm["recency"] = (
    reference_date.normalize()
    - rfm["last_purchase_date"]
).dt.days


# Score R

recency_percentile = (
    rfm["recency"]
    .rank(
        method="average",
        pct=True
    )
)

rfm["r_score"] = pd.cut(
    recency_percentile,
    bins=[0, 0.20, 0.40, 0.60, 0.80, 1.00],
    labels=[5, 4, 3, 2, 1],
    include_lowest=True
).astype(int)


# Score F

def frequency_score(frequency):
    if frequency == 1:
        return 1
    elif frequency == 2:
        return 2
    elif frequency <= 5:
        return 3
    elif frequency <= 10:
        return 4
    else:
        return 5


rfm["f_score"] = (
    rfm["frequency"]
    .apply(frequency_score)
)


# Score M

monetary_percentile = (
    rfm["monetary"]
    .rank(
        method="average",
        pct=True
    )
)

rfm["m_score"] = pd.cut(
    monetary_percentile,
    bins=[0, 0.20, 0.40, 0.60, 0.80, 1.00],
    labels=[1, 2, 3, 4, 5],
    include_lowest=True
).astype(int)


# Segmentation

def assign_segment(row):

    r = row["r_score"]
    f = row["f_score"]
    m = row["m_score"]

    if r >= 4 and f >= 4 and m >= 4:
        return "Champions"

    elif f >= 4 and m >= 3:
        return "Loyal"

    elif r >= 4 and f <= 3:
        return "Potential"

    elif r <= 2 and (f >= 3 or m >= 3):
        return "At Risk"

    elif r <= 2 and f <= 2 and m <= 2:
        return "Low Value"

    else:
        return "Regular"


rfm["segment"] = rfm.apply(
    assign_segment,
    axis=1
)


# Scores 

rfm["rfm_code"] = (
    rfm["r_score"].astype(str)
    + rfm["f_score"].astype(str)
    + rfm["m_score"].astype(str)
)

rfm["rfm_total_score"] = (
    rfm["r_score"]
    + rfm["f_score"]
    + rfm["m_score"]
)

rfm["rfm_reference_date"] = (
    reference_date.date()
)


# Colonnes finales

rfm_final = rfm[
    [
        "customer_id",
        "last_purchase_datetime",
        "recency",
        "frequency",
        "monetary",
        "r_score",
        "f_score",
        "m_score",
        "rfm_code",
        "rfm_total_score",
        "segment",
        "rfm_reference_date"
    ]
].copy()


# Sauvegarde DuckDB

connection.register(
    "rfm_dataframe",
    rfm_final
)

connection.execute(
    """
    CREATE OR REPLACE TABLE customer_rfm AS
    SELECT *
    FROM rfm_dataframe
    """
)

connection.unregister(
    "rfm_dataframe"
)


# Validation


rfm_check = connection.execute(
    """
    SELECT
        COUNT(*) AS rows,
        COUNT(DISTINCT customer_id) AS customers,
        MIN(recency) AS min_recency,
        MAX(recency) AS max_recency,
        MIN(rfm_total_score) AS min_score,
        MAX(rfm_total_score) AS max_score
    FROM customer_rfm
    """
).fetchone()


print("Table créée : customer_rfm")
print("Nombre de lignes :", rfm_check[0])
print("Clients distincts :", rfm_check[1])
print(
    "Grain customer valide :",
    rfm_check[0] == rfm_check[1]
)
print("Recency min :", rfm_check[2])
print("Recency max :", rfm_check[3])
print("Score RFM total min :", rfm_check[4])
print("Score RFM total max :", rfm_check[5])


print()
print("Répartition des segments")

segments = connection.execute(
    """
    SELECT
        segment,
        COUNT(*) AS customers
    FROM customer_rfm
    GROUP BY segment
    ORDER BY customers DESC
    """
).fetchall()

for segment, customers in segments:
    print(segment, ":", customers)


connection.close()