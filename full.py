import cv2
import numpy as np
import pydirectinput
import time
import keyboard
import win32gui
import win32con
import mss

# --- الإعدادات الأساسية ---
WINDOW_TITLE = "Saryong - The Awakening of the Twins"
MIN_AREA = 1100
IS_RUNNING = True

# ألوان الماتينات (بني + وردي)
LOWER_BROWN = np.array([0, 110, 48])
UPPER_BROWN = np.array([25, 255, 198])
LOWER_PINK = np.array([130, 40, 40])
UPPER_PINK = np.array([175, 255, 255])

sct = mss.mss()


def get_all_windows():
    """البحث عن جميع نوافذ اللعبة المفتوحة"""
    windows = []

    def enum_handler(hwnd, lParam):
        if win32gui.IsWindowVisible(hwnd) and WINDOW_TITLE in win32gui.GetWindowText(
            hwnd
        ):
            windows.append(hwnd)

    win32gui.EnumWindows(enum_handler, None)
    return windows


def is_metin_by_structure(cnt, win_h):
    """فحص الشكل وتجنب المناطق المحظورة"""
    area = cv2.contourArea(cnt)
    x, y, w, h = cv2.boundingRect(cnt)

    # Dead Zones: تجاهل شريط الدم (أعلى 22%) وشريط المهارات (أسفل 15%)
    if y < win_h * 0.22 or (y + h) > win_h * 0.85:
        return False

    hull = cv2.convexHull(cnt)
    hull_area = cv2.contourArea(hull)
    solidity = float(area) / hull_area if hull_area > 0 else 0
    aspect_ratio = float(w) / h

    return solidity > 0.75 and 0.5 < aspect_ratio < 1.6


keyboard.add_hotkey("f10", lambda: globals().update(IS_RUNNING=not IS_RUNNING))

print("🚀 Bot is running in Background Mode (No Windows). Press F10 to Pause.")

while True:
    if keyboard.is_pressed("end"):
        break
    if not IS_RUNNING:
        time.sleep(0.5)
        continue

    game_windows = get_all_windows()

    for hwnd in game_windows:
        if not IS_RUNNING:
            break

        try:
            # تفعيل النافذة
            win32gui.ShowWindow(hwnd, win32con.SW_RESTORE)
            win32gui.SetForegroundWindow(hwnd)
            time.sleep(0.05)

            rect = win32gui.GetWindowRect(hwnd)
            win_x, win_y, win_w, win_h = (
                rect[0],
                rect[1],
                rect[2] - rect[0],
                rect[3] - rect[1],
            )
            monitor = {"top": win_y, "left": win_x, "width": win_w, "height": win_h}

            # التقاط سريع (لقطتين لاكتشاف الحركة)
            img1 = np.array(sct.grab(monitor))
            gray1 = cv2.cvtColor(img1, cv2.COLOR_BGRA2GRAY)
            time.sleep(0.06)
            img2 = np.array(sct.grab(monitor))
            frame_bgr = cv2.cvtColor(img2, cv2.COLOR_BGRA2BGR)
            gray2 = cv2.cvtColor(img2, cv2.COLOR_BGRA2GRAY)

            # معالجة الحركة والألوان
            diff = cv2.absdiff(gray1, gray2)
            _, motion_mask = cv2.threshold(diff, 25, 255, cv2.THRESH_BINARY)
            hsv = cv2.cvtColor(frame_bgr, cv2.COLOR_BGR2HSV)

            mask_combined = cv2.bitwise_or(
                cv2.inRange(hsv, LOWER_BROWN, UPPER_BROWN),
                cv2.inRange(hsv, LOWER_PINK, UPPER_PINK),
            )

            kernel = np.ones((7, 7), np.uint8)
            clean_mask = cv2.morphologyEx(mask_combined, cv2.MORPH_CLOSE, kernel)
            contours, _ = cv2.findContours(
                clean_mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE
            )

            best_target = None
            min_dist = float("inf")

            for cnt in contours:
                area = cv2.contourArea(cnt)
                if MIN_AREA < area < 12000:
                    if is_metin_by_structure(cnt, win_h):
                        x, y, w, h = cv2.boundingRect(cnt)
                        roi_motion = motion_mask[y : y + h, x : x + w]

                        # فحص الثبات
                        if (np.sum(roi_motion) / 255) < (area * 0.06):
                            cx, cy = x + w // 2, y + h // 2
                            dist = np.sqrt(
                                (cx - win_w // 2) ** 2 + (cy - win_h // 2) ** 2
                            )
                            if dist < min_dist:
                                min_dist = dist
                                best_target = (win_x + cx, win_y + cy)

            if best_target:
                pydirectinput.click(best_target[0], best_target[1])
                print(f"⚔️ [Account {hwnd}] Metin Found & Attacked.")
                time.sleep(0.8)  # راحة قصيرة قبل الحساب التالي
            else:
                # تدوير الكاميرا
                pydirectinput.mouseDown(button="right")
                pydirectinput.moveRel(180, 0, duration=0.1)
                pydirectinput.mouseUp(button="right")

        except Exception:
            continue

    time.sleep(0.01)
