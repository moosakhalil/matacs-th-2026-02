# AI Proposal Triage Design

**Name:** MUHAMMAD MOOSA KHALIL
**Reference:** MATACS-TH-2026-02
**Time spent:** about 60-70 minutes on the design, plus 50 minutes on the optional prototype

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

I used Claude to help plan the design, draft the write up, prompt, diagram and prototype, and check the scoring arithmetic. I then reviewed each file, ran the scorer myself to confirm it reproduces my ranking, and fixed the repository structure when uploading.

One place I corrected the AI: its first version of the prototype configuration hard coded a specific AI provider and model name. I changed it to neutral settings (LLM_API_KEY and LLM_MODEL) so the tool is not tied to one vendor and the model can be swapped through configuration alone.
