"""Self-check du pipeline PySpark : mêmes fonctions que les notebooks
Databricks (databricks/*.py), exécutées ici en SparkSession locale contre les
vraies données générées dans data/raw/. Sert de CI (GitHub Actions + Azure
Pipelines) sans nécessiter de cluster Databricks.
"""
import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from transformations import (  # noqa: E402
    build_kpi_project,
    clean_all,
    get_spark,
    load_raw_csvs,
    run_quality_checks,
)

RAW_DIR = str(Path(__file__).parent.parent / "data" / "raw")


@pytest.fixture(scope="module")
def spark():
    s = get_spark("test-pilotage-projets")
    yield s
    s.stop()


@pytest.fixture(scope="module")
def raw(spark):
    return load_raw_csvs(spark, RAW_DIR)


@pytest.fixture(scope="module")
def clean(raw):
    return clean_all(raw)


def test_raw_has_injected_duplicates(raw):
    # le générateur injecte volontairement un project_id dupliqué
    dup = raw["projects"].groupBy("project_id").count().filter("count > 1").count()
    assert dup >= 1


def test_clean_projects_deduplicated(clean):
    dup = clean["projects"].groupBy("project_id").count().filter("count > 1").count()
    assert dup == 0


def test_clean_risks_probability_in_bounds(clean):
    out_of_bounds = clean["risks"].filter("probability < 1 OR probability > 5").count()
    assert out_of_bounds == 0


def test_clean_status_reports_advancement_in_bounds(clean):
    out_of_bounds = clean["status_reports"].filter(
        "advancement_pct < 0 OR advancement_pct > 100"
    ).count()
    assert out_of_bounds == 0


def test_clean_status_reports_deduplicated(clean):
    dup = clean["status_reports"].groupBy("report_id").count().filter("count > 1").count()
    assert dup == 0


def test_milestone_atteint_always_has_date_actual(clean):
    bad = clean["milestones"].filter("status = 'Atteint' AND date_actual IS NULL").count()
    assert bad == 0


def test_budget_outliers_are_flagged_not_dropped(clean, raw):
    # le flag ne doit pas faire disparaître de lignes : même volumétrie qu'en brut
    assert clean["budget_lines"].count() == raw["budget_lines"].count()
    assert clean["budget_lines"].filter("is_outlier = true").count() >= 1


def test_quality_checks_report_has_expected_shape(spark, raw, clean):
    dq = run_quality_checks(spark, raw, clean)
    assert set(dq.columns) == {"table", "check", "n_violations", "status"}
    assert dq.count() >= 8
    # les contrôles "clean_*" doivent tous être PASS : la fiabilisation a fait son travail
    failed_clean_checks = dq.filter(
        "check LIKE '%clean%' AND status = 'FAIL'"
    ).collect()
    assert failed_clean_checks == []


def test_kpi_project_no_orphan_rows(clean):
    kpi = build_kpi_project(clean)
    assert kpi.count() == clean["projects"].count()


def test_kpi_project_pct_milestones_late_in_bounds(clean):
    kpi = build_kpi_project(clean)
    bad = kpi.filter(
        "pct_milestones_late IS NOT NULL AND (pct_milestones_late < 0 OR pct_milestones_late > 100)"
    ).count()
    assert bad == 0


def test_kpi_project_budget_variance_is_consistent(clean):
    kpi = build_kpi_project(clean)
    row = kpi.filter("budget_planned_to_date_eur IS NOT NULL").first()
    assert row is not None
    expected_variance = row["budget_actual_to_date_eur"] - row["budget_planned_to_date_eur"]
    assert abs(row["budget_variance_eur"] - expected_variance) < 0.01
