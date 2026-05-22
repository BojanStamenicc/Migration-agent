# Discovery Agent — User Manual

A Claude Agent SDK script that analyzes the legacy PHP repo (`thehoth`) and the new system repo (`unity`) to produce a complete HothX migration mapping for stakeholder review.

---

## 1. What it does

Runs three sequential analyses and writes three files to the project root:

| Step | Function | Output |
|------|----------|--------|
| 1 | `discover_legacy_order_ecosystem()` | `legacy_order_ecosystem.json` |
| 2 | `determine_new_system_targets()` | `new_system_targets.json` |
| 3 | `generate_validation_report(...)` | `STAKEHOLDER_VALIDATION_REPORT.md` |

The final Markdown report is what stakeholders sign off on **before** any ETL script is written.

---

## 2. Prerequisites

Already installed on this machine:

- **Python 3.12** — `/opt/homebrew/bin/python3.12`
- **Virtual env** — `.venv/` in the project root, with `claude-agent-sdk` and `anyio` installed
- **Claude Code CLI** — required by the SDK at runtime (`claude --version` should print `2.x`)

If you move to a new machine, re-run:

```bash
brew install python@3.12
npm install -g @anthropic-ai/claude-code
cd "/Users/bojanStamenic/Desktop/Agent for migrations"
/opt/homebrew/bin/python3.12 -m venv .venv
.venv/bin/pip install -r requirements.txt
```

---

## 3. One-time setup per session

```bash
cd "/Users/bojanStamenic/Desktop/Agent for migrations"
source .venv/bin/activate
```

Your shell prompt should now show `(.venv)`.

### Authenticate

Pick one:

```bash
claude login                       # uses your Claude.ai subscription
# OR
export ANTHROPIC_API_KEY=sk-ant-...  # uses pay-per-token API
```

### Place the repos

The script expects `thehoth/` and `unity/` next to `discovery_agent.py`. Clone:

```bash
git clone <thehoth-url> thehoth
git clone <unity-url>   unity
```

Or symlink if they live elsewhere:

```bash
ln -s /absolute/path/to/thehoth thehoth
ln -s /absolute/path/to/unity   unity
```

If either is missing, the agent will print a `WARNING` and fall back to scanning the project root — the output will be poor.

---

## 4. Running the agent

### Full run (all three steps)

```bash
python discovery_agent.py
```

You'll see progress lines:

```
[1/3] Wrote legacy_order_ecosystem.json
[2/3] Wrote new_system_targets.json
[3/3] Wrote STAKEHOLDER_VALIDATION_REPORT.md
Discovery complete. Review the report before generating ETL.
```

Typical runtime: a few minutes per step depending on repo size.

### Run a single step (cheaper while iterating)

```bash
# Step 1 only
python -c "import anyio; from discovery_agent import discover_legacy_order_ecosystem; anyio.run(discover_legacy_order_ecosystem)"

# Step 2 only
python -c "import anyio; from discovery_agent import determine_new_system_targets; anyio.run(determine_new_system_targets)"

# Step 3 only (reuses the two JSON files from disk)
python -c "
import anyio, json
from pathlib import Path
from discovery_agent import generate_validation_report
legacy = json.loads(Path('legacy_order_ecosystem.json').read_text())
unity  = json.loads(Path('new_system_targets.json').read_text())
anyio.run(generate_validation_report, legacy, unity)
"
```

---

## 5. What to check in the output

### `legacy_order_ecosystem.json`

- `primary_order_table` — should be a real table from `thehoth/`.
- `related_tables[].evidence` — every entry should cite a real `file:line`. Spot-check 2–3 by opening the cited file.
- `subscription_determination.per_product_recommendation` — each product flagged `always` / `never` / `sometimes` (with deciding flags for `sometimes`).
- `hothservices_investigation.overlap_analysis` — must answer: do HothServices and official orders contain distinct orders or overlap?
- `hothservices_investigation.mapping_to_unity_hothxproduct` — the mapping rule that the ETL will eventually encode.

### `new_system_targets.json`

- `subscription_order_target` and `one_time_order_target` — both should be populated with real Unity tables.
- `hothxproduct_target.exists_in_unity` — true/false based on what was found.
- `orphaned_fields` — any legacy field that has no clear Unity home becomes a stakeholder question.

### `STAKEHOLDER_VALIDATION_REPORT.md`

- Mapping matrix lists only tables that appear in the JSON inputs (no inventions).
- "Questions for Stakeholders" section captures every `stakeholder_questions` entry from both JSON files.
- At least one sample transformation is a HothServices → HothXProduct example.

---

## 6. Troubleshooting

| Symptom | Likely cause | Fix |
|---------|--------------|-----|
| `command not found: python` | venv not activated | `source .venv/bin/activate` |
| `No JSON object found in response` | Claude returned prose this turn | Re-run the step; if persistent, the repo dir is empty |
| `WARNING: thehoth not found` | repo missing or not symlinked | See section 3 |
| Auth / 401 errors | not logged in | `claude login` or re-export `ANTHROPIC_API_KEY` |
| Empty `related_tables` | agent scanned wrong directory | Confirm `thehoth/` exists in the project root |
| Very slow / hangs | large repo, many files | Wait — Grep/Read passes can take minutes per step |

---

## 7. Files in this project

```
.
├── discovery_agent.py              # The agent (4 functions + orchestrator)
├── requirements.txt                # Python deps
├── USER_MANUAL.md                  # This file
├── .venv/                          # Python 3.12 virtual env
├── thehoth/                        # Legacy PHP repo (you provide)
├── unity/                          # New system repo (you provide)
│
├── legacy_order_ecosystem.json     # Output of step 1
├── new_system_targets.json         # Output of step 2
└── STAKEHOLDER_VALIDATION_REPORT.md  # Output of step 3 — review this
```

---

## 8. Next step after a successful run

Send `STAKEHOLDER_VALIDATION_REPORT.md` to stakeholders. They answer the questions in section 6 of the report. **Only after their sign-off** do you proceed to ETL script generation — the agent's mapping is a proposal, not a decision.



To swap in real repos: delete the mock thehoth/ and unity/ directories and clone the real ones into their place — no script changes needed.


cd "/Users/bojanStamenic/Desktop/Agent for migrations"
rm -f legacy_order_ecosystem.json new_system_targets.json STAKEHOLDER_VALIDATION_REPORT.md
source .venv/bin/activate
python discovery_agent.py


Step 1 — legacy scan

python -c "import anyio; from discovery_agent import discover_legacy_order_ecosystem; anyio.run(discover_legacy_order_ecosystem)"
Writes legacy_order_ecosystem.json.

Step 2 — unity scan

python -c "import anyio; from discovery_agent import determine_new_system_targets; anyio.run(determine_new_system_targets)"
Writes new_system_targets.json.

Step 3 — stakeholder report (needs the two JSON files from steps 1 & 2)

python -c "
import anyio, json
from pathlib import Path
from discovery_agent import generate_validation_report
legacy = json.loads(Path('legacy_order_ecosystem.json').read_text())
unity  = json.loads(Path('new_system_targets.json').read_text())
anyio.run(generate_validation_report, legacy, unity)
"
Writes STAKEHOLDER_VALIDATION_REPORT.md.

Steps 1 and 2 are independent — run them in any order. Step 3 requires both JSON files to exist on disk.