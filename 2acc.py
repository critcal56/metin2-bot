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
MIN_AREA = 1500
HP_BAR_REGION = (400, 25, 500, 60)
IS_RUNNING = True


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
        mask1 = cv2.inRange(hsv, np.array([0, 180, 100]), np.array([10, 255, 255]))
        mask2 = cv2.inRange(hsv, np.array([170, 180, 100]), np.array([180, 255, 255]))
        return np.sum(cv2.add(mask1, mask2) > 0) > 800
    except:
        return False


# --- STARTUP ---
print("🚀 Checking for Game Windows...")
TARGETS = get_target_windows()
num_accounts = len(TARGETS)

if num_accounts == 0:
    print("❌ No game windows found! Please open the game first.")
    exit()
elif num_accounts == 1:
    print(f"✅ Found 1 Account. Running in Single-Account Mode.")
else:
    print(f"✅ Found {num_accounts} Accounts. Running in Multi-Account Mode.")

# --- MAIN LOOP ---
while True:
    if keyboard.is_pressed("end"):
        break
    if not IS_RUNNING:
        time.sleep(0.5)
        continue

    for i, hwnd in enumerate(TARGETS):
        if not IS_RUNNING:
            break

        # التبديل فقط إذا كان هناك أكثر من حساب
        if num_accounts > 1:
            print(f"\n🔄 Switching to Account {i+1}...")
            win32gui.ShowWindow(hwnd, win32con.SW_RESTORE)
            shell.SendKeys("%")
            win32gui.SetForegroundWindow(hwnd)
            time.sleep(0.8)  # وقت استقرار الصورة

        # فحص الحالة
        if is_metin_alive():
            print(f"   - [Status] Working...")
            if num_accounts == 1:
                time.sleep(1)  # إذا كان حساب واحد، ننتظر قليلاً قبل الفحص القادم
        else:
            print(f"   - [Status] Searching...")
            scr = pyautogui.screenshot()
            frame = cv2.cvtColor(np.array(scr), cv2.COLOR_RGB2BGR)
            hsv = cv2.cvtColor(frame, cv2.COLOR_BGR2HSV)
            mask = cv2.inRange(hsv, LOWER_PINK, UPPER_PINK)
            contours, _ = cv2.findContours(
                mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE
            )

            attack_sent = False
            for cnt in contours:
                if cv2.contourArea(cnt) > MIN_AREA:
                    x, y, w, h = cv2.boundingRect(cnt)
                    target_x, target_y = x + w // 2, y + h // 2
                    pydirectinput.moveTo(target_x, target_y, duration=0.2)
                    pydirectinput.click()
                    print(f"   - [Action] Clicked on Metin!")
                    attack_sent = True
                    time.sleep(1.2)
                    break

            if not attack_sent:
                pydirectinput.mouseDown(button="right")
                pydirectinput.moveRel(250, 0, duration=0.3)
                pydirectinput.mouseUp(button="right")
                time.sleep(0.5)

    # إذا كان حساب واحد، لا نحتاج لانتظار طويل بين الدورات
    if num_accounts > 1:
        time.sleep(0.8)
    else:
        time.sleep(0.1)
