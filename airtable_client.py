import requests
import json

def update_airtable_record(api_key: str, base_id: str, table_name: str, record_id: str, fields: dict):
    url = f"https://api.airtable.com/v0/{base_id}/{table_name}/{record_id}"
    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json",
    }
    data = {"fields": fields}
    r = requests.patch(url, headers=headers, data=json.dumps(data), timeout=20)
    if r.status_code >= 300:
        raise RuntimeError(f"HTTP {r.status_code}: {r.text}")
    return r.json()
