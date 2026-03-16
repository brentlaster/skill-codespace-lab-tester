---
name: codespace-cc-installer
description: >
  Automates the full installation and authentication of Claude Code inside a running GitHub Codespace
  in Chrome. Use this skill whenever the user wants to install Claude Code in a Codespace, set up
  Claude Code in a Codespace, or says things like "install claude in the codespace", "set up claude code
  in the codespace", "get claude running in the codespace", or provides a Codespace URL and wants
  Claude Code installed and authenticated. Also trigger when the user mentions installing the Claude CLI,
  setting up the Claude terminal, or authenticating Claude in a browser-based VS Code environment.
  This skill drives Chrome to type commands in the Codespace terminal, handle the OAuth authentication
  flow across tabs, and complete the interactive setup prompts.
---

# Codespace Claude Code Installer

You are a browser automation agent that installs and authenticates Claude Code inside a running GitHub Codespace through Chrome. The user will point you at a Chrome tab containing an already-running Codespace with a visible terminal. Your job is to execute the entire installation and authentication flow end-to-end, as quickly as possible.

## Speed Principles

This workflow has many sequential steps, so minimizing unnecessary delays is critical:
- **Don't take extra screenshots** unless you need to verify something unexpected. If you just performed an action and know what the next screen will be, proceed directly.
- **Use short waits** (2-3 seconds) between steps rather than long ones. Only use longer waits (15+ seconds) for npm install.
- **Use JavaScript extraction** (`javascript_tool`) to read text from pages rather than zooming/screenshot OCR — it's faster and more accurate.
- **Read the popup dialog URL** using `read_page` before dismissing it — the auth URL is right there in the DOM, so you don't need to parse the terminal.

## Before You Start

1. **Get the Codespace tab** — use `tabs_context_mcp` to discover Chrome tabs. If the user provided a URL, navigate to it. The Codespace should already be fully loaded with a visible terminal.
2. **Take a screenshot** to confirm you can see VS Code with a terminal panel. Note the tab ID — you'll need it later.
3. **Dismiss any notifications** (port forwarding popups, etc.) by clicking their X buttons.
4. **Click on the terminal area** to ensure it has focus before typing anything.

## Phase 1: Install Claude Code

### Step 1: Install via npm

GitHub Codespaces come with Node.js pre-installed, so npm is available. Type the install command in the terminal:

```
npm install -g @anthropic-ai/claude-code
```

Press Enter and wait for the installation to complete. This typically takes 15-30 seconds. Wait about 15 seconds, then take a screenshot. You'll know it's done when you see a clean command prompt again (the `$` prompt returns).

**If you see permission errors (EACCES):** Try the alternative install approach:
```
curl -fsSL https://claude.ai/install.sh | bash
```
After the curl install, run `source ~/.bashrc` to update the PATH.

### Step 2: Launch Claude Code

Once installation is complete, type:

```
claude --dangerously-skip-permissions
```

Press Enter. Wait about 5 seconds for Claude Code to start up and show its first interactive prompt.

## Phase 2: Interactive Setup

Claude Code presents interactive prompts that use **arrow-key navigation**, not number typing. Each prompt has a `>` marker showing the currently selected option. Press **Enter** to confirm the highlighted option, or press **ArrowDown/ArrowUp** to move between options first.

### Step 3: Theme selection

Claude Code first asks to choose a theme. Option 1 (Dark mode) is pre-selected (the `>` marker is already on it).

**Action:** Just press **Enter** to confirm Dark mode.

Wait 2 seconds for the next prompt.

### Step 4: Login method selection

Claude Code asks how to authenticate. Option 1 (Claude account with subscription) is pre-selected.

**Action:** Just press **Enter** to confirm.

After this, two things happen simultaneously:
- A **popup dialog** appears asking "Do you want Code to open the external website?" — this contains the auth URL in its body text.
- The **terminal** behind the popup shows the auth URL and a "Paste code here if prompted >" prompt.

### Step 5: Extract the auth URL from the popup, then dismiss it

**This is the fastest approach.** Before dismissing the popup dialog, extract the auth URL from it using `read_page` or `javascript_tool`. The dialog contains the full URL as visible text.

Use JavaScript to extract it efficiently:
```javascript
// Look for the dialog text that contains the oauth URL
document.querySelector('.dialog-message-text, .monaco-dialog-box .dialog-message-text, [class*="dialog"] a, [class*="dialog"] p')?.textContent
```

If JavaScript doesn't find it cleanly, use `read_page` to locate the dialog element and read its text content. The URL starts with `https://claude.ai/oauth/authorize?...`.

**IMPORTANT:** The popup URL uses a `localhost` redirect_uri which won't work. You need the **terminal URL** instead, which uses `platform.claude.com` as the redirect. So after reading the popup URL, modify it:
- Replace `redirect_uri=http%3A%2F%2Flocalhost%3A[PORT]%2Fcallback` with `redirect_uri=https%3A%2F%2Fplatform.claude.com%2Foauth%2Fcode%2Fcallback`

Alternatively, just dismiss the popup and read the URL from the terminal instead (see Fallback below).

After extracting the URL, click **"Cancel"** to dismiss the popup dialog.

**Fallback — reading URL from terminal:** If extracting from the popup doesn't work, dismiss the popup and zoom into the terminal area where the URL is printed. The URL spans multiple wrapped lines. Use `zoom` on the terminal text area to read it piece by piece, or use `read_page` to try to extract terminal text content.

### Step 6: Open the auth URL in a new tab

Create a new Chrome tab using `tabs_create_mcp`, then navigate to the authentication URL. Note this new tab's ID.

Wait 3-5 seconds for the page to load.

### Step 7: Authorize and get the code

On the authorization page, click the **"Authorize"** button. Wait 2-3 seconds for the page to redirect.

After authorization, you'll land on a page showing "Authentication Code" with a code and a "Copy Code" button.

**Extract the code using JavaScript** — this is faster and more reliable than clicking Copy Code:
```javascript
document.querySelector('code, pre, [class*="code"]')?.textContent
```

This returns the full auth code string. Save it — you'll need to type it in the terminal.

### Step 8: Paste the auth code in the terminal

Switch back to the **Codespace tab** (use the original tab ID). Click on the terminal area to ensure focus.

The terminal should show "Paste code here if prompted >". **Type the auth code directly** using the `type` action — this is more reliable than clipboard paste in VS Code web terminals.

Press **Enter** after typing the code.

### Step 9: Continue through post-auth screens

After entering the code, Claude Code shows informational screens. You need to press Enter to continue through them:

1. **"Login successful. Press Enter to continue..."** — press **Enter**
2. **"Security notes" / "Press Enter to continue..."** — press **Enter**

Wait 2 seconds between each press.

### Step 10: Answer the three setup questions

These use the same arrow-key selection UI. Option 1 is pre-selected by default with the `>` marker.

1. **"Use Claude Code's terminal setup?"** — Option 1 ("Yes, use recommended settings") is pre-selected. Press **Enter**.
2. **"Security guide" / "Yes, I trust this folder"** — Option 1 is pre-selected. Press **Enter**.
3. **"Bypass Permissions mode"** — Option 1 is "No, exit" (pre-selected). You need option 2 ("Yes, I accept"). Press **ArrowDown** once to move the `>` to option 2, then press **Enter**.

Wait 2 seconds between each answer for the next question to appear.

### Step 11: Final startup

After the last question, Claude Code displays a welcome message with the Claude mascot, account info, and tips. It then shows the `>` input prompt, meaning it's ready.

Wait 5 seconds for the welcome screen to finish rendering, then press **Enter** one final time to ensure you're at a clean prompt.

## Completion

Take a final screenshot to confirm Claude Code is running. You should see:
- The Claude Code welcome banner with "Welcome back [name]!"
- Model info (e.g., "Opus 4.6 (1M context)")
- A `>` input prompt ready for commands
- "bypass permissions on" at the bottom

Let the user know that Claude Code is installed, authenticated, and ready to use.

## Troubleshooting

### "command not found" after npm install
The npm global bin path may not be in the shell's PATH. Try:
```bash
export PATH="$HOME/.npm-global/bin:$PATH"
```
Or open a new terminal with Ctrl+Shift+` and try `claude --dangerously-skip-permissions` again.

### Auth URL extraction fails
If you can't extract the URL from the popup or terminal text:
1. Try `read_page` with `filter: "all"` on the Codespace tab to find dialog elements
2. Zoom into the terminal text area and read the URL line by line
3. The URL always starts with `https://claude.ai/oauth/authorize?code=true&client_id=`

### Popup won't dismiss
Try pressing **Escape**, or look for a small X button. If the popup is a VS Code notification (bottom-right corner), there's usually a close icon. If it's a browser-level dialog, look for Cancel/Don't Allow/Block options.

### Paste/type doesn't work in terminal
If typing the auth code doesn't register:
1. Click directly on the terminal text area (not the header or tabs) to regain focus
2. Try Ctrl+Shift+V (VS Code terminal paste shortcut)
3. As a last resort, type the code character by character

### Terminal lost focus after tab switch
After switching back from the auth tab, always click on the terminal text area before typing. Click in the lower portion of the terminal where the prompt text is.
