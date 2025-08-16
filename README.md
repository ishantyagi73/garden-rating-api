# SNG Garden Rating API (MVP)

Computes Crop Guess (broad), Stage, Health Score (0–5), Recommendations from a photo, and writes back to Airtable.

## Env
AIRTABLE_API_KEY=keyXXXX
AIRTABLE_BASE_ID=appXXXX
AIRTABLE_TABLE_NAME=Submissions
ATTACHMENT_FIELD=Photos
PORT=8000

## Run locally
pip install -r requirements.txt
uvicorn app:app --host 0.0.0.0 --port 8000
# test
curl -X POST http://localhost:8000/rate \
  -H "Content-Type: application/json" \
  -d '{"record_id":"recTEST","photo_url":"https://example.com/photo.jpg"}'

## Render (Web Service)
Build:  pip install -r requirements.txt
Start:  uvicorn app:app --host 0.0.0.0 --port $PORT
Env: AIRTABLE_API_KEY, AIRTABLE_BASE_ID, AIRTABLE_TABLE_NAME, ATTACHMENT_FIELD

## No paid Airtable? Use the poller
# Local
export AIRTABLE_API_KEY=keyXXXX
export AIRTABLE_BASE_ID=appXXXX
export AIRTABLE_TABLE_NAME=Submissions
export API_URL=https://YOUR-RENDER-API.onrender.com/rate
python poller.py

## Render Background Worker
Build:  pip install -r requirements.txt
Start:  python poller.py
Env: same as above + API_URL=https://YOUR-RENDER-API.onrender.com/rate
