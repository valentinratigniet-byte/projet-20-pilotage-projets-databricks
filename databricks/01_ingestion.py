# Databricks notebook source
# MAGIC %md
# MAGIC # 01 — Ingestion
# MAGIC Charge les CSV bruts (`data/raw/`) vers des tables Delta `raw_*`. Sur
# MAGIC Databricks Community Edition (pas de Unity Catalog) : uploader le dossier
# MAGIC `data/raw/` via **Data > Add data > Upload file to DBFS**, cible
# MAGIC `/FileStore/pilotage-projets/raw/`, adapter `RAW_DIR` ci-dessous si besoin,
# MAGIC puis exécuter ce notebook en premier.

# COMMAND ----------

import sys

sys.path.append("/Workspace/pilotage-projets/src")  # adapter au chemin réel du repo importé
from transformations import RAW_TABLES, load_raw_csvs  # noqa: E402

# COMMAND ----------

RAW_DIR = "/dbfs/FileStore/pilotage-projets/raw"  # à adapter : chemin d'upload dans le workspace

dbutils.widgets.text("raw_dir", RAW_DIR)
raw_dir = dbutils.widgets.get("raw_dir")

# COMMAND ----------

tables = load_raw_csvs(spark, raw_dir)

for name in RAW_TABLES:
    df = tables[name]
    (
        df.write.format("delta")
        .mode("overwrite")
        .option("overwriteSchema", "true")
        .saveAsTable(f"raw_{name}")
    )
    print(f"raw_{name}: {df.count()} lignes écrites")

# COMMAND ----------

# MAGIC %md
# MAGIC Vérification rapide : les 5 tables `raw_*` doivent apparaître dans le catalogue
# MAGIC (`Data` > `default` dans la barre latérale) avec les volumétries ci-dessus.
