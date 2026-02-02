import cv2
import numpy as np
import pyautogui
import pydirectinput
import time
import keyboard

# --- CONFIGURATION ---
LOWER_PINK = np.array([135, 45, 45])
UPPER_PINK = np.array([180, 255, 255])

# الألوان التي استخرجتها لماتين الموت
LOWER_DEATH1 = np.array([0, 100, 80])
UPPER_DEATH1 = np.array([15, 200, 180])
LOWER_DEATH2 = np.array([140, 100, 10])
UPPER_DEATH2 = np.array([165, 160, 150])

# --- تعديلات الحجم والمنطقة ---
MIN_AREA = 1500  # رفعنا المساحة ليتجاهل لمعان الدرع الصغير
HP_BAR_REGION = (350, 20, 600, 80)
IS_RUNNING = True

pyautogui.FAILSAFE = False


def toggle_bot():
    global IS_RUNNING
    IS_RUNNING = not IS_RUNNING
    print(f"--- Bot Status: {'Running' if IS_RUNNING else 'Paused'} ---")


keyboard.add_hotkey("f10", toggle_bot)


def is_metin_alive():
    try:
        scr = pyautogui.screenshot(region=HP_BAR_REGION)
        frame = cv2.cvtColor(np.array(scr), cv2.COLOR_RGB2BGR)
        hsv = cv2.cvtColor(frame, cv2.COLOR_BGR2HSV)
        mask1 = cv2.inRange(hsv, np.array([0, 150, 50]), np.array([10, 255, 255]))
        mask2 = cv2.inRange(hsv, np.array([170, 150, 50]), np.array([180, 255, 255]))
        red_mask = cv2.add(mask1, mask2)
        return np.sum(red_mask) > 300
    except:
        return False


def fast_scan():
    scr = pyautogui.screenshot()
    frame = cv2.cvtColor(np.array(scr), cv2.COLOR_RGB2BGR)
    h, w, _ = frame.shape
    center_x, center_y = w // 2, h // 2

    # تحديد منطقة "ممنوع الضغط" وسط الشاشة (مكان الشخصية)
    # 100 بكسل حول المركز
    dead_zone_x = (center_x - 80, center_x + 80)
    dead_zone_y = (center_y - 80, center_y + 120)

    roi_y, roi_x = int(h * 0.1), int(w * 0.05)
    search_area = frame[roi_y : h - int(h * 0.1), roi_x : w - int(w * 0.05)]
    hsv = cv2.cvtColor(search_area, cv2.COLOR_BGR2HSV)

    mask_pink = cv2.inRange(hsv, LOWER_PINK, UPPER_PINK)
    mask_d1 = cv2.inRange(hsv, LOWER_DEATH1, UPPER_DEATH1)
    mask_d2 = cv2.inRange(hsv, LOWER_DEATH2, UPPER_DEATH2)
    combined = cv2.add(mask_pink, cv2.add(mask_d1, mask_d2))

    # تنقية لربط أجزاء الماتين الكبيرة
    kernel = np.ones((5, 5), np.uint8)
    combined = cv2.dilate(combined, kernel, iterations=2)

    contours, _ = cv2.findContours(combined, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
    targets = []

    for cnt in contours:
        area = cv2.contourArea(cnt)
        if area > MIN_AREA:  # الفلتر الأول: الحجم الكبير فقط
            x, y, cw, ch = cv2.boundingRect(cnt)
            tx, ty = x + cw // 2 + roi_x, y + ch // 2 + roi_y

            # الفلتر الثاني: تجاهل أي شيء يقع فوق الشخصية مباشرة
            if (
                dead_zone_x[0] < tx < dead_zone_x[1]
                and dead_zone_y[0] < ty < dead_zone_y[1]
            ):
                continue

            dist = np.sqrt((tx - center_x) ** 2 + (ty - center_y) ** 2)
            targets.append({"pos": (tx, ty), "dist": dist})

    targets.sort(key=lambda x: x["dist"])
    return targets


def attack_and_confirm(target_pos):
    if not IS_RUNNING:
        return
    pydirectinput.moveTo(target_pos[0], target_pos[1])
    pydirectinput.click()
    time.sleep(1.5)

    start = time.time()
    while time.time() - start < 55:
        if not IS_RUNNING or keyboard.is_pressed("end"):
            break
        pydirectinput.press("z")
        if not is_metin_alive():
            time.sleep(0.3)
            if not is_metin_alive():
                break
        time.sleep(0.1)


print("V43: Anti-Character Logic - Ready")
print("⌨️ F10: Pause | End: Quit")
time.sleep(5)

while True:
    if keyboard.is_pressed("end"):
        break
    if IS_RUNNING:
        found = fast_scan()
        if found:
            attack_and_confirm(found[0]["pos"])
        else:
            pydirectinput.mouseDown(button="right")
            pydirectinput.moveRel(250, 0, duration=0.1)
            pydirectinput.mouseUp(button="right")
            time.sleep(0.1)
    else:
        time.sleep(0.5)
