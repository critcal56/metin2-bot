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
from typing import Optional, Tuple

# --- قاعدة بيانات الماتينات لكل Lv ---
METIN_DATABASE = {
    "Lv 50": {"lower": [130, 40, 40], "upper": [175, 255, 255], "area": 1500},
    "Lv 60": {"lower": [0, 110, 48], "upper": [25, 255, 198], "area": 1500},
    "Lv 70": {"lower": [125, 45, 90], "upper": [165, 255, 255], "area": 1500},
    "Lv 80": {"lower": [140, 50, 50], "upper": [179, 255, 255], "area": 1500},
}


class MetinBotPro(ctk.CTk):
    def __init__(self):
        super().__init__()
        self.title("CRITICAL Farm Bot")
        self.geometry("420x500")
        self.resizable(False, False)
        ctk.set_appearance_mode("dark")

        # Bot state
        self.is_running = False
        self.acc1_hwnd = None
        self.acc2_hwnd = None
        self.bot_thread = None
        self.last_focus_time = 0  # Track last window focus time

        # Rotation counters for each account
        self.acc1_rotation_count = 0
        self.acc2_rotation_count = 0
        self.max_rotations = 6  # عدد الدورانات قبل التحرك

        # Timing settings
        self.swap_delay = 0.2  # Increased for SetForegroundWindow
        self.click_delay = 0.8
        self.scan_delay = 0.1  # زيادة وقت الانتظار بعد الدوران
        self.focus_cooldown = 0.5  # Minimum time between window switches
        self.movement_duration = 1.5  # مدة المشي للبحث عن ماتينات

        # Account settings
        self.acc1_active = ctk.BooleanVar(value=True)
        self.acc2_active = ctk.BooleanVar(value=True)
        self.acc1_target = ctk.StringVar(value="Lv 50")
        self.acc2_target = ctk.StringVar(value="Lv 50")

        # UI setup
        self.setup_ui()

        # Hotkey setup with error handling
        try:
            keyboard.add_hotkey("f10", self.toggle_bot)
        except Exception as e:
            print(f"Warning: Could not register F10 hotkey: {e}")

    def setup_ui(self):
        # Header
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

        # Account cards
        self.create_card("ACCOUNT 01", self.acc1_active, self.acc1_target, 1)
        self.create_card("ACCOUNT 02", self.acc2_active, self.acc2_target, 2)

        # Control buttons
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

        # Glow line
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

        # Top section
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

        # Bottom section
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

    def update_status(self, num: int, text: str, color: str):
        """Update account status label safely from any thread"""
        try:
            self.after(
                0,
                lambda: getattr(self, f"acc{num}_status_text").configure(
                    text=text, text_color=color
                ),
            )
        except Exception as e:
            print(f"Error updating status: {e}")

    def bind_window(self, num: int):
        """Bind the currently focused window to an account slot"""

        def task():
            try:
                self.update_status(num, "LINKING...", "#f59e0b")
                time.sleep(2)
                hwnd = win32gui.GetForegroundWindow()

                if hwnd and win32gui.IsWindow(hwnd):
                    if num == 1:
                        self.acc1_hwnd = hwnd
                    else:
                        self.acc2_hwnd = hwnd

                    window_title = win32gui.GetWindowText(hwnd)
                    print(f"Account {num} bound to: {window_title} (HWND: {hwnd})")
                    self.update_status(num, "READY", "#38bdf8")
                else:
                    self.update_status(num, "FAILED", "#ef4444")
            except Exception as e:
                print(f"Error binding window: {e}")
                self.update_status(num, "ERROR", "#ef4444")

        threading.Thread(target=task, daemon=True).start()

    def toggle_bot(self):
        """Toggle bot on/off via hotkey"""
        if self.is_running:
            self.stop_bot()
        else:
            self.start_bot()

    def start_bot(self):
        """Start the bot"""
        if not self.is_running:
            self.is_running = True
            self.header.configure(text_color="#10b981")
            self.sub_status.configure(text="● SYSTEM ACTIVE", text_color="#10b981")
            self.glow_line.configure(fg_color="#10b981")
            print("Bot started!")

    def stop_bot(self):
        """Stop the bot"""
        if self.is_running:
            self.is_running = False
            self.header.configure(text_color="#e11d48")
            self.sub_status.configure(text="● SYSTEM PAUSED", text_color="#e11d48")
            self.glow_line.configure(fg_color="#e11d48")
            print("Bot stopped!")

    def is_metin_by_structure(self, cnt, win_h: int) -> bool:
        """Check if contour matches metin stone structure"""
        try:
            area = cv2.contourArea(cnt)
            if area < 100:  # Too small
                return False

            x, y, w, h = cv2.boundingRect(cnt)

            # Position check (not too high or too low on screen)
            if y < win_h * 0.22 or (y + h) > win_h * 0.85:
                return False

            # Shape analysis
            hull = cv2.convexHull(cnt)
            hull_area = cv2.contourArea(hull)
            if hull_area == 0:
                return False

            solidity = float(area) / hull_area
            aspect_ratio = float(w) / h if h > 0 else 0

            # Metin stones are roughly solid and not too elongated
            return solidity > 0.75 and 0.5 < aspect_ratio < 1.6
        except Exception as e:
            print(f"Error in structure check: {e}")
            return False

    def focus_window(self, hwnd) -> bool:
        """Safely bring window to foreground"""
        try:
            if not hwnd or not win32gui.IsWindow(hwnd):
                return False

            # Rate limiting to prevent SetForegroundWindow errors
            current_time = time.time()
            if current_time - self.last_focus_time < self.focus_cooldown:
                time.sleep(self.focus_cooldown - (current_time - self.last_focus_time))

            # Check if window is minimized
            if win32gui.IsIconic(hwnd):
                win32gui.ShowWindow(hwnd, win32con.SW_RESTORE)
                time.sleep(0.1)

            # Multi-step approach for reliable focus
            try:
                # First show the window
                win32gui.ShowWindow(hwnd, win32con.SW_SHOW)
                time.sleep(0.05)

                # Then bring to front
                win32gui.BringWindowToTop(hwnd)
                time.sleep(0.05)

                # Finally set foreground
                win32gui.SetForegroundWindow(hwnd)

            except Exception as e:
                # If SetForegroundWindow fails, try alternative method
                try:
                    # Simulate Alt key press to allow window switching
                    import ctypes

                    ctypes.windll.user32.keybd_event(0x12, 0, 0, 0)  # Alt down
                    win32gui.SetForegroundWindow(hwnd)
                    ctypes.windll.user32.keybd_event(0x12, 0, 2, 0)  # Alt up
                except:
                    print(f"Could not focus window: {e}")
                    return False

            self.last_focus_time = time.time()
            time.sleep(self.swap_delay)
            return True

        except Exception as e:
            print(f"Error focusing window: {e}")
            return False

    def process_window(self, hwnd, num: int):
        """Main processing logic for one game window"""
        if not hwnd or not win32gui.IsWindow(hwnd):
            self.update_status(num, "INVALID", "#ef4444")
            return

        # Create mss instance for this thread (thread-safe)
        sct = mss.mss()

        try:
            # Focus the window
            if not self.focus_window(hwnd):
                sct.close()
                return

            # Get window position and size
            rect = win32gui.GetWindowRect(hwnd)
            win_x, win_y = rect[0], rect[1]
            win_w, win_h = rect[2] - rect[0], rect[3] - rect[1]

            if win_w <= 0 or win_h <= 0:
                sct.close()
                return

            monitor = {"top": win_y, "left": win_x, "width": win_w, "height": win_h}

            # Capture two frames to detect motion
            img1 = np.array(sct.grab(monitor))
            gray1 = cv2.cvtColor(img1, cv2.COLOR_BGRA2GRAY)

            time.sleep(0.06)

            img2 = np.array(sct.grab(monitor))
            frame_bgr = cv2.cvtColor(img2, cv2.COLOR_BGRA2BGR)
            gray2 = cv2.cvtColor(img2, cv2.COLOR_BGRA2GRAY)

            # Calculate motion mask
            diff = cv2.absdiff(gray1, gray2)
            _, motion_mask = cv2.threshold(diff, 25, 255, cv2.THRESH_BINARY)

            # Convert to HSV for color detection
            hsv = cv2.cvtColor(frame_bgr, cv2.COLOR_BGR2HSV)

            # Get target configuration
            target_key = self.acc1_target.get() if num == 1 else self.acc2_target.get()
            conf = METIN_DATABASE[target_key]

            # Create color mask
            mask = cv2.inRange(hsv, np.array(conf["lower"]), np.array(conf["upper"]))
            mask = cv2.morphologyEx(mask, cv2.MORPH_CLOSE, np.ones((7, 7), np.uint8))

            # Find contours
            contours, _ = cv2.findContours(
                mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE
            )

            # Find best target (closest to center, stationary)
            best_target = None
            min_dist = float("inf")

            for cnt in contours:
                area = cv2.contourArea(cnt)

                if area > conf["area"] and self.is_metin_by_structure(cnt, win_h):
                    x, y, w, h = cv2.boundingRect(cnt)

                    # Check if area is stationary (low motion)
                    roi_motion = motion_mask[y : y + h, x : x + w]
                    motion_pixels = np.sum(roi_motion) / 255

                    if motion_pixels < (area * 0.06):  # Mostly stationary
                        cx, cy = x + w // 2, y + h // 2
                        dist = np.sqrt((cx - win_w // 2) ** 2 + (cy - win_h // 2) ** 2)

                        if dist < min_dist:
                            min_dist = dist
                            best_target = (win_x + cx, win_y + cy)

            # Act on target
            if best_target:
                self.update_status(num, "ATTACKING", "#10b981")
                # إعادة تعيين عداد الدوران عند إيجاد ماتين
                if num == 1:
                    self.acc1_rotation_count = 0
                else:
                    self.acc2_rotation_count = 0

                pydirectinput.click(best_target[0], best_target[1])
                time.sleep(self.click_delay)
            else:
                # الحصول على عداد الدوران الحالي
                rotation_count = (
                    self.acc1_rotation_count if num == 1 else self.acc2_rotation_count
                )

                # فحص إذا وصل للحد الأقصى من الدورانات
                if rotation_count >= self.max_rotations:
                    # المشي للخلف والدوران للبحث عن ماتينات
                    self.update_status(num, "MOVING BACK", "#a855f7")
                    print(
                        f"Account {num}: No metin found after {self.max_rotations} rotations, moving backward..."
                    )

                    # المشي للخلف
                    pydirectinput.keyDown("s")
                    time.sleep(self.movement_duration)
                    pydirectinput.keyUp("s")

                    # دوران الكاميرا 180 درجة
                    pydirectinput.mouseDown(button="right")
                    pydirectinput.moveRel(360, 0, duration=0.2)
                    pydirectinput.mouseUp(button="right")

                    print(f"Account {num}: Moved backward and rotated camera")

                    # إعادة تعيين العداد
                    if num == 1:
                        self.acc1_rotation_count = 0
                    else:
                        self.acc2_rotation_count = 0

                    time.sleep(0.3)
                else:
                    # دوران الكاميرا للبحث
                    self.update_status(
                        num,
                        f"SCANNING ({rotation_count + 1}/{self.max_rotations})",
                        "#f59e0b",
                    )

                    # زيادة العداد
                    if num == 1:
                        self.acc1_rotation_count += 1
                    else:
                        self.acc2_rotation_count += 1

                    # دوران الكاميرا
                    pydirectinput.mouseDown(button="right")
                    pydirectinput.moveRel(180, 0, duration=0.1)
                    pydirectinput.mouseUp(button="right")
                    time.sleep(self.scan_delay)

        except Exception as e:
            print(f"Error processing window {num}: {e}")
            self.update_status(num, "ERROR", "#ef4444")
        finally:
            # Always close mss instance
            try:
                sct.close()
            except:
                pass

    def bot_loop(self):
        """Main bot loop running in separate thread"""
        print("Bot loop started!")

        while True:
            try:
                if self.is_running:
                    # Process account 1
                    if self.acc1_active.get() and self.acc1_hwnd:
                        self.process_window(self.acc1_hwnd, 1)

                    # Longer delay between accounts to prevent focus issues
                    time.sleep(0.3)

                    # Process account 2
                    if self.acc2_active.get() and self.acc2_hwnd:
                        self.process_window(self.acc2_hwnd, 2)

                    # Small delay before next cycle
                    time.sleep(0.2)
                else:
                    # Bot is paused
                    time.sleep(0.1)

            except Exception as e:
                print(f"Error in bot loop: {e}")
                time.sleep(0.1)

    def on_closing(self):
        """Clean up when closing the application"""
        print("Shutting down...")
        self.is_running = False
        try:
            keyboard.unhook_all_hotkeys()
        except:
            pass
        self.destroy()


if __name__ == "__main__":
    app = MetinBotPro()
    app.protocol("WM_DELETE_WINDOW", app.on_closing)

    # Start bot loop in daemon thread
    bot_thread = threading.Thread(target=app.bot_loop, daemon=True)
    bot_thread.start()

    print("Application started! Press F10 to toggle bot.")
    app.mainloop()
