# Codespace Lab Tester

A Claude skill for automated QA testing of training labs that run in GitHub Codespaces. It drives Chrome to open a repository, launch a Codespace, and systematically execute every step in a `labs.md` file — running commands, merging code via diff patterns, handling interactive prompts, and producing a detailed pass/fail report.

## What It Does

Given a GitHub repository URL containing training labs, this skill:

1. Opens the repo in Chrome and launches a new Codespace
2. Waits for the dev container to build and post-create scripts to finish
3. Reads the entire `labs.md` file and builds a structured execution plan
4. Executes every lab step sequentially — terminal commands, `code -d` diff-merge operations, interactive programs, multi-server setups, etc.
5. Logs results per step (PASS / FAIL / WARN / SKIP) with error details
6. Generates a markdown test report with per-lab tables, error details, and recommendations

## How It Works

The skill operates through Claude's Chrome MCP (Model Context Protocol) integration, which gives it the ability to interact with a browser. It clicks buttons, types in VS Code's web terminal, takes screenshots to verify output, and navigates the Codespace UI — all autonomously.

The core workflow has four phases:

**Phase 1 — Launch:** Navigate to the GitHub repo, find the Codespace launch button (README badge or Code dropdown), create a new Codespace, and wait for full initialization including post-create/post-attach scripts.

**Phase 2 — Parse:** Read the full `labs.md` and build an explicit execution plan. This is the most critical phase. Every command is extracted via grep, mapped to its lab and step number, classified by type (`[MERGE]`, `[RUN]`, `[VIEW]`, `[CD]`, `[INPUT]`, etc.), and cross-referenced to ensure merge steps precede run steps. This prevents the most common failure mode: running a skeleton file before merging in the complete version.

**Phase 3 — Execute:** Work through each lab step against the execution plan. The skill handles terminal commands, `code -d` diff-merge patterns (automated as `cp` operations), background server management, interactive input prompts, and multi-terminal workflows.

**Phase 4 — Report:** Generate a structured markdown report with summary stats, per-lab result tables, detailed error descriptions, and actionable recommendations.

## Lab Conventions

This skill is designed for training repos following the TechUpSkills convention:

- Labs defined in a `labs.md` file at the repo root
- Labs numbered as `**Lab N - Title**` with numbered steps
- Skeleton/starter code in topic directories (e.g., `agents/`, `mcp/`)
- Complete solution files in `extra/` with `.txt` extension
- `code -d ../extra/solution.txt skeleton.py` used for students to diff and merge
- `devcontainer.json` with post-create and post-attach scripts for environment setup

Skeleton files are intentionally incomplete and not guaranteed to be runnable before merging. The skill understands this convention and does not report pre-merge skeleton errors as bugs.

## Prerequisites

- **Claude desktop app** with Cowork mode enabled
- **Claude in Chrome** MCP extension installed and connected
- **GitHub account** with Codespaces access
- The target repository must have a `labs.md` file and a `.devcontainer` configuration

## How to Use

### As an installed Claude skill

Install the `.skill` file (click "Copy to your skills" if presented in Cowork, or manually place the `codespace-lab-tester/` directory in your Claude skills folder). Then just ask Claude:

- "Test the labs in https://github.com/skillrepos/ai-security"
- "QA the codespace labs for this repo"
- "Run through all the lab exercises and give me a report"

Claude will automatically pick up the skill and follow its instructions.

### Trigger phrases

The skill activates on phrases like:

- "test this lab" / "test the labs"
- "run through the labs"
- "QA the codespace labs"
- "validate training materials"
- "test the lab exercises"
- Any request involving a GitHub URL + running labs in a Codespace

### What you get back

A markdown test report saved to your workspace folder, containing:

- Summary stats (passed/failed/warnings/skipped)
- Per-lab result tables with step-by-step status
- Detailed error descriptions with commands, expected vs. actual output, and suggested fixes
- Recommendations for improving the course materials

## File Structure

```
codespace-lab-tester/
├── README.md                    # This file
├── SKILL.md                     # Main skill instructions (read by Claude at runtime)
└── references/
    └── lab-patterns.md          # Reference guide for code block types, diff-merge
                                 #   patterns, server patterns, and environment setup
```

## Lessons Learned

The SKILL.md includes a "Lessons from Live Testing" section based on real test runs. Key findings:

- **Build the execution plan first.** The single most important step. Grep for all commands, map them to labs/steps, and verify merge-before-run ordering. Skipping this causes missed steps and false bug reports.
- **Use `Ctrl+Shift+\`` for new terminals** when existing tabs are stale.
- **Run servers with `&`** for background execution in multi-server labs, and clean up with `kill %1 %2` between labs.
- **Use `Ctrl+C` to exit interactive programs** — typing "quit" often gets processed as input.
- **Local LLM queries are slow** (1-2 minutes on a 4-core Codespace) — be patient.
- **Chrome MCP disconnects are normal** during wait operations — just retry the next tool call.

## Example Test Report

See [lab-test-report-ai-security.md](../lab-test-report-ai-security.md) for a complete example report generated from testing the [ai-security](https://github.com/skillrepos/ai-security) repository (5 labs, ~45 steps).
