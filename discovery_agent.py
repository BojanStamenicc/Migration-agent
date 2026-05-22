"""
Discovery Agent for HothX legacy → Unity migration.

Analyzes the legacy PHP repo (thehoth) and the new system repo (unity) to produce
a complete mapping of HothX from source to target, including related tables,
implicit relationships, and business logic for distinguishing campaign orders
from one-time orders.

Run from project root:
    python discovery_agent.py

Outputs (written next to this script):
    - legacy_order_ecosystem.json
    - new_system_targets.json
    - STAKEHOLDER_VALIDATION_REPORT.md
"""

import anyio
import json
import os
import re
from pathlib import Path

from claude_agent_sdk import (
    ClaudeAgentOptions,
    AssistantMessage,
    TextBlock,
    query,
)

ROOT = Path(__file__).parent.resolve()
LEGACY_REPO = ROOT / "thehoth"
UNITY_REPO = ROOT / "unity"

LEGACY_OUT = ROOT / "legacy_order_ecosystem.json"
UNITY_OUT = ROOT / "new_system_targets.json"
REPORT_OUT = ROOT / "STAKEHOLDER_VALIDATION_REPORT.md"


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _options(cwd: Path, system_prompt: str) -> ClaudeAgentOptions:
    """Configure the SDK with file-reading tools rooted at the given repo."""
    return ClaudeAgentOptions(
        cwd=str(cwd),
        system_prompt=system_prompt,
        allowed_tools=["Read", "Glob", "Grep", "Bash"],
        permission_mode="acceptEdits",
        model="claude-opus-4-7",
    )


async def _run(prompt: str, options: ClaudeAgentOptions) -> str:
    """Run a single Claude Agent SDK query and return the concatenated text."""
    chunks: list[str] = []
    async for msg in query(prompt=prompt, options=options):
        if isinstance(msg, AssistantMessage):
            for block in msg.content:
                if isinstance(block, TextBlock):
                    chunks.append(block.text)
    return "".join(chunks)


def _extract_json(text: str) -> dict:
    """Pull the first complete JSON object out of an assistant response.

    Tries fenced ```json blocks first, then scans for a balanced {...} block,
    respecting string literals and escapes so braces inside strings don't break
    the count.
    """
    fence = re.search(r"```(?:json)?\s*(\{.*?\})\s*```", text, re.DOTALL)
    if fence:
        try:
            return json.loads(fence.group(1))
        except json.JSONDecodeError:
            pass  # fall through to balanced scan

    start = text.find("{")
    while start != -1:
        depth = 0
        in_str = False
        esc = False
        for i in range(start, len(text)):
            ch = text[i]
            if in_str:
                if esc:
                    esc = False
                elif ch == "\\":
                    esc = True
                elif ch == '"':
                    in_str = False
            else:
                if ch == '"':
                    in_str = True
                elif ch == "{":
                    depth += 1
                elif ch == "}":
                    depth -= 1
                    if depth == 0:
                        try:
                            return json.loads(text[start : i + 1])
                        except json.JSONDecodeError:
                            break  # try next '{'
        start = text.find("{", start + 1)

    raise ValueError(f"No JSON object found in response:\n{text[:1000]}")


# ---------------------------------------------------------------------------
# Function 1: Legacy ecosystem discovery
# ---------------------------------------------------------------------------

async def discover_legacy_order_ecosystem() -> dict:
    """
    Walk the legacy PHP repo (thehoth) and identify every table related to
    orders, including implicit relationships discovered via code search, the
    subscription-vs-one-time determination logic, and the HothServices history.
    """
    system_prompt = (
        "You are a senior data engineer auditing a legacy PHP codebase to plan "
        "a migration. You read schema files, models, services, and SQL strings "
        "embedded in PHP. You are exhaustive: implicit joins, raw SQL, and "
        "soft FK columns (order_id, subscription_id, product_id) all count. "
        "When you cannot prove a relationship, you flag it for stakeholders "
        "instead of guessing."
    )
    prompt = f"""
Analyze the legacy PHP repository at `{LEGACY_REPO}` to map the full HothX order ecosystem.

Search the repo with Glob/Grep/Read for:
  1. Schema files (*.sql, migrations/, *Schema*.php, doctrine yml/xml) — find every
     table whose name contains: order, order_item, subscription, recurring, payment,
     invoice, product, campaign, item, hothx, hoth, hs (HothServices).
  2. Explicit FK declarations — `FOREIGN KEY`, `REFERENCES`, `@ManyToOne`, `belongsTo`,
     `hasMany`, Eloquent/Doctrine relations.
  3. Implicit relationships — `JOIN`, `WHERE x.order_id = y.id`, queries that link
     tables without a declared FK. Cite file + line.
  4. Subscription determination — `is_subscription`, `$order->type == 'subscription'`,
     `billing_frequency`, `recurring`, `subscription_id IS NOT NULL`. For each
     HothX product family, decide whether it is ALWAYS / NEVER / SOMETIMES a
     campaign order, and if SOMETIMES, list the exact flags/columns that decide.
  5. Campaign linkage — `campaign_order` table or code that joins orders to
     campaign tracking.
  6. HothServices investigation — search for `hsorder`, `hothservices`, `hs_order`,
     `HothService`. Determine:
       - Does HothServices order data still live in legacy order tables, or did
         it ever?
       - Are HothServices and the official orders table distinct, or do they
         overlap?
       - Mapping logic from HothServices and related tables to whatever maps to
         HothXProduct in Unity.

Output ONE JSON object (no prose, no markdown fences around prose) with this exact shape:

{{
  "primary_order_table": "<string>",
  "related_tables": [
    {{
      "name": "<string>",
      "relationship_type": "explicit_fk | implicit_code_join | shared_column | unknown",
      "evidence": "<file:line + short quote>",
      "columns_mapped": ["..."],
      "purpose_in_ecosystem": "<string>"
    }}
  ],
  "subscription_determination": {{
    "method": "<SQL/code expression>",
    "code_evidence": "<file:lines>",
    "per_product_recommendation": [
      {{"product": "<name>", "campaign_status": "always|never|sometimes",
        "deciding_flags": ["..."]}}
    ],
    "edge_cases_found": ["..."],
    "confidence": "high|medium|low",
    "stakeholder_questions": ["..."]
  }},
  "campaign_order_links": {{
    "tables": ["..."],
    "evidence": "<file:line>"
  }},
  "hothservices_investigation": {{
    "hothservices_table_exists": true|false,
    "table_name": "<string|null>",
    "current_relationship_to_orders": "<string>",
    "historical_migration_evidence": "<string with file refs>",
    "overlap_analysis": {{
      "distinct_orders": true|false,
      "explanation": "<string>",
      "code_evidence": "<file:line>"
    }},
    "mapping_to_unity_hothxproduct": {{
      "legacy_source_tables": ["..."],
      "unity_target": "<string>",
      "mapping_logic": "<string>",
      "confidence": "high|medium|low",
      "stakeholder_questions": ["..."]
    }}
  }},
  "total_tables_found": <int>,
  "tables_without_clear_relationship": [
    {{"name": "<string>", "reason": "<string>", "recommendation": "<string>"}}
  ]
}}

Return ONLY the JSON object.
""".strip()

    text = await _run(prompt, _options(LEGACY_REPO if LEGACY_REPO.exists() else ROOT, system_prompt))
    data = _extract_json(text)
    LEGACY_OUT.write_text(json.dumps(data, indent=2))
    print(f"[1/3] Wrote {LEGACY_OUT.name}")
    return data


# ---------------------------------------------------------------------------
# Function 2: New-system target discovery
# ---------------------------------------------------------------------------

async def determine_new_system_targets() -> dict:
    """Analyze the Unity repo to determine target tables and required fields."""
    system_prompt = (
        "You are a data engineer reverse-engineering a target schema from a "
        "modern codebase. You read migrations, ORM models, and type "
        "definitions. You distinguish subscription/recurring tables from "
        "transactional/one-time tables and document required fields, types, "
        "nullability, and FK dependencies. When a field has no clear legacy "
        "source, you mark it orphaned and ask the stakeholder."
    )
    prompt = f"""
Analyze the new system repository at `{UNITY_REPO}` to determine the target
schema for the HothX order migration.

Search with Glob/Grep/Read for:
  1. All order-related tables (orders, order_items, campaign_orders, products,
     subscription_orders, transactional_orders, hothx_products, etc.).
  2. The split between subscription/recurring storage and one-time/transactional
     storage. Identify which table each type lives in.
  3. Required fields per table: column name, type, nullable, default, constraints.
  4. FK dependencies (customers, products, payments, subscription_plans).
  5. Whether Unity has a HothXProduct table (or equivalent) and the fields it
     expects from legacy HothServices data.

Output ONE JSON object with this exact shape:

{{
  "subscription_order_target": {{
    "table_name": "<string>",
    "database": "<string>",
    "required_fields": [
      {{"name": "<col>", "type": "<type>", "nullable": false, "source": "<legacy hint>"}}
    ],
    "dependencies": ["..."]
  }},
  "one_time_order_target": {{
    "table_name": "<string>",
    "database": "<string>",
    "required_fields": [...],
    "dependencies": ["..."]
  }},
  "hothxproduct_target": {{
    "exists_in_unity": true|false,
    "table_name": "<string|null>",
    "description": "<string>",
    "required_fields": [...],
    "dependencies": ["..."],
    "mapping_notes": "<string>"
  }},
  "orphaned_fields": [
    {{"field": "<legacy.column>", "reason": "<string>", "recommendation": "<string>"}}
  ]
}}

Return ONLY the JSON object.
""".strip()

    text = await _run(prompt, _options(UNITY_REPO if UNITY_REPO.exists() else ROOT, system_prompt))
    data = _extract_json(text)
    UNITY_OUT.write_text(json.dumps(data, indent=2))
    print(f"[2/3] Wrote {UNITY_OUT.name}")
    return data


# ---------------------------------------------------------------------------
# Function 3: Stakeholder validation report
# ---------------------------------------------------------------------------

async def generate_validation_report(legacy: dict, unity: dict) -> str:
    """Produce a human-readable Markdown report combining both discoveries."""
    system_prompt = (
        "You are a migration lead writing a stakeholder validation report. "
        "Your audience is non-engineers: product, ops, compliance. Be concrete, "
        "cite code/files, surface every uncertainty as an explicit question, "
        "and never invent table names that did not appear in the input JSON."
    )
    prompt = f"""
Using ONLY the two JSON inputs below, produce a Markdown stakeholder validation
report. Do not invent tables or fields that are not present in the inputs.

LEGACY DISCOVERY (legacy_order_ecosystem.json):
```json
{json.dumps(legacy, indent=2)}
```

UNITY DISCOVERY (new_system_targets.json):
```json
{json.dumps(unity, indent=2)}
```

The report MUST contain these sections, in order:

1. **Executive Summary** — bullet list of headline findings (table counts,
   implicit relationships, HothServices outcome).
2. **Table Mapping Matrix** — Markdown table:
   `| Legacy Table | New Target | Confidence | Needs Review |`
3. **Subscription Determination Logic** — quote the method + code evidence from
   legacy.subscription_determination, list edge cases.
4. **HothServices Investigation Summary** — overlap analysis, mapping to
   HothXProduct, lineage requirements.
5. **Data Quality Flags** — tables without clear relationships, orphaned fields.
6. **Questions for Stakeholders** — Markdown table:
   `| # | Question | Impact | Suggested By |`
   Pull every `stakeholder_questions` entry from both inputs; deduplicate.
7. **Sample Transformations** — 2-3 worked examples. At least ONE must be a
   HothServices → HothXProduct example.
8. End with the literal line:
   `**Stakeholder approval required before ETL generation.**`

Return ONLY the Markdown report, no preamble.
""".strip()

    text = await _run(prompt, _options(ROOT, system_prompt))
    # Strip outer markdown fences if any
    fenced = re.match(r"^```(?:markdown|md)?\s*\n(.*)\n```\s*$", text.strip(), re.DOTALL)
    report = fenced.group(1) if fenced else text
    REPORT_OUT.write_text(report)
    print(f"[3/3] Wrote {REPORT_OUT.name}")
    return report


# ---------------------------------------------------------------------------
# Function 4: Orchestrator
# ---------------------------------------------------------------------------

async def run_discovery() -> None:
    """Run all three discovery phases end-to-end."""
    if not LEGACY_REPO.exists():
        print(f"WARNING: {LEGACY_REPO} not found — agent will search project root.")
    if not UNITY_REPO.exists():
        print(f"WARNING: {UNITY_REPO} not found — agent will search project root.")

    legacy = await discover_legacy_order_ecosystem()
    unity = await determine_new_system_targets()
    await generate_validation_report(legacy, unity)
    print("\nDiscovery complete. Review the report before generating ETL.")


if __name__ == "__main__":
    if not os.environ.get("ANTHROPIC_API_KEY"):
        print("INFO: ANTHROPIC_API_KEY not set — relying on `claude login` credentials.")
    anyio.run(run_discovery)
