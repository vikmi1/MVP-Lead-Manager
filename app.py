from contextlib import asynccontextmanager
from fastapi import FastAPI, Depends, HTTPException

import config
import database
import notifier
from auth import verify_api_key
from models import LeadCreate, LeadOut


@asynccontextmanager
async def lifespan(app: FastAPI):
    database.init_db(config.DB_PATH)
    yield


app = FastAPI(title="Lead-Capture Service", version="1.0.0", lifespan=lifespan)


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
