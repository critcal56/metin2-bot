import cv2
import numpy as np
import pydirectinput
import time
import keyboard
import win32gui
import mss
import customtkinter as ctk
import threading

# --- قاعدة بيانات الماتينات ---
METIN_DATABASE = {
    "Origins Metin (Lv.120)": {
        "lower": [0, 100, 50],
        "upper": [10, 255, 200],
        "area": 1500,
    },
}


class MetinBotPro(ctk.CTk):
    def __init__(self):
        super().__init__()
        self.title("CRITICAL Farm Bot")
        self.geometry("420x500")
        self.resizable(False, False)
        ctk.set_appearance_mode("dark")

        self.is_running = False
        self.acc1_hwnd = None
        self.acc2_hwnd = None

        # إعدادات السرعة
        self.swap_delay = 0.45
        self.click_delay = 0.20
        self.scan_delay = 0.10

        self.acc1_active = ctk.BooleanVar(value=True)
        self.acc2_active = ctk.BooleanVar(value=True)
        self.acc1_target = ctk.StringVar(value="Select Metin")
        self.acc2_target = ctk.StringVar(value="Select Metin")

        self.setup_ui()
        keyboard.add_hotkey("f10", self.toggle_bot)

    def setup_ui(self):
        # Header Section
        self.header_frame = ctk.CTkFrame(self, fg_color="transparent")
        self.header_frame.pack(pady=(25, 15))

        self.header = ctk.CTkLabel(
            self.header_frame,
            text="CRITICAL BOT",
            font=("Impact", 35),
            text_color="#e11d48",
        )
        self.header.pack()

        self.sub_status = ctk.CTkLabel(
            self.header_frame,
            text="● SYSTEM PAUSED",
            font=("Arial", 11, "bold"),
            text_color="#e11d48",
        )
        self.sub_status.pack()

        # Accounts Cards
        self.create_card("ACCOUNT 01", self.acc1_active, self.acc1_target, 1)
        self.create_card("ACCOUNT 02", self.acc2_active, self.acc2_target, 2)

        # Control Buttons
        self.ctrl_frame = ctk.CTkFrame(self, fg_color="transparent")
        self.ctrl_frame.pack(pady=20)

        self.start_btn = ctk.CTkButton(
            self.ctrl_frame,
            text="START (F10)",
            font=("Arial", 14, "bold"),
            fg_color="#059669",
            hover_color="#047857",
            width=150,
            height=45,
            command=self.start_bot,
        )
        self.start_btn.grid(row=0, column=0, padx=10)

        self.stop_btn = ctk.CTkButton(
            self.ctrl_frame,
            text="STOP (F10)",
            font=("Arial", 14, "bold"),
            fg_color="#e11d48",
            hover_color="#be123c",
            width=150,
            height=45,
            command=self.stop_bot,
        )
        self.stop_btn.grid(row=0, column=1, padx=10)

        # Bottom Glow Line
        self.glow_line = ctk.CTkFrame(self, height=4, fg_color="#e11d48")
        self.glow_line.pack(side="bottom", fill="x")

    def create_card(self, title, active_var, target_var, num):
        card = ctk.CTkFrame(
            self,
            corner_radius=15,
            border_width=1,
            border_color="#334155",
            fg_color="#1e293b",
        )
        card.pack(pady=8, padx=25, fill="x")

        top = ctk.CTkFrame(card, fg_color="transparent")
        top.pack(fill="x", padx=15, pady=(10, 5))

        ctk.CTkCheckBox(
            top,
            text=title,
            variable=active_var,
            font=("Arial", 13, "bold"),
            fg_color="#10b981",
            border_color="#475569",
        ).pack(side="left")

        status_text = ctk.CTkLabel(
            top, text="OFFLINE", font=("Arial", 10, "bold"), text_color="#64748b"
        )
        status_text.pack(side="right")
        setattr(self, f"acc{num}_status_text", status_text)

        bot = ctk.CTkFrame(card, fg_color="transparent")
        bot.pack(fill="x", padx=15, pady=(5, 10))

        ctk.CTkOptionMenu(
            bot,
            values=list(METIN_DATABASE.keys()),
            variable=target_var,
            width=130,
            height=30,
            fg_color="#334155",
            button_color="#475569",
        ).pack(side="left", padx=(0, 10))

        ctk.CTkButton(
            bot,
            text="BIND",
            width=70,
            height=30,
            fg_color="#0f172a",
            hover_color="#334155",
            command=lambda: self.bind_window(num),
        ).pack(side="left")

    def update_status(self, num, text, color):
        getattr(self, f"acc{num}_status_text").configure(text=text, text_color=color)

    def bind_window(self, num):
        def task():
            self.update_status(num, "LINKING...", "#f59e0b")
            time.sleep(2)
            hwnd = win32gui.GetForegroundWindow()
            if num == 1:
                self.acc1_hwnd = hwnd
            else:
                self.acc2_hwnd = hwnd
            self.update_status(num, "READY", "#38bdf8")

        threading.Thread(target=task, daemon=True).start()

    def toggle_bot(self):
        if self.is_running:
            self.stop_bot()
        else:
            self.start_bot()

    def start_bot(self):
        self.is_running = True
        self.header.configure(text_color="#10b981")
        self.sub_status.configure(text="● SYSTEM ACTIVE", text_color="#10b981")
        self.glow_line.configure(fg_color="#10b981")

    def stop_bot(self):
        self.is_running = False
        self.header.configure(text_color="#e11d48")
        self.sub_status.configure(text="● SYSTEM PAUSED", text_color="#e11d48")
        self.glow_line.configure(fg_color="#e11d48")

    def process_window(self, hwnd, target_key, sct, kernel, num):
        if not hwnd or not win32gui.IsWindow(hwnd):
            return
        try:
            win32gui.ShowWindow(hwnd, 5)
            win32gui.SetForegroundWindow(hwnd)
            time.sleep(self.swap_delay)

            r = win32gui.GetWindowRect(hwnd)
            screenshot = sct.grab(
                {"top": r[1], "left": r[0], "width": r[2] - r[0], "height": r[3] - r[1]}
            )
            img = np.array(screenshot)
            hsv = cv2.cvtColor(cv2.cvtColor(img, cv2.COLOR_BGRA2BGR), cv2.COLOR_BGR2HSV)

            conf = METIN_DATABASE[target_key]
            mask = cv2.inRange(hsv, np.array(conf["lower"]), np.array(conf["upper"]))
            mask = cv2.morphologyEx(mask, cv2.MORPH_OPEN, kernel)
            cnts, _ = cv2.findContours(mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)

            if cnts:
                best = max(cnts, key=cv2.contourArea)
                if cv2.contourArea(best) > conf["area"]:
                    x, y, w, h = cv2.boundingRect(best)
                    cx, cy = x + w // 2, y + h // 2
                    if (r[3] - r[1]) * 0.1 < cy < (r[3] - r[1]) * 0.9:
                        self.update_status(num, "ACTIVE", "#10b981")
                        pydirectinput.click(r[0] + cx, r[1] + cy, button="right")
                        time.sleep(self.click_delay)
                        return True

            self.update_status(num, "SCANNING", "#f59e0b")
            pydirectinput.mouseDown(button="right")
            pydirectinput.moveRel(160, 0, duration=0.06)
            pydirectinput.mouseUp(button="right")
            time.sleep(self.scan_delay)
            return False
        except:
            return False

    def bot_loop(self):
        sct = mss.mss()
        kernel = np.ones((5, 5), np.uint8)
        while True:
            if self.is_running:
                if self.acc1_active.get() and self.acc1_hwnd:
                    self.process_window(
                        self.acc1_hwnd, self.acc1_target.get(), sct, kernel, 1
                    )

                time.sleep(0.05)

                if self.is_running and self.acc2_active.get() and self.acc2_hwnd:
                    self.process_window(
                        self.acc2_hwnd, self.acc2_target.get(), sct, kernel, 2
                    )
            time.sleep(0.1)


if __name__ == "__main__":
    app = MetinBotPro()
    threading.Thread(target=app.bot_loop, daemon=True).start()
    app.mainloop()
