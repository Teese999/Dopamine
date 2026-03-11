#!/usr/bin/env python3
"""
Claude Code Entertainment Hook
Two modes:
  degrade  — Opens YouTube Shorts or Instagram Reels (closes on Stop)
  progress — Opens a useful article about current topic (stays open)

Usage:
  python3 entertainment.py login              # Open login pages
  python3 entertainment.py mode degrade       # Switch to degrade mode
  python3 entertainment.py mode progress      # Switch to progress mode
  python3 entertainment.py setup shorts       # Set degrade source to YouTube Shorts
  python3 entertainment.py setup reels        # Set degrade source to Instagram Reels
  (stdin JSON from Claude hooks)              # Normal hook mode
"""

import json
import sys
import os
import platform
import subprocess
import webbrowser
import tempfile
import time
import re
from urllib.parse import quote_plus

STATE_DIR = os.path.join(tempfile.gettempdir(), "claude-entertainment")

URLS = {
    "shorts": "https://www.youtube.com/shorts",
    "reels": "https://www.instagram.com/reels/",
}

LOGIN_URLS = [
    "https://accounts.google.com",
    "https://www.instagram.com/accounts/login/",
]

# Shorts/Reels are 9:16
WIN_WIDTH = 400
WIN_HEIGHT = 750

# Progress mode: wider for articles
ARTICLE_WIDTH = 800
ARTICLE_HEIGHT = 900


def config_path():
    return os.path.join(STATE_DIR, "config.json")


def state_file(session_id):
    return os.path.join(STATE_DIR, f"session_{session_id}")


def load_config():
    try:
        with open(config_path()) as f:
            return json.load(f)
    except (FileNotFoundError, json.JSONDecodeError):
        return {"platform": "shorts", "mode": "degrade"}


def save_config(cfg):
    os.makedirs(STATE_DIR, exist_ok=True)
    with open(config_path(), "w") as f:
        json.dump(cfg, f)


STALE_THRESHOLD = 3 * 3600  # 3 hours


def cleanup_stale_sessions():
    """Remove state files older than STALE_THRESHOLD."""
    if not os.path.isdir(STATE_DIR):
        return
    now = time.time()
    for name in os.listdir(STATE_DIR):
        if not name.startswith("session_"):
            continue
        path = os.path.join(STATE_DIR, name)
        try:
            if now - os.path.getmtime(path) > STALE_THRESHOLD:
                os.remove(path)
        except OSError:
            pass


def is_open(session_id):
    return os.path.exists(state_file(session_id))


def mark_open(session_id, url, mode, pid=None):
    os.makedirs(STATE_DIR, exist_ok=True)
    with open(state_file(session_id), "w") as f:
        json.dump({"url": url, "pid": pid, "mode": mode, "ts": time.time()}, f)


def mark_closed(session_id):
    path = state_file(session_id)
    if os.path.exists(path):
        os.remove(path)


# --- Topic extraction ---

# Common tool-related keywords to filter out
NOISE_WORDS = {
    "bash", "read", "write", "edit", "glob", "grep", "agent",
    "the", "a", "an", "is", "are", "was", "were", "be", "been",
    "have", "has", "had", "do", "does", "did", "will", "would",
    "could", "should", "may", "might", "shall", "can",
    "and", "or", "but", "if", "then", "else", "when", "where",
    "how", "what", "which", "who", "whom", "this", "that",
    "for", "from", "with", "into", "of", "to", "in", "on", "at",
    "by", "as", "not", "no", "all", "each", "every", "some",
    "file", "files", "directory", "path", "command", "run",
    "true", "false", "null", "none", "undefined",
}


def extract_topic(tool_input):
    """Extract meaningful topic keywords from tool input."""
    keywords = set()

    if not tool_input:
        return None

    # Get text from tool input
    text = ""
    if isinstance(tool_input, dict):
        # From Bash commands
        cmd = tool_input.get("command", "")
        desc = tool_input.get("description", "")
        # From file operations
        file_path = tool_input.get("file_path", "")
        pattern = tool_input.get("pattern", "")
        prompt = tool_input.get("prompt", "")

        text = f"{cmd} {desc} {file_path} {pattern} {prompt}"
    elif isinstance(tool_input, str):
        text = tool_input

    if not text:
        return None

    # Extract meaningful words
    # File extensions as tech indicators
    ext_map = {
        ".py": "python", ".js": "javascript", ".ts": "typescript",
        ".tsx": "react typescript", ".jsx": "react javascript",
        ".rs": "rust", ".go": "golang", ".rb": "ruby",
        ".java": "java", ".kt": "kotlin", ".swift": "swift",
        ".css": "css", ".scss": "sass css", ".html": "html",
        ".sql": "sql database", ".prisma": "prisma orm",
        ".vue": "vue.js", ".svelte": "svelte",
        ".docker": "docker", ".yml": "yaml", ".yaml": "yaml",
        ".sh": "bash shell", ".zsh": "zsh shell",
    }

    for ext, tech in ext_map.items():
        if ext in text.lower():
            keywords.update(tech.split())

    # Extract tech terms from common patterns
    tech_patterns = [
        r'\b(react|vue|angular|svelte|next|nuxt|remix)\b',
        r'\b(node|deno|bun|npm|yarn|pnpm)\b',
        r'\b(python|pip|django|flask|fastapi)\b',
        r'\b(rust|cargo|tokio)\b',
        r'\b(docker|kubernetes|k8s|nginx|redis|postgres|mongo)\b',
        r'\b(git|github|gitlab)\b',
        r'\b(api|rest|graphql|grpc|websocket)\b',
        r'\b(css|tailwind|styled|sass|scss)\b',
        r'\b(test|jest|pytest|mocha|vitest)\b',
        r'\b(aws|gcp|azure|vercel|netlify)\b',
        r'\b(prisma|typeorm|sequelize|drizzle)\b',
        r'\b(express|fastify|koa|nest)\b',
    ]

    for pat in tech_patterns:
        matches = re.findall(pat, text.lower())
        keywords.update(matches)

    # Extract from file path segments
    path_parts = re.findall(r'[\w-]+', text)
    for part in path_parts:
        lower = part.lower()
        if lower not in NOISE_WORDS and len(lower) > 2:
            # Only add if it looks like a meaningful term
            if any(c.isalpha() for c in lower):
                keywords.add(lower)

    # Limit to most relevant keywords
    keywords -= NOISE_WORDS
    if not keywords:
        return None

    # Pick top 3-4 keywords
    kw_list = sorted(keywords, key=len, reverse=True)[:4]
    return " ".join(kw_list)


def build_search_url(topic):
    """Build a search URL — redirects directly to top article via DuckDuckGo."""
    query = f"\\ {topic} best practices tutorial"
    return f"https://duckduckgo.com/?q={quote_plus(query)}"


# --- Browser operations ---

def detect_browser_mac():
    """Detect the default browser on macOS."""
    try:
        result = subprocess.run(
            ["defaults", "read",
             "com.apple.LaunchServices/com.apple.launchservices.secure",
             "LSHandlers"],
            capture_output=True, text=True, timeout=5
        )
        output = result.stdout.lower()
        if "chrome" in output:
            return "chrome"
        if "firefox" in output:
            return "firefox"
        if "arc" in output:
            return "arc"
    except Exception:
        pass
    return "safari"


def get_terminal_bounds_mac():
    """Get the terminal window position on macOS. Returns (x, y, w, h) or None."""
    for app in ["Terminal", "iTerm2", "Alacritty", "kitty", "WezTerm", "Ghostty"]:
        script = f'''
            tell application "System Events"
                if exists process "{app}" then
                    tell process "{app}"
                        set frontWin to front window
                        set winPos to position of frontWin
                        set winSize to size of frontWin
                        return (item 1 of winPos) & "," & (item 2 of winPos) & "," & (item 1 of winSize) & "," & (item 2 of winSize)
                    end tell
                end if
            end tell
        '''
        try:
            r = subprocess.run(["osascript", "-e", script],
                               capture_output=True, text=True, timeout=3)
            if r.returncode == 0 and "," in r.stdout:
                parts = r.stdout.strip().split(",")
                return tuple(int(p.strip()) for p in parts)
        except Exception:
            continue
    return None


def position_window_mac(browser, width, height):
    """Position browser window next to terminal."""
    bounds = get_terminal_bounds_mac()
    if bounds:
        tx, ty, tw, th = bounds
        wx = tx + tw + 10
        wy = ty
    else:
        wx, wy = 100, 100

    app_name = {
        "chrome": "Google Chrome",
        "safari": "Safari",
        "firefox": "Firefox",
        "arc": "Arc",
    }.get(browser, "Safari")

    if browser == "chrome":
        script = f'''
            tell application "Google Chrome"
                set bounds of front window to {{{wx}, {wy}, {wx + width}, {wy + height}}}
            end tell
        '''
    elif browser == "arc":
        script = f'''
            tell application "System Events"
                tell process "Arc"
                    set frontWin to front window
                    set position of frontWin to {{{wx}, {wy}}}
                    set size of frontWin to {{{width}, {height}}}
                end tell
            end tell
        '''
    elif browser == "safari":
        script = f'''
            tell application "Safari"
                set bounds of front window to {{{wx}, {wy}, {wx + width}, {wy + height}}}
            end tell
        '''
    else:
        script = f'''
            tell application "System Events"
                tell process "{app_name}"
                    set frontWin to front window
                    set position of frontWin to {{{wx}, {wy}}}
                    set size of frontWin to {{{width}, {height}}}
                end tell
            end tell
        '''

    try:
        subprocess.run(["osascript", "-e", script],
                       capture_output=True, timeout=5)
    except Exception:
        pass


def open_new_window(url, width=WIN_WIDTH, height=WIN_HEIGHT):
    """Open URL in a NEW browser window, sized appropriately."""
    system = platform.system()

    if system == "Darwin":
        browser = detect_browser_mac()
        bounds = get_terminal_bounds_mac()
        if bounds:
            tx, ty, tw, th = bounds
            wx, wy = tx + tw + 10, ty
        else:
            wx, wy = 100, 100

        if browser == "chrome":
            script = f'''
                tell application "Google Chrome"
                    set newWin to make new window
                    set URL of active tab of newWin to "{url}"
                    set bounds of newWin to {{{wx}, {wy}, {wx + width}, {wy + height}}}
                end tell
            '''
            subprocess.run(["osascript", "-e", script],
                           capture_output=True, timeout=5)
            return None
        elif browser == "firefox":
            subprocess.Popen(
                ["open", "-na", "Firefox", "--args", "--new-window", url],
                stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL
            )
            time.sleep(1)
            position_window_mac(browser, width, height)
            return None
        elif browser == "arc":
            script = f'''
                tell application "Arc"
                    make new window
                    tell front window
                        set URL of active tab to "{url}"
                    end tell
                end tell
            '''
            subprocess.run(["osascript", "-e", script],
                           capture_output=True, timeout=5)
            time.sleep(0.5)
            position_window_mac(browser, width, height)
            return None
        else:
            script = f'''
                tell application "Safari"
                    set newDoc to make new document with properties {{URL:"{url}"}}
                end tell
            '''
            subprocess.run(["osascript", "-e", script],
                           capture_output=True, timeout=5)
            time.sleep(0.5)
            position_window_mac(browser, width, height)
            return None

    elif system == "Windows":
        for browser_cmd in ["chrome", "msedge", "firefox"]:
            try:
                proc = subprocess.Popen(
                    [browser_cmd, "--new-window",
                     f"--window-size={width},{height}", url],
                    stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL
                )
                return proc.pid
            except FileNotFoundError:
                continue
        subprocess.Popen(
            ["cmd", "/c", "start", "", url],
            stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL
        )
        return None

    elif system == "Linux":
        for browser_cmd in ["google-chrome", "chromium-browser", "firefox"]:
            try:
                proc = subprocess.Popen(
                    [browser_cmd, "--new-window",
                     f"--window-size={width},{height}", url],
                    stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL
                )
                time.sleep(1)
                try:
                    subprocess.run(
                        ["xdotool", "getactivewindow", "windowsize",
                         str(width), str(height)],
                        capture_output=True, timeout=3
                    )
                except Exception:
                    pass
                return proc.pid
            except FileNotFoundError:
                continue
        webbrowser.open_new(url)
        return None

    return None


def close_window(url):
    """Close the browser window containing the URL."""
    system = platform.system()

    if system == "Darwin":
        browser = detect_browser_mac()

        if browser == "chrome":
            script = f'''
                tell application "Google Chrome"
                    repeat with w in every window
                        set dominated to false
                        repeat with t in every tab of w
                            if URL of t contains "{url}" then
                                set dominated to true
                                exit repeat
                            end if
                        end repeat
                        if dominated then
                            close w
                            return
                        end if
                    end repeat
                end tell
            '''
        elif browser == "arc":
            script = f'''
                tell application "Arc"
                    repeat with w in every window
                        repeat with t in every tab of w
                            if URL of t contains "{url}" then
                                close w
                                return
                            end if
                        end repeat
                    end repeat
                end tell
            '''
        elif browser == "firefox":
            script = f'''
                tell application "System Events"
                    tell process "Firefox"
                        set frontmost to true
                        keystroke "w" using {{command down, shift down}}
                    end tell
                end tell
            '''
        else:
            script = f'''
                tell application "Safari"
                    repeat with w in every window
                        set dominated to false
                        repeat with t in every tab of w
                            if URL of t contains "{url}" then
                                set dominated to true
                                exit repeat
                            end if
                        end repeat
                        if dominated then
                            close w
                            return
                        end if
                    end repeat
                end tell
            '''

        try:
            subprocess.run(["osascript", "-e", script],
                           capture_output=True, timeout=5)
        except Exception:
            pass

    elif system == "Windows":
        try:
            ps_script = '''
            Add-Type @"
            using System;
            using System.Runtime.InteropServices;
            public class Win32 {
                [DllImport("user32.dll")]
                public static extern bool EnumWindows(EnumWindowsProc lpEnumFunc, IntPtr lParam);
                [DllImport("user32.dll")]
                public static extern int GetWindowText(IntPtr hWnd, System.Text.StringBuilder lpString, int nMaxCount);
                [DllImport("user32.dll")]
                public static extern bool PostMessage(IntPtr hWnd, uint Msg, IntPtr wParam, IntPtr lParam);
                public delegate bool EnumWindowsProc(IntPtr hWnd, IntPtr lParam);
            }
"@
            $WM_CLOSE = 0x0010
            [Win32]::EnumWindows({
                param($hWnd, $lParam)
                $sb = New-Object System.Text.StringBuilder 256
                [Win32]::GetWindowText($hWnd, $sb, 256) | Out-Null
                $title = $sb.ToString()
                if ($title -match "Shorts|Reels") {
                    [Win32]::PostMessage($hWnd, $WM_CLOSE, [IntPtr]::Zero, [IntPtr]::Zero)
                    return $false
                }
                return $true
            }, [IntPtr]::Zero)
            '''
            subprocess.run(
                ["powershell", "-Command", ps_script],
                capture_output=True, timeout=10
            )
        except Exception:
            pass

    elif system == "Linux":
        try:
            result = subprocess.run(
                ["xdotool", "search", "--name", "Shorts|Reels"],
                capture_output=True, text=True, timeout=5
            )
            for wid in result.stdout.strip().split("\n"):
                if wid:
                    subprocess.run(
                        ["xdotool", "windowclose", wid],
                        capture_output=True, timeout=5
                    )
                    break
        except Exception:
            pass


# --- Main logic ---

def open_entertainment(session_id, tool_input=None):
    cleanup_stale_sessions()
    if is_open(session_id):
        return

    cfg = load_config()
    mode = cfg.get("mode", "degrade")

    if mode == "progress":
        topic = extract_topic(tool_input)
        if not topic:
            topic = "software engineering"
        url = build_search_url(topic)
        pid = open_new_window(url, ARTICLE_WIDTH, ARTICLE_HEIGHT)
        mark_open(session_id, url, mode, pid)
    else:
        url = URLS.get(cfg.get("platform", "shorts"), URLS["shorts"])
        pid = open_new_window(url, WIN_WIDTH, WIN_HEIGHT)
        mark_open(session_id, url, mode, pid)


def close_entertainment(session_id):
    path = state_file(session_id)
    if not os.path.exists(path):
        return
    try:
        with open(path) as f:
            state = json.load(f)
        # In progress mode, don't close — let the dev read
        if state.get("mode") == "progress":
            mark_closed(session_id)
            return
        close_window(state.get("url", ""))
    except Exception:
        pass
    mark_closed(session_id)


# --- CLI commands ---

def cmd_login():
    for url in LOGIN_URLS:
        webbrowser.open(url)
    print("Opened login pages for YouTube and Instagram.")


def cmd_setup(platform_name):
    if platform_name not in URLS:
        print(f"Unknown platform '{platform_name}'. Use: {', '.join(URLS.keys())}")
        sys.exit(1)
    cfg = load_config()
    cfg["platform"] = platform_name
    save_config(cfg)
    print(f"Degrade source set to: {platform_name} ({URLS[platform_name]})")


def cmd_mode(mode_name):
    if mode_name not in ("degrade", "progress"):
        print(f"Unknown mode '{mode_name}'. Use: degrade, progress")
        sys.exit(1)
    cfg = load_config()
    cfg["mode"] = mode_name
    save_config(cfg)
    emoji = {"degrade": "📉", "progress": "📈"}
    desc = {
        "degrade": "YouTube Shorts / Reels (auto-close)",
        "progress": "Useful articles on current topic (stays open)",
    }
    print(f"{emoji[mode_name]} Mode: {mode_name} — {desc[mode_name]}")


def cmd_hook():
    try:
        input_data = json.load(sys.stdin)
    except Exception:
        return

    session_id = input_data.get("session_id", "unknown")
    event = input_data.get("hook_event_name", "")

    if event == "PreToolUse":
        tool_input = input_data.get("tool_input", {})
        open_entertainment(session_id, tool_input)
    elif event in ("Stop", "SessionEnd"):
        close_entertainment(session_id)


def main():
    if len(sys.argv) > 1:
        cmd = sys.argv[1]
        if cmd == "login":
            cmd_login()
        elif cmd == "setup":
            name = sys.argv[2] if len(sys.argv) > 2 else "shorts"
            cmd_setup(name)
        elif cmd == "mode":
            name = sys.argv[2] if len(sys.argv) > 2 else "degrade"
            cmd_mode(name)
        else:
            print(__doc__)
    else:
        cmd_hook()


if __name__ == "__main__":
    main()
