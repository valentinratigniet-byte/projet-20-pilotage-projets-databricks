# Dictionnaire de données

## Sources brutes (`data/raw/*.csv`, générées par `data/generate_data.py`)

### projects
| Colonne | Type | Description |
|---|---|---|
| project_id | texte | Identifiant unique (`PRJ-0001`...) |
| project_name | texte | Nom du projet |
| program | texte | Programme de rattachement |
| department | texte | Département porteur |
| project_manager | texte | Chef de projet |
| start_date_planned / end_date_planned | date | Dates prévues |
| start_date_actual / end_date_actual | date | Dates réelles (vide si non démarré/terminé) |
| budget_planned_eur | nombre | Budget total prévu |
| status | texte | `En cours` / `Terminé` / `Suspendu` |

### milestones
| Colonne | Type | Description |
|---|---|---|
| milestone_id | texte | Identifiant unique |
| project_id | texte | Clé étrangère vers `projects` |
| milestone_name, type | texte | Nom, `Jalon contractuel`/`Jalon interne` |
| date_planned / date_actual | date | Date prévue / réelle |
| status | texte | `À venir` / `Atteint` / `En retard` |

### budget_lines
| Colonne | Type | Description |
|---|---|---|
| budget_line_id | texte | Identifiant unique |
| project_id | texte | Clé étrangère |
| month | date | Mois de la ligne budgétaire |
| cost_category | texte | Ingénierie / Achats / Sous-traitance / Qualité |
| amount_planned_eur / amount_actual_eur | nombre | Montant prévu / réel du mois |

### risks
| Colonne | Type | Description |
|---|---|---|
| risk_id | texte | Identifiant unique |
| project_id | texte | Clé étrangère |
| category | texte | Technique / Planning / Fournisseur / Qualité |
| probability, impact | entier 1-5 | Échelle de cotation |
| status | texte | `Ouvert` / `Clos` |
| date_raised / date_closed | date | Dates |

### status_reports
| Colonne | Type | Description |
|---|---|---|
| report_id | texte | Identifiant unique |
| project_id | texte | Clé étrangère |
| report_date | date | Date du compte-rendu |
| advancement_pct | nombre | Avancement physique déclaré (0-100) |
| reported_by, comment | texte | Métadonnées |

## Tables fiabilisées (`clean_*`, produites par `src/transformations.py`)

Mêmes colonnes que les tables brutes, plus :
- `projects.slippage_days` : écart en jours entre fin réelle et fin prévue.
- `milestones.delay_days` : écart en jours entre jalon réel et prévu ; `status`
  corrigé (`Atteint` sans date réelle → `À vérifier`).
- `budget_lines.is_outlier` : `true` si le montant réel dépasse 5× la médiane
  de sa catégorie de coût (valeur conservée, pas supprimée).
- `risks.severity` : `probability × impact`, bornés à [1,5] au préalable.

## Mart KPI (`mart_kpi_project`, une ligne par projet)

| Colonne | Description |
|---|---|
| pct_milestones_late | % de jalons au statut "En retard" |
| avg_delay_days | Retard moyen (jours) des jalons atteints |
| budget_planned_to_date_eur / budget_actual_to_date_eur | Cumuls prévu/réel (hors lignes `is_outlier`) |
| budget_variance_eur / budget_variance_pct | Dérive budgétaire, absolue et relative |
| n_open_risks / n_open_risks_high_severity | Risques ouverts, dont sévérité ≥ 15 (échelle 1-25) |
| latest_advancement_pct | Dernier avancement déclaré |

## Table de supervision (`monitoring_dq_results`)

Une ligne par contrôle qualité exécuté : `table`, `check`, `n_violations`,
`status` (`PASS`/`FAIL`). Voir `src/transformations.py::run_quality_checks`
pour la liste des 10 contrôles.
