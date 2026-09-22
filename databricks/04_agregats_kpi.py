# Databricks notebook source
# MAGIC %md
# MAGIC # 04 — Marts KPI (base des rapports Power BI)
# MAGIC Construit `mart_kpi_project` (une ligne par projet : jalons en retard,
# MAGIC dérive budgétaire, risques ouverts, avancement) à partir de `clean_*`.
# MAGIC C'est la table que Power BI consomme (voir `powerbi/`).

# COMMAND ----------

import sys

sys.path.append("/Workspace/pilotage-projets/src")
from transformations import RAW_TABLES, build_kpi_project  # noqa: E402

# COMMAND ----------

clean = {name: spark.table(f"clean_{name}") for name in RAW_TABLES}
kpi = build_kpi_project(clean)

(
    kpi.write.format("delta")
    .mode("overwrite")
    .option("overwriteSchema", "true")
    .saveAsTable("mart_kpi_project")
)

print(f"mart_kpi_project: {kpi.count()} lignes (1 par projet)")
display(kpi)

# COMMAND ----------

# MAGIC %md
# MAGIC ## Requêtes SQL équivalentes
# MAGIC Les mêmes agrégats en SQL pur (`sql/requetes_analytiques.sql`) — utilisable
# MAGIC directement dans **Databricks SQL** ou l'éditeur SQL du notebook (`%sql`) :

# COMMAND ----------

# MAGIC %sql
# MAGIC SELECT
# MAGIC   program,
# MAGIC   COUNT(*) AS n_projects,
# MAGIC   ROUND(AVG(pct_milestones_late), 1) AS avg_pct_milestones_late,
# MAGIC   ROUND(SUM(budget_variance_eur), 0) AS total_budget_variance_eur,
# MAGIC   SUM(n_open_risks_high_severity) AS total_open_risks_high_severity
# MAGIC FROM mart_kpi_project
# MAGIC GROUP BY program
# MAGIC ORDER BY total_budget_variance_eur DESC
