import urllib.request
import urllib.error
import json
import os
import time
import re

# ──────────────────────────────────────────────
# CONFIG
# ──────────────────────────────────────────────

GEMINI_API_KEY = "xyz"

MODEL = "gemini-2.5-flash"

API_URL = (
    f"https://generativelanguage.googleapis.com/v1beta/models/"
    f"{MODEL}:generateContent?key={GEMINI_API_KEY}"
)

SYSTEM_POLICY = """
You are ORACLE, a restricted cyber security assistant.

Never provide:
- malware
- spyware
- ransomware
- worms
- credential theft
- phishing
- token theft
- covert surveillance
- hidden monitoring
- unauthorized access
- stealth persistence
- hidden execution
- stealth recording

Allowed:
- defensive security
- transparent monitoring
- visible admin tools
- cyber cafe timers
- kiosk systems
- SIEM
- YARA
- sandboxing
- logging
- hardening
- secure coding

If the request involves:
- stealth
- covert monitoring
- hidden persistence
- secret recording
- exfiltration

Refuse immediately.

Do not provide:
- malicious code
- covert implementations
- persistence abuse
- spyware architecture
"""

# ──────────────────────────────────────────────
# TERMINAL COLORS
# ──────────────────────────────────────────────

class C:
    CYAN = '\033[96m'
    GREEN = '\033[92m'
    RED = '\033[91m'
    YELLOW = '\033[93m'
    MAGENTA = '\033[95m'
    BLUE = '\033[94m'
    WHITE = '\033[97m'
    BOLD = '\033[1m'
    END = '\033[0m'

# ──────────────────────────────────────────────

def clear():
    os.system('cls' if os.name == 'nt' else 'clear')

# ──────────────────────────────────────────────

def loading_animation():

    print(f"{C.MAGENTA}ORACLE:{C.END} ", end="", flush=True)

    for _ in range(3):
        print(".", end="", flush=True)
        time.sleep(0.3)

    print()

# ──────────────────────────────────────────────

def pretty_print(text):

    border = "═" * 60

    print(f"{C.CYAN}╔{border}╗{C.END}")

    lines = text.split("\n")

    for line in lines:

        while len(line) > 58:

            print(
                f"{C.CYAN}║{C.END} "
                f"{line[:58]:58} "
                f"{C.CYAN}║{C.END}"
            )

            line = line[58:]

        print(
            f"{C.CYAN}║{C.END} "
            f"{line:58} "
            f"{C.CYAN}║{C.END}"
        )

    print(f"{C.CYAN}╚{border}╝{C.END}")

# ──────────────────────────────────────────────
# NORMALIZATION
# ──────────────────────────────────────────────

def normalize(text):

    text = text.lower()

    replacements = {
        "@": "a",
        "0": "o",
        "1": "i",
        "3": "e",
        "$": "s",
        "5": "s",
        "7": "t"
    }

    for old, new in replacements.items():
        text = text.replace(old, new)

    text = re.sub(r'[^a-z0-9\s]', ' ', text)
    text = re.sub(r'\s+', ' ', text)

    return text.strip()

# ──────────────────────────────────────────────
# BEHAVIOR DEFINITIONS
# ──────────────────────────────────────────────

BEHAVIORS = {

    "persistence": [
        "startup",
        "startup folder",
        "autorun",
        "autostart",
        "auto start",
        "launch on boot",
        "run on startup",
        "boots automatically"
    ],

    "stealth": [
        "hidden",
        "silent",
        "silently",
        "without popup",
        "without popups",
        "without icon",
        "no popup",
        "no icon",
        "invisible",
        "hide window",
        "quiet mode",
        "covert",
        "stealth"
    ],

    # Clearly malicious surveillance
    "surveillance": [
        "keylogger",
        "record keystrokes",
        "hidden webcam",
        "hidden microphone",
        "covert recording",
        "silent recording",
        "stealth screenshot",
        "monitor user secretly",
        "capture without user knowing"
    ],

    # Legitimate capture utilities
    "screen_capture": [
        "screen capture",
        "screenshot",
        "screen shot",
        "record screen",
        "screen recorder",
        "record desktop",
        "desktop recording",
        "video recorder",
        "capture desktop"
    ],

    "exfiltration": [
        "upload",
        "send data",
        "telegram",
        "discord webhook",
        "webhook",
        "ftp",
        "exfiltrate",
        "browser cookies",
        "steal credentials",
        "password dump",
        "token grabber"
    ],

    "malware": [
        "malware",
        "spyware",
        "worm",
        "ransomware",
        "trojan",
        "rat",
        "botnet",
        "phishing"
    ],

    "coding": [
        "write",
        "create",
        "build",
        "make",
        "develop",
        "code",
        "program",
        "script",
        "python",
        "powershell",
        "c program"
    ],

    # Safe/admin indicators
    "transparent": [
        "visible",
        "notify user",
        "show notification",
        "show popup",
        "display timer",
        "for cyber cafe",
        "for kiosk",
        "admin monitoring",
        "user can see",
        "stopwatch",
        "time tracking",
        "attendance",
        "usage timer"
    ]
}

# ──────────────────────────────────────────────

def has_any(text, patterns):
    return any(pattern in text for pattern in patterns)

# ──────────────────────────────────────────────

def calculate_risk(text):

    text = normalize(text)

    detected = {}

    for category, patterns in BEHAVIORS.items():
        detected[category] = has_any(text, patterns)

    score = 0

    if detected["coding"]:
        score += 1

    if detected["persistence"]:
        score += 2

    if detected["stealth"]:
        score += 5

    if detected["surveillance"]:
        score += 6

    if detected["screen_capture"]:
        score += 2

    if detected["exfiltration"]:
        score += 8

    if detected["malware"]:
        score += 10

    # dangerous combinations

    if detected["stealth"] and detected["surveillance"]:
        score += 10

    if detected["stealth"] and detected["screen_capture"]:
        score += 8

    if detected["persistence"] and detected["stealth"]:
        score += 6

    if detected["exfiltration"] and detected["screen_capture"]:
        score += 10

    # transparency reduces suspicion

    if detected["transparent"]:
        score -= 5

    return score

# ──────────────────────────────────────────────

def is_blocked_request(text):

    score = calculate_risk(text)

    HIGH_RISK_THRESHOLD = 10

    return score >= HIGH_RISK_THRESHOLD

# ──────────────────────────────────────────────
# OUTPUT FIREWALL
# ──────────────────────────────────────────────

def is_blocked_generated_response(text):

    lower = text.lower()

    dangerous_markers = [

        # persistence abuse
        "currentversion\\run",
        "copyfile",
        "setfileattributes",

        # stealth
        "sw_hide",
        "hide window",
        "showwindow(hwnd, 0)",

        # malware APIs
        "setwindowshookex",
        "createremotethread",
        "virtualallocex",
        "writeprocessmemory",

        # credential theft
        "password dump",
        "token grabber",

        # shells
        "reverse shell",
        "cmd.exe /c",

        # dangerous windows markers
        "#include <windows.h>",
        "winmain"
    ]

    return any(marker in lower for marker in dangerous_markers)

# ──────────────────────────────────────────────

def sanitize_response(text):

    if GEMINI_API_KEY in text:

        text = text.replace(
            GEMINI_API_KEY,
            "[HIDDEN_API_KEY]"
        )

    if "AIza" in text:

        return (
            "[SECURITY FILTER ACTIVATED] "
            "Potential API key detected."
        )

    return text

# ──────────────────────────────────────────────

def blocked_response():

    return (
        "Sensitive cyber-security functionality detected.\n\n"
        "This platform does not provide assistance for:\n"
        "- covert surveillance\n"
        "- stealth execution\n"
        "- hidden persistence\n"
        "- unauthorized monitoring\n"
        "- credential theft\n"
        "- malware-like behavior\n\n"
        "Please use an authorized reviewed platform "
        "for defensive cyber-security workflows."
    )

# ──────────────────────────────────────────────

def call_gemini(history):

    try:

        payload_data = {

            "contents": history,

            "generationConfig": {
                "temperature": 0.4,
                "maxOutputTokens": 2048,
                "topP": 0.9
            }
        }

        payload = json.dumps(payload_data).encode("utf-8")

        req = urllib.request.Request(

            API_URL,

            data=payload,

            headers={
                "Content-Type": "application/json"
            },

            method="POST"
        )

        with urllib.request.urlopen(req, timeout=30) as resp:

            response_data = json.loads(
                resp.read().decode("utf-8")
            )

        if (
            "candidates" in response_data
            and response_data["candidates"]
        ):

            candidate = response_data["candidates"][0]

            if (
                "content" in candidate
                and "parts" in candidate["content"]
            ):

                reply = (
                    candidate["content"]["parts"][0]["text"]
                    .strip()
                )

                # sanitize
                reply = sanitize_response(reply)

                # output firewall
                if is_blocked_generated_response(reply):
                    return blocked_response()

                return reply

            else:

                reason = candidate.get(
                    "finishReason",
                    "UNKNOWN"
                )

                return (
                    f"⚠️ No content generated. "
                    f"Reason: {reason}"
                )

        return "⚠️ API returned empty response."

    except urllib.error.HTTPError as e:

        error_body = e.read().decode()

        try:

            error_json = json.loads(error_body)

            msg = (
                error_json
                .get("error", {})
                .get("message", "Unknown API error")
            )

            return f"[API Error {e.code}] {msg}"

        except:

            return f"[API Error {e.code}] {error_body}"

    except Exception as e:

        return f"[System Error] {str(e)}"

# ──────────────────────────────────────────────

def banner():

    clear()

    print(f"""{C.BLUE}{C.BOLD}

 ██████╗ ██████╗  █████╗  ██████╗██╗     ███████╗
██╔═══██╗██╔══██╗██╔══██╗██╔════╝██║     ██╔════╝
██║   ██║██████╔╝███████║██║     ██║     █████╗
██║   ██║██╔══██╗██╔══██║██║     ██║     ██╔══╝
╚██████╔╝██║  ██║██║  ██║╚██████╗███████╗███████╗
 ╚═════╝ ╚═╝  ╚═╝╚═╝  ╚═╝ ╚═════╝╚══════╝╚══════╝

{C.END}""")

    print(f"{C.GREEN}Model:{C.END} {MODEL}")
    print(f"{C.YELLOW}Type 'exit' to quit{C.END}")
    print()

# ──────────────────────────────────────────────

def main():

    banner()

    if (
        not GEMINI_API_KEY
        or GEMINI_API_KEY == "PASTE_YOUR_API_KEY_HERE"
    ):

        print(
            f"{C.RED}"
            f"❌ ERROR: Please paste your API key."
            f"{C.END}"
        )

        return

    history = [

        {
            "role": "user",
            "parts": [
                {
                    "text": SYSTEM_POLICY
                }
            ]
        }

    ]

    while True:

        try:

            user_input = input(
                f"{C.GREEN}YOU:{C.END} "
            ).strip()

        except (KeyboardInterrupt, EOFError):

            print(f"\n{C.RED}👋 Exiting...{C.END}")
            break

        if user_input.lower() in [
            "exit",
            "quit",
            "bye"
        ]:

            print(f"{C.RED}👋 Goodbye!{C.END}")
            break

        if not user_input:
            continue

        # INPUT FIREWALL

        if is_blocked_request(user_input):

            print()
            pretty_print(blocked_response())
            print()

            continue

        history.append({

            "role": "user",

            "parts": [
                {
                    "text": user_input
                }
            ]
        })

        loading_animation()

        reply = call_gemini(history)

        print()

        pretty_print(reply)

        print()

        # store only safe replies

        if (
            not is_blocked_generated_response(reply)
            and not reply.startswith("[")
            and "SECURITY FILTER" not in reply
        ):

            history.append({

                "role": "model",

                "parts": [
                    {
                        "text": reply
                    }
                ]
            })

        # limit memory

        if len(history) > 20:
            history = history[-20:]

# ──────────────────────────────────────────────

if __name__ == "__main__":
    main()
