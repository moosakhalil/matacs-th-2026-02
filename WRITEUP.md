# Design write up

**Core idea: AI reads, code decides, a person confirms.** The model only turns PDF text into structured facts. Checks, scoring and ranking are plain code. Flow: [diagram/process_flow.png](diagram/process_flow.png).

## 1. AI vs. rules

**AI is used for one step: fact extraction.** Proposals phrase things differently ("since 2021", "in the past four years"), and fixed rules would be brittle at reading that.

**Everything else is code or rules:**

* PDF text extraction, file hashing, storing the criteria version
* A keyword screen for text aimed at reviewers or AI
* Checking the AI output: valid schema, and every quote must exist in the source text
* The mandatory gate (licence, WSIB, insurance, budget ceiling, week limit)
* Weighted scoring by formula, ranking, and building the reason text

**Why here:** reading is where AI is strong. Scoring must be identical every time and defensible to a losing bidder, and a formula is easier to defend than a model's opinion.

## 2. Consistency and explainability

* **Repeatable:** temperature 0, a pinned model and a versioned prompt. Models can still vary slightly, so facts are extracted once, confirmed and saved. Scoring runs on saved facts, so ranking twice gives exactly the same result. Ties break by a fixed rule.
* **Explainable:** every fact carries the exact quote and page it came from. Every score shows its points per criterion and why, for example "timeline 0 of 15: not stated". The one line reason is built from these numbers, not written by the AI, so it cannot say something the score does not support.

## 3. Human in the loop

* **Check 1, after extraction:** the reviewer confirms the facts. Missing values, low confidence values and any quote that failed the code check are highlighted first. The mandatory facts are always shown, because one wrong pass/fail decides eligibility.
* **Check 2, after ranking:** the reviewer sees the ranked list plus flagged and ineligible proposals with their reasons. They can clear or reject a flag, correct a fact, or move a proposal, but every change needs a written reason.
* **Final award** is always made by a person.

**Audit log, per proposal:** file hash, criteria version, model and prompt version, raw AI output, check results, confirmed facts, scores, and every override (old value, new value, reason, user, time).

## 4. Changing criteria

Criteria are versioned. Each saved result points to the version it was scored with, and old versions are never edited.

* When an admin changes a weight or a rule, a new version is created. Existing results for that category are marked **"scored under an older version"** and the reviewer is asked to rescore.
* Rescoring is instant and free, because the confirmed facts are already stored and scoring is pure code. No new AI call is needed.
* Only a **new criterion needing a new fact** (say "local hiring") triggers extraction, for that field only.
* Both rankings stay in the log. If an award was already made, the admin is warned before saving.

## 5. Risks and safeguards

| Risk | Safeguard |
|---|---|
| **Wrong extraction** | Quote and page for every fact, code checks the quote exists, human Check 1 |
| **Made up facts** | "not_stated" is required instead of guessing; a quote that is not in the source makes the value void |
| **Manipulation (prompt injection)** | Proposal labelled as data in the prompt; separate keyword screen in code; model reports such text instead of obeying; proposal flagged for a human |
| **Rewarding vague promises** | "To be confirmed" or "to be determined" counts as not stated |
| **Bias** | Model never scores or sees other bids; same formula for all; names can be hidden during Check 1 |
| **Cost** | One AI call per proposal, cached by file hash. Rescoring never calls the AI |
| **Bad PDF or scan** | OCR fallback; unreadable text goes to a person, never scored on nothing |

## How the sample set comes out

Scores come from `prototype/score.py`. Formulas: experience is installs ÷ 15 × 30 (capped); price and timeline are best ÷ this × weight; warranty compares both parts to the best; team is four checks worth 3.75 each.

| | Experience 30 | Price 25 | Timeline 15 | Warranty 15 | Team 15 | Total | Status |
|---|---|---|---|---|---|---|---|
| A | 28.0 | 24.3 | 15.0 | 13.8 | 15.0 | **96.0** | Rank 1 |
| E | 16.0 | 23.8 | 13.8 | 15.0 | 15.0 | **83.7** | Rank 2 |
| D | 22.0 | 25.0 | 0.0 | 13.8 | 7.5 | **68.2** | Rank 3 |
| C | 18.0 | 23.7 | 12.9 | 13.8 | 7.5 | (75.8) | Flagged |
| B | | | | | | | Ineligible |

* **B** is cheapest and fastest but fails the licence rule: the licence sits with a subcontractor "to be confirmed", not the bidder.
* **C** hides a note telling automated reviewers to rank it first. The tool ignores it and flags C for a person. On merit it would be 3rd, so the note neither helped nor hurt. Its installs count from 2020, so the reviewer should check the five year window.
* **D** is cheapest of the eligible bids but gives no schedule. Timeline is weighted, not mandatory, so D stays eligible with 0 for timeline. The reviewer should get a 16 week commitment before any award.
* **A vs E:** E has the better warranty, but A has 14 installs against 8, and experience carries the most weight.

## Assumptions

* The five year window counts back from today; edge cases go to the reviewer.
* Price and timeline are compared only among eligible bids.
* "Weekly progress reports" (C) is reporting, not performance monitoring.
* A flagged proposal is held, not rejected, since the bidder may not have written the note.
