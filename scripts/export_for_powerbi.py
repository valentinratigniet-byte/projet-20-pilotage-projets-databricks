"""Exécute le pipeline (clean + KPI) en PySpark local et exporte les tables en
CSV dans data/powerbi_export/, pour que Power BI Desktop les importe directement
(pas de connecteur Spark nécessaire pour la démo — voir databricks/README.md
pour le lien Databricks Community Edition -> Power BI par export identique).
"""
import csv
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from transformations import build_kpi_project, clean_all, get_spark, load_raw_csvs  # noqa: E402

RAW_DIR = str(Path(__file__).parent.parent / "data" / "raw")
OUT_DIR = Path(__file__).parent.parent / "data" / "powerbi_export"


def main():
    OUT_DIR.mkdir(exist_ok=True)
    spark = get_spark("export-powerbi")
    raw = load_raw_csvs(spark, RAW_DIR)
    clean = clean_all(raw)
    kpi = build_kpi_project(clean)

    for name, df in {**clean, "kpi_project": kpi}.items():
        # df.collect() + csv stdlib plutôt que df.write.csv() (HADOOP_HOME/winutils.exe
        # requis sur Windows) ou toPandas() (incompatible pyspark 3.5.3 / Python 3.12,
        # distutils retiré) : le volume tient largement en mémoire driver (< 1000 lignes).
        final_path = OUT_DIR / f"{name}.csv"
        rows = df.collect()
        with open(final_path, "w", newline="", encoding="utf-8") as f:
            writer = csv.writer(f)
            writer.writerow(df.columns)
            writer.writerows(rows)
        print(f"{name}.csv -> {final_path} ({len(rows)} lignes)")

    spark.stop()


if __name__ == "__main__":
    main()
