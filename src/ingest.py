from pathlib import Path

import pandas as pd


# Chemins du projet
PROJECT_ROOT = Path(__file__).resolve().parents[1]

INPUT_FILE = PROJECT_ROOT / "data" / "raw" / "online_retail_II.xlsx"
OUTPUT_DIR = PROJECT_ROOT / "data" / "interim"
OUTPUT_FILE = OUTPUT_DIR / "transactions_consolidated.parquet"


# Chargement des deux feuilles Excel
print("Chargement des données...")

df_2009_2010 = pd.read_excel(
    INPUT_FILE,
    sheet_name="Year 2009-2010"
)

df_2010_2011 = pd.read_excel(
    INPUT_FILE,
    sheet_name="Year 2010-2011"
)

print("2009-2010 :", df_2009_2010.shape)
print("2010-2011 :", df_2010_2011.shape)


# Standardisation des types
# Certaines colonnes contiennent des types mixtes dans le fichier Excel.

for df in [df_2009_2010, df_2010_2011]:
    df["Invoice"] = df["Invoice"].astype("string")
    df["StockCode"] = df["StockCode"].astype("string")
    df["Description"] = df["Description"].astype("string")
    df["Country"] = df["Country"].astype("string")

    df["Customer ID"] = pd.to_numeric(
        df["Customer ID"],
        errors="coerce"
    ).astype("Int64")

    df["Quantity"] = pd.to_numeric(
        df["Quantity"],
        errors="raise"
    ).astype("int64")

    df["Price"] = pd.to_numeric(
        df["Price"],
        errors="raise"
    ).astype("float64")

    df["InvoiceDate"] = pd.to_datetime(
        df["InvoiceDate"],
        errors="raise"
    )


# Ajout de la provenance
df_2009_2010["SourcePeriod"] = "2009-2010"
df_2010_2011["SourcePeriod"] = "2010-2011"


# Suppression du chevauchement identifié lors de l'audit
df_2009_2010_unique = df_2009_2010[
    df_2009_2010["InvoiceDate"] < "2010-12-01"
].copy()


# Consolidation
df_consolidated = pd.concat(
    [
        df_2009_2010_unique,
        df_2010_2011
    ],
    ignore_index=True
)

df_consolidated["SourcePeriod"] = (
    df_consolidated["SourcePeriod"].astype("string")
)


# Contrôles
print("\nDataset consolidé")
print("Nombre de lignes :", len(df_consolidated))
print("Nombre de colonnes :", len(df_consolidated.columns))

print(
    "Période :",
    df_consolidated["InvoiceDate"].min(),
    "vers",
    df_consolidated["InvoiceDate"].max()
)

print("\nTypes des colonnes :")
print(df_consolidated.dtypes)


# Export Parquet
OUTPUT_DIR.mkdir(
    parents=True,
    exist_ok=True
)

df_consolidated.to_parquet(
    OUTPUT_FILE,
    index=False,
    engine="pyarrow"
)

print("\nFichier créé :")
print(OUTPUT_FILE)