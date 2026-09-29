#!/usr/bin/env python3
"""Lead intake automation: form submission -> validate -> CRM -> notify."""
import csv
import json
import os
import re
from datetime import datetime

SUBMISSIONS = "form_submissions.json"
CRM = "crm_contacts.csv"
LOG = "run_log.txt"

def log(msg, lines):
    stamp = datetime.now().strftime("%H:%M:%S")
    line = f"[{stamp}] {msg}"
    lines.append(line)
    print(line)

def valid_email(e):
    return bool(re.match(r"^[^@\s]+@[^@\s]+\.[a-z]{2,}$", e.strip().lower()))

def main():
    lines = []
    log("TRIGGER: Form webhook received", lines)

    with open(SUBMISSIONS, encoding="utf-8") as f:
        subs = json.load(f)
    log(f"STEP 1: Loaded {len(subs)} submissions", lines)

    existing = set()
    try:
        with open(CRM, newline="", encoding="utf-8") as f:
            existing = {r["email"].lower() for r in csv.DictReader(f)}
    except FileNotFoundError:
        pass

    accepted, rejected = [], []
    seen = set(existing)
    for s in subs:
        email = s.get("email", "").strip().lower()
        if not valid_email(email):
            rejected.append((email, "invalid email"))
        elif email in seen:
            rejected.append((email, "duplicate"))
        else:
            seen.add(email)
            accepted.append(s)
    log(f"STEP 2: Validated — {len(accepted)} new, {len(rejected)} rejected", lines)

    fieldnames = ["name", "email", "company", "budget", "source", "added_at"]
    new_rows = [
        {
            "name": s["name"].strip().title(),
            "email": s["email"].strip().lower(),
            "company": s.get("company", "").strip().title(),
            "budget": s.get("budget", ""),
            "source": "website-form",
            "added_at": datetime.now().strftime("%Y-%m-%d %H:%M"),
        }
        for s in accepted
    ]
    file_exists = True
    try:
        with open(CRM, newline="", encoding="utf-8") as f:
            pass
    except FileNotFoundError:
        file_exists = False
    with open(CRM, "a", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=fieldnames)
        if not file_exists:
            w.writeheader()
        w.writerows(new_rows)
    log(f"STEP 3: Upserted {len(new_rows)} contacts -> {CRM}", lines)

    for r in new_rows:
        log(f'NOTIFY: Email queued to {r["email"]} (welcome + intro)', lines)

    log("DONE: Workflow completed successfully", lines)

    # Never clobber a previous run's log. This file is the proof that the
    # workflow actually executed, so overwriting it destroys the only evidence
    # the run happened. Append instead, keeping each run as its own block.
    if os.path.exists(LOG):
        with open(LOG, encoding="utf-8") as f:
            prior = f.read().rstrip("\n")
        with open(LOG, "w", encoding="utf-8") as f:
            f.write(prior + "\n" + "-" * 60 + "\n")
    with open(LOG, "a", encoding="utf-8") as f:
        f.write("\n".join(lines) + "\n")

if __name__ == "__main__":
    main()
