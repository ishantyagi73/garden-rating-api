import os
import io
import requests
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel, HttpUrl
from typing import Optional
from PIL import Image

from heuristics import (
    estimate_green_fraction,
    estimate_yellow_brown_fraction,
    estimate_edge_density,
    guess_crop_family,
    guess_stage,
)
from airtable_client import update_airtable_record

AIRTABLE_API_KEY = os.getenv("AIRTABLE_API_KEY")
AIRTABLE_BASE_ID = os.getenv("AIRTABLE_BASE_ID")
AIRTABLE_TABLE_NAME = os.getenv("AIRTABLE_TABLE_NAME")
# If your attachment field/table names differ, edit here & in poller.py
ATTACHMENT_FIELD = os.getenv("ATTACHMENT_FIELD", "Photos")

app = FastAPI(title="SNG Garden Rating API", version="0.1.0")


class RatePayload(BaseModel):
    record_id: str
    photo_url: HttpUrl
    school_name: Optional[str] = None


@app.get("/health")
def health():
    ok = all([AIRTABLE_API_KEY, AIRTABLE_BASE_ID, AIRTABLE_TABLE_NAME])
    return {"status": "ok" if ok else "missing_env", "table": AIRTABLE_TABLE_NAME}


@app.post("/rate")
def rate(payload: RatePayload):
    # 1) Download image
    try:
        r = requests.get(str(payload.photo_url), timeout=20)
        r.raise_for_status()
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Failed to download image: {e}")
    try:
        img = Image.open(io.BytesIO(r.content)).convert("RGB")
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Failed to decode image: {e}")

    # 2) Compute simple features
    green_frac = estimate_green_fraction(img)
    yellow_brown_frac = estimate_yellow_brown_fraction(img)
    edge_density = estimate_edge_density(img)

    # 3) Guess crop family + stage (broad, heuristic)
    crop_guess = guess_crop_family(green_frac, edge_density, img)
    stage_guess = guess_stage(green_frac, edge_density, yellow_brown_frac, img)

    # 4) Health score (0–5)
    health = 5.0 * (0.5 * green_frac + 0.3 * edge_density + 0.2 * (1.0 - yellow_brown_frac))
    health = max(0.0, min(5.0, round(health, 1)))

    # 5) Recommendations (2–3 bullets)
    recs = []
    if yellow_brown_frac > 0.22:
        recs.append("Some yellowing detected—consider a balanced feed or compost tea.")
    if edge_density < 0.25:
        recs.append("Sparse canopy—check watering consistency and spacing; remove weeds.")
    if green_frac > 0.55 and edge_density > 0.30:
        recs.append("Vigorous growth—maintain irrigation; stake/trellis if vining.")
    if not recs:
        recs = [
            "Maintain regular irrigation.",
            "Mulch around base to reduce weeds and retain moisture.",
        ]

    # 6) Update Airtable
    if not all([AIRTABLE_API_KEY, AIRTABLE_BASE_ID, AIRTABLE_TABLE_NAME]):
        # Return results but don't attempt to update if env missing
        return {
            "record_id": payload.record_id,
            "crop_guess": crop_guess,
            "stage": stage_guess,
            "health_score": health,
            "recommendations": recs,
            "note": "Missing Airtable env vars; not updating record.",
        }

    fields = {
        "Crop Guess": crop_guess,
        "Stage": stage_guess,
        "Health Score": health,
        "Recommendations": "\n".join("• " + x for x in recs),
        "Processed?": True,
    }
    try:
        update_airtable_record(
            api_key=AIRTABLE_API_KEY,
            base_id=AIRTABLE_BASE_ID,
            table_name=AIRTABLE_TABLE_NAME,
            record_id=payload.record_id,
            fields=fields,
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Airtable update failed: {e}")

    return {
        "record_id": payload.record_id,
        "crop_guess": crop_guess,
        "stage": stage_guess,
        "health_score": health,
        "recommendations": recs,
    }
