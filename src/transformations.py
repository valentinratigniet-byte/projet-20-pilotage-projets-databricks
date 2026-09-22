"""Logique PySpark du pipeline (raw -> clean -> contrôles qualité -> marts KPI).

Module partagé entre les notebooks Databricks (databricks/*.py) et les tests
(tests/test_transformations.py) : la même fonction tourne en local (pytest,
SparkSession locale) et sur un cluster Databricks (le `spark` fourni par le
notebook), donc les tests prouvent le comportement réel du pipeline.
"""
from __future__ import annotations

from functools import reduce

from pyspark.sql import DataFrame, SparkSession, Window
from pyspark.sql import functions as F
from pyspark.sql import types as T

RAW_TABLES = ["projects", "milestones", "budget_lines", "risks", "status_reports"]

HIGH_SEVERITY_THRESHOLD = 15  # probability(1-5) * impact(1-5) >= 15


def get_spark(app_name: str = "pilotage-projets") -> SparkSession:
    return (
        SparkSession.builder.appName(app_name)
        .master("local[*]")
        .config("spark.sql.shuffle.partitions", "4")
        .config("spark.ui.showConsoleProgress", "false")
        .getOrCreate()
    )


def load_raw_csvs(spark: SparkSession, raw_dir: str) -> dict[str, DataFrame]:
    return {
        name: spark.read.csv(f"{raw_dir}/{name}.csv", header=True, inferSchema=True)
        for name in RAW_TABLES
    }


# --------------------------------------------------------------------------
# Nettoyage / fiabilisation
# --------------------------------------------------------------------------

def clean_projects(df: DataFrame) -> DataFrame:
    return (
        df.dropDuplicates(["project_id"])
        .withColumn("project_name", F.trim("project_name"))
        .withColumn("start_date_planned", F.to_date("start_date_planned"))
        .withColumn("end_date_planned", F.to_date("end_date_planned"))
        .withColumn("start_date_actual", F.to_date("start_date_actual"))
        .withColumn("end_date_actual", F.to_date("end_date_actual"))
        .withColumn("budget_planned_eur", F.col("budget_planned_eur").cast(T.DoubleType()))
        .withColumn(
            "slippage_days",
            F.when(
                F.col("end_date_actual").isNotNull(),
                F.datediff("end_date_actual", "end_date_planned"),
            ),
        )
    )


def clean_milestones(df: DataFrame) -> DataFrame:
    cleaned = (
        df.dropDuplicates(["milestone_id"])
        .withColumn("date_planned", F.to_date("date_planned"))
        .withColumn("date_actual", F.to_date("date_actual"))
    )
    # incohérence source : status "Atteint" sans date_actual -> corrigé en "À vérifier"
    # plutôt que supprimée, pour rester traçable dans le mart de qualité.
    cleaned = cleaned.withColumn(
        "status",
        F.when(
            (F.col("status") == "Atteint") & F.col("date_actual").isNull(),
            F.lit("À vérifier"),
        ).otherwise(F.col("status")),
    )
    return cleaned.withColumn(
        "delay_days",
        F.when(F.col("date_actual").isNotNull(), F.datediff("date_actual", "date_planned")),
    )


def clean_budget_lines(df: DataFrame) -> DataFrame:
    cleaned = (
        df.withColumn("amount_planned_eur", F.col("amount_planned_eur").cast(T.DoubleType()))
        .withColumn("amount_actual_eur", F.col("amount_actual_eur").cast(T.DoubleType()))
        .withColumn("month", F.to_date("month"))
    )
    # flag des valeurs aberrantes par catégorie (au-delà de 5x la médiane de la
    # catégorie) plutôt qu'une suppression silencieuse : la ligne reste visible
    # pour investigation côté métier, seulement exclue des agrégats KPI.
    median_by_category = cleaned.groupBy("cost_category").agg(
        F.expr("percentile_approx(amount_actual_eur, 0.5)").alias("median_actual")
    )
    cleaned = cleaned.join(median_by_category, on="cost_category", how="left")
    return cleaned.withColumn(
        "is_outlier",
        F.col("amount_actual_eur") > F.col("median_actual") * 5,
    ).drop("median_actual")


def clean_risks(df: DataFrame) -> DataFrame:
    cleaned = (
        df.dropDuplicates(["risk_id"])
        .withColumn("probability", F.least(F.greatest(F.col("probability"), F.lit(1)), F.lit(5)))
        .withColumn("impact", F.least(F.greatest(F.col("impact"), F.lit(1)), F.lit(5)))
        .withColumn("date_raised", F.to_date("date_raised"))
        .withColumn("date_closed", F.to_date("date_closed"))
    )
    return cleaned.withColumn("severity", F.col("probability") * F.col("impact"))


def clean_status_reports(df: DataFrame) -> DataFrame:
    return (
        df.dropDuplicates(["report_id"])
        .withColumn("report_date", F.to_date("report_date"))
        .withColumn(
            "advancement_pct",
            F.least(F.greatest(F.col("advancement_pct").cast(T.DoubleType()), F.lit(0.0)), F.lit(100.0)),
        )
    )


def clean_all(raw: dict[str, DataFrame]) -> dict[str, DataFrame]:
    return {
        "projects": clean_projects(raw["projects"]),
        "milestones": clean_milestones(raw["milestones"]),
        "budget_lines": clean_budget_lines(raw["budget_lines"]),
        "risks": clean_risks(raw["risks"]),
        "status_reports": clean_status_reports(raw["status_reports"]),
    }


# --------------------------------------------------------------------------
# Contrôles qualité (supervision / monitoring)
# --------------------------------------------------------------------------

def _check(spark: SparkSession, table: str, check: str, n_violations: int, threshold: int = 0) -> DataFrame:
    # Construit la ligne via des littéraux Catalyst (spark.range + F.lit) plutôt que
    # spark.createDataFrame(liste_python, schema) : ce dernier chemin sérialise les
    # objets Python vers un worker dédié, qui crashe sur cette machine (cf. README
    # § limites connues) sans lien avec la logique métier.
    status = "PASS" if n_violations <= threshold else "FAIL"
    return spark.range(1).select(
        F.lit(table).alias("table"),
        F.lit(check).alias("check"),
        F.lit(int(n_violations)).cast(T.LongType()).alias("n_violations"),
        F.lit(status).alias("status"),
    )


def run_quality_checks(spark: SparkSession, raw: dict[str, DataFrame], clean: dict[str, DataFrame]) -> DataFrame:
    rows = []

    rows.append(_check(spark, "projects", "raw_duplicate_project_id",
                        raw["projects"].groupBy("project_id").count().filter("count > 1").count()))
    rows.append(_check(spark, "projects", "clean_duplicate_project_id",
                        clean["projects"].groupBy("project_id").count().filter("count > 1").count()))
    rows.append(_check(spark, "milestones", "orphan_project_id",
                        clean["milestones"].join(clean["projects"], "project_id", "left_anti").count()))
    rows.append(_check(spark, "milestones", "atteint_sans_date_actual_apres_correction",
                        clean["milestones"].filter("status = 'Atteint' AND date_actual IS NULL").count()))
    rows.append(_check(spark, "risks", "probability_hors_bornes_raw",
                        raw["risks"].filter("probability < 1 OR probability > 5").count()))
    rows.append(_check(spark, "risks", "probability_hors_bornes_clean",
                        clean["risks"].filter("probability < 1 OR probability > 5").count()))
    rows.append(_check(spark, "status_reports", "advancement_hors_bornes_raw",
                        raw["status_reports"].filter("advancement_pct < 0 OR advancement_pct > 100").count()))
    rows.append(_check(spark, "status_reports", "advancement_hors_bornes_clean",
                        clean["status_reports"].filter("advancement_pct < 0 OR advancement_pct > 100").count()))
    rows.append(_check(spark, "status_reports", "duplicate_report_id_clean",
                        clean["status_reports"].groupBy("report_id").count().filter("count > 1").count()))
    rows.append(_check(spark, "budget_lines", "outliers_flagged",
                        clean["budget_lines"].filter("is_outlier = true").count(), threshold=1000))

    return reduce(DataFrame.unionByName, rows)


# --------------------------------------------------------------------------
# Marts KPI (base des rapports Power BI)
# --------------------------------------------------------------------------

def build_kpi_project(clean: dict[str, DataFrame]) -> DataFrame:
    projects = clean["projects"]
    milestones = clean["milestones"]
    budget_lines = clean["budget_lines"].filter("is_outlier = false")
    risks = clean["risks"]
    reports = clean["status_reports"]

    milestone_kpi = milestones.groupBy("project_id").agg(
        F.count("*").alias("n_milestones"),
        F.sum(F.when(F.col("status") == "En retard", 1).otherwise(0)).alias("n_milestones_late"),
        F.avg("delay_days").alias("avg_delay_days"),
    )

    budget_kpi = budget_lines.groupBy("project_id").agg(
        F.sum("amount_planned_eur").alias("budget_planned_to_date_eur"),
        F.sum("amount_actual_eur").alias("budget_actual_to_date_eur"),
    )

    risk_kpi = risks.filter("status = 'Ouvert'").groupBy("project_id").agg(
        F.count("*").alias("n_open_risks"),
        F.sum(F.when(F.col("severity") >= HIGH_SEVERITY_THRESHOLD, 1).otherwise(0)).alias("n_open_risks_high_severity"),
    )

    latest_report = reports.withColumn(
        "rn", F.row_number().over(
            Window.partitionBy("project_id").orderBy(F.col("report_date").desc())
        )
    ).filter("rn = 1").select("project_id", F.col("advancement_pct").alias("latest_advancement_pct"))

    kpi = (
        projects.select("project_id", "project_name", "program", "department", "status",
                         "budget_planned_eur", "slippage_days")
        .join(milestone_kpi, "project_id", "left")
        .join(budget_kpi, "project_id", "left")
        .join(risk_kpi, "project_id", "left")
        .join(latest_report, "project_id", "left")
        .fillna({"n_milestones": 0, "n_milestones_late": 0, "n_open_risks": 0, "n_open_risks_high_severity": 0})
    )

    kpi = kpi.withColumn(
        "pct_milestones_late",
        F.when(F.col("n_milestones") > 0, F.col("n_milestones_late") / F.col("n_milestones") * 100),
    ).withColumn(
        "budget_variance_eur",
        F.col("budget_actual_to_date_eur") - F.col("budget_planned_to_date_eur"),
    ).withColumn(
        "budget_variance_pct",
        F.when(
            F.col("budget_planned_to_date_eur") > 0,
            F.col("budget_variance_eur") / F.col("budget_planned_to_date_eur") * 100,
        ),
    )

    return kpi
