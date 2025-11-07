import time
import os, sys, math, json, threading, asyncio
import cv2
import numpy as np
import websockets
import Jetson.GPIO as GPIO
from websockets.exceptions import ConnectionClosed
from smbus2 import SMBus
import functions_jetson as fj

# -------------------- 路徑與工具 --------------------
sys.path.append(os.path.abspath(os.path.dirname(__file__)))
from masks import rMagenta, rRed, rGreen, rBlue, rOrange, rBlack
from functions_jetson import *

# =================== BNO055 ===================
BNO055_ADDRESS = 0x28
BNO055_OPR_MODE_ADDR = 0x3D
BNO055_PWR_MODE_ADDR = 0x3E
BNO055_ID = 0xA0
BNO055_CHIP_ID_ADDR = 0x00
BNO055_CALIB_STAT_ADDR = 0x35
OPERATION_MODE_CONFIG = 0x00
OPERATION_MODE_NDOF = 0x0C
BNO055_EULER_H_LSB = 0x1A
BNO055_BUS = 7  # Jetson I2C bus（請按實機調整）

# ====== 角度與限幅 Helper ======
def clamp(v, lo, hi):
    return lo if v < lo else (hi if v > hi else v)

MECH_SIGN = +1
straight_const = 90  # ★伺服中立角

def rel_to_servo_deg(rel_deg: int) -> int:
    servo = int(round(straight_const + MECH_SIGN * rel_deg))
    return clamp(servo, 0, 180)

def LEFT(deg=55):   return -abs(int(deg))
def RIGHT(deg=55):  return +abs(int(deg))

def ang_diff_deg(target_deg: float, current_deg: float) -> float:
    return ((target_deg - current_deg + 180.0) % 360.0) - 180.0

# ---- Prebuilt morphology kernels (避免每圈建立) ----
K5 = cv2.getStructuringElement(cv2.MORPH_RECT, (5,5))
K3 = cv2.getStructuringElement(cv2.MORPH_RECT, (3,3))

# ======================================================
# WebSocket Hub（取代 UART）
# ======================================================
WS_HOST = "0.0.0.0"
WS_PORT = 8765

def pwm_to_percent(pwm: int) -> int:
    pct = round((pwm - 1500) / 180 * 100)
    return max(-100, min(100, pct))

class WsHub:
    def __init__(self, host="0.0.0.0", port=8765):
        self.host = host
        self.port = port
        self.clients = set()
        self._loop = None
        self._thread = None
        self._stop_evt = threading.Event()
        self.started_evt = threading.Event()
        self._last_angle_rel = 0
        self._last_angle_servo = rel_to_servo_deg(0)
        self._last_speed_pct = 0

    def start(self):
        self._thread = threading.Thread(target=self._run_loop, daemon=True)
        self._thread.start()

    def stop(self):
        self._stop_evt.set()
        if self._loop:
            asyncio.run_coroutine_threadsafe(self._shutdown(), self._loop)
        if self._thread:
            self._thread.join(timeout=1)

    def wait_for_start(self, timeout=None):
        return self.started_evt.wait(timeout)

    def write(self, value):
        if isinstance(value, float) and value < 10.0:
            time.sleep(float(value))
            return
        if isinstance(value, tuple) and len(value) == 2 and value[0] == "S":
            self._last_speed_pct = int(value[1])
        elif isinstance(value, int) and value >= 1000:
            self._last_speed_pct = pwm_to_percent(value)
        else:
            rel = int(value)
            rel = clamp(rel, -180, 180)
            self._last_angle_rel = rel
            self._last_angle_servo = rel_to_servo_deg(rel)
        self.broadcast(f"M,{self._last_angle_rel},{self._last_speed_pct}\n")

    def multi_write(self, seq):
        for v in seq:
            self.write(v)

    def stop_car(self):
        self._last_angle_rel = 0
        self._last_angle_servo = rel_to_servo_deg(0)
        self._last_speed_pct = 0
        self.broadcast("STOP\n")

    def broadcast(self, text):
        if self._loop:
            asyncio.run_coroutine_threadsafe(self._async_broadcast(text), self._loop)

    # ★可附加額外欄位，方便發給 Pico W
    def broadcast_json(self, leftArea, rightArea, yaw, angle, speed, **extra):
        msg = {
            "leftArea": int(leftArea),
            "rightArea": int(rightArea),
            "yaw": float(yaw),
            "angle": int(angle),
            "speed": int(speed),
        }
        if extra:
            msg.update(extra)
        self.broadcast(json.dumps(msg) + "\n")

    def _run_loop(self):
        self._loop = asyncio.new_event_loop()
        asyncio.set_event_loop(self._loop)
        self._loop.run_until_complete(self._main())

    async def _main(self):
        async def handler(ws):
            self.clients.add(ws)
            print("WS client connected:", ws.remote_address)
            try:
                await ws.send('{"from":"jetson","status":"ready"}\n')
                async for msg in ws:
                    if isinstance(msg, (bytes, bytearray)):
                        msg = msg.decode("utf-8", errors="ignore")
                    if "START" in msg:
                        self.started_evt.set()
            except ConnectionClosed as e:
                print(f"WS disconnected: {e.code} {e.reason}")
            finally:
                self.clients.discard(ws)

        async with websockets.serve(
            handler, self.host, self.port,
            ping_interval=None, compression=None, max_size=None, close_timeout=1.0
        ):
            print(f"WebSocket server at ws://{self.host}:{self.port}")
            while not self._stop_evt.is_set():
                await asyncio.sleep(0.1)

    async def _async_broadcast(self, text):
        dead = []
        for ws in list(self.clients):
            try:
                await ws.send(text)
            except Exception:
                dead.append(ws)
        for ws in dead:
            self.clients.discard(ws)

    async def _shutdown(self):
        for ws in list(self.clients):
            try:
                await ws.close()
            except:
                pass
        self.clients.clear()

# 啟動 WS 並替換原 UART API
ws_hub = WsHub(WS_HOST, WS_PORT)
ws_hub.start()
write          = ws_hub.write
multi_write    = ws_hub.multi_write
wait_for_start = ws_hub.wait_for_start
stop_car       = ws_hub.stop_car

# ===== 立刻停車的輔助 =====
t = 0
class HaltRun(Exception): pass
def inc_t():
    global t
    t += 1
    print(f"[t++] -> {t}")

# ======================================================
# 影像 / 演算法 Helper
# ======================================================
def gstreamer_csi_pipeline(sensor_id=0, capture_width=640, capture_height=480,
                           display_width=640, display_height=480,
                           framerate=30, flip_method=0):
    return (
        f"nvarguscamerasrc sensor-id={sensor_id} ! "
        f"video/x-raw(memory:NVMM), width={capture_width}, height={capture_height}, "
        f"format=NV12, framerate={framerate}/1 ! "
        f"nvvidconv flip-method={flip_method} ! "
        f"video/x-raw, width={display_width}, height={display_height}, format=BGRx ! "
        f"videoconvert ! video/x-raw, format=BGR ! "
        f"appsink max-buffers=1 drop=true sync=false"
    )

class Pillar:
    def __init__(self, area, dist, x, y, target):
        self.area = area
        self.dist = dist
        self.x = x
        self.y = y
        self.target = target
        self.w = 0
        self.h = 0
    def setDimentions(self, w, h):
        self.w = w
        self.h = h

def _contours_to_mask(contours, size):
    mask = np.zeros(size, dtype=np.uint8)
    if contours:
        cv2.drawContours(mask, contours, -1, 255, thickness=cv2.FILLED)
    return mask

def _geom_filter(contours, w, *, edge_margin=18, min_area=110, max_tilt=26):
    kept = []
    for c in contours:
        area = cv2.contourArea(c)
        if area < min_area: continue
        (cx, _), (cw, ch), theta = cv2.minAreaRect(c)
        tilt = abs(theta)
        tilt = (90 - tilt) if tilt > 45 else tilt
        near_edge = (cx < edge_margin) or (cx > (w - edge_margin))
        if near_edge and tilt <= max_tilt:
            kept.append(c)
    return kept

def wall_contours_no_lines(img_lab, ROI, img_bgr=None):
    x1, y1, x2, y2 = ROI
    h, w = y2 - y1, x2 - x1
    c_black = find_contours(img_lab, rBlack, ROI)
    m_black = _contours_to_mask(c_black, (h, w))
    m = cv2.morphologyEx(m_black, cv2.MORPH_CLOSE, K5, iterations=1)
    m = cv2.morphologyEx(m,     cv2.MORPH_OPEN,  K3, iterations=1)
    contours, _ = cv2.findContours(m, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
    kept = _geom_filter(contours, w)
    return kept

def dominant_vertical_area(contours, ROI, max_tilt=26):
    if not contours: return 0
    best = 0
    for c in contours:
        area = cv2.contourArea(c)
        if area <= 0: continue
        _, (w, h), theta = cv2.minAreaRect(c)
        tilt = abs(theta)
        tilt = (90 - tilt) if tilt > 45 else tilt
        if tilt <= max_tilt: best = max(best, area)
    return best

def find_best_pillar(contours, target, colour, img_lab):
    global s, leftArea, rightArea, maxDist, tempParking, speed, endConst
    num_p, best, best_dist = 0, None, math.inf
    for cnt in contours:
        area = cv2.contourArea(cnt)
        if ((area > 150 and colour == "red") or
            (area > 200 and colour == "green") or
            (area > 100 and colour == "red" and tempParking)):
            approx = cv2.approxPolyDP(cnt, 0.01 * cv2.arcLength(cnt, True), True)
            x, y, w, h = cv2.boundingRect(approx)
            x += ROI3[0] + w // 2
            y += ROI3[1] + h
            temp_dist = round(math.dist([x, y], [320, 480]), 0)
            if 160 < temp_dist < 380: num_p += 1
            if (((area > 6500 and target == redTarget) or (area > 8000 and target == greenTarget))
                and (not tempParking) and is_moving()):
                multi_write([0, 0.1, -40, 0.5, ("S", speed)])
                if s != 0: s += 1.5
            if((target == greenTarget and (leftArea > 13000 or rightArea > 13000 or temp_dist > maxDist)) or
               (target == redTarget  and (leftArea > 13000 or rightArea > 15000 or temp_dist > maxDist))):
                continue
            if temp_dist < best_dist:
                best_dist = temp_dist
                best = Pillar(area, temp_dist, x, y, target)
                best.setDimentions(w, h)
    return best, num_p

def draw_roi_boxes(img, rois, color=(255, 204, 0), thickness=2):
    for i, R in enumerate(rois, 1):
        if R is None or len(R) != 4:
            continue
        x1, y1, x2, y2 = R
        if x1 == x2 == y1 == y2 == 0:
            continue
        cv2.rectangle(img, (int(x1), int(y1)), (int(x2), int(y2)), color, thickness)
        cv2.putText(img, f"ROI{i}", (int(x1) + 4, int(y1) + 18),
            cv2.FONT_HERSHEY_SIMPLEX, 0.6, color, 2)

def draw_contours_list(img, contours, roi, color, label=None, thickness=2, show_bbox=True):
    if contours is None or len(contours) == 0 or roi is None or len(roi) != 4:
        return
    ox, oy = int(roi[0]), int(roi[1])
    for c in contours:
        c2 = c + np.array([[[ox, oy]]])
        cv2.drawContours(img, [c2], -1, color, thickness)
        if show_bbox:
            x, y, w, h = cv2.boundingRect(c2)
            cv2.rectangle(img, (x, y), (x + w, y + h), color, 1)
    if label:
        cv2.putText(img, label, (ox + 4, oy + 16), cv2.FONT_HERSHEY_SIMPLEX, 0.5, color, 2)

# ---- 在 ROI 區塊內印文字（黑邊+指定色）
def _put_text_in_roi(img, roi, text, line_idx=0, color=(255, 255, 255)):
    x1, y1, x2, y2 = map(int, roi)
    x = x1 + 8
    y = y1 + 24 + 22 * int(line_idx)
    cv2.putText(img, text, (x, y), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 0, 0), 3)
    cv2.putText(img, text, (0 + x, y), cv2.FONT_HERSHEY_SIMPLEX, 0.6, color, 1)

# ---- 取某 ROI 內洋紅色最大輪廓的面積/中心/外接框
def _largest_magenta_in_roi(img_lab, roi):
    if roi is None or len(roi) != 4:
        return 0, None, None
    x1, y1, x2, y2 = map(int, roi)
    contours = find_contours(img_lab, rMagenta, roi)
    if not contours:
        return 0, None, None
    c = max(contours, key=cv2.contourArea)
    area = int(cv2.contourArea(c))
    M = cv2.moments(c)
    if M["m00"] > 0:
        cx_local = int(M["m10"] / M["m00"])
        cy_local = int(M["m01"] / M["m00"])
    else:
        x, y, w, h = cv2.boundingRect(c)
        cx_local = x + w // 2
        cy_local = y + h // 2
    cx = cx_local + x1
    cy = cy_local + y1
    x, y, w, h = cv2.boundingRect(c)
    bbox = (x + x1, y + y1, w, h)
    return area, (cx, cy), bbox

# ---------- BNO055 I2C ----------
def write_byte(bus, reg, value):
    bus.write_byte_data(BNO055_ADDRESS, reg, value)

def read_bytes(bus, reg, length):
    return bus.read_i2c_block_data(BNO055_ADDRESS, reg, length)

def read_chip_id(bus):
    return bus.read_byte_data(BNO055_ADDRESS, BNO055_CHIP_ID_ADDR)

def read_calibration_status(bus):
    calib = bus.read_byte_data(BNO055_ADDRESS, BNO055_CALIB_STAT_ADDR)
    sys_cal = (calib >> 6) & 0x03
    gyro_cal = (calib >> 4) & 0x03
    accel_cal = (calib >> 2) & 0x03
    mag_cal = calib & 0x03
    return sys_cal, gyro_cal, accel_cal, mag_cal

def init_bno055(bus, wait_for_calibration=True):
    led_off()
    print("🔧 初始化 BNO055...")
    try:
        chip_id = read_chip_id(bus)
        if chip_id != BNO055_ID:
            print(f" 無法找到 BNO055 (ID: 0x{chip_id:X}, 期望: 0x{BNO055_ID:X})")
            return False
        print(f" 找到 BNO055 (ID: 0x{chip_id:X})")
    except Exception as e:
        print(f" 讀取晶片 ID 失敗: {e}")
        print(f"   請檢查 I2C 總線編號是否正確 (當前: {BNO055_BUS})")
        return False
    write_byte(bus, BNO055_OPR_MODE_ADDR, OPERATION_MODE_CONFIG)
    time.sleep(0.025)
    write_byte(bus, BNO055_PWR_MODE_ADDR, 0x00)
    time.sleep(0.01)
    write_byte(bus, BNO055_OPR_MODE_ADDR, OPERATION_MODE_NDOF)
    print(" 等待感測器穩定...")
    time.sleep(0.5)
    if wait_for_calibration:
        print(" 等待陀螺儀校準...")
        timeout = 2
        start_time = time.time()
        while time.time() - start_time < timeout:
            sys_cal, gyro_cal, accel_cal, mag_cal = read_calibration_status(bus)
            print(f"   校準狀態 - Sys:{sys_cal} Gyro:{gyro_cal} Accel:{accel_cal} Mag:{mag_cal}")
            if gyro_cal >= 1:
                print(" 陀螺儀校準完成")
                break
            time.sleep(0.1)
        else:
            print(" 陀螺儀校準超時,但仍繼續使用")
    print(" BNO055 初始化完成")
    return True

def read_heading(bus, samples=1):
    readings = []
    for _ in range(samples):
        try:
            data = read_bytes(bus, BNO055_EULER_H_LSB, 2)
            heading = int.from_bytes(data, byteorder='little', signed=True) / 16.0
            readings.append(heading)
            time.sleep(0.005)
        except Exception:
            continue
    if readings:
        return sum(readings) / len(readings)
    return 0.0

# ---- IMU background updater ----
relative_heading = 0.0
def imu_loop(bus, zero, dt=0.05):
    global relative_heading
    while True:
        h = read_heading(bus, samples=1)
        rel = h - zero
        if rel > 180: rel -= 360
        elif rel < -180: rel += 360
        relative_heading = rel
        time.sleep(dt)

# =================== RGB（只提供 show/off，支援共陽/共陰） ===================
class RgbLED:
    def __init__(self, pin_r=13, pin_g=12, pin_b=22, common_anode=False):
        # 預設 BCM: 13/12/22 ≈ 測試檔 BOARD 33/32/15
        self.r, self.g, self.b = pin_r, pin_g, pin_b
        self.common_anode = common_anode
        GPIO.setup(self.r, GPIO.OUT, initial=self._logic(False))
        GPIO.setup(self.g, GPIO.OUT, initial=self._logic(False))
        GPIO.setup(self.b, GPIO.OUT, initial=self._logic(False))

    def _logic(self, on: bool):
        # 共陽: 亮→LOW；共陰: 亮→HIGH
        if self.common_anode:
            return GPIO.LOW if on else GPIO.HIGH
        else:
            return GPIO.HIGH if on else GPIO.LOW

    def _drive(self, r, g, b):
        GPIO.output(self.r, self._logic(bool(r)))
        GPIO.output(self.g, self._logic(bool(g)))
        GPIO.output(self.b, self._logic(bool(b)))

    def show(self, color: str):
        c = (color or "off").lower()
        table = {
            "off": (0,0,0),
            "red": (1,0,0),
            "green": (0,1,0),
            "blue": (0,0,1),
            "orange": (1,1,1),  # 近似黃 (R+G)
        }
        self._drive(*table.get(c, (0,0,0)))

    def off(self):
        self._drive(0,0,0)

#===========================================================
GPIO.setmode(GPIO.BCM)
GPIO.setwarnings(False)
LED_PIN = 21
BUTTON_PIN = 18
GPIO.setup(LED_PIN, GPIO.OUT)
GPIO.setup(BUTTON_PIN, GPIO.IN, pull_up_down=GPIO.PUD_DOWN)

# === 初始化 RGB ===
# 若 LED 為共陽，設 common_anode=True；共陰用 False（預設）
rgb = RgbLED(pin_r=13, pin_g=12, pin_b=22, common_anode=False)

def led_on(): GPIO.output(LED_PIN, GPIO.HIGH)
def led_off(): GPIO.output(LED_PIN, GPIO.LOW)

def wait_for_button_press():
    led_on()
    print(" 請按下按鈕以開始！")
    while GPIO.input(BUTTON_PIN) == GPIO.LOW:
        time.sleep(0.05)
    print(" 按鈕被按下，開始執行！")
    time.sleep(0.3)

# ======================================================
# Main
# ======================================================
if __name__ == "__main__":
    bno_bus = None
    cap = None
    try:

        bno_bus = SMBus(BNO055_BUS)
        if not init_bno055(bno_bus, wait_for_calibration=True):
            print(" BNO055 初始化失敗,請檢查:")
            print("   1. I2C 總線編號 (當前: BNO055_BUS = 7)")
            print("   2. 硬體接線是否正確")
            print("   3. 使用 'sudo i2cdetect -y -r 7' 檢查裝置")
            sys.exit(2)
        print(" 等待數據完全穩定...")
        time.sleep(1)
        zero_heading = read_heading(bno_bus, samples=3)
        print(f" 歸零完成,初始角度: {zero_heading:.2f}° (將作為 0° 基準)")
        threading.Thread(target=imu_loop, args=(bno_bus, zero_heading, 0.05), daemon=True).start()

        cap = cv2.VideoCapture(gstreamer_csi_pipeline(), cv2.CAP_GSTREAMER)
        if not cap.isOpened():
            print("Camera open failed")
            sys.exit(1)
        try:
            cap.set(cv2.CAP_PROP_BUFFERSIZE, 1)
        except Exception:
            pass

        # ---- 狀態/參數初始化 ----
        eTurnMethod = ""
        lapsComplete = False
        redTarget, greenTarget = 120, 510
        lastTarget = 0
        tempParking = False
        sTime = 0
        s = 0
        endConst = 50
        lotType = "light"
        turnDir = "none"
        pillarAtStart = -1
        t = 0
        t2 = 0
        B = 0
        rTurn = False
        lTurn = False
        tSignal = False

        ROI1 = [0, 180, 330, 245]
        ROI2 = [330, 180, 640, 245]
        ROI3 = [redTarget - 70, 45, greenTarget + 70, 360]
        ROI4 = [200, 305, 440, 350]
        ROI5 = [0, 0, 0, 0]
        ROI6 = [0, 0, 0, 0]
        tArea = 0
        mag6_area = 0
        mag6_center = 0
        mag6_bbox = 0

        kp, kd = 0.02, 0.03
        cKp, cKd, cy = 0.15, 0.3, 0.28

        angle = 0
        prevAngle = angle
        tDeviation = 50
        sharpLeft = LEFT(tDeviation)
        sharpRight = RIGHT(tDeviation)
        speed, reverseSpeed = 55, -40
        startArea = 4000
        aDiff = 0
        prevDiff = 0
        prevError = 0
        maxDist = 370
        leftArea = 0
        rightArea = 0
        error= 0
        ERROR = 0
        ERROR_1 = 0
        count = 0
        c = 0

        # ===== 計圈線之門檻（也用於 LED 遲滯）=====
        BLUE_ON_THRESH    = 90
        BLUE_OFF_THRESH   = 60
        BLUE_COOLDOWN_SEC = 2
        blue_next_allowed_time = 0
        blue_armed = True

        ORANGE_ON_THRESH    = 90
        ORANGE_OFF_THRESH   = 60
        ORANGE_COOLDOWN_SEC = 2
        orange_next_allowed_time = 0
        orange_armed = True

        wait_for_button_press()
        write(("S", speed))
        write(0)
        time.sleep(0.5)

        debug = ("debug" in "".join(sys.argv).lower())
        pTimer = time.time()
        start = False

        TX_M_PERIOD    = 0.02
        TX_JSON_PERIOD = 0.02  # 20Hz
        last_tx_m      = 0.0
        last_tx_json   = 0.0

        last_angle_sent = None
        last_angle_tx_time = 0.0
        ANGLE_TX_MIN_DT = 0.02

        log_every = 10
        frame_id = 0

        # ===== LED 狀態（藍/橘）＋ 遲滯 =====
        led_state = "off"   # "blue" / "orange" / "green" / "red" / "off"
        blue_seen = False
        orange_seen = False
        last_led_log = 0.0

        # ==== 起始左右判斷 ====
        a = 0
        start_turn = 0
        while a == 0:
            rightArea = leftArea = areaFront = tArea = 0
            ok, img = cap.read()
            if not ok:
                continue
            img_lab = cv2.cvtColor(img, cv2.COLOR_BGR2Lab)
            img_lab = cv2.GaussianBlur(img_lab, (3,3), 0)

            contours_left  = pOverlap(img_lab, ROI1)
            contours_right = pOverlap(img_lab, ROI2)
            leftArea  = max_contour(contours_left,  ROI1)[0]
            rightArea = max_contour(contours_right, ROI2)[0]

            if leftArea - rightArea > 0:
                print("右轉"); start_turn = 1; a = 1
            else:
                print("左轉"); start_turn = 2; a = 1

        write(start_turn)

        # ★依起跑方向決定用哪種顏色計圈：turn==1→橘線；turn==2→藍線
        use_color_for_lap = "orange" if start_turn == 1 else "blue"
        print("[LapCounter] using:", use_color_for_lap)

        # ==== 等待柱子顏色判斷 ====
        color = 0
        detect_start = time.time()
        TIMEOUT = 2.0
        while a == 1:
            ok, img = cap.read()
            if not ok:
                continue
            img_lab = cv2.cvtColor(img, cv2.COLOR_BGR2Lab)
            img_lab = cv2.GaussianBlur(img_lab, (3,3), 0)

            contours_left  = pOverlap(img_lab, ROI1, True)
            contours_right = pOverlap(img_lab, ROI2, True)
            leftArea  = max_contour(contours_left,  ROI1)[0]
            rightArea = max_contour(contours_right, ROI2)[0]

            contours_red   = find_contours(img_lab, rRed,   ROI3)
            contours_green = find_contours(img_lab, rGreen, ROI3)
            best_red,   _ = find_best_pillar(contours_red,   redTarget,   "red",   img_lab)
            best_green, _ = find_best_pillar(contours_green, greenTarget, "green", img_lab)
            candidates = [p for p in (best_red, best_green) if p is not None]
            cPillar = min(candidates, key=lambda P: P.dist) if candidates else Pillar(0, 1000000, 0, 0, 0)
            seen_green_wait = (cPillar.target == greenTarget and cPillar.area > 0)
            seen_red_wait   = (cPillar.target == redTarget   and cPillar.area > 0)

            # === RGB：看到綠亮綠；看到紅亮紅；其他關燈（等待階段）===
            if seen_green_wait:
                rgb.show("green")
            elif seen_red_wait:
                rgb.show("red")
            else:
                rgb.off()

            if start_turn == 2:
                if seen_green_wait: color = 1; print("green"); a = 2
                elif seen_red_wait: color = 2; print("red"); a = 2
                elif time.time() - detect_start > TIMEOUT: color = 3; a = 2
            else:
                if seen_green_wait: color = 4; print("green"); a = 2
                elif seen_red_wait: color = 5; print("red"); a = 2
                elif time.time() - detect_start > TIMEOUT: color = 6; a = 2

        print(color)
        write(color)
        time2 = time.time()
        while a == 2:
            while time.time() - time2 < 4.5:
                print(time.time() - time2)
            a=3

        # =================== 主迴圈 ===================
        try:
            while True:
                fps_start = time.time()

                # 取影像
                ok, img = cap.read()
                if not ok:
                    continue
                img_lab = cv2.cvtColor(img, cv2.COLOR_BGR2Lab)
                img_lab = cv2.GaussianBlur(img_lab, (3,3), 0)

                # ROI5 轉彎補強
                contours_turn, contours_turn_m = [], []
                if ROI5[0] != 0:
                    contours_turn   = find_contours(img_lab, rBlack,   ROI5)
                    contours_turn_m = find_contours(img_lab, rMagenta, ROI5)
                    tArea = max_contour(contours_turn, ROI5)[0] + max_contour(contours_turn_m, ROI5)[0]

                # 左右牆
                contours_left  = pOverlap(img_lab, ROI1, True)
                contours_right = pOverlap(img_lab, ROI2, True)
                leftArea  = max_contour(contours_left, ROI1)[0]
                rightArea = max_contour(contours_right, ROI2)[0]

                # 前方黑
                contours_parking = find_contours(img_lab, rBlack, ROI4)
                areaFront = max_contour(contours_parking, ROI4)[0]

                # 紅/綠柱
                contours_red   = find_contours(img_lab, rRed,   ROI3)
                contours_green = find_contours(img_lab, rGreen, ROI3)

                # 角落藍/橘線
                contours_blue   = find_contours(img_lab, rBlue,   ROI4)
                contours_orange = find_contours(img_lab, rOrange, ROI4)
                maxO = max_contour(contours_orange,  ROI4)[0]
                maxB = max_contour(contours_blue,    ROI4)[0]

                # ★依 turn 選色偵測計圈（原邏輯保持）
                now_ts = time.time()
                if use_color_for_lap == "blue":
                    if maxB <= BLUE_OFF_THRESH and not blue_armed:
                        blue_armed = True
                    if maxB >= BLUE_ON_THRESH and blue_armed and now_ts >= blue_next_allowed_time:
                        blue_armed = False
                        blue_next_allowed_time = now_ts + BLUE_COOLDOWN_SEC
                        inc_t()
                else:
                    if maxO <= ORANGE_OFF_THRESH and not orange_armed:
                        orange_armed = True
                    if maxO >= ORANGE_ON_THRESH and orange_armed and now_ts >= orange_next_allowed_time:
                        orange_armed = False
                        orange_next_allowed_time = now_ts + ORANGE_COOLDOWN_SEC
                        inc_t()

                if t >= 13:
                    # ===== ROI6 洋紅偵測（保持原本）=====
                    ROI6 = [0, 45, 640, 480]
                    mag6_area, mag6_center, mag6_bbox = _largest_magenta_in_roi(img_lab, ROI6)
                    if count == 0:
                        stop_car()
                        led_off()

                # ========== 常規導柱 / 牆循計算 ==========
                best_red,   _ = find_best_pillar(contours_red,   redTarget,   "red",   img_lab)
                best_green, _ = find_best_pillar(contours_green, greenTarget, "green", img_lab)
                candidates = [p for p in (best_red, best_green) if p is not None]
                cPillar = min(candidates, key=lambda P: P.dist) if candidates else Pillar(0, 1000000, 0, 0, 0)

                if t == 0 and cPillar.area > startArea:
                    startArea = cPillar.area
                    startTarget = cPillar.target

                if turnDir == "none":
                    if maxO > 110:
                        turnDir = "right"
                    elif maxB > 110:
                        turnDir = "left"

                if (turnDir == "right" and maxO > 100) or (turnDir == "left" and maxB > 100):
                    t2 = t
                    if t2 == 7 and not pillarAtStart:
                        ROI3[1] = 110
                    if cPillar.area != 0 and ((leftArea > 1000 and turnDir == "left") or (rightArea > 1000 and turnDir == "right")):
                        ROI5 = [270, 110, 370, 150]
                    if turnDir == "right":
                        rTurn = True
                    else:
                        lTurn = True
                    if t == 0 and pillarAtStart == -1:
                        pillarAtStart = True if ((startArea > 2000 and startTarget == greenTarget) or (startArea > 1500 and startTarget == redTarget)) else False
                    tSignal = True
                elif (turnDir == "left" and maxO > 100) or (turnDir == "right" and maxB > 100):
                    if t2 == 11:
                        s = 2
                        sTime = time.time()

                # 舵角（一般循跡）
                if count == 0:
                    if cPillar.area == 0:
                        aDiff = leftArea-rightArea
                        angle = int(aDiff*kp + (aDiff - prevDiff)*kd)
                        angle = clamp(angle, sharpLeft, sharpRight)
                        prevDiff = aDiff
                    else:
                        error = cPillar.x - cPillar.target
                        angle = int(0 + error*cKp + (error - prevError)*cKd)
                        angle = clamp(angle, sharpLeft, sharpRight)
                        if cPillar.target == greenTarget and cPillar.x > 320 and cPillar.area > 1000:
                            lastTarget = greenTarget
                        elif cPillar.target == redTarget and cPillar.x < 320 and cPillar.area > 1000:
                            lastTarget = redTarget
                        prevError = error
                    frame_id += 1
                    if frame_id % log_every == 0:
                        print(t, lTurn, rTurn, leftArea, rightArea, cPillar.target, angle, f"{relative_heading:.2f}",
                              "mag6:", mag6_area, mag6_center)

                # 首次輸出速度與角度
                if not start:
                    multi_write([("S", speed), 0.03, angle])
                    start = True

                # ====== 傳輸限頻 ======
                now = time.time()
                if (last_angle_sent is None or angle != last_angle_sent) and (now - last_angle_tx_time >= ANGLE_TX_MIN_DT):
                    write(angle)
                    last_angle_sent = angle
                    last_angle_tx_time = now

                # ====== JSON 遙測 ======
                if now - last_tx_json >= TX_JSON_PERIOD:
                    m_area = int(mag6_area) if mag6_area > 0 else 0
                    m_cx = int(mag6_center[0]) if mag6_center else -1
                    m_cy = int(mag6_center[1]) if mag6_center else -1

                    ws_hub.broadcast_json(
                        leftArea=leftArea,
                        rightArea=rightArea,
                        yaw=relative_heading,
                        angle=angle,
                        speed=ws_hub._last_speed_pct,
                        magArea=m_area,
                        magCX=m_cx,
                        magCY=m_cy
                    )
                    last_tx_json = now

                # ====== RGB：線條優先（藍→橘→綠→紅→關）＋ 遲滯 ======
                # 用與計圈相同的門檻做遲滯：超過 ON 視為看到；低於 OFF 視為沒看到
                if maxB >= BLUE_ON_THRESH:
                    blue_seen = True
                elif maxB <= BLUE_OFF_THRESH:
                    blue_seen = False

                if maxO >= ORANGE_ON_THRESH:
                    orange_seen = True
                elif maxO <= ORANGE_OFF_THRESH:
                    orange_seen = False

                # 優先：藍 / 橘（線條） -> 綠 / 紅（柱子） -> 關
                if blue_seen:
                    target_led = "blue"
                elif orange_seen:
                    target_led = "orange"
                else:
                    seen_green = (best_green is not None and best_green.area > 0)
                    seen_red   = (best_red   is not None and best_red.area   > 0)
                    if seen_green:
                        target_led = "green"
                    elif seen_red:
                        target_led = "red"
                    else:
                        target_led = "off"

                if target_led != led_state:
                    rgb.show(target_led if target_led != "off" else "off")
                    led_state = target_led

                # 偶爾印資訊，協助現場調門檻
                if now - last_led_log > 1.0:
                    print(f"[LED] B:{int(maxB)} O:{int(maxO)} -> {led_state}")
                    last_led_log = now

                # ======= Debug 視覺化 =======
                if debug:
                    draw_roi_boxes(img, [ROI1, ROI2, ROI3, ROI4, ROI5, ROI6], color=(255, 204, 0), thickness=2)
                    COLOR_BLUE    = (255 , 0 , 0)
                    COLOR_ORANGE  = (0, 165, 255)
                    COLOR_LWALL   = (0, 255, 0)
                    COLOR_RWALL   = (0, 255, 255)
                    COLOR_RED     = (0, 0, 255)
                    COLOR_GREEN   = (0, 255, 0)
                    COLOR_FRONT   = (200, 200, 200)
                    COLOR_TURN    = (128, 128, 255)
                    COLOR_MAGENTA = (255, 0, 255)

                    try:
                        draw_contours_list(img, contours_left, ROI1, COLOR_LWALL,  label="Lwall",  thickness=2)
                        draw_contours_list(img, contours_right,ROI2, COLOR_LWALL,  label="Rwall",  thickness=2)
                        draw_contours_list(img, contours_red,  ROI3, COLOR_RED,    label="pillar(R)", thickness=2)
                        draw_contours_list(img, contours_green,ROI3, COLOR_GREEN,  label="pillar(G)", thickness=2)
                        draw_contours_list(img, contours_blue, ROI4, COLOR_BLUE,   label="blue",  thickness=2)
                        draw_contours_list(img, contours_orange,ROI4,COLOR_ORANGE, label="orange",thickness=2)
                        draw_contours_list(img, contours_parking,ROI4,COLOR_FRONT, label="front", thickness=2)
                        if ROI5[0] != 0:
                            draw_contours_list(img, contours_turn,  ROI5, COLOR_TURN, label="turn(B)", thickness=2)
                            draw_contours_list(img, contours_turn_m,ROI5, COLOR_TURN, label="turn(M)", thickness=2)
                        if ROI6[1] != 0 and mag6_area > 0 and mag6_center is not None and mag6_bbox is not None:
                            x, y, w, h = mag6_bbox
                            cv2.rectangle(img, (x, y), (x + w, y + h), COLOR_MAGENTA, 2)
                            cv2.circle(img, (mag6_center[0], mag6_center[1]), 5, COLOR_MAGENTA, -1)

                    except Exception:
                        pass

                    cv2.putText(img, f"B:{int(maxB)}  t:{t}", (10, 60),  cv2.FONT_HERSHEY_DUPLEX, 0.8, (0,0,0), 4)
                    cv2.putText(img, f"B:{int(maxB)}  t:{t}", (10, 60),  cv2.FONT_HERSHEY_DUPLEX, 0.8, (255,255,255), 1)

                    fps = "fps: " + str(int(1 / max(1e-6, (time.time() - fps_start))))
                    elapsed = "time: " + str(int(time.time() - pTimer)) + "s"
                    cv2.putText(img, fps,     (500, 30), cv2.FONT_HERSHEY_DUPLEX, 1, (0,0,0), 4)
                    cv2.putText(img, elapsed, (10,  30), cv2.FONT_HERSHEY_DUPLEX, 1, (0,0,0), 4)
                    cv2.putText(img, fps,     (500, 30), cv2.FONT_HERSHEY_DUPLEX, 1, (255,255,255), 1)
                    cv2.putText(img, elapsed, (10,  30), cv2.FONT_HERSHEY_DUPLEX, 1, (255,255,255), 1)

                    if cPillar and cPillar.area > 0:
                        cv2.circle(img, (int(cPillar.x), int(cPillar.y)), 6, (0, 0, 255), -1)
                        cv2.putText(img, f"Pillar a:{int(cPillar.area)} d:{int(cPillar.dist)}",
                                    (int(cPillar.x)+6, int(cPillar.y)-8),
                                    cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0,0,255), 2)

                    cv2.imshow("jetson_debug", img)
                    if cv2.waitKey(1) == ord('q'):
                        stop_car()
                        break

                prevAngle = angle
                tSignal = False
                prevError = error

        except HaltRun:
            pass

    except Exception as e:
        print(" Unhandled exception:", repr(e))

    finally:
        try:
            if cap is not None:
                cap.release()
            cv2.destroyAllWindows()
        except Exception:
            pass
        try:
            rgb.off()
        except Exception:
            pass
        if bno_bus:
            bno_bus.close()
        ws_hub.stop()
        print("程式結束")
