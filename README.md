# Dopamine 🧠⚡

**Watch Shorts while Claude works. Read articles while Claude codes.**

A Claude Code hook that opens entertainment or educational content while AI handles your tasks — and closes it when the work is done.

## Two Modes

### 📉 Degrade Mode
Opens YouTube Shorts or Instagram Reels in a compact window next to your terminal. Auto-closes when Claude finishes. Pure dopamine, zero guilt — the AI is doing the work anyway.

### 📈 Progress Mode
Opens a relevant article based on what Claude is currently working on. Building a React component? Here's a React best practices article. Writing Python? Here's a Python tutorial. The window stays open so you can keep reading.

## How It Works

```
You ask Claude to do something
  → Claude starts using tools
    → Dopamine opens a browser window next to your terminal
      → You watch/read while Claude works
        → Claude finishes
          → Degrade: window closes automatically
          → Progress: window stays open for reading
```

## Install

```bash
# 1. Copy the hook script
mkdir -p ~/.claude/hooks
cp entertainment.py ~/.claude/hooks/entertainment.py

# 2. Add hooks to ~/.claude/settings.json
# (merge with your existing settings)
```

Add to your `~/.claude/settings.json`:

```json
{
  "hooks": {
    "PreToolUse": [
      {
        "hooks": [
          {
            "type": "command",
            "command": "python3 ~/.claude/hooks/entertainment.py"
          }
        ]
      }
    ],
    "Stop": [
      {
        "hooks": [
          {
            "type": "command",
            "command": "python3 ~/.claude/hooks/entertainment.py"
          }
        ]
      }
    ],
    "SessionEnd": [
      {
        "hooks": [
          {
            "type": "command",
            "command": "python3 ~/.claude/hooks/entertainment.py"
          }
        ]
      }
    ]
  }
}
```

```bash
# 3. (Optional) Log in to YouTube / Instagram
python3 ~/.claude/hooks/entertainment.py login
```

## Usage

```bash
# Switch modes
python3 ~/.claude/hooks/entertainment.py mode degrade     # 📉 Shorts/Reels
python3 ~/.claude/hooks/entertainment.py mode progress    # 📈 Useful articles

# Change degrade source
python3 ~/.claude/hooks/entertainment.py setup shorts     # YouTube Shorts (default)
python3 ~/.claude/hooks/entertainment.py setup reels      # Instagram Reels

# Log in to services
python3 ~/.claude/hooks/entertainment.py login
```

## Features

- **Cross-platform** — macOS, Windows, Linux
- **Smart window placement** — opens next to your terminal, sized for vertical video (degrade) or comfortable reading (progress)
- **Topic detection** — in progress mode, extracts tech keywords from Claude's current task (file paths, frameworks, languages) and finds a relevant article
- **One window per session** — doesn't spam browser windows on every tool call
- **Auto-cleanup** — degrade mode closes the window when Claude stops; progress mode keeps it open

## Browser Support

| OS | Browsers |
|----|----------|
| macOS | Chrome, Safari, Firefox, Arc |
| Windows | Chrome, Edge, Firefox |
| Linux | Chrome, Chromium, Firefox |

Window positioning and auto-close work best on macOS (via AppleScript). On Windows/Linux it's best-effort.

## Requirements

- Python 3.6+
- [Claude Code](https://claude.ai/code)
- A browser
- Questionable life choices (degrade mode) or self-improvement ambitions (progress mode)

## How Topic Detection Works (Progress Mode)

Dopamine reads the tool input that Claude is currently processing and extracts:

- **File extensions** → `.tsx` = React + TypeScript, `.py` = Python, etc.
- **Framework keywords** → React, Vue, Django, Express, Prisma, etc.
- **Path segments** → meaningful directory/file names

Then opens the top DuckDuckGo result for `"{topic} best practices tutorial"`.

## License

MIT
