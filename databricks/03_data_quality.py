# Databricks notebook source
# MAGIC %md
# MAGIC # 03 — Contrôles qualité & supervision
# MAGIC Exécute les contrôles qualité (`src/transformations.py::run_quality_checks`)
# MAGIC sur `raw_*` vs `clean_*` et écrit le résultat dans `monitoring_dq_results`,
# MAGIC la table que consulte un job planifié (voir `azure-pipelines.yml`) pour
# MAGIC alerter en cas de `status = 'FAIL'`.

# COMMAND ----------

import sys
from datetime import datetime

from pyspark.sql import functions as F

sys.path.append("/Workspace/pilotage-projets/src")
from transformations import RAW_TABLES, clean_all, run_quality_checks  # noqa: E402

# COMMAND ----------

raw = {name: spark.table(f"raw_{name}") for name in RAW_TABLES}
clean = {name: spark.table(f"clean_{name}") for name in RAW_TABLES}

dq = run_quality_checks(spark, raw, clean).withColumn("run_at", F.lit(datetime.utcnow().isoformat()))

(
    dq.write.format("delta")
    .mode("append")
    .option("mergeSchema", "true")
    .saveAsTable("monitoring_dq_results")
)

display(dq)

# COMMAND ----------

n_failed = dq.filter("status = 'FAIL'").count()
if n_failed > 0:
    # Sur un vrai environnement : notification (webhook Teams/e-mail) au lieu du
    # print — voir README § "Aller plus loin" pour ne pas sur-construire une
    # intégration Teams non demandée par l'offre.
    print(f"⚠️ {n_failed} contrôle(s) qualité en échec — voir monitoring_dq_results")
else:
    print("✅ Tous les contrôles qualité sont PASS")
