# AI Proposal Triage Design

**Name:** YOUR FULL NAME
**Reference:** MATACS-TH-2026-02
**Time spent:** about X minutes on the design, plus X minutes on the optional prototype

## Files

| File | What it is |
|---|---|
| [WRITEUP.md](WRITEUP.md) | Answers to the five questions, plus how the sample set ranks |
| [diagram/process_flow.png](diagram/process_flow.png) | Flow from upload to ranked output, with AI steps, rule steps and human checks marked |
| [PROMPTS.md](PROMPTS.md) | The extraction prompt, exactly as it would be sent |
| [ranking.json](ranking.json) | Expected ranking of proposals A to E |
| [prototype/](prototype/) | Optional: a small scorer that produces the ranking from extracted facts |

## The design in one line

AI reads each proposal and pulls out facts with a quote for each one. Code checks those quotes, applies the pass/fail rules and scores with the admin's weights. A person confirms the facts and the final ranking.

## Result on the sample set

1. **A** ranked first (96.0)
2. **E** ranked second (83.7)
3. **D** ranked third (68.2)
* **C** flagged: contains text telling automated reviewers to rank it first
* **B** ineligible: the electrical licence is not held by the bidder

## Running the prototype

No API key is needed for the scorer:

```
cd prototype
python score.py --explain
```

`extract.py` shows the live AI step. It needs a key in `prototype/.env` (copy `.env.example`) and proposal text files in `prototype/proposals/`, which is ignored by git so no proposal text is stored here.

## How I used AI

WRITE THIS YOURSELF, 2 or 3 sentences. Say which tool you used and for what, for example drafting the structure and checking the score arithmetic, and that you reviewed every number and decision yourself.

Then give one real place you disagreed with or corrected the AI and why. Only use something that actually happened.
