import cv2
import numpy as np
import pyautogui
import pydirectinput
import time

# --- CONFIGURATION ---
LOWER_PINK = np.array([135, 45, 45])
UPPER_PINK = np.array([180, 255, 255])
MIN_AREA = 500

# إحداثيات شريط دم الماتين (تأكد أنها تغطي منطقة الشريط الأحمر في أعلى الشاشة)
# [x_start, y_start, width, height]
HP_BAR_REGION = (350, 20, 600, 80)

pyautogui.FAILSAFE = False


def is_metin_alive():
    """التحقق من وجود شريط دم الماتين في أعلى الشاشة"""
    # نلتقط صورة لشريط الدم فقط
    scr = pyautogui.screenshot(region=HP_BAR_REGION)
    frame = cv2.cvtColor(np.array(scr), cv2.COLOR_RGB2BGR)
    hsv = cv2.cvtColor(frame, cv2.COLOR_BGR2HSV)

    # اللون الأحمر لشريط الدم (نطاقين للأحمر في HSV)
    mask1 = cv2.inRange(hsv, np.array([0, 150, 50]), np.array([10, 255, 255]))
    mask2 = cv2.inRange(hsv, np.array([170, 150, 50]), np.array([180, 255, 255]))
    red_mask = cv2.add(mask1, mask2)

    # إذا وجدنا كمية كافية من اللون الأحمر، فالماتين لا يزال موجوداً
    return np.sum(red_mask) > 300


def fast_scan():
    """مسح سريع جداً للعثور على الأهداف"""
    scr = pyautogui.screenshot()
    frame = cv2.cvtColor(np.array(scr), cv2.COLOR_RGB2BGR)
    h, w, _ = frame.shape

    roi_y, roi_x = int(h * 0.15), int(w * 0.1)
    search_area = frame[roi_y : h - int(h * 0.2), roi_x : w - int(w * 0.1)]

    hsv = cv2.cvtColor(search_area, cv2.COLOR_BGR2HSV)
    mask = cv2.inRange(hsv, LOWER_PINK, UPPER_PINK)

    contours, _ = cv2.findContours(mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
    targets = []

    for cnt in contours:
        if cv2.contourArea(cnt) > MIN_AREA:
            x, y, cw, ch = cv2.boundingRect(cnt)
            targets.append({"pos": (x + cw // 2 + roi_x, y + ch // 2 + roi_y)})

    return targets


def attack_and_confirm(target_pos):
    """الهجوم مع التأكد من شريط الدم"""
    print(f"🚀 Attacking target at {target_pos}")
    pydirectinput.moveTo(target_pos[0], target_pos[1])
    pydirectinput.click()

    # انتظار وقت الجري والبدء في الضرب
    time.sleep(3)

    print("⚔️ Checking HP bar...")
    attack_start = time.time()

    while time.time() - attack_start < 50:  # حد أقصى 50 ثانية
        pydirectinput.press("z")  # جمع

        # الفحص الحقيقي: هل شريط الدم موجود؟
        if not is_metin_alive():
            # ننتظر ثانية ونعيد الفحص للتأكد (تجنباً للرمش)
            time.sleep(1)
            if not is_metin_alive():
                print("✅ HP Bar gone. Metin destroyed!")
                break

        time.sleep(0.5)


# --- الحلقة الرئيسية ---
print("V33: HP-Aware System - Starting in 5s")
time.sleep(5)

while True:
    targets = fast_scan()

    if targets:
        # ترتيب الأهداف (يمكنك اختيار الأقرب)
        # سيهجم على الأول، ثم يعيد المسح ويجد الثاني
        attack_and_confirm(targets[0]["pos"])
        time.sleep(1)  # استراحة للجمع
    else:
        # دوران سريع للكاميرا للبحث
        print("🔍 Scanning...")
        pydirectinput.mouseDown(button="right")
        pydirectinput.moveRel(150, 0, duration=0.2)
        pydirectinput.mouseUp(button="right")
        # لا نضع sleep طويل هنا لكي يلحق يصور بسرعة وهو يلف
