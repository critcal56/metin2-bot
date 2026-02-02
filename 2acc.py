import cv2
import numpy as np
import pyautogui
import pydirectinput
import time
import keyboard
import win32gui
import win32con
import win32com.client

# --- CONFIGURATION ---
shell = win32com.client.Dispatch("WScript.Shell")
WINDOW_TITLE = "Saryong - The Awakening of the Twins"
LOWER_PINK = np.array([135, 45, 45])
UPPER_PINK = np.array([180, 255, 255])
MIN_AREA = 2000
HP_BAR_REGION = (400, 20, 500, 80)
IS_RUNNING = True

# --- DEAD ZONE SETTINGS ---
# سنحدد مربعاً في منتصف الشاشة يمنع الضغط فيه (موقع الشخصية)
DEAD_ZONE_WIDTH = 150  # عرض المنطقة المحظورة
DEAD_ZONE_HEIGHT = 200  # طول المنطقة المحظورة


def is_in_dead_zone(x, y, win_w, win_h):
    """التحقق مما إذا كانت الإحداثيات تقع فوق الشخصية في المنتصف"""
    center_x = win_w // 2
    center_y = win_h // 2

    # حدود المنطقة الميتة
    margin_x = DEAD_ZONE_WIDTH // 2
    margin_y = DEAD_ZONE_HEIGHT // 2

    return (center_x - margin_x < x < center_x + margin_x) and (
        center_y - margin_y < y < center_y + margin_y
    )


def toggle_bot():
    global IS_RUNNING
    IS_RUNNING = not IS_RUNNING
    print(f"\n[!] Bot Status: {'RUNNING' if IS_RUNNING else 'PAUSED'}")


keyboard.add_hotkey("f10", toggle_bot)


def get_target_windows():
    hwnds = []

    def callback(hwnd, extra):
        if win32gui.IsWindowVisible(hwnd) and WINDOW_TITLE in win32gui.GetWindowText(
            hwnd
        ):
            hwnds.append(hwnd)

    win32gui.EnumWindows(callback, None)
    return hwnds


def is_metin_alive():
    try:
        scr = pyautogui.screenshot(region=HP_BAR_REGION)
        frame = cv2.cvtColor(np.array(scr), cv2.COLOR_RGB2BGR)
        hsv = cv2.cvtColor(frame, cv2.COLOR_BGR2HSV)
        mask1 = cv2.inRange(hsv, np.array([0, 150, 100]), np.array([10, 255, 255]))
        mask2 = cv2.inRange(hsv, np.array([160, 150, 100]), np.array([180, 255, 255]))
        return np.sum(cv2.add(mask1, mask2) > 0) > 600
    except:
        return False


# --- STARTUP ---
print("🚀 Launching Dead-Zone Protected Version...")
TARGETS = get_target_windows()
if not TARGETS:
    exit()

while True:
    if keyboard.is_pressed("end"):
        break
    if not IS_RUNNING:
        time.sleep(0.5)
        continue

    for i, hwnd in enumerate(TARGETS):
        if not IS_RUNNING:
            break

        rect = win32gui.GetWindowRect(hwnd)
        win_x, win_y, win_w, win_h = (
            rect[0],
            rect[1],
            rect[2] - rect[0],
            rect[3] - rect[1],
        )

        win32gui.ShowWindow(hwnd, win32con.SW_RESTORE)
        win32gui.SetForegroundWindow(hwnd)
        time.sleep(1.0)

        if is_metin_alive():
            print(f"   - [Acc {i+1}] Busy.")
            continue

        print(f"   - [Acc {i+1}] Scanning...")
        scr = pyautogui.screenshot(region=(win_x, win_y, win_w, win_h))
        frame = cv2.cvtColor(np.array(scr), cv2.COLOR_RGB2BGR)
        hsv = cv2.cvtColor(frame, cv2.COLOR_BGR2HSV)
        mask = cv2.inRange(hsv, LOWER_PINK, UPPER_PINK)
        contours, _ = cv2.findContours(mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)

        # ترتيب الأهداف حسب المساحة
        sorted_contours = sorted(contours, key=cv2.contourArea, reverse=True)

        target_found = False
        for cnt in sorted_contours:
            if cv2.contourArea(cnt) < MIN_AREA:
                continue

            x, y, w, h = cv2.boundingRect(cnt)
            obj_center_x = x + (w // 2)
            obj_center_y = y + (h // 2)

            # --- فحص المنطقة الميتة ---
            if is_in_dead_zone(obj_center_x, obj_center_y, win_w, win_h):
                # إذا كان الهدف فوق الشخصية، تجاهله وابحث عن الذي يليه
                continue

            # إذا وصلنا هنا، الهدف آمن وخارج نطاق الشخصية
            target_x, target_y = win_x + obj_center_x, win_y + obj_center_y
            pydirectinput.moveTo(target_x, target_y, duration=0.2)
            pydirectinput.click()
            print(f"   - [Acc {i+1}] Clicked on Safe Target!")
            time.sleep(4.0)
            target_found = True
            break  # اخرج من حلقة الأهداف بعد الضغط بنجاح

        if not target_found:
            # تدوير الكاميرا إذا لم يجد شيئاً أو كانت كل الأهداف في المنطقة الميتة
            print(f"   - [Acc {i+1}] Rotating...")
            pydirectinput.moveTo(win_x + win_w // 2, win_y + win_h // 2)
            pydirectinput.mouseDown(button="right")
            pydirectinput.moveRel(400, 0, duration=0.6)
            pydirectinput.mouseUp(button="right")
            time.sleep(0.5)

    time.sleep(0.2)
