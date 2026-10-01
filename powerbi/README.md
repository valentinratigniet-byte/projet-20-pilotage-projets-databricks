# dashboard-pilotage-projets.pbix

Modèle construit via le MCP `powerbi-modeling` (comme les projets 01/09/13 du
portfolio) : étoile `dim_project` + 3 faits (`fact_budget_lines`,
`fact_risks`, `fact_milestones`) + mart pré-agrégé `mart_kpi_project`
(relation 1:1 bidirectionnelle avec `dim_project`), 16 mesures DAX réparties
en 4 dossiers d'affichage (Portefeuille, Budget, Jalons, Risques, Avancement).

La construction des **visuels** (cartes, graphiques, mise en page) s'est faite
dans Power BI Desktop — le MCP ne pilote que la couche modèle, pas le canevas
de rapport. Captures des 3 pages dans `../outputs/` (et dans le
[README principal](../README.md#-aperçu)). Détail des visuels :

## Page 1 — Portefeuille
- Cartes : `Nb projets`, `Dérive budgétaire (€)`, `Dérive budgétaire (%)`,
  `% jalons en retard (moyenne)`
- Barres (`program` en axe) : `Dérive budgétaire (€)` par programme
- Table : projets triés par `Dérive budgétaire (€)` décroissant (top 10)

## Page 2 — Budget
- Courbe : `Montant budget prévu (lignes)` vs `Montant budget réel (lignes)`
  par mois (`fact_budget_lines[month]`)
- Barres empilées : montant réel par `cost_category`
- Indicateur : `% projets en dépassement`

## Page 3 — Risques
- Matrice/nuage de points : `probability` × `impact` (taille = nombre de
  risques), filtré `status = Ouvert`
- Carte : `Risques ouverts sévérité élevée`
- Table : risques ouverts sévérité ≥ 15, triés par `severity` décroissant

Thème portfolio (Petrol & Ambre) déjà appliqué dans le `.pbix` fourni —
Petrol `#137A8B` (signature), Ambre `#E4A93C` (accent), vert `#2FA36B` /
rouge `#D9534F` (sémantique). Pour le réappliquer après une recréation du
modèle (Affichage → Thèmes dans Power BI Desktop) : fichier de thème
personnel de Valentin, non versionné dans ce repo — reproductible avec ces
codes couleur sans dépendre du fichier original.

Pour régénérer les données sources après un nouveau `python
scripts/export_for_powerbi.py` : **Accueil → Actualiser** dans Power BI
Desktop (le modèle pointe vers les CSV de `data/powerbi_export/`, pas de
reconstruction nécessaire).
