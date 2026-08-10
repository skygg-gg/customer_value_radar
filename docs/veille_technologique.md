# Veille technologique 

## Objectif

L'objectif est de choisir une stack adaptée à l'analyse de plus d'un million de lignes transactionnelles.

## Outils retenus

### Python / Pandas

Utilisés pour :

- l'ingestion 
- le nettoyage 
- l'audit qualité 
- l'analyse exploratoire 
- la segmentation RFM

Python a été retenu pour sa flexibilité et son écosystème data.

### SQL

SQL est utilisé pour :

- créer les tables analytiques 
- agréger les données 
- calculer les indicateurs métier 
- construire les tables fact_orders, fact_order_lines, dim_customers et dim_products 
- préparer les données utilisées pour l'analyse RFM
- SQL pour les transformations et agrégations structurées ;
- Pandas pour l'audit, l'analyse exploratoire et calculs analytiques.

### Parquet

Parquet est utilisé comme format intermédiaire entre les données sources et le warehouse.

Il a été préféré au CSV car il :

- conserve mieux les types 
- est compressé 
- est adapté aux traitements analytiques 
- est facilement utilisable avec Python et DuckDB



### DuckDB

DuckDB est utilisé comme base analytique locale.

Il a été préféré à PostgreSQL car :

- il ne nécessite pas de serveur 
- il fonctionne directement avec Python 
- il est adapté aux requêtes analytiques 
- il s'intègre facilement avec Parquet

PostgreSQL serait plus pertinent dans un environnement de production multi-utilisateur.



### Tableau

Tableau est retenu pour les dashboards métier.

Il permet de présenter :

- les KPI commerciaux 
- les tendances de ventes 
- les produits et pays principaux 
- les segments clients RFM

L'objectif est de rendre les résultats accessibles à un utilisateur non technique.



### Streamlit

Streamlit est retenu pour créer une application analytique simple en Python.

Il permet de réutiliser directement les données et analyses déjà produites dans le projet.



### Git / GitHub

Git et GitHub sont utilisés pour :

- versionner le code 
- suivre les évolutions du projet 
- conserver l'historique des modifications 
- partager le repository


## Synthèse


 Langage principal : Python 
 Requêtes et transformations : SQL 
 Manipulation et analyse : Pandas
 Stockage intermédiaire : Parquet 
 Base analytique : DuckDB 
 Business Intelligence : Tableau 
 Application interactive : Streamlit 
 Versionnement : Git / GitHub 

## Conclusion

Le choix a été guidé par :

- la simplicité 
- la rapidité de développement 
- le faible coût 
- la reproductibilité 
- l'adéquation avec un projet analytique local.

Une architecture cloud ou une base serveur pourrait être envisagée dans un contexte de production ou de plus grande volumétrie.