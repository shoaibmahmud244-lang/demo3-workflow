# Demo 3 — form-to-CRM automation

A webhook-triggered pipeline: form submission → validation → CRM upsert →
per-contact email. Everything the listing claims is produced by `automate.py`,
and `run_log.txt` is a real execution log, not an illustration.

## What it does

1. Receives a batch of form submissions
2. Validates each record and rejects the invalid ones
3. Upserts valid contacts into a CSV, keyed on email — re-running does not
   create duplicates
4. Queues a personalised email per accepted contact
5. Logs every step with timestamps

## Files

| File | Purpose |
|---|---|
| `automate.py` | The workflow |
| `form_submissions.json` | Input payloads (5 records, 2 deliberately invalid) |
| `crm_contacts.csv` | Output — accepted contacts after upsert |
| `run_log.txt` | Timestamped execution log, appended per run |

## Run it

```bash
python3 automate.py
```

Idempotent by design: run it as many times as you like, `crm_contacts.csv`
converges on the same rows.

## Two bugs found by running it twice instead of once

**The run log destroyed itself.** It was opened with mode `"w"`, so every run
overwrote the previous log. That matters more than it looks: the second run
correctly re-validated all five contacts as duplicates and reported
`Upserted 0 contacts` — while `crm_contacts.csv` still held three rows. The log
did not merely get lost, it **contradicted the data**. The file is now the
evidence that the workflow ran, so it appends behind a separator instead.

**`os` was never imported.** Found while fixing the first one — a missing-import
defect on the same code path, and the same class of bug the scraper demo had.

`run_log.txt` in this repo contains three runs, so the append behaviour is
visible in the history rather than just described.
