# Databricks notebook source
# MAGIC %md
# MAGIC # 01 — Ingestion
# MAGIC Charge les CSV bruts (`data/raw/`) vers des tables Delta `raw_*`. Sur
# MAGIC Databricks Free Edition : uploader les CSV dans le volume Unity Catalog
# MAGIC `workspace.default.raw` (voir `databricks/README.md`), cible
# MAGIC `/Volumes/workspace/default/raw/`, adapter `RAW_DIR` ci-dessous si besoin,
# MAGIC puis exécuter ce notebook en premier.

# COMMAND ----------

import os
import sys

sys.path.append(os.path.abspath("../src"))  # notebook lancé depuis databricks/, src/ à côté
from transformations import RAW_TABLES, load_raw_csvs  # noqa: E402

# COMMAND ----------

RAW_DIR = "/Volumes/workspace/default/raw"  # volume Unity Catalog (Free Edition)

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
