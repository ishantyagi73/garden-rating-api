import os
import time
import requests

AIRTABLE_API_KEY = os.getenv("AIRTABLE_API_KEY")
AIRTABLE_BASE_ID = os.getenv("AIRTABLE_BASE_ID")
AIRTABLE_TABLE_NAME = os.getenv("AIRTABLE_TABLE_NAME", "Submissions")
AIRTABLE_VIEW = os.getenv("AIRTABLE_VIEW")  # optional
API_URL = os.getenv("API_URL", "http://localhost:8000/rate")
ATTACHMENT_FIELD = os.getenv("ATTACHMENT_FIELD", "Photos")

def list_unprocessed(limit=25):
    """Fetch records where Processed? is not checked and there is at least one attachment."""
    assert AIRTABLE_API_KEY and AIRTABLE_BASE_ID and AIRTABLE_TABLE_NAME, "Missing Airtable env vars"
    url = f"https://api.airtable.com/v0/{AIRTABLE_BASE_ID}/{AIRTABLE_TABLE_NAME}"
    headers = {"Authorization": f"Bearer {AIRTABLE_API_KEY}"}
    params = {
        "pageSize": limit,
        "filterByFormula": f"AND(NOT({{Processed?}}), ARRAY_LENGTH({{{ATTACHMENT_FIELD}}}) > 0)".replace("{ATTACHMENT_FIELD}", ATTACHMENT_FIELD),
    }
    if AIRTABLE_VIEW:
        params["view"] = AIRTABLE_VIEW
    r = requests.get(url, headers=headers, params=params, timeout=20)
    r.raise_for_status()
    return r.json().get("records", [])

def process_record(rec):
    rec_id = rec["id"]
    fields = rec.get("fields", {})
    attachments = fields.get(ATTACHMENT_FIELD, [])
    if not attachments:
        print(f"[skip] {rec_id} has no attachments")
        return
    photo_url = attachments[0]["url"]
    payload = {
        "record_id": rec_id,
        "photo_url": photo_url,
        "school_name": fields.get("School Name"),
    }
    try:
        r = requests.post(API_URL, json=payload, timeout=60)
        print(f"[rate] {rec_id} -> {r.status_code} {r.text[:140]}")
    except Exception as e:
        print(f"[error] {rec_id}: {e}")

def main():
    print("Poller started. Press Ctrl+C to stop.")
    while True:
        try:
            recs = list_unprocessed(limit=25)
            if not recs:
                print("No unprocessed records. Sleeping 30s...")
                time.sleep(30)
                continue
            for rec in recs:
                process_record(rec)
        except KeyboardInterrupt:
            print("Stopping.")
            break
        except Exception as e:
            print("Poller error:", e)
            time.sleep(15)

if __name__ == "__main__":
    main()
