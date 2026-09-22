"""Génère un jeu de données synthétique de portefeuille de projets d'ingénierie
(type PMO industriel : jalons, budget, risques, avancement) dans data/raw/.

Volontairement "sale" par endroits (doublons, valeurs nulles, avancement hors
bornes, incohérences de dates) pour que les contrôles qualité PySpark aient
vraiment quelque chose à détecter — voir src/transformations.py::run_quality_checks.
Seedé (SEED=20) pour être reproductible.
"""
import csv
import random
from datetime import date, timedelta
from pathlib import Path

from faker import Faker

SEED = 20
random.seed(SEED)
fake = Faker("fr_FR")
Faker.seed(SEED)

OUT_DIR = Path(__file__).parent / "raw"
OUT_DIR.mkdir(exist_ok=True)

PROGRAMS = ["Modernisation Site A", "Extension Ligne B", "Refonte Atelier C", "Qualification Produit D"]
DEPARTMENTS = ["Ingénierie", "Méthodes", "Qualité", "Achats"]
COST_CATEGORIES = ["Ingénierie", "Achats", "Sous-traitance", "Qualité"]
RISK_CATEGORIES = ["Technique", "Planning", "Fournisseur", "Qualité"]

N_PROJECTS = 40
TODAY = date(2026, 9, 1)


def random_date(start: date, end: date) -> date:
    delta = (end - start).days
    return start + timedelta(days=random.randint(0, max(delta, 0)))


def gen_projects():
    rows = []
    for i in range(1, N_PROJECTS + 1):
        project_id = f"PRJ-{i:04d}"
        start_planned = random_date(date(2024, 1, 1), date(2026, 3, 1))
        duration_days = random.randint(120, 540)
        end_planned = start_planned + timedelta(days=duration_days)
        # dérive réelle : la plupart glissent un peu, certains beaucoup
        slippage = int(random.gauss(20, 35))
        start_actual = start_planned + timedelta(days=max(0, int(random.gauss(3, 5))))
        finished = end_planned < TODAY and random.random() < 0.7
        end_actual = (end_planned + timedelta(days=slippage)) if finished else None
        budget_planned = round(random.uniform(80_000, 1_800_000), 2)
        status = "Terminé" if finished else random.choices(
            ["En cours", "Suspendu"], weights=[0.9, 0.1]
        )[0]
        rows.append({
            "project_id": project_id,
            "project_name": f"{random.choice(PROGRAMS)} - lot {i}",
            "program": random.choice(PROGRAMS),
            "department": random.choice(DEPARTMENTS),
            "project_manager": fake.name(),
            "start_date_planned": start_planned.isoformat(),
            "end_date_planned": end_planned.isoformat(),
            "start_date_actual": start_actual.isoformat(),
            "end_date_actual": end_actual.isoformat() if end_actual else "",
            "budget_planned_eur": budget_planned,
            "status": status,
        })
    # doublon volontaire (même project_id ré-exporté deux fois par l'outil source)
    rows.append(dict(rows[3]))
    return rows


def gen_milestones(projects):
    rows = []
    mid = 1
    for p in projects[:N_PROJECTS]:  # ne pas dupliquer les jalons du doublon
        start = date.fromisoformat(p["start_date_planned"])
        end = date.fromisoformat(p["end_date_planned"])
        n_milestones = random.randint(3, 6)
        for k in range(n_milestones):
            frac = (k + 1) / n_milestones
            date_planned = start + timedelta(days=int((end - start).days * frac))
            late_days = int(random.gauss(8, 25))
            reached = date_planned < TODAY and random.random() < 0.75
            date_actual = date_planned + timedelta(days=late_days) if reached else None
            if date_actual and date_actual > TODAY:
                date_actual = None
                reached = False
            status = "Atteint" if reached else ("En retard" if date_planned < TODAY else "À venir")
            rows.append({
                "milestone_id": f"MS-{mid:05d}",
                "project_id": p["project_id"],
                "milestone_name": f"Jalon {k + 1}/{n_milestones}",
                "type": random.choice(["Jalon contractuel", "Jalon interne"]),
                "date_planned": date_planned.isoformat(),
                "date_actual": date_actual.isoformat() if date_actual else "",
                "status": status,
            })
            mid += 1
    # incohérence volontaire : un jalon "Atteint" avec date_actual vide
    rows[5]["status"] = "Atteint"
    rows[5]["date_actual"] = ""
    return rows


def gen_budget_lines(projects):
    rows = []
    bid = 1
    for p in projects[:N_PROJECTS]:
        start = date.fromisoformat(p["start_date_planned"])
        end_str = p["end_date_actual"] or p["end_date_planned"]
        end = date.fromisoformat(end_str)
        months = max(1, (end.year - start.year) * 12 + (end.month - start.month) + 1)
        months = min(months, 30)
        monthly_planned = round(float(p["budget_planned_eur"]) / months, 2)
        # dérive de coûts corrélée au glissement planning (déjà présente dans end_date_actual)
        drift_factor = random.uniform(0.92, 1.35)
        for m in range(months):
            month = (start.replace(day=1) + timedelta(days=31 * m)).replace(day=1)
            actual = round(monthly_planned * drift_factor * random.uniform(0.85, 1.15), 2)
            rows.append({
                "budget_line_id": f"BL-{bid:06d}",
                "project_id": p["project_id"],
                "month": month.isoformat(),
                "cost_category": random.choice(COST_CATEGORIES),
                "amount_planned_eur": monthly_planned,
                "amount_actual_eur": actual,
            })
            bid += 1
    # valeur aberrante volontaire (saisie x100)
    rows[10]["amount_actual_eur"] = rows[10]["amount_actual_eur"] * 100
    return rows


def gen_risks(projects):
    rows = []
    rid = 1
    for p in projects[:N_PROJECTS]:
        for _ in range(random.randint(1, 5)):
            probability = random.randint(1, 5)
            impact = random.randint(1, 5)
            date_raised = random_date(date.fromisoformat(p["start_date_planned"]), TODAY)
            closed = random.random() < 0.5
            date_closed = random_date(date_raised, TODAY) if closed else None
            rows.append({
                "risk_id": f"RSK-{rid:05d}",
                "project_id": p["project_id"],
                "category": random.choice(RISK_CATEGORIES),
                "description": fake.sentence(nb_words=8),
                "probability": probability,
                "impact": impact,
                "status": "Clos" if closed else "Ouvert",
                "date_raised": date_raised.isoformat(),
                "date_closed": date_closed.isoformat() if date_closed else "",
            })
            rid += 1
    # probabilité hors bornes volontaire (erreur de saisie)
    rows[2]["probability"] = 7
    return rows


def gen_status_reports(projects):
    rows = []
    sid = 1
    for p in projects[:N_PROJECTS]:
        start = date.fromisoformat(p["start_date_planned"])
        end_str = p["end_date_actual"] or p["end_date_planned"]
        end = min(date.fromisoformat(end_str), TODAY)
        n_weeks = max(1, (end - start).days // 14)
        n_weeks = min(n_weeks, 20)
        for w in range(n_weeks):
            report_date = start + timedelta(days=14 * w)
            if report_date > TODAY:
                break
            advancement = round(min(100.0, max(0.0, (w + 1) / n_weeks * 100 * random.uniform(0.85, 1.05))), 1)
            rows.append({
                "report_id": f"RPT-{sid:06d}",
                "project_id": p["project_id"],
                "report_date": report_date.isoformat(),
                "advancement_pct": advancement,
                "reported_by": fake.name(),
                "comment": fake.sentence(nb_words=10),
            })
            sid += 1
    # avancement hors bornes volontaire + doublon report_id
    rows[7]["advancement_pct"] = 143.0
    rows.append(dict(rows[20]))
    return rows


def write_csv(rows, filename, fieldnames):
    path = OUT_DIR / filename
    with open(path, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)
    print(f"{filename}: {len(rows)} lignes -> {path}")


def main():
    projects = gen_projects()
    milestones = gen_milestones(projects)
    budget_lines = gen_budget_lines(projects)
    risks = gen_risks(projects)
    status_reports = gen_status_reports(projects)

    write_csv(projects, "projects.csv", list(projects[0].keys()))
    write_csv(milestones, "milestones.csv", list(milestones[0].keys()))
    write_csv(budget_lines, "budget_lines.csv", list(budget_lines[0].keys()))
    write_csv(risks, "risks.csv", list(risks[0].keys()))
    write_csv(status_reports, "status_reports.csv", list(status_reports[0].keys()))


if __name__ == "__main__":
    main()
