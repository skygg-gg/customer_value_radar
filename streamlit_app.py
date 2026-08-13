from pathlib import Path

import duckdb
import streamlit as st


# Config

ROOT = Path(__file__).resolve().parent
DB_PATH = ROOT / "data" / "warehouse" / "customer_value_radar.duckdb"

st.set_page_config(
    page_title="Customer Value Radar",
    page_icon="📊",
    layout="wide",
)

st.title("Customer Value Radar")
st.caption("E-commerce performance and customer value analysis")


if not DB_PATH.exists():
    st.error("Database not found. Run `python src/run_pipeline.py` first.")
    st.stop()


con = duckdb.connect(str(DB_PATH), read_only=True)


# 

def query(sql, params=None):
    if params:
        return con.execute(sql, params).df()

    return con.execute(sql).df()


def metric_row(metrics):
    columns = st.columns(len(metrics))

    for column, (label, value) in zip(columns, metrics):
        column.metric(label, value)


# Executive Overview

def executive_page():

    st.header("Executive Overview")

    kpi = query("""
        SELECT
            SUM(net_product_sales_value) AS net_sales,
            COUNT(*) FILTER (
                WHERE has_product_sale
            ) AS purchase_orders,
            SUM(gross_product_sales_value)
                / COUNT(*) FILTER (
                    WHERE has_product_sale
                ) AS average_order_value,
            COUNT(DISTINCT customer_id) FILTER (
                WHERE has_product_sale
            ) AS customers
        FROM fact_orders
    """).iloc[0]

    metric_row([
        ("Net Product Sales", f"£{kpi.net_sales / 1_000_000:.2f}M"),
        ("Purchase Orders", f"{kpi.purchase_orders:,.0f}"),
        ("Average Order Value", f"£{kpi.average_order_value:,.2f}"),
        ("Identified Customers", f"{kpi.customers:,.0f}"),
    ])

    st.divider()

    monthly = query("""
        SELECT
            DATE_TRUNC('month', order_datetime) AS month,
            SUM(net_product_sales_value) AS net_sales,
            COUNT(*) FILTER (
                WHERE has_product_sale
            ) AS purchase_orders
        FROM fact_orders
        GROUP BY 1
        ORDER BY 1
    """)

    st.subheader("Monthly Net Product Sales")
    st.line_chart(monthly, x="month", y="net_sales")

    st.caption(
        "Data available through 09 Dec 2011 — "
        "December 2011 is therefore incomplete."
    )

    left, right = st.columns(2)

    with left:
        st.subheader("Monthly Purchase Orders")
        st.line_chart(
            monthly,
            x="month",
            y="purchase_orders",
        )

    countries = query("""
        SELECT
            country,
            SUM(net_product_sales_value) AS net_sales
        FROM fact_orders
        GROUP BY country
        ORDER BY net_sales DESC
        LIMIT 10
    """)

    with right:
        st.subheader("Top 10 Countries by Net Product Sales")
        st.bar_chart(
            countries,
            x="country",
            y="net_sales",
        )


# Customer Value & RFM

def rfm_page():

    st.header("Customer Value & RFM")

    rfm = query("""
        SELECT *
        FROM customer_rfm
    """)

    champions = rfm["segment"].eq("Champions")
    at_risk = rfm["segment"].eq("At Risk")

    metric_row([
        ("RFM Customers", f"{len(rfm):,}"),
        ("Champions", f"{champions.sum():,}"),
        (
            "Champions Value Share",
            f"{rfm.loc[champions, 'monetary'].sum() / rfm['monetary'].sum():.1%}",
        ),
        ("At Risk Customers", f"{at_risk.sum():,}"),
    ])

    st.divider()

    segments = query("""
        SELECT
            segment,
            COUNT(*) AS customers,
            AVG(recency) AS average_recency,
            AVG(frequency) AS average_frequency,
            AVG(monetary) AS average_monetary,
            SUM(monetary) AS total_monetary
        FROM customer_rfm
        GROUP BY segment
    """)

    segments["value_share"] = (
        segments["total_monetary"]
        / segments["total_monetary"].sum()
    )

    left, right = st.columns(2)

    with left:
        st.subheader("Customers by RFM Segment")

        st.bar_chart(
            segments.sort_values("customers", ascending=False),
            x="segment",
            y="customers",
            horizontal=True,
        )

    with right:
        st.subheader("Customer Value Share by RFM Segment")

        st.bar_chart(
            segments.sort_values("value_share", ascending=False),
            x="segment",
            y="value_share",
            horizontal=True,
        )

    st.divider()

    st.subheader("RFM Segment Profile")

    st.scatter_chart(
        segments,
        x="average_recency",
        y="average_frequency",
        color="segment",
        size="average_monetary",
        x_label="Average Recency (days)",
        y_label="Average Purchase Frequency",
        height=500,
    )

    st.caption("Bubble size represents average monetary value.")

    st.divider()

    st.subheader("Customer Explorer")

    segment = st.selectbox(
        "Select a customer segment",
        ["All"] + sorted(rfm["segment"].unique().tolist()),
    )

    customers = rfm.copy()

    if segment != "All":
        customers = customers[
            customers["segment"] == segment
        ]

    customers = customers[
        [
            "customer_id",
            "recency",
            "frequency",
            "monetary",
            "rfm_total_score",
            "segment",
        ]
    ].sort_values("monetary", ascending=False)

    st.dataframe(
        customers,
        hide_index=True,
        width="stretch",
    )


# Sales & Cancellations

def sales_page():

    st.header("Sales & Cancellations")

    kpi = query("""
        SELECT
            SUM(gross_product_sales_value) AS gross_sales,
            -SUM(product_cancellation_value) AS cancellations,
            -SUM(product_cancellation_value)
                / SUM(gross_product_sales_value) AS cancellation_rate,
            COUNT(DISTINCT Invoice) FILTER (
                WHERE has_product_cancellation
            ) AS cancellation_invoices
        FROM fact_orders
    """).iloc[0]

    metric_row([
        ("Gross Product Sales", f"£{kpi.gross_sales / 1_000_000:.2f}M"),
        ("Cancellation Value", f"£{kpi.cancellations / 1_000_000:.2f}M"),
        ("Cancellation Rate", f"{kpi.cancellation_rate:.1%}"),
        ("Cancellation Invoices", f"{kpi.cancellation_invoices:,.0f}"),
    ])

    st.divider()

    monthly = query("""
        SELECT
            DATE_TRUNC('month', order_datetime) AS month,
            SUM(gross_product_sales_value) / 1000000 AS gross_sales_m,
            100 * -SUM(product_cancellation_value)
                / SUM(gross_product_sales_value) AS cancellation_rate
        FROM fact_orders
        GROUP BY 1
        ORDER BY 1
    """)

    left, right = st.columns(2)

    with left:
        st.subheader("Monthly Gross Product Sales")

        st.bar_chart(
            monthly,
            x="month",
            y="gross_sales_m",
            y_label="Gross Sales (£M)",
        )

    with right:
        st.subheader("Monthly Cancellation Rate")

        st.line_chart(
            monthly,
            x="month",
            y="cancellation_rate",
            y_label="Cancellation Rate (%)",
        )

    st.caption(
        "Data available through 09 Dec 2011 — "
        "December 2011 is therefore incomplete."
    )

    st.divider()

    products = query("""
        SELECT
            fol.StockCode AS stock_code,
            COALESCE(
                dp.product_description,
                fol.StockCode
            ) AS product,
            SUM(fol.gross_product_sales_value) AS gross_sales,
            -SUM(fol.product_cancellation_value) AS cancellation_value,
            SUM(fol.net_product_sales_value) AS net_sales
        FROM fact_order_lines fol

        LEFT JOIN dim_products dp
            ON fol.StockCode = dp.stock_code

        WHERE fol.line_category = 'product'

        GROUP BY
            fol.StockCode,
            dp.product_description
    """)

    left, right = st.columns(2)

    with left:
        st.subheader("Top 10 Products by Net Sales")

        st.bar_chart(
            products.nlargest(10, "net_sales"),
            x="product",
            y="net_sales",
            horizontal=True,
            sort=False,
            x_label="Product",
            y_label="Net Sales (£)",
        )

    with right:
        st.subheader("Top 10 Products by Cancellation Value")

        st.bar_chart(
            products.nlargest(10, "cancellation_value"),
            x="product",
            y="cancellation_value",
            horizontal=True,
            sort=False,
            x_label="Product",
            y_label="Cancellation Value (£)",
        )

    st.divider()

    st.subheader("Product Explorer")

    countries = query("""
        SELECT DISTINCT country
        FROM fact_orders
        WHERE country IS NOT NULL
        ORDER BY country
    """)["country"].tolist()

    country = st.selectbox(
        "Select a country",
        ["All"] + countries,
    )

    if country != "All":

        products = query("""
            SELECT
                fol.StockCode AS stock_code,
                COALESCE(
                    dp.product_description,
                    fol.StockCode
                ) AS product_description,
                ROUND(SUM(fol.gross_product_sales_value), 2) AS gross_sales,
                ROUND(-SUM(fol.product_cancellation_value), 2) AS cancellation_value,
                ROUND(SUM(fol.net_product_sales_value), 2) AS net_sales

            FROM fact_order_lines fol

            LEFT JOIN dim_products dp
                ON fol.StockCode = dp.stock_code

            WHERE
                fol.line_category = 'product'
                AND fol.Country = ?

            GROUP BY
                fol.StockCode,
                dp.product_description

            ORDER BY net_sales DESC
        """, [country])

    else:

        products = products.rename(
            columns={"product": "product_description"}
        )[
            [
                "stock_code",
                "product_description",
                "gross_sales",
                "cancellation_value",
                "net_sales",
            ]
        ].sort_values("net_sales", ascending=False)

    st.dataframe(
        products,
        hide_index=True,
        width="stretch",
    )


# Navigation

page = st.sidebar.radio(
    "Navigation",
    [
        "Executive Overview",
        "Customer Value & RFM",
        "Sales & Cancellations",
    ],
)


if page == "Executive Overview":
    executive_page()

elif page == "Customer Value & RFM":
    rfm_page()

else:
    sales_page()


con.close()