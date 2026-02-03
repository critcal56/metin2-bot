import cv2
import numpy as np
import pydirectinput
import time
import keyboard
import win32gui
import win32con
import mss

# --- SETTINGS ---
WINDOW_TITLE = "Saryong - The Awakening of the Twins"
MIN_AREA = 1000
MAX_AREA = 8000
IS_RUNNING = True

sct = mss.mss()


def is_metin_by_structure(cnt):
    area = cv2.contourArea(cnt)
    x, y, w, h = cv2.boundingRect(cnt)
    hull = cv2.convexHull(cnt)
    hull_area = cv2.contourArea(hull)
    solidity = float(area) / hull_area if hull_area > 0 else 0
    aspect_ratio = float(w) / h

    # Strict structure check
    if solidity > 0.78 and 0.6 < aspect_ratio < 1.4:
        return True
    return False


def toggle_bot():
    global IS_RUNNING
    IS_RUNNING = not IS_RUNNING
    print(f"\n[!] BOT {'ACTIVE' if IS_RUNNING else 'PAUSED'}")


keyboard.add_hotkey("f10", toggle_bot)

print("🚀 Anti-Motion Geometry Bot Active. Ignoring moving objects...")

while True:
    if keyboard.is_pressed("end"):
        break
    if not IS_RUNNING:
        time.sleep(0.5)
        continue

    hwnds = []
    win32gui.EnumWindows(
        lambda h, e: (
            hwnds.append(h)
            if (
                win32gui.IsWindowVisible(h)
                and WINDOW_TITLE in win32gui.GetWindowText(h)
            )
            else None
        ),
        None,
    )

    for hwnd in hwnds:
        if not IS_RUNNING:
            break
        try:
            win32gui.ShowWindow(hwnd, win32con.SW_RESTORE)
            win32gui.SetForegroundWindow(hwnd)
            time.sleep(0.1)

            rect = win32gui.GetWindowRect(hwnd)
            win_x, win_y, win_w, win_h = (
                rect[0],
                rect[1],
                rect[2] - rect[0],
                rect[3] - rect[1],
            )
            monitor = {"top": win_y, "left": win_x, "width": win_w, "height": win_h}

            # --- MOTION DETECTION LOGIC ---
            # Capture Frame 1
            img1 = np.array(sct.grab(monitor))
            gray1 = cv2.cvtColor(img1, cv2.COLOR_BGRA2GRAY)

            time.sleep(0.1)  # Small gap to detect movement

            # Capture Frame 2
            img2 = np.array(sct.grab(monitor))
            gray2 = cv2.cvtColor(img2, cv2.COLOR_BGRA2GRAY)

            # Find difference between frames (Movement)
            diff = cv2.absdiff(gray1, gray2)
            _, motion_mask = cv2.threshold(diff, 25, 255, cv2.THRESH_BINARY)

            # --- STRUCTURAL ANALYSIS ---
            blurred = cv2.GaussianBlur(gray2, (5, 5), 0)
            _, thresh = cv2.threshold(
                blurred, 0, 255, cv2.THRESH_BINARY_INV + cv2.THRESH_OTSU
            )
            contours, _ = cv2.findContours(
                thresh, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE
            )

            best_target = None
            min_dist = float("inf")

            for cnt in contours:
                if MIN_AREA < cv2.contourArea(cnt) < MAX_AREA:
                    if is_metin_by_structure(cnt):
                        x, y, w, h = cv2.boundingRect(cnt)

                        # Check if this specific area has motion
                        roi_motion = motion_mask[y : y + h, x : x + w]
                        motion_amount = np.sum(roi_motion) / 255

                        # If motion is low, it's a static object (Metin)
                        if motion_amount < (cv2.contourArea(cnt) * 0.05):
                            cx_rel, cy_rel = x + w // 2, y + h // 2
                            if win_h * 0.30 < cy_rel < win_h * 0.70:
                                dist = np.sqrt(
                                    (cx_rel - (win_w // 2)) ** 2
                                    + (cy_rel - (win_h // 2)) ** 2
                                )
                                if dist < min_dist:
                                    min_dist = dist
                                    best_target = (win_x + cx_rel, win_y + cy_rel)

            if best_target:
                pydirectinput.press("z")
                pydirectinput.click(best_target[0], best_target[1])
                print(f"[+] Attacking Static Target on window {hwnd}")
                time.sleep(0.4)
            else:
                # Camera Rotation
                pydirectinput.moveTo(win_x + win_w // 2, win_y + win_h // 2)
                pydirectinput.mouseDown(button="right")
                pydirectinput.moveRel(250, 0, duration=0.2)
                pydirectinput.mouseUp(button="right")

            time.sleep(0.2)

        except Exception:
            continue

    time.sleep(0.01)
