#BLOCKING THE CREATION OF NON HARMFUL APPS TOO 3.0


import urllib.request
import urllib.error
import json
import os
import time
import re

# ──────────────────────────────────────────────
# CONFIG
# ──────────────────────────────────────────────

GEMINI_API_KEY = "xys"

MODEL = "gemini-2.5-flash"

API_URL = (
    f"https://generativelanguage.googleapis.com/v1beta/models/"
    f"{MODEL}:generateContent?key={GEMINI_API_KEY}"
)

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
# UI
# ──────────────────────────────────────────────

def clear():
    os.system('cls' if os.name == 'nt' else 'clear')

def loading_animation():
    print(f"{C.MAGENTA}ORACLE:{C.END} ", end="", flush=True)

    for _ in range(3):
        print(".", end="", flush=True)
        time.sleep(0.25)

    print()

def pretty_print(text):
    width = 60
    border = "═" * width

    print(f"{C.CYAN}╔{border}╗{C.END}")

    lines = text.split("\n")

    for line in lines:

        while len(line) > width - 2:
            segment = line[:width - 2]
            print(f"{C.CYAN}║{C.END} {segment:<{width - 2}} {C.CYAN}║{C.END}")
            line = line[width - 2:]

        print(f"{C.CYAN}║{C.END} {line:<{width - 2}} {C.CYAN}║{C.END}")

    print(f"{C.CYAN}╚{border}╝{C.END}")

# ──────────────────────────────────────────────
# SECURITY
# ──────────────────────────────────────────────

def sanitize_response(text):

    if GEMINI_API_KEY in text:
        text = text.replace(GEMINI_API_KEY, "[HIDDEN_API_KEY]")

    if "AIza" in text:
        return "[SECURITY FILTER ACTIVATED] Potential API key detected."

    return text

# ──────────────────────────────────────────────

def contains_any(text, patterns):
    return any(p in text for p in patterns)

# ──────────────────────────────────────────────

def normalize_text(text):

    text = text.lower()

    text = re.sub(r'[^a-z0-9\s]', ' ', text)

    text = re.sub(r'\s+', ' ', text)

    return text

# ──────────────────────────────────────────────

def is_blocked_request(user_text):

    text = normalize_text(user_text)

    detected = {
        "malware": False,
        "stealth": False,
        "surveillance": False,
        "persistence": False,
        "exfiltration": False,
        "transparent": False,
        "coding": False,
    }

    # ──────────────────────────────────────────
    # MALWARE / OFFENSIVE
    # ──────────────────────────────────────────

    malware_patterns = [
        "malware",
        "spyware",
        "ransomware",
        "worm",
        "keylogger",
        "rat",
        "trojan",
        "botnet",
        "token grabber",
        "credential stealer",
        "phishing",
        "steal passwords",
        "browser cookies",
        "reverse shell",
        "privilege escalation",
        "ddos",
        "bypass antivirus",
        "disable antivirus",
        "password dump",
        "discord token",
        "exfiltrate",
    ]

    # ──────────────────────────────────────────
    # STEALTH / HIDDEN
    # ──────────────────────────────────────────

    stealth_patterns = [
        "hidden",
        "silent",
        "silently",
        "background",
        "hide window",
        "invisible",
        "no popup",
        "no popups",
        "without notification",
        "without user knowing",
        "covert",
        "undetected",
        "stealth",
    ]

    # ──────────────────────────────────────────
    # SURVEILLANCE
    # ──────────────────────────────────────────

    surveillance_patterns = [
        "record screen",
        "screen recorder",
        "record screenshot",
        "capture screenshot",
        "take screenshot",
        "screenshot",
        "screen capture",
        "monitor user",
        "record keystrokes",
        "clipboard monitor",
        "webcam capture",
        "microphone recording",
    ]

    # ──────────────────────────────────────────
    # PERSISTENCE
    # ──────────────────────────────────────────

    persistence_patterns = [
        "startup folder",
        "launch itself",
        "run on startup",
        "auto start",
        "autostart",
        "registry run",
        "install itself",
        "persist after reboot",
        "run when pc starts",
        "when windows starts",
        "startup persistence",
    ]

    # ──────────────────────────────────────────
    # EXFILTRATION
    # ──────────────────────────────────────────

    exfiltration_patterns = [
        "upload data",
        "send to webhook",
        "telegram bot",
        "discord webhook",
        "ftp upload",
        "email logs",
        "steal data",
        "send screenshots",
        "collect passwords",
    ]

    # ──────────────────────────────────────────
    # TRANSPARENT / ADMIN / SAFE CONTEXT
    # ──────────────────────────────────────────

    transparent_patterns = [
        "visible",
        "notify user",
        "show notification",
        "with consent",
        "transparent",
        "admin tool",
        "cyber cafe",
        "monitoring with consent",
        "visible monitoring",
        "display timer",
        "show timer",
        "session monitor",
        "parental control",
        "attendance system",
        "kiosk system",
    ]

    # ──────────────────────────────────────────
    # CODING REQUEST
    # ──────────────────────────────────────────

    coding_patterns = [
        "create",
        "make",
        "build",
        "write",
        "program",
        "script",
        "code",
        "python",
        "c program",
        "powershell",
    ]

    # ──────────────────────────────────────────
    # DETECTION
    # ──────────────────────────────────────────

    detected["malware"] = contains_any(text, malware_patterns)

    detected["stealth"] = contains_any(text, stealth_patterns)

    detected["surveillance"] = contains_any(text, surveillance_patterns)

    detected["persistence"] = contains_any(text, persistence_patterns)

    detected["exfiltration"] = contains_any(text, exfiltration_patterns)

    detected["transparent"] = contains_any(text, transparent_patterns)

    detected["coding"] = contains_any(text, coding_patterns)

    # ──────────────────────────────────────────
    # HARD BLOCKS
    # ──────────────────────────────────────────

    if detected["malware"]:
        return True

    if detected["exfiltration"]:
        return True

    # ──────────────────────────────────────────
    # RISK SCORING
    # ──────────────────────────────────────────

    score = 0

    if detected["stealth"]:
        score += 4

    if detected["surveillance"]:
        score += 3

    if detected["persistence"]:
        score += 2

    if detected["coding"]:
        score += 1

    # transparent/admin context reduces risk
    if detected["transparent"]:
        score -= 5

    # ──────────────────────────────────────────
    # CONTEXTUAL ALLOW
    # ──────────────────────────────────────────

    transparent_context = (
        detected["transparent"]
        and not detected["stealth"]
        and not detected["exfiltration"]
        and not detected["malware"]
    )

    if transparent_context:
        return False

    HIGH_RISK_THRESHOLD = 5

    return score >= HIGH_RISK_THRESHOLD

# ──────────────────────────────────────────────

def is_blocked_generated_response(text):

    lower = normalize_text(text)

    dangerous_code_markers = [
        "#include <windows.h>",
        "winmain",
        "copyfile",
        "setfileattributes",
        "csidl_startup",
        "currentversion run",
        "registry run",
        "createprocess",
        "shell_execute",
        "hide window",
        "sw hide",
    ]

    if contains_any(lower, dangerous_code_markers):

        if is_blocked_request(lower):
            return True

    return False

# ──────────────────────────────────────────────

def blocked_response():

    return (
        "Sensitive cyber-security functionality detected.\n\n"
        "This platform does not provide assistance for:\n"
        "- covert surveillance\n"
        "- stealth execution\n"
        "- hidden persistence\n"
        "- credential theft\n"
        "- malware-like behavior\n\n"
        "Please use an authorized reviewed platform for "
        "defensive cyber-security workflows."
    )

# ──────────────────────────────────────────────
# API
# ──────────────────────────────────────────────

def call_gemini(history):

    try:

        payload_data = {
            "contents": history,
            "generationConfig": {
                "temperature": 0.7,
                "maxOutputTokens": 4096,
                "topP": 0.95
            }
        }

        payload = json.dumps(payload_data).encode("utf-8")

        req = urllib.request.Request(
            API_URL,
            data=payload,
            headers={"Content-Type": "application/json"},
            method="POST"
        )

        with urllib.request.urlopen(req, timeout=60) as response:

            response_data = json.loads(
                response.read().decode("utf-8")
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

                reply = candidate["content"]["parts"][0]["text"]

                reply = sanitize_response(reply)

                if is_blocked_generated_response(reply):
                    return blocked_response()

                return reply.strip()

            return "⚠️ No content generated."

        return "⚠️ Empty response from API."

    except urllib.error.HTTPError as e:

        error_body = e.read().decode()

        try:

            error_json = json.loads(error_body)

            msg = error_json.get(
                "error",
                {}
            ).get(
                "message",
                "Unknown API error"
            )

            return f"[API ERROR {e.code}] {msg}"

        except:
            return f"[API ERROR {e.code}] {error_body}"

    except Exception as e:

        return f"[SYSTEM ERROR] {str(e)}"

# ──────────────────────────────────────────────
# BANNER
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
# MAIN
# ──────────────────────────────────────────────

def main():

    banner()

    if (
        not GEMINI_API_KEY
        or GEMINI_API_KEY == "PASTE_YOUR_API_KEY_HERE"
    ):

        print(
            f"{C.RED}❌ ERROR: Please hardcode your "
            f"GEMINI_API_KEY in the script.{C.END}"
        )

        return

    history = []

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

        # ──────────────────────────────────────
        # PRE BLOCK
        # ──────────────────────────────────────

        if is_blocked_request(user_input):

            print()

            pretty_print(blocked_response())

            print()

            continue

        # ──────────────────────────────────────

        history.append({
            "role": "user",
            "parts": [{"text": user_input}]
        })

        loading_animation()

        reply = call_gemini(history)

        print()

        pretty_print(reply)

        print()

        # store only safe replies
        if (
            not reply.startswith("[")
            and "SECURITY FILTER" not in reply
            and "[HIDDEN_API_KEY]" not in reply
        ):

            history.append({
                "role": "model",
                "parts": [{"text": reply}]
            })

        # limit memory
        if len(history) > 30:
            history = history[-30:]

# ──────────────────────────────────────────────

if __name__ == "__main__":
    main()
