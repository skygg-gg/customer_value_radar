# Customer Value Radar — Notes du projet

Projet e-commerce réalisé dans le cadre du Bloc 6 CDSD.

### Problématique

Comment exploiter des données transactionnelles e-commerce afin de mieux comprendre :

- la performance commerciale 
- le comportement client 
- la création de valeur client

### Objectif

Construire une chaîne de données reproductible :

**Source  Audit  Ingestion  Warehouse  Analyse  Restitution**


## 2. Dataset

Dataset utilisé : Online Retail II

- Source : UCI Machine Learning Repository
- Période : décembre 2009 à décembre 2011
- Fichier : online_retail_II.xlsx
- 2 feuilles :
  - Year 2009-2010
  - Year 2010-2011
- Volume brut : 1 067 371 lignes


# 3. Audit qualité

Notebook :

notebooks/data_audit_quality.ipynb

## Chevauchement des deux feuilles

Une période commune existe du 1er au 9 décembre 2010.

Résultats :

- 22 523 lignes présentes dans les deux feuilles 
- 1 088 factures concernées 
- comparaison ligne par ligne : observations identiques.

### Décision

Conserver cette période uniquement depuis la feuille Year 2010-2011.

### Résultat

Dataset consolidé : 1 044 848 lignes



## Quantités négatives

Résultats :

- 22 557 lignes avec Quantity < 0 
- 19 164 liées à des factures commençant par C (Annulation / Cancelled)
- soit environ 84,96 %
- 3 393 autres mouvements négatifs

Les autres cas contiennent notamment :

- dommages 
- pertes 
- corrections 
- produits jetés 
- mouvements de stock

### Conclusion

Toutes les quantités négatives ne représentent pas la même situation métier.

### Décision

Ne pas les supprimer automatiquement.


## Prix négatifs et prix nuls

### Prix négatifs

- 5 lignes associées à "Adjust bad debt".

### Prix nuls

- 6 024 lignes souvent associées à des corrections ou mouvements non valorisés.

### Décision

- conserver les données pour la traçabilité et ne pas les considérer automatiquement comme ventes commerciales.


## Prix extrêmes

Plusieurs prix élevés correspondent à :

- "Manual"
- "DOTCOM POSTAGE"
- "AMAZON FEE"
- "Bank Charges"
- "POSTAGE"
- commissions ou ajustements.

Le cas "FLAG OF ST GEORGE CAR FLAG" montre qu'un seuil global peut également identifier un vrai produit comme anomalie.

### Conclusion

Un prix élevé n'est pas suffisant pour déterminer qu'une ligne est incorrecte.

### Décision

Ne pas appliquer de seuil arbitraire de suppression.


## Customer ID manquants

Résultats :

- 235 287 lignes sans Customer ID 
- soit 22,52 % du dataset 
- aucune facture ne mélange lignes avec et sans Customer ID.

### Décision

- aucune imputation artificielle 
- conservation pour certaines analyses commerciales 
- exclusion des analyses nécessitant l'identification du client.


## Descriptions manquantes

Résultats :

- 4 275 lignes sans Description
- soit environ 0,41 % 
- toutes ont un prix nul 
- toutes ont également un Customer ID manquant.

### Décision

Conserver pour la traçabilité, sans imputation 


## Lignes strictement identiques

Après correction du chevauchement :

- 11 812 lignes seraient supprimées avec drop_duplicates() 
- 22 813 lignes appartiennent à des groupes dupliqués 
- 4 387 factures sont concernées 
- impact en volume : environ 1,13 %

### Conclusion

Le dataset ne contient pas d'identifiant unique de ligne de commande.

Il est donc impossible de prouver qu'une ligne identique est forcément un doublon technique.

### Décision actuelle

Ne pas supprimer automatiquement ces lignes.

Leur impact devra être étudié avant de définir la règle Silver.


# 4. Pipeline d'ingestion

Script : src/ingest.py

Pipeline actuel :
Excel
Lecture des 2 feuilles
Standardisation des types 
Ajout de SourcePeriod
Correction du chevauchement
Consolidation
Parquet