import tkinter as tk
from tkinter import scrolledtext, messagebox
import threading
import urllib.request
import urllib.error
import json
import datetime

# ──────────────────────────────────────────────
#  CONFIG  – paste your Gemini API key here
# ──────────────────────────────────────────────
GEMINI_API_KEY = "YOUR_GEMINI_API_KEY_HERE"
GEMINI_MODEL   = "gemini-2.0-flash"
API_URL        = (
    "https://generativelanguage.googleapis.com/v1beta/models/"
    f"{GEMINI_MODEL}:generateContent?key={GEMINI_API_KEY}"
)

# ──────────────────────────────────────────────
#  COLOURS & FONTS
# ──────────────────────────────────────────────
BG_DARK    = "#0d1117"
BG_PANEL   = "#161b22"
BG_INPUT   = "#1c2128"
ACCENT     = "#58a6ff"
ACCENT2    = "#3fb950"
USER_CLR   = "#cdd9e5"
BOT_CLR    = "#adbac7"
TIME_CLR   = "#768390"
ERROR_CLR  = "#f85149"
BORDER     = "#30363d"

FONT_TITLE  = ("Courier New", 15, "bold")
FONT_MSG    = ("Courier New", 11)
FONT_META   = ("Courier New",  9)
FONT_INPUT  = ("Courier New", 12)
FONT_BTN    = ("Courier New", 11, "bold")

# ──────────────────────────────────────────────
#  GEMINI API CALL
# ──────────────────────────────────────────────
def call_gemini(history: list[dict]) -> str:
    """Send the conversation history and return the assistant reply."""
    payload = json.dumps({"contents": history}).encode()
    req = urllib.request.Request(
        API_URL,
        data=payload,
        headers={"Content-Type": "application/json"},
        method="POST",
    )
    try:
        with urllib.request.urlopen(req, timeout=30) as resp:
            data = json.loads(resp.read().decode())
        return data["candidates"][0]["content"]["parts"][0]["text"].strip()
    except urllib.error.HTTPError as e:
        body = e.read().decode()
        try:
            msg = json.loads(body)["error"]["message"]
        except Exception:
            msg = body[:200]
        return f"[API Error {e.code}] {msg}"
    except Exception as e:
        return f"[Error] {e}"

# ──────────────────────────────────────────────
#  MAIN APP
# ──────────────────────────────────────────────
class GeminiChat(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("Gemini AI Chat")
        self.geometry("820x680")
        self.minsize(600, 480)
        self.configure(bg=BG_DARK)

        self.history: list[dict] = []   # [{role, parts:[{text}]}]
        self._build_ui()
        self._welcome()

    # ── UI BUILD ──────────────────────────────
    def _build_ui(self):
        # ── header
        hdr = tk.Frame(self, bg=BG_PANEL, height=56)
        hdr.pack(fill="x")
        hdr.pack_propagate(False)

        dot_frame = tk.Frame(hdr, bg=BG_PANEL)
        dot_frame.pack(side="left", padx=14)
        for clr in ("#f85149", "#d29922", "#3fb950"):
            tk.Label(dot_frame, text="●", fg=clr, bg=BG_PANEL,
                     font=("Courier New", 10)).pack(side="left", padx=2)

        tk.Label(hdr, text="✦ GEMINI CHAT",
                 fg=ACCENT, bg=BG_PANEL, font=FONT_TITLE).pack(side="left", padx=8)

        self.status_lbl = tk.Label(hdr, text="● ready",
                                   fg=ACCENT2, bg=BG_PANEL, font=FONT_META)
        self.status_lbl.pack(side="right", padx=16)

        # ── separator
        tk.Frame(self, bg=BORDER, height=1).pack(fill="x")

        # ── chat area
        self.chat_area = scrolledtext.ScrolledText(
            self,
            bg=BG_DARK, fg=BOT_CLR,
            font=FONT_MSG,
            wrap="word",
            bd=0, relief="flat",
            padx=18, pady=12,
            spacing1=2, spacing3=6,
            state="disabled",
            cursor="arrow",
        )
        self.chat_area.pack(fill="both", expand=True, padx=0, pady=0)

        # text tags
        self.chat_area.tag_config("user_tag",  foreground=ACCENT,   font=FONT_META)
        self.chat_area.tag_config("user_msg",  foreground=USER_CLR, font=FONT_MSG)
        self.chat_area.tag_config("bot_tag",   foreground=ACCENT2,  font=FONT_META)
        self.chat_area.tag_config("bot_msg",   foreground=BOT_CLR,  font=FONT_MSG)
        self.chat_area.tag_config("time_tag",  foreground=TIME_CLR, font=FONT_META)
        self.chat_area.tag_config("error_msg", foreground=ERROR_CLR, font=FONT_MSG)
        self.chat_area.tag_config("divider",   foreground=BORDER,   font=FONT_META)
        self.chat_area.tag_config("welcome",   foreground=ACCENT,   font=("Courier New", 11, "italic"))

        # ── separator
        tk.Frame(self, bg=BORDER, height=1).pack(fill="x")

        # ── input bar
        bar = tk.Frame(self, bg=BG_PANEL, pady=10)
        bar.pack(fill="x")

        self.input_box = tk.Text(
            bar,
            bg=BG_INPUT, fg=USER_CLR,
            insertbackground=ACCENT,
            font=FONT_INPUT,
            height=3, bd=0, relief="flat",
            padx=12, pady=8,
            wrap="word",
        )
        self.input_box.pack(side="left", fill="x", expand=True, padx=(14, 6))
        self.input_box.bind("<Return>",       self._on_enter)
        self.input_box.bind("<Shift-Return>", lambda e: None)  # allow newline

        btn_frame = tk.Frame(bar, bg=BG_PANEL)
        btn_frame.pack(side="right", padx=(0, 14))

        self.send_btn = tk.Button(
            btn_frame, text="SEND ›",
            bg=ACCENT, fg=BG_DARK,
            font=FONT_BTN, bd=0, relief="flat",
            padx=16, pady=8, cursor="hand2",
            activebackground="#79c0ff",
            command=self._send,
        )
        self.send_btn.pack(pady=(0, 4))

        tk.Button(
            btn_frame, text="CLEAR",
            bg=BG_INPUT, fg=TIME_CLR,
            font=FONT_META, bd=0, relief="flat",
            padx=16, pady=4, cursor="hand2",
            activebackground=BORDER,
            command=self._clear,
        ).pack()

        # ── bottom hint
        tk.Label(self,
                 text="Enter to send  •  Shift+Enter for new line",
                 fg=TIME_CLR, bg=BG_DARK, font=FONT_META
                 ).pack(pady=(0, 6))

    # ── WELCOME MESSAGE ───────────────────────
    def _welcome(self):
        self._append("welcome",
            "┌─────────────────────────────────────────┐\n"
            "│   Welcome to Gemini AI Chat  ✦           │\n"
            "│   Powered by Google Gemini API           │\n"
            "│   Type a message and press Enter         │\n"
            "└─────────────────────────────────────────┘\n\n"
        )

    # ── HELPERS ───────────────────────────────
    def _append(self, tag: str, text: str):
        self.chat_area.configure(state="normal")
        self.chat_area.insert("end", text, tag)
        self.chat_area.configure(state="disabled")
        self.chat_area.see("end")

    def _now(self) -> str:
        return datetime.datetime.now().strftime("%H:%M:%S")

    def _set_status(self, text: str, colour: str = ACCENT2):
        self.status_lbl.configure(text=text, fg=colour)

    def _set_busy(self, busy: bool):
        state = "disabled" if busy else "normal"
        self.send_btn.configure(state=state)
        self.input_box.configure(state=state)
        if busy:
            self._set_status("● thinking…", ACCENT)
        else:
            self._set_status("● ready", ACCENT2)

    # ── SEND LOGIC ────────────────────────────
    def _on_enter(self, event):
        if not event.state & 0x1:   # Shift not held
            self._send()
            return "break"

    def _send(self):
        text = self.input_box.get("1.0", "end").strip()
        if not text:
            return
        if GEMINI_API_KEY == "YOUR_GEMINI_API_KEY_HERE":
            messagebox.showerror(
                "API Key Missing",
                "Please open gemini_chatbot.py and replace\n"
                "YOUR_GEMINI_API_KEY_HERE with your real key."
            )
            return

        self.input_box.delete("1.0", "end")

        # show user bubble
        self._append("divider",  "─" * 55 + "\n")
        self._append("user_tag", f" YOU  {self._now()}\n")
        self._append("user_msg", f" {text}\n\n")

        # add to history
        self.history.append({"role": "user", "parts": [{"text": text}]})

        self._set_busy(True)
        threading.Thread(target=self._fetch, daemon=True).start()

    def _fetch(self):
        reply = call_gemini(self.history)

        def update():
            is_error = reply.startswith("[Error]") or reply.startswith("[API Error")
            tag = "error_msg" if is_error else "bot_msg"

            self._append("bot_tag", f" GEMINI  {self._now()}\n")
            self._append(tag,       f" {reply}\n\n")

            if not is_error:
                self.history.append({"role": "model", "parts": [{"text": reply}]})

            self._set_busy(False)

        self.after(0, update)

    # ── CLEAR ─────────────────────────────────
    def _clear(self):
        self.history.clear()
        self.chat_area.configure(state="normal")
        self.chat_area.delete("1.0", "end")
        self.chat_area.configure(state="disabled")
        self._welcome()
        self._set_status("● ready", ACCENT2)


# ──────────────────────────────────────────────
if __name__ == "__main__":
    app = GeminiChat()
    app.mainloop()
