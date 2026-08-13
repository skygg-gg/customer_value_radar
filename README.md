# Customer Value Radar

Projet d’analyse de données e-commerce visant à mesurer la performance commerciale, la valeur client, les comportements d’achat et les annulations.

Le projet repose sur une chaîne de traitement reproductible utilisant **Python, SQL, DuckDB, Tableau et Streamlit**.

## Objectifs

Le projet permet notamment de :

* suivre l’évolution des ventes ;
* analyser la valeur et la fréquence d’achat des clients ;
* segmenter les clients grâce à une analyse RFM ;
* identifier les clients à forte valeur et ceux présentant un risque de désengagement ;
* analyser la performance des produits ;
* mesurer les annulations ;
* comparer l’activité selon les pays.

## Données

Source : **Online Retail II**, UCI Machine Learning Repository.

Le jeu de données contient **1 067 371 lignes** et couvre la période du **1er décembre 2009 au 9 décembre 2011**.

Selon la documentation UCI, un numéro de facture commençant par `C` correspond à une **annulation**.

**Référence :**
Chen, D. (2012). *Online Retail II* [Dataset].
UCI Machine Learning Repository.
DOI : `10.24432/C5CG6D`
Licence : **CC BY 4.0**

## Architecture

Le projet suit une architecture analytique simple :

```text
Fichier Excel
    ↓
Parquet
    ↓
Bronze
    ↓
Silver
    ↓
Gold
    ↓
Tableau / Streamlit
```

Les principales tables analytiques sont :

* `fact_order_lines`
* `fact_orders`
* `dim_customers`
* `dim_products`
* `customer_rfm`

La base analytique est stockée dans **DuckDB**.

## Analyse RFM

L’analyse RFM repose sur :

* **Recency (récence)** : nombre de jours depuis le dernier achat observé ;
* **Frequency (fréquence)** : nombre de commandes d’achat ;
* **Monetary (valeur monétaire)** : valeur nette générée par le client.

Les clients sont répartis en six segments :

* Champions
* Loyal (fidèles)
* Potential (potentiels)
* Regular (réguliers)
* At Risk (à risque)
* Low Value (faible valeur)

## Principaux résultats

| Indicateur             | Résultat |
| ---------------------- | -------: |
| Ventes produit nettes  | £18,98 M |
| Ventes produit brutes  | £19,70 M |
| Valeur des annulations |  £0,72 M |
| Taux d’annulation      |    3,7 % |
| Commandes d’achat      |   39 516 |
| Panier moyen           |  £498,56 |
| Clients identifiés     |    5 852 |
| Champions              |    1 160 |

Les Champions représentent **67,6 % de la valeur client RFM**.

> Le mois de décembre 2011 est incomplet car le jeu de données s’arrête au 9 décembre 2011.

## Visualisations

Trois tableaux de bord Tableau ont été réalisés :

* **Executive Overview (vue d’ensemble)**
* **Customer Value & RFM (valeur client et RFM)**
* **Sales & Cancellations (ventes et annulations)**

L’application Streamlit reprend ces trois axes et ajoute des fonctions d’exploration interactive des clients et des produits.

## Exécution du projet

Créer et activer l’environnement virtuel :

```bash
python -m venv .venv
source .venv/bin/activate
```

Installer les dépendances :

```bash
python -m pip install -r requirements.txt
```

Placer le fichier source dans :

```text
data/raw/online_retail_II.xlsx
```

Exécuter toute la chaîne de traitement :

```bash
python src/run_pipeline.py
```

Exporter les données Tableau :

```bash
python src/export_tableau.py
```

Lancer l’application Streamlit :

```bash
python -m streamlit run streamlit_app.py
```

## Technologies

**Python · Pandas · SQL · DuckDB · Parquet · Tableau · Streamlit · Git · GitHub**

## Limites principales

* certaines lignes ne possèdent pas de `Customer ID` et ne peuvent donc pas être utilisées pour l’analyse RFM individuelle ;
* `Country` représente le pays observé sur la transaction et non nécessairement la résidence permanente du client ;
* un même `StockCode` peut avoir plusieurs descriptions observées ;
* les factures commençant par `C` sont considérées comme des annulations selon UCI, sans supposer qu’il s’agit systématiquement de retours physiques ;
* la période observée est limitée au contenu du jeu de données.
