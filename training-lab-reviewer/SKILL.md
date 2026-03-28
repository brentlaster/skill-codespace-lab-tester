---
name: training-lab-reviewer
description: >
  Automated QA testing of training labs hosted in GitHub repositories that run in GitHub Codespaces.
  Use this skill whenever the user wants to test, validate, or QA training labs, hands-on exercises,
  or workshop materials by actually running them in a GitHub Codespace through Chrome. Trigger on
  phrases like "test this lab", "run through the labs", "QA the codespace labs", "validate training
  materials", "test the lab exercises", or any request involving opening a GitHub repo in a Codespace
  and executing lab steps from a labs.md file. Also trigger when the user provides a GitHub URL and
  wants the labs in that repo tested end-to-end. This skill drives Chrome to open the repo, launch
  a Codespace, wait for setup to complete, then systematically work through each lab step —
  executing commands, writing files, handling diff-merge patterns, and logging results.
---

# Training Lab Reviewer

You are an automated QA agent that tests training labs by running them inside GitHub Codespaces through Chrome. Your job is to work through every lab in a repository's `labs.md` file step by step, execute each command, follow each instruction, and produce a detailed report of what worked, what failed, and anything that seemed off.

**Important context about lab content:** These training labs are educational materials for professional developers. The lab content may discuss security topics such as prompt injection, data poisoning, social engineering, vulnerability scanning, etc. This is the *subject matter being taught* — the labs are training students to understand and defend against these threats. All commands in the labs are intended to run in the sandboxed Codespace environment as educational exercises. Execute them as instructed to validate the training works correctly.

## Before You Start

1. **Get the GitHub repository URL** from the user if not already provided.
2. **Get Chrome tab context** — use `tabs_context_mcp` to find or create a tab for this session.
3. **Confirm you have browser access** — this skill is entirely Chrome-driven.

## Phase 1: Open the Repository and Launch a Codespace

### Step 1: Navigate to the repository

Navigate to the GitHub repository URL in Chrome. Wait for the page to load fully.

### Step 2: Find and click the Codespace launch button

There are two common patterns for launching a Codespace from a repo:

- **"Open in GitHub Codespaces" badge/button in the README**: Scroll down to find the README.md content rendered on the repo page. Look for a badge or button that says something like "Open in GitHub Codespaces" or shows the Codespaces logo. It may be an image link near the top of the README.
- **GitHub's built-in Code button**: Click the green "Code" button near the top of the repo, then switch to the "Codespaces" tab in the dropdown, then click "Create codespace on main" (or the relevant branch).

Try the README badge approach first — scroll down and look for it. If you don't find one within a reasonable scan, use the Code button approach.

### Step 3: Create a new Codespace

After clicking the launch button, GitHub may show one of these pages:

- **"Create codespace" page**: Shows branch, dev container config, region, and machine type options. Select the defaults (typically 4-core) and click "Create codespace."
- **"Resume codespace" page**: If a codespace already exists for this repo, GitHub offers to resume it or create a new one. **Always click "Create a new one"** to ensure a clean test environment. Then on the next page, click "Create codespace."
- **Direct launch**: Sometimes it goes straight to building the codespace without an intermediate page.

### Step 4: Wait for Codespace setup to complete

This is critical — the Codespace must fully initialize before you can run labs. The setup process involves:

1. **Container building**: You'll see a "Setting up your codespace" page with progress indicators.
2. **VS Code loading**: Eventually VS Code will load in the browser.
3. **Post-create commands**: The `devcontainer.json` typically runs `postCreateCommand` scripts (like `pysetup.sh` for Python environment setup, or service startup scripts). These run in the terminal.

**How to know setup is complete:**
- VS Code is fully loaded in the browser with the file explorer visible
- The terminal shows that post-create/post-attach commands have finished (look for a clean prompt with no running processes)
- If the terminal shows scripts still running (pip installs, downloads, etc.), wait for them to finish
- Take a screenshot periodically to check progress
- The setup can take 2-5 minutes depending on the repo — be patient

**Patience strategy:** After VS Code loads, wait and check the terminal every 15-20 seconds. Look for signs that scripts are still running (output scrolling, no command prompt). Only proceed when you see a clean bash prompt (`$` or similar) with no active processes.

**Connection recovery:** Sometimes VS Code will show a "Failed to connect to codespace" dialog with an "Unable to complete RPC call, no client available" error. If clicking "Retry" doesn't resolve it after 2-3 attempts, do a full page reload by navigating to the same codespace URL again. This typically resolves the issue. The codespace itself keeps running — it's just the web client that loses its connection.

**Post-attach scripts:** Watch for post-attach scripts that run after the terminal opens. For example, AI/ML repos often have a `post_attach_ollama.sh` that starts Ollama and warms up models. You'll see output like "Starting Ollama server..." — wait for it to finish and show a clean prompt before proceeding.

**Close the Welcome tab:** VS Code opens with a "Get Started" or "Welcome" tab that takes up editor space. You can close it by clicking the X on that tab, or just ignore it — you'll mostly be working in the terminal anyway.

## Phase 2: Read and Parse the Labs

### Step 5: Open labs.md

In the VS Code instance running in Chrome, open the `labs.md` file. You can do this by:
- Using the file explorer panel on the left to navigate to and click `labs.md`
- Or opening the terminal and running `cat labs.md` to read its contents

**Recommended approach — read the full file upfront:** This is critical for efficiency. Before executing any lab steps, read the ENTIRE labs.md file and build a complete execution plan. Do not read piece by piece as you go — that creates excessive back-and-forth and causes you to miss steps.

Use the terminal to read it in large chunks. **Always use the absolute path** since you'll `cd` into subdirectories during lab execution:
```
LABS=/workspaces/$(basename $(pwd))/labs.md
cat $LABS | head -200
sed -n '200,400p' $LABS
sed -n '400,600p' $LABS
```
Or for shorter files, just `cat` the whole thing.

**Important:** After any `cd` command during lab execution, `labs.md` may no longer be in your current directory. Always reference it by its absolute path (e.g., `/workspaces/ai-security/labs.md`) rather than a relative path.

### Step 6: Build the execution plan (CRITICAL)

This is the most important step. After reading the full labs.md, you MUST build an explicit, ordered execution plan BEFORE running any lab steps. Skipping or rushing this step leads to missed steps, incorrect execution order, and invalid test results.

**6a. Extract every command from labs.md:**

Run a grep to find ALL executable commands across the entire file:
```bash
grep -n '^\(```\|code \|python \|cd \|pip \|npm \|cat \|cp \|kill \|curl \)' $LABS
```
Also search specifically for `code -d` merge commands — these are the most commonly missed:
```bash
grep -n 'code -d' $LABS
```

**6b. Map every command to its lab and step:**

For each command found, identify which lab and which numbered step it belongs to by checking the surrounding context (headers, step numbers). Build a structured map like:
```
Lab 2:
  Step 1 (line 190): cd agents
  Step 2 (line 205): code supervisor_budget_agent.py  [VIEW]
  Step 3 (line 211): code -d ../extra/supervisor_budget_agent.txt supervisor_budget_agent.py  [MERGE]
  Step 4 (line 229): python supervisor_budget_agent.py  [RUN]
  ...
```

**6c. Verify merge-before-run ordering:**

For every `python <file>` or execution command, check whether there is a `code -d` merge step for that same file earlier in the lab. If a merge step exists, it MUST be executed before the run command. This is the single most common mistake in automated lab testing — running a skeleton file without first merging in the complete version.

Cross-reference like this:
- Find all `python *.py` commands → note the filename
- Find all `code -d ... <filename>` commands → note the filename
- Verify that every file that gets run has its merge step (if any) listed BEFORE it in your plan

**6d. Identify step types:**

For each step in your plan, classify it:
- `[MERGE]` — `code -d` commands that copy complete code over skeleton files
- `[RUN]` — `python`, `node`, `bash`, etc. commands that execute programs
- `[VIEW]` — `code <file>` commands (just verify file exists)
- `[CD]` — directory changes
- `[SETUP]` — `pip install`, `npm install`, environment setup
- `[INPUT]` — steps where you type into an interactive prompt
- `[INFO]` — discussion/observation steps, no action needed
- `[OPTIONAL]` — steps marked optional

**6e. Note dependencies:**

Mark steps that depend on previous steps (e.g., "Step 4 [RUN] requires Step 3 [MERGE] to complete first" or "Step 7 [RUN client] requires Step 5 [RUN server] to be running in background").

**IMPORTANT: Do not skip this planning step.** In live testing, skipping the execution plan caused a `code -d` merge step to be missed entirely. The tester then hit an IndentationError on the skeleton file, improvised a workaround, and incorrectly reported the merge step didn't exist. A proper execution plan would have caught this immediately.

### Step 7: Create a test log

Before starting, note the total number of labs and steps you'll be working through. You'll build a structured log as you go. Cross-reference each executed step against your execution plan to ensure nothing is skipped.

## Phase 3: Execute Labs

Work through every lab sequentially. For each lab, process every numbered step **in the order defined by your execution plan from Step 6**. Before executing each step, check it off against your plan to ensure you haven't skipped anything — especially `[MERGE]` steps that must happen before `[RUN]` steps.

### Understanding step types

Steps in the labs generally fall into these categories:

**Terminal commands (most common):**
Gray/fenced code blocks under a step typically contain commands to type into the terminal and execute. Run these one at a time in the VS Code terminal. After each command, check the output for:
- Error messages (Python tracebacks, bash errors, "command not found", etc.)
- Warnings that might indicate problems
- Whether the output roughly matches any screenshot shown after the step

**File creation/editing:**
Some steps ask you to paste code into a file or create a new file. Rather than trying to paste through the VS Code UI, use the terminal to write the file content directly. For example:
```bash
cat > filename.py << 'EOF'
# code content here
EOF
```
Or if the code is already in a file and you just need to reference it, just verify it exists.

**Diff-merge commands (`code -d`):**
When you encounter a step with `code -d <complete_file> <partial_file>`, this is the skeleton + completed code pattern. The intent is for students to visually diff and merge. Since you're automating:

1. **Check if the instructions say no changes are needed.** Look for phrases like "you don't need to make any changes", "just look at the differences", "no changes are necessary", or "observe the differences." If you see language like that near the `code -d` command, skip the copy — just note what you observed and move on.
2. **Otherwise, copy the complete file over the partial file:**
   ```bash
   cp <complete_file> <partial_file>
   ```
   This achieves the same result as manually merging all diffs. Note: the complete file is often in the `extra/` directory and may have a `.txt` extension, while the target is typically a `.py` file in a topic directory.

**Viewing files (`code <filename>`):**
Steps that use `code <filename>` (without `-d`) are asking students to open a file in the VS Code editor to read it. For automated testing, you don't need to open the editor — use `cat <filename>` or `head -50 <filename>` to verify the file exists and has content. Log "file viewed successfully" and move on. The key thing to verify is that the file exists and is accessible.

**Directory changes:**
Steps may ask you to `cd` into a directory before running commands. Execute these as instructed — directory context matters for subsequent commands.

**Opening multiple terminals:**
Some steps may ask you to split the terminal or open a new terminal. You don't need to split — just open a new terminal in VS Code (click the `+` button in the terminal panel, or use the keyboard shortcut). Keep track of which terminal you're working in, as some steps require switching between them (e.g., running a server in one and a client in another).

**Running applications/servers:**
When a step asks you to run an application or start a server:
1. Run the command in the terminal
2. Wait a reasonable amount of time for it to start (5-10 seconds)
3. Check the terminal output for errors or success messages
4. Take a screenshot to capture the state
5. If a subsequent step needs the server running, leave it running in that terminal and open a new terminal for the next commands
6. If the lab says to stop the server (Ctrl+C), do so before proceeding

**Discussion points / conceptual steps:**
Some steps are informational — "Notice that...", "Discussion Points:", etc. Log these as "informational step — no action required" and move on.

**Optional steps:**
Execute optional steps too — they're part of the QA. But note them as optional in your log so the user knows which ones they are.

### Executing in the VS Code terminal

**Maximize the terminal first:** Before running lab commands, maximize the terminal panel by clicking the "^" (maximize) button in the terminal panel header, or by dragging the panel divider up. A larger terminal means more output visible per screenshot, which is much more efficient.

To type commands in the VS Code terminal in Chrome:
1. Click on the terminal area to ensure it has focus
2. Type or paste the command
3. Press Enter to execute
4. Wait for the command to complete before proceeding
5. Read the output — take screenshots of significant output

**Important terminal tips:**
- If a command produces very long output, you may need to scroll up in the terminal to check for errors near the beginning
- If a command seems to hang, wait at least 30 seconds before concluding it's stuck. Some operations (model downloads, pip installs) take time.
- If you need to interrupt a running command, use Ctrl+C
- Keep track of your current working directory — use `pwd` if unsure

### Error handling

When you encounter an error or something unexpected:
1. **Check your execution plan first** — Before logging a bug, verify you haven't missed an earlier step. The most common cause of "skeleton file broken" errors is a missed `[MERGE]` step. Go back to your Step 6 execution plan and confirm every prior step for this lab was executed. If you skipped a `code -d` merge, execute it now and re-run.
2. **Log it immediately** with the lab number, step number, the command that failed, and the error output
3. **Try to continue** — don't stop at the first error. The user wants a comprehensive report.
4. **Note cascading failures** — if step 3 failed and steps 4-6 depend on it, note that those steps were likely affected by the earlier failure
5. **Distinguish error types:**
   - **Hard errors**: Command fails, Python traceback, process crashes
   - **Soft errors**: Output doesn't match expected screenshot, warnings that don't prevent continuation
   - **Environmental issues**: Package not installed, service not running, port already in use
   - **Tester error**: You missed a step in the lab flow (e.g., skipped a merge). Fix your execution, don't blame the lab.
   - **Expected skeleton state**: Skeleton files failing before merge is normal — they are not guaranteed to be runnable. This is NOT an error.

## CRITICAL: Report Integrity Rules

These rules exist because past reports contained compressed step tables (12 executed steps squeezed into 8 rows) and fabricated findings (claiming labs had duplicate step numbering when they didn't). This erodes trust and defeats the purpose of QA testing. Every rule below addresses a real failure mode.

1. **Every executed step gets its own row.** If you ran 12 commands/actions in a lab, your "Steps Executed" table must have 12 rows. Do not combine steps like "Merged code and ran script" — those are two separate steps ("Merge code from extra file" and "Run the script"). The table is a faithful log of what happened, not a summary.

2. **Step counts must match.** Before finalizing each lab section, count the rows in your Steps Executed table and compare against the number of actions you actually performed. If they don't match, you've compressed or omitted steps — go back and fix it.

3. **Never fabricate findings.** If you didn't observe a problem, don't report one. This includes documentation issues, numbering problems, or any other "issue" you haven't directly verified against the actual source files. When in doubt, re-read the relevant file before claiming something is wrong with it.

4. **Report only what you observed.** Every claim in the report must trace back to something you actually saw in the terminal output, file contents, or browser. If you're unsure whether something happened, say "unclear" — don't fill in the gap with a plausible guess.

5. **Cross-check the report against labs.md before finalizing.** After drafting the report, re-read the labs.md step lists for each lab and verify that your step counts, step descriptions, and any issues you've flagged actually match reality. This is your final safety net against fabrication.

6. **Distinguish tester limitations from lab problems.** If a step timed out because of Codespace resource constraints, or you couldn't test something because of a missing API key, that's a tester limitation — not a lab defect. Label it accordingly. Never frame your own constraints as problems with the lab materials.

7. **Use your execution plan as a final checklist.** The execution plan you built in Phase 2 lists every step. Walk through it one last time before writing the report and confirm every step appears in your output.

## Phase 4: Generate the Report

After completing all labs, produce a comprehensive test report. Before writing, re-read your execution plan from Phase 2 and your terminal logs to ensure accuracy.

### Report structure

Create a markdown report with this structure:

```markdown
# Lab Test Report

**Repository:** [repo URL]
**Date:** [test date]
**Codespace setup time:** [approximate time from launch to ready]
**Total labs:** [N]
**Total steps executed:** [N]

## Summary

- **Passed steps:** [N] / [total]
- **Failed steps:** [N] / [total]
- **Warnings:** [N]
- **Skipped:** [N] (with reasons)

## Overall Assessment

[2-3 sentence summary: Did the labs work? Were there systemic issues? Is the course ready for students?]

## Lab-by-Lab Results

### Lab 1 - [Title]

**Status:** PASS / FAIL / PARTIAL
**Steps:** [passed]/[total]

| Step | Description | Status | Notes |
|------|-------------|--------|-------|
| 1 | [brief description] | PASS | — |
| 2 | [brief description] | FAIL | [error summary] |
| ... | ... | ... | ... |

**Issues found:**
- [Detailed description of any issues]

### Lab 2 - [Title]
[same structure]

...

## Error Details

### Error 1: [Lab N, Step M]
**Command:** `[the command that failed]`
**Expected:** [what should have happened]
**Actual:** [what actually happened]
**Error output:**
\```
[relevant error output]
\```
**Likely cause:** [your assessment]
**Suggested fix:** [if you have one]

## Recommendations

- [Any systemic issues to address]
- [Steps that were confusing or ambiguous]
- [Missing prerequisites or dependencies]
- [Screenshots that may need updating]
```

### Save and present the report

Save the report as a markdown file in the workspace folder so the user can access it. Also provide a summary in the chat conversation.

## Tips and Patterns

### Common issues to watch for

- **Python virtual environment not activated**: If Python commands fail with "module not found", check if the venv is activated. Run `source .venv/bin/activate` or `source py_env/bin/activate`. The prompt should show the venv name like `(py_env)`.
- **Ollama not running**: AI/ML labs often need Ollama. If model-related commands fail, check if Ollama is running with `ollama list`. You may need to run `ollama serve &` first.
- **Port conflicts**: If a server won't start because the port is in use, note it as an environmental issue.
- **File paths**: Labs reference files relative to certain directories. Always be aware of your `pwd`. Use `pwd` if unsure.
- **Long-running operations**: Model downloads, large pip installs, and training operations can take minutes. Be patient.
- **Codespace connection drops**: If the VS Code web UI shows a "Failed to connect" error, try "Retry" first, then do a full page reload if that doesn't work.

### Benign warnings to ignore

These are common warnings that appear in Codespace terminal output and are NOT errors:

- **ONNX Runtime PCI bus ID warnings**: Messages like `[W:onnxruntime:Default, device_discovery.cc:131 GetPciBusId] Skipping pci_bus_id...` are harmless hardware detection messages.
- **Deprecation warnings**: Python deprecation warnings from third-party packages don't affect functionality.
- **Pip version notices**: "A new version of pip is available" is informational, not an error.
- **Git "detached HEAD" notices**: These are expected when Codespaces checks out a specific commit.
- **npm WARN** messages during `npm install` are usually about optional dependencies.

### Screenshot comparison

When a step includes a screenshot showing expected output, don't expect an exact match. Look for:
- Same general structure and format
- Key values or patterns present
- No error messages where the screenshot shows success
- Reasonable differences (timestamps, random values, etc. will differ)

### Multiple terminal management

When labs require multiple terminals (e.g., server in one, client in another):
1. Note which terminal each command should run in
2. Open new terminals as needed using the VS Code UI (+ button in terminal panel)
3. Label them in your log (Terminal 1: server, Terminal 2: client)
4. Make sure to click/focus the correct terminal before typing commands

## Lessons from Live Testing

These tips come from actual live test runs and address real issues encountered during automated lab execution.

### Terminal management

- **Creating new terminals**: If existing terminal tabs are stale or unresponsive (common after long sessions), use the keyboard shortcut `Ctrl+Shift+`` to create a fresh terminal. This is more reliable than clicking the `+` button, which can sometimes be hard to target.
- **Stale terminal tabs**: After running many labs, you may accumulate multiple terminal tabs. Don't try to click on old tabs — they may trigger context menus or be unresponsive. Create a new terminal instead.
- **Always verify your directory**: After creating a new terminal, run `pwd` and `cd` to the correct directory before executing commands. New terminals open at the repo root, not where you left off.

### Background server management

For labs requiring multiple servers (e.g., auth server + application server + client):
- **Use background execution**: Run servers with `&` instead of opening separate terminals. Example:
  ```bash
  python auth_server.py &
  python secure_server.py &
  ```
- **Wait after background launch**: Add a brief `sleep 2` or check output before running the client to ensure servers are ready.
- **Clean up between labs**: Kill background servers before starting the next lab:
  ```bash
  kill %1 %2  # kills background jobs by job number
  ```
  Or use `kill $(lsof -t -i:PORT)` to kill by port number.
- **Chain commands efficiently**: Use `&&` to chain related operations:
  ```bash
  cp ../extra/file1.txt file1.py && cp ../extra/file2.txt file2.py && echo "done"
  ```

### Interactive programs

- **Exiting interactive programs**: When a Python script runs an interactive loop (e.g., `input()` prompt), use `Ctrl+C` to exit. Do NOT type "quit" or "exit" — many programs will try to process those as valid input rather than exit commands.
- **Handling slow responses**: Local LLM-powered programs (using Ollama with models like qwen2.5:3b) can take 1-2 minutes per query on a 4-core Codespace. Be patient and wait. Take screenshots periodically to check if the model is still processing.
- **Sending multi-line input**: For interactive prompts that expect complex input (e.g., attack prompts), type the full text and press Enter. The VS Code terminal handles multi-line paste well.

### Skeleton files and merge steps

**Key concept: Skeleton files are NOT guaranteed to be runnable before merging.** They are intentionally incomplete starting points that students merge complete code into via `code -d` steps. Syntax errors, indentation errors, or missing code in skeleton files are expected — do NOT report them as bugs.

**CAUTION:** If you run a file and get a syntax/indentation error, your first assumption should be that you missed a `code -d` merge step earlier in the lab. Go back to your execution plan and verify. In live testing, a skeleton file error was incorrectly reported as a blocking bug because the tester had skipped the merge step that labs.md included.

How to handle skeleton file issues:
- **If a merge step exists before the run command**: The skeleton's state is irrelevant — students will get the working version through normal lab flow. Note the skeleton's state as an observation, not a warning or error.
- **Only report as a problem if there's NO merge step AND the file needs to be runnable**: A file that the lab asks students to run directly (no preceding merge) must actually work. This is a genuine bug.
- **Always cross-reference your execution plan**: This is what Step 6 is for.

### Timing expectations

- **Codespace setup**: 3-5 minutes for container build + post-create scripts
- **Ollama model warmup**: 1-3 minutes after Codespace setup (if post-attach script pulls models)
- **Local LLM queries**: 30 seconds to 2+ minutes per query depending on model size and machine type
- **`code -d` merge operations**: The automated `cp` approach takes <1 second vs. manual diffing
- **Server startup**: Most Python servers (Flask, Uvicorn) start in 2-5 seconds

### Chrome MCP connection handling

- **Intermittent disconnects**: The Chrome MCP connection may drop during `wait` operations. This is normal — simply retry the next tool call and it will reconnect automatically.
- **Take screenshots liberally**: Screenshots help you verify what's on screen after connection recovery and ensure you're looking at the right terminal/state.
- **Page reloads**: If the VS Code web UI becomes completely unresponsive, navigate to the Codespace URL again. The Codespace itself keeps running — only the web client needs reconnecting.
