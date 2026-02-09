import cv2
import numpy as np
import pydirectinput
import time
import keyboard
import win32gui
import win32con
import mss
import customtkinter as ctk
import threading

# --- قاعدة بيانات الماتينات المحدثة ---
METIN_DATABASE = {
    "Origins Metin (Lv.120)": {
        "lower": [0, 100, 50],  # درجات الأحمر والبني الداكن
        "upper": [10, 255, 200],
        "area": 2000,
    },
}


class MetinBotGUI(ctk.CTk):
    def __init__(self):
        super().__init__()
        self.title("Critical Bot v.1")
        self.geometry("450x650")
        ctk.set_appearance_mode("dark")

        self.is_running = False
        self.selected_metin = "Origins Metin (Lv.120)"
        self.window_title = "Origins"

        # --- واجهة المستخدم ---
        self.label_title = ctk.CTkLabel(
            self, text="Critical Dashboard", font=("Arial", 22, "bold")
        )
        self.label_title.pack(pady=20)

        self.option_menu = ctk.CTkOptionMenu(
            self, values=list(METIN_DATABASE.keys()), command=self.update_selection
        )
        self.option_menu.pack(pady=10)

        self.btn_start = ctk.CTkButton(
            self, text="START (F10)", fg_color="#2ecc71", command=self.start_bot
        )
        self.btn_start.pack(pady=10)

        self.btn_stop = ctk.CTkButton(
            self, text="STOP (F10)", fg_color="#e74c3c", command=self.stop_bot
        )
        self.btn_stop.pack(pady=10)

        self.log_box = ctk.CTkTextbox(self, width=400, height=200)
        self.log_box.pack(pady=15, padx=20)
        self.log(f"✅ Ready! Targeting: {self.selected_metin}")

        self.status_label = ctk.CTkLabel(
            self,
            text="STATUS: PAUSED",
            text_color="#e74c3c",
            font=("Arial", 15, "bold"),
        )
        self.status_label.pack(pady=10)

        keyboard.add_hotkey("f10", self.toggle_hotkey)

    def log(self, message):
        self.log_box.insert("end", f"[{time.strftime('%H:%M:%S')}] {message}\n")
        self.log_box.see("end")

    def update_selection(self, choice):
        self.selected_metin = choice
        self.log(f"🎯 Target: {choice}")

    def start_bot(self):
        self.is_running = True
        self.status_label.configure(text="STATUS: RUNNING", text_color="#2ecc71")
        self.log("▶️ Bot Running...")

    def stop_bot(self):
        self.is_running = False
        self.status_label.configure(text="STATUS: PAUSED", text_color="#e74c3c")
        self.log("⏸️ Bot Stopped.")

    def toggle_hotkey(self):
        if self.is_running:
            self.stop_bot()
        else:
            self.start_bot()

    def bot_loop(self):
        sct = mss.mss()
        kernel = np.ones((5, 5), np.uint8)

        while True:
            if self.is_running:
                hwnd = win32gui.FindWindow(None, self.window_title)
                if hwnd:
                    try:
                        rect = win32gui.GetWindowRect(hwnd)
                        win_x, win_y, win_w, win_h = (
                            rect[0],
                            rect[1],
                            rect[2] - rect[0],
                            rect[3] - rect[1],
                        )

                        img = np.array(
                            sct.grab(
                                {
                                    "top": win_y,
                                    "left": win_x,
                                    "width": win_w,
                                    "height": win_h,
                                }
                            )
                        )
                        frame = cv2.cvtColor(img, cv2.COLOR_BGRA2BGR)
                        hsv = cv2.cvtColor(frame, cv2.COLOR_BGR2HSV)

                        config = METIN_DATABASE[self.selected_metin]
                        mask = cv2.inRange(
                            hsv, np.array(config["lower"]), np.array(config["upper"])
                        )
                        mask = cv2.morphologyEx(mask, cv2.MORPH_OPEN, kernel)

                        contours, _ = cv2.findContours(
                            mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE
                        )

                        found = False
                        for cnt in contours:
                            area = cv2.contourArea(cnt)
                            if area > config["area"]:
                                x, y, w, h = cv2.boundingRect(cnt)
                                # تجنب الضغط على مناطق الواجهة
                                if y > win_h * 0.20 and (y + h) < win_h * 0.85:
                                    cx, cy = x + w // 2, y + h // 2
                                    pydirectinput.click(win_x + cx, win_y + cy)
                                    self.log("⚔️ Attack: Metin Origins Found!")
                                    found = True
                                    time.sleep(1.2)
                                    break

                        if not found:
                            # دوران سريع للبحث
                            pydirectinput.mouseDown(button="right")
                            pydirectinput.moveRel(180, 0, duration=0.08)
                            pydirectinput.mouseUp(button="right")
                    except:
                        pass
            time.sleep(0.01)


if __name__ == "__main__":
    app = MetinBotGUI()
    threading.Thread(target=app.bot_loop, daemon=True).start()
    app.mainloop()
