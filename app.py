import asyncio
import csv
import io
import json
from contextlib import asynccontextmanager
from pathlib import Path
from fastapi import FastAPI, Depends, HTTPException, Request
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from fastapi.responses import RedirectResponse, Response

import config
import database
import demo
import notifier
from auth import verify_api_key
from models import LeadCreate, LeadOut


@asynccontextmanager
async def lifespan(app: FastAPI):
    database.init_db(config.DB_PATH)
    reset_task = None
    if config.DEMO_MODE:
        demo.reset_demo_data(config.DB_PATH)
        reset_task = asyncio.create_task(
            demo.reset_periodically(config.DB_PATH, config.DEMO_RESET_MINUTES)
        )
    yield
    if reset_task:
        reset_task.cancel()


app = FastAPI(title="Lead-Capture Service", version="1.0.0", lifespan=lifespan)

BASE_DIR = Path(__file__).parent
templates = Jinja2Templates(directory=str(BASE_DIR / "templates"))
templates.env.globals["demo_mode"] = config.DEMO_MODE
templates.env.globals["demo_reset_minutes"] = config.DEMO_RESET_MINUTES
app.mount("/static", StaticFiles(directory=str(BASE_DIR / "static")), name="static")


@app.post("/lead", status_code=201)
def create_lead(lead: LeadCreate):
    try:
        lead_id = database.create_lead(
            config.DB_PATH,
            lead.name,
            lead.contact,
            lead.source,
            lead.comment,
            lead.consent,
        )
    except Exception:
        raise HTTPException(status_code=500, detail="db error")

    notifier.log_event(lead_id, lead.contact, lead.source)

    try:
        notifier.send_email(lead_id, lead.name, lead.contact, lead.source, lead.comment)
    except Exception:
        pass

    try:
        notifier.send_to_sheet(
            lead_id, lead.name, lead.contact, lead.source, lead.comment, lead.consent
        )
    except Exception:
        pass

    return {
        "status": "ok",
        "message": "Anfrage gespeichert",
        "lead_id": lead_id,
    }


@app.get("/leads", response_model=list[LeadOut])
def get_leads(
    limit: int = 50,
    offset: int = 0,
    _: str = Depends(verify_api_key),
):
    try:
        return database.get_leads(config.DB_PATH, limit, offset)
    except Exception:
        raise HTTPException(status_code=500, detail="db error")


@app.delete("/lead/{lead_id}")
def delete_lead(lead_id: int, _: str = Depends(verify_api_key)):
    deleted = database.delete_lead(config.DB_PATH, lead_id)
    if not deleted:
        raise HTTPException(status_code=404, detail="not found")
    return {"status": "ok", "message": f"Lead {lead_id} deleted"}


@app.get("/", include_in_schema=False)
def form_page(request: Request):
    return templates.TemplateResponse(request, "form.html")


@app.get("/admin", include_in_schema=False)
def admin_page(request: Request):
    leads = database.get_leads(config.DB_PATH)
    return templates.TemplateResponse(request, "admin.html", {"leads": leads})


@app.post("/admin/delete/{lead_id}", include_in_schema=False)
def admin_delete(request: Request, lead_id: int):
    database.delete_lead(config.DB_PATH, lead_id)
    return RedirectResponse(url=f"{request.scope.get('root_path', '')}/admin", status_code=303)


# Большой лимит, чтобы экспортировать все заявки, а не только первые 50
EXPORT_LIMIT = 1_000_000
EXPORT_FIELDS = ["id", "created_at", "name", "contact", "source", "comment", "consent"]


@app.get("/admin/export.csv", include_in_schema=False)
def export_csv():
    leads = database.get_leads(config.DB_PATH, limit=EXPORT_LIMIT, offset=0)
    buffer = io.StringIO()
    writer = csv.DictWriter(buffer, fieldnames=EXPORT_FIELDS, extrasaction="ignore")
    writer.writeheader()
    for lead in leads:
        writer.writerow(lead)
    # BOM, чтобы Excel корректно показывал немецкие умляуты
    content = "﻿" + buffer.getvalue()
    return Response(
        content=content,
        media_type="text/csv; charset=utf-8",
        headers={"Content-Disposition": "attachment; filename=leads.csv"},
    )


@app.get("/admin/export.json", include_in_schema=False)
def export_json():
    leads = database.get_leads(config.DB_PATH, limit=EXPORT_LIMIT, offset=0)
    content = json.dumps(leads, ensure_ascii=False, indent=2)
    return Response(
        content=content,
        media_type="application/json; charset=utf-8",
        headers={"Content-Disposition": "attachment; filename=leads.json"},
    )
