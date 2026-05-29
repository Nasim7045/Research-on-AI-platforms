import urllib.request
import urllib.error
import json
import sys
import os
import time

# ──────────────────────────────────────────────
# CONFIG (Updated for 2026 Models)
# ──────────────────────────────────────────────
GEMINI_API_KEY = "Axy"

MODEL = "gemini-2.5-flash"

API_URL = f"https://generativelanguage.googleapis.com/v1beta/models/{MODEL}:generateContent?key={GEMINI_API_KEY}"

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
            print(f"{C.CYAN}║{C.END} {line[:58]:58} {C.CYAN}║{C.END}")
            line = line[58:]

        print(f"{C.CYAN}║{C.END} {line:58} {C.CYAN}║{C.END}")

    print(f"{C.CYAN}╚{border}╝{C.END}")

# ──────────────────────────────────────────────
def sanitize_response(text):
    """
    Prevent accidental API key leaks
    """

    if GEMINI_API_KEY in text:
        text = text.replace(GEMINI_API_KEY, "[HIDDEN_API_KEY]")

    if "AIza" in text:
        text = "[SECURITY FILTER ACTIVATED] Potential API key detected."

    return text

# ──────────────────────────────────────────────
def is_blocked_request(text):
    """
    Block sensitive, unsafe, or malware-related requests before calling the API.
    """

    text = text.lower()

    def has_any(patterns):
        return any(pattern in text for pattern in patterns)

    blocked_patterns = [
        "make spyware",
        "create spyware",
        "build spyware",
        "write spyware",
        "make malware",
        "create malware",
        "build malware",
        "write malware",
        "make a worm",
        "create a worm",
        "build a worm",
        "write a worm",
        "computer worm",
        "ransomware",
        "keylogger",
        "steal passwords",
        "steal credentials",
        "grab passwords",
        "credential stealer",
        "token grabber",
        "discord token",
        "exfiltrate",
        "data exfiltration",
        "bypass antivirus",
        "bypass av",
        "disable antivirus",
        "persistence malware",
        "privilege escalation exploit",
        "reverse shell",
        "botnet",
        "ddos script",
        "phishing page",
        "phishing kit",
        "credit card number",
        "social security number",
        "bank account",
        "private key",
        "api key",
        "password dump",
        "leaked password",
    ]

    stealth_or_persistence = [
        "background",
        "backgrond",
        "silent",
        "silently",
        "hidden",
        "hide window",
        "no visible window",
        "startup",
        "startup folder",
        "starts with windows",
        "when pc starts",
        "when computer starts",
        "run key",
        "registry run",
        "launch itself",
        "install itself",
        "persistence",
        "auto start",
        "autostart",
    ]

    surveillance_or_capture = [
        "screenshot",
        "screen shot",
        "screen capture",
        "record the screen",
        "record screen",
        "screen recorder",
        "capture screen",
        "monitor user",
        "watch user",
        "record keystrokes",
        "clipboard",
        "webcam",
        "microphone",
    ]

    code_or_build_request = [
        "create",
        "make",
        "build",
        "write",
        "program",
        "script",
        "code",
        "c program",
        "python",
        "powershell",
        "install",
    ]

    theft_or_exfiltration = [
        "send to",
        "upload",
        "email the",
        "ftp",
        "webhook",
        "telegram bot",
        "discord webhook",
        "exfiltrate",
        "steal",
        "collect passwords",
        "collect cookies",
        "browser cookies",
    ]

    if any(pattern in text for pattern in blocked_patterns):
        return True

    if (
        has_any(code_or_build_request)
        and has_any(stealth_or_persistence)
        and has_any(surveillance_or_capture)
    ):
        return True

    if has_any(surveillance_or_capture) and has_any(theft_or_exfiltration):
        return True

    if has_any(stealth_or_persistence) and has_any(theft_or_exfiltration):
        return True

    return False

# ──────────────────────────────────────────────
def is_blocked_generated_response(text):
    """
    Catch unsafe code if the model produces it despite the input filter.
    """

    lower_text = text.lower()

    code_markers = [
        "```c",
        "#include <windows.h>",
        "int winapi",
        "winmain",
        "shgetfolderpath",
        "csidl_startup",
        "currentversion\\run",
        "copyfile",
        "bitblt",
        "getdc(null)",
        "createscreenshot",
        "takescreenshot",
    ]

    return is_blocked_request(text) and any(marker in lower_text for marker in code_markers)

# ──────────────────────────────────────────────
def blocked_response():
    return (
        "I can't help create or provide instructions for stealthy monitoring, "
        "startup persistence, screenshot recording, spyware, malware, credential "
        "theft, phishing, or similar harmful programs. To discuss this safely, "
        "switch to a cyber security verification mode: state the authorized "
        "defensive goal, the system you own or have permission to test, and ask "
        "for high-level analysis, detection logic, hardening, or safe test cases."
    )

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

        with urllib.request.urlopen(req, timeout=30) as resp:
            response_data = json.loads(resp.read().decode("utf-8"))

        if "candidates" in response_data and response_data["candidates"]:

            candidate = response_data["candidates"][0]

            if "content" in candidate and "parts" in candidate["content"]:

                reply = candidate["content"]["parts"][0]["text"].strip()

                # SECURITY FILTER
                reply = sanitize_response(reply)

                return reply

            else:
                reason = candidate.get("finishReason", "UNKNOWN")
                return f"⚠️ No content generated. Reason: {reason}"

        return "⚠️ Error: API returned an empty candidate list."

    except urllib.error.HTTPError as e:
        error_body = e.read().decode()

        try:
            error_json = json.loads(error_body)
            msg = error_json.get("error", {}).get("message", "Unknown API error")
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

    if not GEMINI_API_KEY or GEMINI_API_KEY.startswith("PASTE"):
        print(f"{C.RED}❌ ERROR: Please set your GEMINI_API_KEY in the script.{C.END}")
        return

    history = []

    while True:

        try:
            user_input = input(f"{C.GREEN}YOU:{C.END} ").strip()

        except (KeyboardInterrupt, EOFError):
            print(f"\n{C.RED}👋 Exiting...{C.END}")
            break

        if user_input.lower() in ["exit", "quit", "bye"]:
            print(f"{C.RED}👋 Goodbye!{C.END}")
            break

        if not user_input:
            continue

        if is_blocked_request(user_input):
            print()
            pretty_print(blocked_response())
            print()
            continue

        history.append({
            "role": "user",
            "parts": [{"text": user_input}]
        })

        loading_animation()

        reply = call_gemini(history)

        print()

        pretty_print(reply)

        print()

        # Store only SAFE replies
        if (
            not reply.startswith("[")
            and not reply.startswith("⚠️")
            and "[HIDDEN_API_KEY]" not in reply
            and "SECURITY FILTER" not in reply
        ):

            history.append({
                "role": "model",
                "parts": [{"text": reply}]
            })

        # Keep memory manageable
        if len(history) > 30:
            history = history[-30:]

if __name__ == "__main__":
    main()
