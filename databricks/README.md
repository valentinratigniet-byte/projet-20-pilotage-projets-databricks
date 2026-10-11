# Exécuter sur Databricks Free Edition

Databricks Free Edition (gratuit, sans carte bancaire, calcul serverless) est utilisé pour prouver que le pipeline tourne réellement
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
   `powerbi/`) ; la connexion Power BI live au SQL Warehouse n'a pas été testée.

## Limite assumée

Le dashboard Power BI est alimenté par export CSV (`scripts/export_for_powerbi.py`,
résultats identiques à l'exécution Databricks) : la connexion live au SQL
Warehouse de la Free Edition via le "Databricks Connector" n'a pas été testée. Sur un vrai environnement Azure Databricks (comme celui visé par
l'offre), Power BI se connecterait directement au SQL Warehouse via le
connecteur natif — la logique de transformation (`src/transformations.py`) est
identique dans les deux cas.
