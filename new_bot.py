import cv2
import numpy as np
import pyautogui
import pydirectinput
import time
import keyboard  # تحتاج لتثبيتها: python -m pip install keyboard

# --- CONFIGURATION ---
LOWER_PINK = np.array([135, 45, 45])
UPPER_PINK = np.array([180, 255, 255])
MIN_AREA = 500
HP_BAR_REGION = (350, 20, 600, 80)

pyautogui.FAILSAFE = False
IS_RUNNING = True  # متغير للتحكم في حالة البوت


def toggle_bot():
    global IS_RUNNING
    IS_RUNNING = not IS_RUNNING
    status = "▶️ Running" if IS_RUNNING else "⏸️ Paused"
    print(f"--- {status} ---")


# تسجيل الاختصار (F10 للتبديل بين الإيقاف والتشغيل)
keyboard.add_hotkey("f10", toggle_bot)


def is_metin_alive():
    """التحقق السريع من شريط الدم"""
    scr = pyautogui.screenshot(region=HP_BAR_REGION)
    frame = cv2.cvtColor(np.array(scr), cv2.COLOR_RGB2BGR)
    hsv = cv2.cvtColor(frame, cv2.COLOR_BGR2HSV)
    mask1 = cv2.inRange(hsv, np.array([0, 150, 50]), np.array([10, 255, 255]))
    mask2 = cv2.inRange(hsv, np.array([170, 150, 50]), np.array([180, 255, 255]))
    red_mask = cv2.add(mask1, mask2)
    return np.sum(red_mask) > 300


def fast_scan():
    """مسح وترتيب الأهداف حسب الأقرب لمركز الشاشة"""
    scr = pyautogui.screenshot()
    frame = cv2.cvtColor(np.array(scr), cv2.COLOR_RGB2BGR)
    h, w, _ = frame.shape
    center_x, center_y = w // 2, h // 2

    roi_y, roi_x = int(h * 0.15), int(w * 0.1)
    search_area = frame[roi_y : h - int(h * 0.2), roi_x : w - int(w * 0.1)]
    hsv = cv2.cvtColor(search_area, cv2.COLOR_BGR2HSV)
    mask = cv2.inRange(hsv, LOWER_PINK, UPPER_PINK)

    contours, _ = cv2.findContours(mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
    targets = []

    for cnt in contours:
        if cv2.contourArea(cnt) > MIN_AREA:
            x, y, cw, ch = cv2.boundingRect(cnt)
            tx, ty = x + cw // 2 + roi_x, y + ch // 2 + roi_y
            dist = np.sqrt((tx - center_x) ** 2 + (ty - center_y) ** 2)
            targets.append({"pos": (tx, ty), "dist": dist})

    targets.sort(key=lambda x: x["dist"])
    return targets


def attack_and_confirm(target_pos):
    """هجوم سريع مع انتقال فوري عند الكسر"""
    if not IS_RUNNING:
        return

    print(f"🚀 Moving to target: {target_pos}")
    pydirectinput.moveTo(target_pos[0], target_pos[1])
    pydirectinput.click()

    time.sleep(1.5)

    attack_start = time.time()
    while time.time() - attack_start < 45:
        # فحص إذا تم إيقاف البوت أثناء الضرب
        if not IS_RUNNING or keyboard.is_pressed("end"):
            break

        pydirectinput.press("z")

        if not is_metin_alive():
            time.sleep(0.2)
            if not is_metin_alive():
                print("✅ Target Down! Searching next...")
                break
        time.sleep(0.1)


# --- Main Loop ---
print("V34-Hotkey: Starting in 5s")
print("⌨️ Press 'F10' to Pause/Resume")
print("⌨️ Press 'End' to Quit completely")
time.sleep(5)

while True:
    # زر الخروج النهائي
    if keyboard.is_pressed("end"):
        print("🛑 Final Exit...")
        break

    if IS_RUNNING:
        targets = fast_scan()

        if targets:
            attack_and_confirm(targets[0]["pos"])
        else:
            print("🔍 Scanning area...")
            pydirectinput.mouseDown(button="right")
            pydirectinput.moveRel(200, 0, duration=0.1)
            pydirectinput.mouseUp(button="right")
            time.sleep(0.1)
    else:
        # وضع الانتظار عند الإيقاف المؤقت
        time.sleep(0.5)
