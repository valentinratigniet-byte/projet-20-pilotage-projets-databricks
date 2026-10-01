# Exécuter sur Databricks Community Edition

Databricks Community Edition (gratuit, sans carte bancaire, cluster mono-nœud
"personal compute") est utilisé pour prouver que le pipeline tourne réellement
sur Databricks — pas seulement en PySpark local (voir `tests/` pour la partie
testée en CI sans dépendre d'un compte externe).

## Étapes

1. Créer un compte sur [community.cloud.databricks.com](https://community.cloud.databricks.com).
2. Démarrer un cluster "Personal Compute" (Runtime ML ou standard, Spark 3.5.x).
3. **Data > Add data > Upload file to DBFS**, uploader les 5 CSV de `data/raw/`
   vers `/FileStore/pilotage-projets/raw/`.
4. **Workspace**, importer le repo entier sous `/Workspace/pilotage-projets/`
   (Repos > Add repo pointant sur ce dépôt GitHub, le plus simple — ou upload
   manuel des `.py` en conservant la structure). Important : `transformations.py`
   doit rester accessible sous `/Workspace/pilotage-projets/src/`, car chaque
   notebook fait `sys.path.append("/Workspace/pilotage-projets/src")` — à
   adapter dans les 4 notebooks si le chemin d'import choisi diffère.
5. Exécuter dans l'ordre : `01_ingestion` → `02_transformation` → `03_data_quality`
   → `04_agregats_kpi`, attachés au cluster créé à l'étape 2.
6. Exporter `mart_kpi_project` (Data > table > **Export** ou `%sql SELECT * FROM
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
