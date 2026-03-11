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

### As a Claude Code Plugin (recommended)

```bash
# 1. Add the marketplace
/plugin marketplace add Teese999/Dopamine

# 2. Install the plugin
/plugin install dopamine
```

### Manual Install

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

### Slash Commands (plugin install)

```
/dopamine degrade     # 📉 Shorts/Reels
/dopamine progress    # 📈 Useful articles
/dopamine shorts      # Set source: YouTube Shorts
/dopamine reels       # Set source: Instagram Reels
/dopamine login       # Log in to YouTube & Instagram
/dopamine             # Show current settings
```

### CLI (manual install)

```bash
python3 ~/.claude/hooks/entertainment.py mode degrade
python3 ~/.claude/hooks/entertainment.py mode progress
python3 ~/.claude/hooks/entertainment.py setup shorts
python3 ~/.claude/hooks/entertainment.py setup reels
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

## Support the Project

If Dopamine made your coding sessions more fun (or more productive), consider buying me a coffee:

| BTC | ETH (ERC-20) | USDT (TRC-20) |
|:---:|:---:|:---:|
| <img src="assets/qr_btc.png" width="150"> | <img src="assets/qr_eth.png" width="150"> | <img src="assets/qr_usdt_trc20.png" width="150"> |
| `15FgAxLWXSQimGUVyH2eGzDpLzZHHmLhWG` | `0xa6ba31dd11cd5943c5ca4a7d7aaf433a0892d7e6` | `THJfpf9MmsNqjr8AWvp5gu88gSS6SawrZU` |

## License

MIT
