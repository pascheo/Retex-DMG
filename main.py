import csv
import io
import os
import sqlite3
from contextlib import contextmanager
from datetime import date, datetime
from typing import Optional

from fastapi import Cookie, FastAPI, Form, HTTPException, Request, Response
from fastapi.responses import HTMLResponse, RedirectResponse, StreamingResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates

ADMIN_PASSWORD = os.environ.get("ADMIN_PASSWORD", "dmg2024")
DB_PATH = os.path.join(os.path.dirname(__file__), "retex_dmg.db")

QUESTIONS = [
    # Section 1 – Messagerie & Communication
    (1, "Accès et connexion à la messagerie Outlook via navigateur web", 1),
    (2, "Lecture, envoi et gestion des e-mails au quotidien", 1),
    (3, "Utilisation du calendrier Outlook (réunions, disponibilités)", 1),
    (4, "Utilisation de Microsoft Teams (réunions, messages instantanés, appels)", 1),
    (5, "Partage de documents via Teams", 1),
    # Section 2 – Accès aux documents & SharePoint
    (6, "Accès aux fichiers et documents depuis SharePoint (anciennement sur serveur)", 2),
    (7, "Navigation dans les bibliothèques de documents SharePoint", 2),
    (8, "Recherche de documents dans SharePoint", 2),
    (9, "Partage et collaboration sur des documents SharePoint", 2),
    (10, "Synchronisation et accès hors connexion aux documents", 2),
    # Section 3 – Outils bureautiques en ligne
    (11, "Utilisation de Word en version web (création, édition de documents)", 3),
    (12, "Utilisation d'Excel en version web (tableurs, formules)", 3),
    (13, "Utilisation de PowerPoint en version web (présentations)", 3),
    (14, "Compatibilité des fichiers existants avec les outils web", 3),
    (15, "Performance et réactivité des outils web (vitesse, stabilité)", 3),
    # Section 4 – Migration des données
    (16, "Retrouver facilement les données migrées depuis les anciens serveurs", 4),
    (17, "Organisation et structure des dossiers après migration", 4),
    (18, "Absence de perte ou d'altération de données suite à la migration", 4),
    (19, "Facilité de travail collaboratif depuis la migration", 4),
    # Section 5 – Expérience générale & Support
    (20, "Facilité de prise en main de l'ensemble des outils E1", 5),
    (21, "Autonomie dans l'utilisation des outils au quotidien", 5),
    (22, "Qualité du support et accompagnement lors du POC", 5),
    (23, "Réponse aux besoins métier avec les outils disponibles", 5),
    (24, "Satisfaction globale avec la licence E1 et les usages web", 5),
]

SECTIONS = {
    1: "Messagerie & Communication (Outlook Web / Teams Web)",
    2: "Accès aux documents & SharePoint",
    3: "Outils bureautiques en ligne (Office Web Apps)",
    4: "Migration des données (Serveurs → SharePoint)",
    5: "Expérience générale & Support",
}

app = FastAPI(title="REX DMG – Full Cloud CD78")
app.mount("/static", StaticFiles(directory="static"), name="static")
templates = Jinja2Templates(directory="templates")


def init_db():
    with sqlite3.connect(DB_PATH) as conn:
        conn.execute("""
            CREATE TABLE IF NOT EXISTS responses (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                nom_prenom TEXT NOT NULL,
                service TEXT NOT NULL,
                date_completion TEXT NOT NULL,
                date_soumission TEXT NOT NULL,
                remarques_generales TEXT
            )
        """)
        conn.execute("""
            CREATE TABLE IF NOT EXISTS answers (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                response_id INTEGER NOT NULL REFERENCES responses(id),
                question_id INTEGER NOT NULL,
                note INTEGER,
                sans_objet INTEGER NOT NULL DEFAULT 0,
                commentaire TEXT
            )
        """)
        conn.commit()


@contextmanager
def get_db():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    try:
        yield conn
    finally:
        conn.close()


init_db()


@app.get("/", response_class=HTMLResponse)
async def form_page(request: Request):
    today = date.today().isoformat()
    return templates.TemplateResponse("form.html", {
        "request": request,
        "questions": QUESTIONS,
        "sections": SECTIONS,
        "today": today,
    })


@app.post("/submit")
async def submit_form(request: Request):
    form = await request.form()

    nom_prenom = form.get("nom_prenom", "").strip()
    service = form.get("service", "").strip()
    date_completion = form.get("date_completion", date.today().isoformat())
    remarques = form.get("remarques_generales", "").strip()

    if not nom_prenom or not service:
        return templates.TemplateResponse("form.html", {
            "request": request,
            "questions": QUESTIONS,
            "sections": SECTIONS,
            "today": date.today().isoformat(),
            "error": "Le nom/prénom et le service sont obligatoires.",
        }, status_code=400)

    # Check for duplicate submission (same name + same date)
    with get_db() as conn:
        existing = conn.execute(
            "SELECT id FROM responses WHERE nom_prenom = ? AND date_completion = ?",
            (nom_prenom, date_completion)
        ).fetchone()
        duplicate_warning = existing is not None

        date_soumission = datetime.now().isoformat(timespec="seconds")
        cursor = conn.execute(
            "INSERT INTO responses (nom_prenom, service, date_completion, date_soumission, remarques_generales) VALUES (?,?,?,?,?)",
            (nom_prenom, service, date_completion, date_soumission, remarques)
        )
        response_id = cursor.lastrowid

        for q_id, _, _ in QUESTIONS:
            sans_objet = 1 if form.get(f"sans_objet_{q_id}") == "on" else 0
            note_raw = form.get(f"note_{q_id}")
            note = None if sans_objet or not note_raw else int(note_raw)
            commentaire = form.get(f"commentaire_{q_id}", "").strip() or None
            conn.execute(
                "INSERT INTO answers (response_id, question_id, note, sans_objet, commentaire) VALUES (?,?,?,?,?)",
                (response_id, q_id, note, sans_objet, commentaire)
            )
        conn.commit()

    return templates.TemplateResponse("form.html", {
        "request": request,
        "questions": QUESTIONS,
        "sections": SECTIONS,
        "today": date.today().isoformat(),
        "success": True,
        "duplicate_warning": duplicate_warning,
    })


# ---------- Admin auth ----------

def check_admin(admin_token: Optional[str] = Cookie(None)) -> bool:
    return admin_token == ADMIN_PASSWORD


@app.get("/admin/login", response_class=HTMLResponse)
async def admin_login_page(request: Request):
    return templates.TemplateResponse("admin.html", {
        "request": request,
        "login_page": True,
        "sections": SECTIONS,
    })


@app.post("/admin/login")
async def admin_login(password: str = Form(...)):
    if password != ADMIN_PASSWORD:
        raise HTTPException(status_code=401, detail="Mot de passe incorrect")
    response = RedirectResponse("/admin", status_code=303)
    response.set_cookie("admin_token", ADMIN_PASSWORD, httponly=True, samesite="strict")
    return response


@app.get("/admin/logout")
async def admin_logout():
    response = RedirectResponse("/admin/login", status_code=303)
    response.delete_cookie("admin_token")
    return response


@app.get("/admin", response_class=HTMLResponse)
async def admin_dashboard(request: Request, service_filter: str = "", admin_token: Optional[str] = Cookie(None)):
    if not check_admin(admin_token):
        return RedirectResponse("/admin/login", status_code=303)

    with get_db() as conn:
        query = "SELECT * FROM responses"
        params: list = []
        if service_filter:
            query += " WHERE service LIKE ?"
            params.append(f"%{service_filter}%")
        query += " ORDER BY date_soumission DESC"
        respondents = conn.execute(query, params).fetchall()

        # Per-respondent average note
        enriched = []
        for r in respondents:
            answers = conn.execute(
                "SELECT note FROM answers WHERE response_id = ? AND sans_objet = 0 AND note IS NOT NULL",
                (r["id"],)
            ).fetchall()
            notes = [a["note"] for a in answers]
            avg = round(sum(notes) / len(notes), 2) if notes else None
            enriched.append({"row": dict(r), "avg": avg})

        # Global section averages
        section_avgs = {}
        for sec_id in SECTIONS:
            q_ids = [q[0] for q in QUESTIONS if q[2] == sec_id]
            placeholders = ",".join("?" * len(q_ids))
            rows = conn.execute(
                f"SELECT note FROM answers WHERE question_id IN ({placeholders}) AND sans_objet = 0 AND note IS NOT NULL",
                q_ids
            ).fetchall()
            notes = [row["note"] for row in rows]
            section_avgs[sec_id] = round(sum(notes) / len(notes), 2) if notes else None

        # Unique services for filter
        services = [row[0] for row in conn.execute("SELECT DISTINCT service FROM responses ORDER BY service").fetchall()]

    return templates.TemplateResponse("admin.html", {
        "request": request,
        "login_page": False,
        "respondents": enriched,
        "section_avgs": section_avgs,
        "sections": SECTIONS,
        "services": services,
        "service_filter": service_filter,
        "total": len(enriched),
    })


@app.get("/admin/detail/{response_id}", response_class=HTMLResponse)
async def admin_detail(response_id: int, request: Request, admin_token: Optional[str] = Cookie(None)):
    if not check_admin(admin_token):
        return RedirectResponse("/admin/login", status_code=303)

    with get_db() as conn:
        row = conn.execute("SELECT * FROM responses WHERE id = ?", (response_id,)).fetchone()
        if not row:
            raise HTTPException(status_code=404, detail="Réponse introuvable")
        answers = conn.execute(
            "SELECT * FROM answers WHERE response_id = ? ORDER BY question_id",
            (response_id,)
        ).fetchall()

    q_map = {q[0]: q[1] for q in QUESTIONS}
    answers_enriched = [
        {"answer": dict(a), "label": q_map.get(a["question_id"], "")}
        for a in answers
    ]

    return templates.TemplateResponse("admin.html", {
        "request": request,
        "login_page": False,
        "detail_view": True,
        "respondent": dict(row),
        "answers": answers_enriched,
        "sections": SECTIONS,
        "questions": QUESTIONS,
    })


@app.get("/admin/export")
async def export_csv(admin_token: Optional[str] = Cookie(None)):
    if not check_admin(admin_token):
        raise HTTPException(status_code=401, detail="Non autorisé")

    with get_db() as conn:
        responses = conn.execute("SELECT * FROM responses ORDER BY date_soumission DESC").fetchall()

    output = io.StringIO()
    writer = csv.writer(output, delimiter=";")

    # Header
    header = ["ID", "Nom/Prénom", "Service", "Date complétion", "Date soumission"]
    for q_id, label, _ in QUESTIONS:
        header += [f"Q{q_id}_note", f"Q{q_id}_sans_objet", f"Q{q_id}_commentaire"]
    header.append("Remarques générales")
    writer.writerow(header)

    with get_db() as conn:
        for r in responses:
            answers = conn.execute(
                "SELECT * FROM answers WHERE response_id = ? ORDER BY question_id",
                (r["id"],)
            ).fetchall()
            a_map = {a["question_id"]: a for a in answers}

            row_data = [r["id"], r["nom_prenom"], r["service"], r["date_completion"], r["date_soumission"]]
            for q_id, _, _ in QUESTIONS:
                a = a_map.get(q_id)
                if a:
                    row_data += [
                        "" if a["sans_objet"] else (a["note"] or ""),
                        "Oui" if a["sans_objet"] else "Non",
                        a["commentaire"] or "",
                    ]
                else:
                    row_data += ["", "", ""]
            row_data.append(r["remarques_generales"] or "")
            writer.writerow(row_data)

    output.seek(0)
    filename = f"retex_dmg_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv"
    return StreamingResponse(
        iter([output.getvalue()]),
        media_type="text/csv; charset=utf-8-sig",
        headers={"Content-Disposition": f'attachment; filename="{filename}"'},
    )


@app.get("/api/stats")
async def api_stats(admin_token: Optional[str] = Cookie(None)):
    if not check_admin(admin_token):
        raise HTTPException(status_code=401, detail="Non autorisé")

    with get_db() as conn:
        total = conn.execute("SELECT COUNT(*) FROM responses").fetchone()[0]
        section_avgs = {}
        for sec_id in SECTIONS:
            q_ids = [q[0] for q in QUESTIONS if q[2] == sec_id]
            placeholders = ",".join("?" * len(q_ids))
            rows = conn.execute(
                f"SELECT note FROM answers WHERE question_id IN ({placeholders}) AND sans_objet = 0 AND note IS NOT NULL",
                q_ids
            ).fetchall()
            notes = [row[0] for row in rows]
            section_avgs[str(sec_id)] = round(sum(notes) / len(notes), 2) if notes else None

    return {"total_responses": total, "section_averages": section_avgs, "sections": SECTIONS}
