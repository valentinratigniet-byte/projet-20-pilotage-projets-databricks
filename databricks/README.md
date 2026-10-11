# Exécuter sur Databricks Community Edition

Databricks Community Edition (gratuit, sans carte bancaire, cluster mono-nœud
"personal compute") est utilisé pour prouver que le pipeline tourne réellement
sur Databricks — pas seulement en PySpark local (voir `tests/` pour la partie
testée en CI sans dépendre d'un compte externe).

## Étapes

> Community Edition a été remplacée par **Databricks Free Edition** (gratuite,
> calcul serverless, Unity Catalog). Les étapes ci-dessous visent la Free Edition.

1. Créer un compte sur [databricks.com/learn/free-edition](https://www.databricks.com/learn/free-edition).
2. **Catalog > workspace > default > Create > Volume**, nommé `raw`, puis y
   uploader les 5 CSV de `data/raw/` (→ `/Volumes/workspace/default/raw/`).
3. **Workspace > Create > Git folder** pointant sur ce dépôt GitHub. Les notebooks
   importent `src/transformations.py` par chemin relatif (`../src`), aucun chemin
   à adapter.
4. Ouvrir `databricks/`, exécuter dans l'ordre sur le calcul serverless :
   `01_ingestion` → `02_transformation` → `03_data_quality` → `04_agregats_kpi`.
   Les tables sont écrites dans `workspace.default`.
5. Exporter `mart_kpi_project` (Data > table > **Export** ou `%sql SELECT * FROM
   mart_kpi_project` puis "Download full results") pour alimenter Power BI (voir
   `powerbi/`), Community Edition n'exposant pas d'endpoint SQL Warehouse
   accessible depuis l'extérieur pour une connexion Power BI live.

## Limite assumée

Community Edition n'a pas Unity Catalog ni de SQL Warehouse externe — le lien
Power BI se fait donc par export plutôt qu'en connexion live "Databricks
Connector". Sur un vrai environnement Azure Databricks (comme celui visé par
l'offre), Power BI se connecterait directement au SQL Warehouse via le
connecteur natif — la logique de transformation (`src/transformations.py`) est
identique dans les deux cas.
