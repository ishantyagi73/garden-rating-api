// Airtable Automation "Run script"
// Trigger: When a record is created
// Inputs: recordId from trigger

const API_URL = 'https://YOUR-RENDER-URL.onrender.com/rate'; // change
const TABLE = 'Submissions'; // change if needed
const ATTACHMENT_FIELD = 'Photos'; // exact field name

let inputConfig = input.config();
let recordId = inputConfig.recordId;

let table = base.getTable(TABLE);
let record = await table.selectRecordAsync(recordId);

if (!record) {
  output.markdown('Record not found');
  return;
}
let attachments = record.getCellValue(ATTACHMENT_FIELD);
if (!attachments || attachments.length === 0) {
  output.markdown('No attachments');
  return;
}
let photoUrl = attachments[0].url;

let payload = {
  record_id: recordId,
  photo_url: photoUrl,
  school_name: record.getCellValueAsString('School Name') || null
};

let res = await fetch(API_URL, {
  method: 'POST',
  headers: {'Content-Type': 'application/json'},
  body: JSON.stringify(payload)
});
let text = await res.text();
output.markdown(text);
