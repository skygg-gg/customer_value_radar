# Cahier des charges 

## 1. Contexte 

Le projet vise à construire une solution d'analyse de la performance commerciale et de la valeur client à partir de données transactionnelles réelles d'un acteur du e-commerce.

Le dataset utilisé est Online Retail II

Il contient les lignes transactionnelles d'un détaillant britannique sur une période allant de décembre 2009 à décembre 2011.

Le projet est réalisé dans le cadre du Bloc 6 : Direction de projets de gestion de données de la certification CDSD.


## 2. Problématique 

Une entreprise e-commerce disposant d'un historique transactionnel important doit être capable de répondre à plusieurs questions :

- Comment évoluent les ventes dans le temps ?
- Quels pays et quels produits contribuent le plus aux ventes ?
- Quelle est l'importance des annulations ?
- Quels clients génèrent le plus de valeur ?
- La valeur commerciale est-elle concentrée sur une faible part des clients ?
- Quels clients peuvent être considérés comme fidèles, à potentiel ou à risque ?
- Comment rendre ces informations facilement accessibles aux équipes métier ?

La problématique principale est :

> **Comment exploiter les données transactionnelles afin d'identifier les principaux moteurs de la performance commerciale et de segmenter les clients selon leur valeur et leur comportement d'achat ?**



## 3. Objectifs du projet

### Objectifs métier

- Mesurer la performance commerciale.
- Identifier les tendances de ventes.
- Identifier les principaux pays contributeurs.
- Identifier les principaux produits.
- Mesurer l'importance des annulations.
- Analyser la concentration de la valeur client.
- Segmenter les clients selon une approche RFM.
- Fournir des indicateurs permettant de différencier les clients à fidéliser, développer ou réactiver.

### Objectifs data

- Construire un pipeline reproductible de traitement des données.
- Préserver les données sources avant application des règles métier.
- Contrôler la qualité des données.
- Structurer les données dans un modèle analytique simple.
- Construire des indicateurs métier fiables.
- Produire une table de segmentation client.
- Mettre les résultats à disposition dans des outils de visualisation.



## 4. Périmètre fonctionnel

Le projet comprend :

- ingestion du fichier source Excel 
- consolidation des périodes disponibles 
- audit de qualité des données 
- stockage intermédiaire en Parquet 
- stockage analytique dans DuckDB 
- création d'une couche Bronze 
- création d'une couche Silver  
- création de tables analytiques 
- analyse exploratoire
- calcul des KPI commerciaux 
- analyse des annulations 
- analyse des produits 
- analyse géographique par pays 
- analyse de la fréquence d'achat 
- analyse de concentration de la valeur client 
- segmentation RFM 
- dashboard Tableau 
- application Streamlit 
- documentation du projet


## 5. Hors périmètre

- prédiction par machine learning ;
- orchestration avec Airflow ;
- traitement distribué avec Spark ;
- infrastructure cloud ;
- traitement en temps réel ;
- base de données de production ;
- déploiement à grande échelle ;
- intégration à un CRM réel.

Ces éléments peuvent constituer des évolutions futures.


## 6. Source de données

### Dataset principal

**Online Retail II — UCI Machine Learning Repository**

Le dataset contient environ 1,07 million d'observations dans sa version d'origine.

Après consolidation des deux feuilles et suppression du chevauchement temporel identifié entre les sources, le périmètre analytique du projet contient :

- 1 044 848 lignes transactionnelles ;
- une période comprise entre décembre 2009 et décembre 2011.

### Variables principales

- `Invoice`
- `StockCode`
- `Description`
- `Quantity`
- `InvoiceDate`
- `Price`
- `Customer ID`
- `Country`



## 7. Principales règles de gestion

### Annulations

Selon la documentation UCI, un numéro de facture commençant par `C` indique une annulation.

Le projet distingue donc les ventes produit et les annulations produit.


### Clients non identifiés

Les lignes sans `Customer ID` sont conservées pour les analyses commerciales agrégées.

Elles sont exclues des analyses nécessitant l'identification individuelle d'un client, notamment :

- RFM ;
- segmentation client ;
- analyses comportementales individuelles.

Aucune valeur de `Customer ID` n'est imputée.

### Doublons apparents

Les observations strictement répétées sont identifiées par un indicateur de qualité.

Elles ne sont pas automatiquement supprimées car le dataset ne permet pas de démontrer qu'elles correspondent nécessairement à des erreurs.

### Valeur des ventes produit

Une vente produit est définie par :

- une ligne classée comme produit ;
- une quantité positive ;
- un prix positif ;
- une facture ne correspondant pas à une annulation.

Une annulation produit est définie par :

- une ligne classée comme produit ;
- une quantité négative ;
- un prix positif ;
- une facture identifiée comme annulation.



## 8. Architecture 

Le pipeline suit l'organisation suivante :


Source Excel
    
Python / Pandas
    
Parquet
    
DuckDB
    
Bronze
    
Silver
    
Tables analytiques
    
EDA / RFM
    
Tableau / Streamlit


## 9. Segmentation RFM

La segmentation RFM repose sur trois dimensions :

- **Recency** : temps écoulé depuis le dernier achat 
- **Frequency** : nombre de commandes produit 
- **Monetary** : valeur nette des ventes produit associée au client

Les clients sont ensuite regroupés dans six segments :

- Champions ;
- Loyal ;
- Potential ;
- Regular ;
- At Risk ;
- Low Value.


## 10. Livrables

Les livrables prévus sont :

- repository GitHub documenté 
- scripts Python d'ingestion et de transformation 
- base analytique DuckDB reproductible 
- notebooks d'audit et d'analyse 
- segmentation RFM 
- dashboard Tableau 
- application Streamlit 
- architecture du projet 
- cahier des charges 
- veille et justification des choix technologiques 
- budget projet 
- rétroplanning 
- registre des risques 
- README 
- présentation de soutenance 
