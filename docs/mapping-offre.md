# Mapping offre → réalisations

Offre ciblée : **Data Engineer and Business Tool Developer F/H** (Framatome,
BU I&C, réf. FRA-REC-2026-27266). Chaque exigence de l'offre est reliée à sa
preuve concrète dans ce repo.

## Data engineering

| Exigence de l'offre | Preuve dans ce projet |
|---|---|
| Recueillir, analyser, formaliser les besoins métier liés à la donnée | `docs/analyse-besoin.md` — cas d'usage PMO (jalons, budget, risques) traduit en modèle de données |
| Traduire les besoins en cas d'usage exploitables | 5 entités sources (`data/generate_data.py`) → marts KPI exploitables par Power BI |
| Concevoir/développer/maintenir des traitements de données sur plateforme data | `databricks/01_ingestion.py` → `04_agregats_kpi.py`, exécutés sur **Databricks Free Edition** (captures `outputs/databricks-0*.png`) |
| Transformation, préparation, fiabilisation des données en Azure Databricks, PySpark et SQL | `src/transformations.py` (PySpark : `clean_*`, `build_kpi_project`) + `sql/requetes_analytiques.sql` (Spark SQL) |
| Développer et automatiser les pipelines de données | Notebooks Databricks chaînés + `azure-pipelines.yml`/`.github/workflows/ci.yml` (exécution automatique à chaque push) |
| Participer à l'industrialisation des développements | Logique factorisée dans un module unique (`src/transformations.py`) importé à la fois par les notebooks et les tests — pas de duplication notebook/CI |
| Maintenance corrective et évolutive | Historique Git, tests de non-régression (`tests/`) qui échouent si une transformation casse une règle métier |
| Supervision, monitoring, contrôles | `run_quality_checks()` → table `monitoring_dq_results`, 10 contrôles (doublons, bornes, intégrité référentielle, valeurs aberrantes), PASS/FAIL exploitable en alerting |
| Qualité, cohérence, fiabilité, documentation des données | Données volontairement "sales" en entrée (doublons, valeurs hors bornes injectées) → corrigées et tracées, pas masquées ; `docs/data-dictionary.md` |

## Reporting et valorisation de la donnée

| Exigence de l'offre | Preuve dans ce projet |
|---|---|
| Concevoir/développer/maintenir des rapports et tableaux de bord Power BI | `powerbi/dashboard-pilotage-projets.pbix` — modèle étoile (dim_project + 3 facts + mart KPI), mesures DAX |
| Pertinence et fiabilité des indicateurs | Indicateurs calculés à partir des marts déjà contrôlés qualité (pas de recalcul divergent côté BI) |
| Amélioration continue des solutions de restitution | Voir `docs/analyse-besoin.md` § itérations (V1 KPI globaux → V2 drill-down risques/budget) |
| Accompagner/former les utilisateurs non spécialistes | README + `docs/data-dictionary.md` rédigés pour un lecteur métier, pas seulement technique |

## Profil souhaité

| Exigence | Preuve |
|---|---|
| Bac+5, expérience data engineering + BI/data analyse | Portfolio de 19 autres projets data (voir [index du portfolio](https://github.com/valentinratigniet-byte)) |
| Python, PySpark, SQL | `src/transformations.py`, `sql/requetes_analytiques.sql`, `tests/` |
| Azure Databricks, Azure DevOps | `databricks/` (Free Edition, gratuit, exécution prouvée par `outputs/databricks-0*.png` — voir limite assumée dans `databricks/README.md`), `azure-pipelines.yml` |
| Power BI | `powerbi/dashboard-pilotage-projets.pbix` |
| Traduire des besoins métier en solutions concrètes | Domaine choisi (pilotage de projets d'ingénierie : jalons, budget, risques) reproduit volontairement le type de données "Management de Projet" cité dans l'offre |

## Limite assumée, dite explicitement

Ce projet est une démonstration de compétences construite pour candidater, pas
un livrable en production chez Framatome/EDF — les données sont **synthétiques**
(générées, voir `data/generate_data.py`) et Databricks tourne en **Free
Edition** (gratuit) plutôt que sur un vrai workspace Azure d'entreprise. La
logique de code (PySpark, SQL, contrôles qualité, structure du pipeline) est en
revanche identique à ce qu'elle serait sur un environnement Azure Databricks
classique — voir `databricks/README.md` pour le détail de ce qui changerait.
