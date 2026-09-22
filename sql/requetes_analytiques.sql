-- Requêtes analytiques SQL sur les tables clean_*/mart_kpi_project
-- (Databricks SQL / Spark SQL — testables aussi via spark.sql() en local,
-- voir tests/test_transformations.py qui exerce la même logique en DataFrame API).

-- 1. Portefeuille : dérive budgétaire et retard par programme
SELECT
    program,
    COUNT(*) AS n_projects,
    ROUND(AVG(pct_milestones_late), 1) AS avg_pct_milestones_late,
    ROUND(SUM(budget_variance_eur), 0) AS total_budget_variance_eur,
    ROUND(SUM(budget_variance_eur) / NULLIF(SUM(budget_planned_to_date_eur), 0) * 100, 1) AS total_budget_variance_pct
FROM mart_kpi_project
GROUP BY program
ORDER BY total_budget_variance_eur DESC;

-- 2. Top 10 projets les plus en dérive budgétaire (en valeur absolue)
SELECT
    project_id,
    project_name,
    department,
    budget_planned_to_date_eur,
    budget_actual_to_date_eur,
    budget_variance_eur,
    ROUND(budget_variance_pct, 1) AS budget_variance_pct
FROM mart_kpi_project
WHERE budget_variance_eur IS NOT NULL
ORDER BY ABS(budget_variance_eur) DESC
LIMIT 10;

-- 3. Projets à risque : jalons en retard ET risques ouverts de sévérité élevée
SELECT
    project_id,
    project_name,
    pct_milestones_late,
    n_open_risks_high_severity,
    latest_advancement_pct
FROM mart_kpi_project
WHERE pct_milestones_late > 30 AND n_open_risks_high_severity > 0
ORDER BY pct_milestones_late DESC;

-- 4. Historique des contrôles qualité en échec (table de supervision)
SELECT run_at, `table`, `check`, n_violations, status
FROM monitoring_dq_results
WHERE status = 'FAIL'
ORDER BY run_at DESC;

-- 5. Répartition des risques ouverts par catégorie et sévérité
SELECT
    category,
    CASE WHEN probability * impact >= 15 THEN 'Élevée'
         WHEN probability * impact >= 8  THEN 'Moyenne'
         ELSE 'Faible' END AS severity_bucket,
    COUNT(*) AS n_risks
FROM clean_risks
WHERE status = 'Ouvert'
GROUP BY category, severity_bucket
ORDER BY category, severity_bucket;
