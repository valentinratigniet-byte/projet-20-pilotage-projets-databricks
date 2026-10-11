# Databricks notebook source
# MAGIC %md
# MAGIC # 02 — Transformation & fiabilisation
# MAGIC Nettoie, type et corrige les 5 tables `raw_*` (dédoublonnage, bornage des
# MAGIC valeurs aberrantes, correction d'incohérences métier) vers des tables Delta
# MAGIC `clean_*`. Logique factorisée dans `src/transformations.py` (même code que
# MAGIC les tests `tests/test_transformations.py`, exécutés en CI hors Databricks).

# COMMAND ----------

import os
import sys

sys.path.append(os.path.abspath("../src"))  # notebook lancé depuis databricks/, src/ à côté
from transformations import RAW_TABLES, clean_all  # noqa: E402

# COMMAND ----------

raw = {name: spark.table(f"raw_{name}") for name in RAW_TABLES}
clean = clean_all(raw)

# COMMAND ----------

for name, df in clean.items():
    (
        df.write.format("delta")
        .mode("overwrite")
        .option("overwriteSchema", "true")
        .saveAsTable(f"clean_{name}")
    )
    print(f"clean_{name}: {df.count()} lignes écrites")

# COMMAND ----------

# MAGIC %md
# MAGIC ## Ce qui a été corrigé (à comparer avec `raw_*`)
# MAGIC - `projects` : project_id dupliqué supprimé.
# MAGIC - `milestones` : statut "Atteint" sans `date_actual` requalifié en "À vérifier"
# MAGIC   (traçable plutôt que supprimé), `delay_days` calculé.
# MAGIC - `budget_lines` : valeurs aberrantes flaggées (`is_outlier`) au lieu d'être
# MAGIC   supprimées silencieusement — décision documentée dans le README.
# MAGIC - `risks` : `probability`/`impact` bornés à [1,5], `severity` calculée.
# MAGIC - `status_reports` : doublons de `report_id` supprimés, `advancement_pct`
# MAGIC   borné à [0,100].

# COMMAND ----------

display(spark.table("clean_projects").limit(10))
