---
allowed-tools: Bash
---

Dopamine plugin control. Run the appropriate command based on the user's argument: "$ARGUMENTS"

Available commands:
- `degrade` — switch to degrade mode (Shorts/Reels, auto-close)
- `progress` — switch to progress mode (useful articles, stays open)
- `shorts` — set degrade source to YouTube Shorts
- `reels` — set degrade source to Instagram Reels
- `login` — open login pages for YouTube and Instagram
- `status` — show current mode and settings

Map the argument to the correct command:

| Argument | Command |
|----------|---------|
| degrade | `python3 "${CLAUDE_PLUGIN_ROOT}/entertainment.py" mode degrade` |
| progress | `python3 "${CLAUDE_PLUGIN_ROOT}/entertainment.py" mode progress` |
| shorts | `python3 "${CLAUDE_PLUGIN_ROOT}/entertainment.py" setup shorts` |
| reels | `python3 "${CLAUDE_PLUGIN_ROOT}/entertainment.py" setup reels` |
| login | `python3 "${CLAUDE_PLUGIN_ROOT}/entertainment.py" login` |
| (empty or status) | `cat "$(python3 -c "import tempfile,os;print(os.path.join(tempfile.gettempdir(),'claude-entertainment','config.json'))")" 2>/dev/null \|\| echo '{"mode":"degrade","platform":"shorts"}'` |

Run the bash command and report the result to the user.
