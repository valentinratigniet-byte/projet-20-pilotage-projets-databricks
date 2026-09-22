# Analyse du besoin métier

## Contexte simulé

Une direction de projets d'ingénierie (type BU Instrumentation & Contrôle-
Commande) pilote un portefeuille de ~40 projets simultanés. Chaque projet a un
planning, un budget, des risques et un avancement suivis dans des outils
différents (planning, ERP achats, registre des risques, comptes-rendus
hebdomadaires) — **aucune vue consolidée** n'existe pour la direction de
programme : impossible de répondre vite à "quels projets dérivent, et de
combien ?".

## Besoin exprimé (reformulé en cas d'usage)

1. **Suivi des délais** — savoir, par projet et par programme, quel pourcentage
   de jalons est en retard et de combien de jours en moyenne.
2. **Suivi budgétaire** — comparer budget prévu vs réalisé par projet, par
   catégorie de coût (ingénierie, achats, sous-traitance, qualité) et par mois.
3. **Suivi des risques** — remonter les risques ouverts de sévérité élevée
   (probabilité × impact) qui menacent le planning ou le budget.
4. **Fiabilité des données sources** — les remontées manuelles (comptes-rendus
   hebdomadaires) contiennent des erreurs de saisie (avancement > 100 %,
   doublons) qu'il faut détecter avant qu'elles ne faussent un comité de
   pilotage.

## Traduction en solution technique

- Cas d'usage 1-3 → un mart unique **`mart_kpi_project`** (une ligne par
  projet, tous les indicateurs prêts à consommer par Power BI) pour que la
  direction n'ait pas à croiser 4 tables pour une lecture simple.
- Cas d'usage 4 → des **contrôles qualité automatisés** (`run_quality_checks`)
  qui tournent à chaque exécution du pipeline et écrivent leur résultat dans
  une table de supervision (`monitoring_dq_results`), plutôt qu'une
  vérification manuelle ponctuelle.

## Itérations

- **V1** (ce repo) : KPI globaux par projet/programme dans `mart_kpi_project`,
  dashboard Power BI avec vue portefeuille + détail budgétaire + risques.
- **V2 (piste, non développée)** : drill-down par catégorie de coût dans le
  temps (courbe planned vs actual mensuelle), alerte automatique (Teams/e-mail)
  quand `monitoring_dq_results` contient un `FAIL` — non construit ici pour
  rester dans le périmètre réellement démontré par l'offre plutôt que
  d'ajouter une intégration non demandée.
