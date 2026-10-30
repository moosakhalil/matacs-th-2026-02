"""
Optional live extraction step. Sends one proposal's text to the model with the
extraction prompt from PROMPTS.md, then checks the answer in code before it is
trusted.

Proposal text is NOT stored in this repo. To try it, put plain text files in
prototype/proposals/ (ignored by git), for example proposals/A.txt, and set
ANTHROPIC_API_KEY in a .env file (see .env.example).

Usage:
    python extract.py proposals/A.txt
"""

import json
import os
import sys
from pathlib import Path

HERE = Path(__file__).parent
CRITERIA = json.loads((HERE / "criteria.json").read_text())

FIELDS = {
    "licence_held_by_bidder": "true only if the bidder itself states it holds an Ontario electrical contractor licence; a subcontractor's licence does not count",
    "wsib_clearance": "true if the bidder confirms current WSIB clearance",
    "liability_5m": "true if the bidder confirms at least $5M liability insurance",
    "qualifying_installs": "number of commercial installs of 100 kW or more the bidder says it completed, and the start year it gives",
    "total_price_cad": "total price in CAD as a number",
    "completion_weeks": "committed completion time in weeks from award, as a number",
    "panel_warranty_years": "panel warranty length in years",
    "workmanship_warranty_years": "workmanship warranty length in years",
    "named_lead": "true if a specific project lead or manager is committed",
    "named_crew": "true if a crew with a stated size or makeup is committed",
    "safety_plan": "true if a safety plan is included",
    "monitoring_plan": "true if ongoing performance monitoring of the system is offered",
}

PROMPT_TEMPLATE = (HERE.parent / "PROMPTS.md").read_text().split("```text")[1].split("```")[0]


def build_prompt(proposal_text):
    field_lines = "\n".join(f"* {name}: {desc}" for name, desc in FIELDS.items())
    return (
        PROMPT_TEMPLATE
        .replace("{{category}}", CRITERIA["category"])
        .replace("{{field_list}}", field_lines)
        .replace("{{proposal_text}}", proposal_text)
    )


def validate(answer, proposal_text):
    """Code checks the AI. Any fact whose quote is not really in the text is rejected."""
    problems = []
    normalised = " ".join(proposal_text.split())
    for name in FIELDS:
        item = answer.get("fields", {}).get(name)
        if item is None:
            problems.append(f"{name}: missing from answer")
            continue
        if item.get("value") == "not_stated":
            continue
        quote = " ".join(str(item.get("quote", "")).split())
        if not quote or quote not in normalised:
            problems.append(f"{name}: quote not found in source, value discarded")
            item["value"] = "needs_review"
    return problems


def main():
    if len(sys.argv) != 2:
        sys.exit("Usage: python extract.py proposals/A.txt")

    try:
        from dotenv import load_dotenv
        load_dotenv(HERE / ".env")
    except ImportError:
        pass
    if not os.getenv("ANTHROPIC_API_KEY"):
        sys.exit("No API key set. Use score.py with the saved facts.json instead.")

    import anthropic

    text = Path(sys.argv[1]).read_text()
    client = anthropic.Anthropic()
    reply = client.messages.create(
        model=os.getenv("MODEL", "claude-sonnet-5-5"),
        max_tokens=2000,
        temperature=0,
        messages=[{"role": "user", "content": build_prompt(text)}],
    )
    answer = json.loads(reply.content[0].text)
    problems = validate(answer, text)

    print(json.dumps(answer, indent=2))
    if problems:
        print("\nValidation problems (sent to reviewer):")
        for p in problems:
            print(" *", p)


if __name__ == "__main__":
    main()
