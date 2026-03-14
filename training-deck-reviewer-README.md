# training-deck-reviewer

A Claude skill for comprehensive QA review of AI/ML technical training decks (.pptx). Performs a 9-phase audit and produces a reviewed deck with fixes applied, a QA report, and an anticipated Q&A document.

## What It Does

This skill runs a thorough multi-phase review of a training presentation:

1. **Deck inventory** — catalogs every slide with titles, content types, and structure
2. **Content accuracy checks** — verifies technical claims, version numbers, and API references using web research
3. **Visual/diagram verification** — checks that diagrams, charts, and images are clear and accurate
4. **Animation testing** — opens the deck in Chrome to verify animations and transitions play correctly
5. **Technology gap analysis** — identifies topics that should be covered but are missing based on current industry state
6. **Content flow review** — checks logical ordering, transitions between topics, and pedagogical progression
7. **Report generation** — produces a detailed QA report organized by severity
8. **Fix application** — applies fixes directly to the deck (typos, outdated years, gap-fill slides, change summary slide, speaker notes, backup slides)
9. **Q&A anticipation** — generates a document of likely attendee questions with suggested answers

## Deliverables

The skill produces three outputs:

- **qa-report.md** — detailed findings organized by severity (critical, warning, info) with specific slide references and suggested fixes
- **[deck-name]_reviewed.pptx** — a copy of the original deck with fixes applied: typos corrected, years updated, gap-fill slides added, a change summary slide, enhanced speaker notes, and backup slides for anticipated questions
- **anticipated-qa.md** — likely questions from attendees based on the deck content, with suggested instructor responses

## When It Triggers

The skill activates on "review this deck", "QA the slides", "check the training materials", "audit the presentation", "verify the deck is up to date", or any request to review, QA, audit, or check a training deck for accuracy, completeness, or quality.

It does **not** trigger for creating slides from scratch or general slide editing — use the `pptx` or `training-course-builder` skills for those tasks.

## Requirements

- A `.pptx` file to review
- **Chrome browser access** — needed for animation testing phase
- **Web search access** — needed for content accuracy verification and technology gap analysis

## Installation

Install the `.skill` file through Claude's Settings → Skills, or copy the `training-deck-reviewer/` folder into your skills directory.
