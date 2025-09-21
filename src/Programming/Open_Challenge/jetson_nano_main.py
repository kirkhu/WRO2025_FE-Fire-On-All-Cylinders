import time
import os, sys, math, json, threading, asyncio
import cv2
import numpy as np
import websockets
from websockets.exceptions import ConnectionClosed
from smbus2 import SMBus
import functions_jetson as fj

# -------------------- 路徑與工具 --------------------
sys.path.append(os.path.abspath(os.path.dirname(__file__)))
from masks import rMagenta, rRed, rGreen, rBlue, rOrange, rBlack
from functions_jetson import * # find_contours, max_contour, pOverlap, display_roi, display_variables, straight_const, is_moving

# =================== BNO055 ===================
BNO055_ADDRESS = 0x28
BNO055_OPR_MODE_ADDR = 0x3D
BNO055_PWR_MODE_ADDR = 0x3E
BNO055_ID = 0xA0
BNO055_CHIP_ID_ADDR = 0x00
OPERATION_MODE_CONFIG = 0x00
OPERATION_MODE_NDOF = 0x0C
BNO055_EULER_H_LSB = 0x1A
BNO055_BUS = 7  # Jetson I2C bus（請按實機調整）

# ====== 角度與限幅 Helper ======
def clamp(v, lo, hi):
    return lo if v < lo else (hi if v > hi else v)

MECH_SIGN = +1
def rel_to_servo_deg(rel_deg: int) -> int:
    servo = int(round(straight_const + MECH_SIGN * rel_deg))
    return clamp(servo, 0, 180)

def LEFT(deg=70):   return -abs(int(deg))
def RIGHT(deg=70):  return +abs(int(deg))

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
            self._thread.join(timeout=2)

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

    def broadcast_json(self, leftArea, rightArea, yaw, angle, speed):
        msg = {"leftArea": int(leftArea), "rightArea": int(rightArea),
               "yaw": float(yaw), "angle": int(angle), "speed": int(speed)}
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
                # 重要：結尾加換行，方便對端以 \n 拆封包
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

        async with websockets.serve(handler, self.host, self.port,
                                     ping_interval=None, compression=None, max_size=None, close_timeout=1.0):
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

# ===== 立刻停車的輔助：t 達 12 直接拋例外結束主迴圈 =====
t = 0  # 全域圈數（預設 0）

class HaltRun(Exception):
    """用來在 t>=12 時跳出主迴圈"""
    pass

def inc_t():
    """任何需要 t 加一的地方都呼叫這個函式。達到 12 直接停車並中止主迴圈。"""
    global t
    t += 1
    print(f"[t++] -> {t}")
    if t >= 12:
        stop_car()
        print("🚨 t>=12，車輛停止並結束主迴圈")
        raise HaltRun()

# ======================================================
# 影像 / 演算法 Helper
# ======================================================
def gstreamer_csi_pipeline(sensor_id=0, capture_width=640, capture_height=480,
                           display_width=640, display_height=480,
                           framerate=30, flip_method=0):
    return (f"nvarguscamerasrc sensor-id={sensor_id} ! "
            f"video/x-raw(memory:NVMM), width={capture_width}, height={capture_height}, "
            f"format=NV12, framerate={framerate}/1 ! "
            f"nvvidconv flip-method={flip_method} ! "
            f"video/x-raw, width={display_width}, height={display_height}, format=BGRx ! "
            f"videoconvert ! video/x-raw, format=BGR ! appsink")

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

# ---------- 側牆 / 停車 / 轉彎等工具 ----------
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
    k5, k3 = cv2.getStructuringElement(cv2.MORPH_RECT, (5,5)), cv2.getStructuringElement(cv2.MORPH_RECT, (3,3))
    m = cv2.morphologyEx(m_black, cv2.MORPH_CLOSE, k5, iterations=1)
    m = cv2.morphologyEx(m, cv2.MORPH_OPEN, k3, iterations=1)
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
            if ((y > ROI3[3] - endConst) or
                (target == greenTarget and (leftArea > 13000 or rightArea > 13000 or temp_dist > maxDist)) or
                (target == redTarget  and (leftArea > 13000 or rightArea > 15000 or temp_dist > maxDist))):
                continue
            if temp_dist < best_dist:
                best_dist = temp_dist
                best = Pillar(area, temp_dist, x, y, target)
                best.setDimentions(w, h)
    return best, num_p

# ---------- BNO055 I2C ----------
def write_byte(bus, reg, value):
    bus.write_byte_data(BNO055_ADDRESS, reg, value)

def read_bytes(bus, reg, length):
    return bus.read_i2c_block_data(BNO055_ADDRESS, reg, length)

def read_chip_id(bus):
    return bus.read_byte_data(BNO055_ADDRESS, BNO055_CHIP_ID_ADDR)

def init_bno055(bus):
    print("🔧 初始化 BNO055...")
    chip_id = read_chip_id(bus)
    if chip_id != BNO055_ID:
        print(f"❌ 無法找到 BNO055 (ID: 0x{chip_id:X})")
        return False
    write_byte(bus, BNO055_OPR_MODE_ADDR, OPERATION_MODE_CONFIG)
    time.sleep(0.025)
    write_byte(bus, BNO055_PWR_MODE_ADDR, 0x00)
    time.sleep(0.01)
    write_byte(bus, BNO055_OPR_MODE_ADDR, OPERATION_MODE_NDOF)
    time.sleep(0.02)
    print("✅ BNO055 初始化完成")
    return True

def read_heading(bus):
    data = read_bytes(bus, BNO055_EULER_H_LSB, 2)
    heading = int.from_bytes(data, byteorder='little', signed=True) / 16.0
    return heading

# ======================================================
# Main
# ======================================================
if __name__ == "__main__":
    bno_bus = None
    try:
        bno_bus = SMBus(BNO055_BUS)
        if not init_bno055(bno_bus):
            sys.exit(1)
        zero_heading = read_heading(bno_bus)
        print("🎯 歸零完成，現在的角度當作 0°")

        cap = cv2.VideoCapture(gstreamer_csi_pipeline(), cv2.CAP_GSTREAMER)
        if not cap.isOpened():
            print("Camera open failed")
            sys.exit(1)

        # ---- 狀態/參數初始化 ----
        eTurnMethod = ""
        lapsComplete = False
        redTarget, greenTarget = 90, 550
        lastTarget = 0
        tempParking = False
        sTime = 0
        s = 0
        endConst = 50
        lotType = "light"
        turnDir = "none"
        parkingL = False
        parkingR = False
        pillarAtStart = -1
        t = 0
        t2 = 0
        rTurn = False
        lTurn = False
        tSignal = False

        ROI1 = [0, 195, 330, 285]
        ROI2 = [330, 195, 640, 285]
        ROI3 = [redTarget - 60, 80, greenTarget + 60, 360]
        ROI4 = [190, 315, 440, 350]
        ROI5 = [0,0,0,0]
        tArea = 0

        kp, kd = 0.03, 0.08
        cKp, cKd, cy = 0.5, 0.8, 0.28

        angle = 0
        prevAngle = angle
        tDeviation = 50
        sharpLeft = LEFT(tDeviation)
        sharpRight = RIGHT(tDeviation)
        speed, reverseSpeed = 45, -40
        startArea = 4000
        aDiff = 0
        prevDiff = 0
        error = 0
        prevError = 0
        maxDist = 370
        leftArea = 0
        rightArea = 0

        # —— 藍線偵測：上升沿 + 冷卻 + 1秒等待（避免重複） ——
        BLUE_ON_THRESH    = 90
        BLUE_OFF_THRESH   = 60
        BLUE_COOLDOWN_SEC = 1.0
        blue_next_allowed_time = 0.0    # 下一次允許計數的時間戳
        blue_armed = True               # True 表示目前允許觸發一次（等上升沿）

        # ---- 等待 START ----
        wait_for_start(timeout=None)
        write(("S", speed))
        write(0)
        time.sleep(0.01)

        debug = ("debug" in "".join(sys.argv).lower())
        pTimer = time.time()
        start = False

        # 傳輸頻率（分開控制 M 與 JSON）
        TX_M_PERIOD    = 0.01   # 角度/速度 M 指令
        TX_JSON_PERIOD = 0.01   # yaw/areas JSON（約 25Hz）
        last_tx_m      = 0.0
        last_tx_json   = 0.0

        # ==== 起始左右判斷 ====
        a = 0
        start_turn = 0
        while a == 0:
            rightArea = leftArea = areaFront = tArea = 0
            ok, img = cap.read()
            if not ok:
                continue
            img = cv2.resize(img, (640, 480), interpolation=cv2.INTER_LINEAR)
            img_lab = cv2.cvtColor(img, cv2.COLOR_BGR2Lab)
            img_lab = cv2.GaussianBlur(img_lab, (5,5), 0)

            contours_left  = pOverlap(img_lab, ROI1)
            contours_right = pOverlap(img_lab, ROI2)
            leftArea  = max_contour(contours_left,  ROI1)[0]
            rightArea = max_contour(contours_right, ROI2)[0]

            if leftArea - rightArea > 0:
                print("右轉")
                start_turn = 1
                a = 1
            else:
                print("左轉")
                start_turn = 2
                a = 1

        write(start_turn)
        time.sleep(0.2)

        # ==== 等待柱子顏色判斷 ====
        time.sleep(1.5)
        color = 0
        detect_start = time.time()
        TIMEOUT = 2.0

        while a == 1:
            ok, img = cap.read()
            if not ok:
                continue

            img = cv2.resize(img, (640, 480), interpolation=cv2.INTER_LINEAR)
            img_lab = cv2.cvtColor(img, cv2.COLOR_BGR2Lab)
            img_lab = cv2.GaussianBlur(img_lab, (5,5), 0)

            # 更新左右牆面積
            contours_left  = pOverlap(img_lab, ROI1, True)
            contours_right = pOverlap(img_lab, ROI2, True)
            leftArea  = max_contour(contours_left,  ROI1)[0]
            rightArea = max_contour(contours_right, ROI2)[0]

            # 找紅/綠柱
            contours_red   = find_contours(img_lab, rRed,   ROI3)
            contours_green = find_contours(img_lab, rGreen, ROI3)
            best_green, _ = find_best_pillar(contours_green, greenTarget, "green", img_lab)
            best_red,   _ = find_best_pillar(contours_red,   redTarget,   "red",   img_lab)
            candidates = [p for p in (best_green, best_red) if p is not None]
            cPillar = min(candidates, key=lambda P: P.dist) if candidates else Pillar(0, 1000000, 0, 0, 0)

            seen_green = (cPillar.target == greenTarget and cPillar.area > 0)
            seen_red   = (cPillar.target == redTarget   and cPillar.area > 0)

            if start_turn == 2:
                if seen_green:
                    color = 1
                    a = 2
                elif seen_red:
                    color = 2
                    a = 2
                elif time.time() - detect_start > TIMEOUT:
                    color = 3
                    a = 2
            else:
                if seen_green:
                    color = 4
                    a = 2
                elif seen_red:
                    color = 5
                    a = 2
                elif time.time() - detect_start > TIMEOUT:
                    color = 6
                    a = 2

        write(color)
        time.sleep(0.2)

        # =================== 主迴圈 ===================
        try:
            while True:
                fps_start = time.time()  # 供 debug FPS 計算

                # 讀 IMU
                current_heading = read_heading(bno_bus)
                relative_heading = current_heading - zero_heading
                if relative_heading > 180:
                    relative_heading -= 360
                elif relative_heading < -180:
                    relative_heading += 360
                print(f"🧭 偏航角（Yaw）：{relative_heading:.2f}°")

                # 影像
                ok, img = cap.read()
                if not ok:
                    continue
                img = cv2.resize(img, (640, 480))
                img_lab = cv2.cvtColor(img, cv2.COLOR_BGR2Lab)
                img_lab = cv2.GaussianBlur(img_lab, (5,5), 0)
                
                # 初始化變數以避免 NameError
                contours_turn = []
                contours_turn_m = []

                # 右側洋紅（未停車）
                rPArea = 0
                if not tempParking:
                    pRight = find_contours(img_lab, rMagenta, ROI2)
                    rPArea = max_contour(pRight, ROI2)[0]

                # ROI5 轉彎補強
                if ROI5[0] != 0:
                    contours_turn   = find_contours(img_lab, rBlack,    ROI5)
                    contours_turn_m = find_contours(img_lab, rMagenta,  ROI5)
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

                # 角落藍/橘（在 ROI4）
                contours_blue   = find_contours(img_lab, rBlue,   ROI4)
                contours_orange = find_contours(img_lab, rOrange, ROI4)
                maxO = max_contour(contours_orange,  ROI4)[0]
                maxB = max_contour(contours_blue,    ROI4)[0]

                # —— 藍線事件（上升沿 + 冷卻 + 回到 OFF 才重臂；含 1 秒等待） ——
                now_ts = time.time()

                # 回到 OFF（<= OFF 門檻）才重臂
                if maxB <= BLUE_OFF_THRESH and not blue_armed:
                    blue_armed = True

                # 上升沿：由 OFF -> ON，且過了冷卻時間
                if maxB >= BLUE_ON_THRESH and blue_armed and now_ts >= blue_next_allowed_time:
                    print(f"[BLUE] rising edge (maxB={int(maxB)})")
                    blue_armed = False
                    blue_next_allowed_time = now_ts + BLUE_COOLDOWN_SEC
                    inc_t()                  # t += 1；達到 12 會直接停車並丟出 HaltRun
                    time.sleep(1.0)          # 防重複

                # 單一最佳紅/綠柱
                best_red,   _ = find_best_pillar(contours_red,   redTarget,   "red",   img_lab)
                best_green, _ = find_best_pillar(contours_green, greenTarget, "green", img_lab)
                candidates = [p for p in (best_red, best_green) if p is not None]
                cPillar = min(candidates, key=lambda P: P.dist) if candidates else Pillar(0, 1000000, 0, 0, 0)

                if t == 0 and cPillar.area > startArea:
                    startArea = cPillar.area
                    startTarget = cPillar.target

                if turnDir == "none":
                    if maxO > 100: turnDir = "right"
                    elif maxB > 100: turnDir = "left"

                if (turnDir == "right" and maxO > 350) or (turnDir == "left" and maxB > 350):
                    t2 = t
                    if t2 == 7 and not pillarAtStart:
                        ROI3[1] = 110
                    if tempParking:
                        ROI5 = [270, 120, 370, 140]
                    if cPillar.area != 0 and ((leftArea > 1000 and turnDir == "left") or (rightArea > 1000 and turnDir == "right")):
                        ROI5 = [270, 120, 370, 140]
                    if turnDir == "right": rTurn = True
                    else: lTurn = True
                    if t == 0 and pillarAtStart == -1:
                        pillarAtStart = True if ((startArea > 2500 and startTarget == greenTarget) or (startArea > 1500 and startTarget == redTarget)) else False
                    tSignal = True
                elif (turnDir == "left" and maxO > 150) or (turnDir == "right" and maxB > 150):
                    if t2 == 11:
                        s = 2
                        sTime = time.time()

                # 停車流程（保留原邏輯）
                if tempParking:
                    contours_magenta_c = find_contours(img_lab, rMagenta, ROI4)
                    areaFrontMagenta = max_contour(contours_magenta_c, ROI4)[0]
                    if areaFrontMagenta > 500 and t == 8:
                        angle = sharpLeft

                if tempParking:
                    contours_magenta_l = find_contours(img_lab, rMagenta, ROI1)
                    contours_magenta_r = find_contours(img_lab, rMagenta, ROI2)
                    leftLot  = max_contour(contours_magenta_l, ROI1)
                    rightLot = max_contour(contours_magenta_r, ROI2)
                    centerLot= max_contour(contours_magenta_c, ROI4)
                    maxAreaL, leftY  = leftLot[0],  leftLot[2]
                    maxAreaR, rightY = rightLot[0], rightLot[2]
                    centerY          = centerLot[2]

                    if leftY >= 220 and maxAreaL > 650 and t2 >= 12 and not (parkingL or parkingR):
                        write(40)
                        parkingL = True
                        if (maxAreaL > 1000 and lotType == "dark") or (maxAreaL > 1800 and lotType == "light"):
                            time.sleep(max(maxAreaL/2500 - 1, 0))
                        ROI4 = [220, 250, 370, 300]

                    if rightY >= 240 and maxAreaR > 600 and t2 >= 12 and not (parkingL or parkingR):
                        write(40)
                        parkingR = True
                        if maxAreaR > 3000:
                            write(0)
                            time.sleep(min(max(maxAreaR/4000 - 0.5, 0), 1))
                        ROI4 = [270, 250, 450, 300]

                    if parkingR:
                        if centerY > 290:
                            multi_write([0, 0.5, 40, sharpLeft, 0.5, 0])
                        else:
                            multi_write([40, sharpRight])

                    elif parkingL:
                        if rightArea > 12000 and maxAreaR > 2000:
                            multi_write([1640, sharpRight, 1])
                        if centerY > 280 and areaFront < 3500:
                            ROI4 = [270, 250, 370, 300]
                            multi_write([1500, 0.1, -40, sharpRight, 0.5, 1500])
                        else:
                            multi_write([1580, sharpLeft])

                    if areaFront > 3500:
                        if parkingL:
                            multi_write([0, 0.2, 50, 1.5])
                        else:
                            multi_write([sharpRight, 0.2, 50, 1.5])
                        stop_car()
                        break

                # 舵角
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

                # ROI5 轉彎補強 -> 可能需要 t+1
                if ((tArea > 1250 and turnDir == "left") or (tArea > 1250 and turnDir == "right")):
                    inc_t()  # 原本是 t = t + 1
                    rTurn = lTurn = False
                    if cPillar.area > 5000 or (tempParking and cPillar.area > 2000) or (turnDir == "right" and cPillar.area > 3500):
                        angle = 0
                    else:
                        angle = sharpRight if turnDir == "right" else sharpLeft

                if ((cPillar.area == 0 and tArea < 100) or (abs(leftArea - rightArea) > 5000 and tArea > 1000)) and not tempParking:
                    tArea = 0
                    ROI5 = [0,0,0,0]

                if rPArea > 5000:
                    angle = sharpLeft

                if not start:
                    multi_write([("S", speed), 0.2, angle])  # 速度用百分比訊號
                    start = True

                if angle != prevAngle or rTurn or lTurn:
                    if ((rightArea >= 1500 and rTurn) or (leftArea >= 1500 and lTurn)) and not tSignal:
                        lTurn = rTurn = False
                    if not (parkingR or parkingL):
                        if rTurn and cPillar.area == 0 and rightArea < 5000:
                            angle = 0 if tempParking else sharpRight
                        elif lTurn and cPillar.area == 0 and leftArea < 5000:
                            angle = sharpLeft
                        angle = clamp(angle, sharpLeft, sharpRight)
                        write(angle)
                        print(t, lTurn, rTurn, leftArea, rightArea, cPillar.target, angle)

                # ＝＝＝ 定期傳輸：分開送 M 與 JSON（含 yaw）＝＝＝
                now = time.time()

                # M 指令（角度/速度百分比）
                if now - last_tx_m >= TX_M_PERIOD:
                    write(angle)
                    last_tx_m = now

                # JSON 遙測（yaw / areas / 角度 / 速度）
                if now - last_tx_json >= TX_JSON_PERIOD:
                    ws_hub.broadcast_json(
                        leftArea=leftArea,
                        rightArea=rightArea,
                        yaw=relative_heading,            # BNO055 相對偏航角
                        angle=angle,                     # 目前打角（相對角）
                        speed=ws_hub._last_speed_pct     # 目前速度百分比
                    )
                    last_tx_json = now

                if debug:
                    # 顯示 ROI 框
                    display_roi(img, [ROI1, ROI2, ROI3, ROI4, ROI5], (255, 204, 0))
                    
                    # 定義顏色
                    COLOR_BLUE   = (255, 0, 0)
                    COLOR_ORANGE = (0, 165, 255)
                    COLOR_LWALL  = (0, 255, 0)
                    COLOR_RWALL  = (0, 255, 255)
                    COLOR_FRONT  = (200, 200, 200)
                    COLOR_RED    = (0, 0, 255)
                    COLOR_GREEN  = (0, 255, 0)
                    COLOR_MAGENTA= (255, 0, 255)

                    # 畫輪廓線條
                    cv2.drawContours(img, contours_left, -1, COLOR_LWALL, 2, offset=(ROI1[0], ROI1[1]))
                    cv2.drawContours(img, contours_right, -1, COLOR_LWALL, 2, offset=(ROI2[0], ROI2[1]))
                    cv2.drawContours(img, contours_parking, -1, COLOR_FRONT, 2, offset=(ROI4[0], ROI4[1]))
                    
                    # 柱子
                    cv2.drawContours(img, contours_red, -1, COLOR_RED, 2, offset=(ROI3[0], ROI3[1]))
                    cv2.drawContours(img, contours_green, -1, COLOR_GREEN, 2, offset=(ROI3[0], ROI3[1]))
                    
                    # 藍/橘線
                    cv2.drawContours(img, contours_blue, -1, COLOR_BLUE, 2, offset=(ROI4[0], ROI4[1]))
                    cv2.drawContours(img, contours_orange, -1, COLOR_ORANGE, 2, offset=(ROI4[0], ROI4[1]))
                    
                    # 轉彎補強
                    if ROI5[0] != 0:
                        cv2.drawContours(img, contours_turn, -1, COLOR_FRONT, 2, offset=(ROI5[0], ROI5[1]))
                        cv2.drawContours(img, contours_turn_m, -1, COLOR_MAGENTA, 2, offset=(ROI5[0], ROI5[1]))
                    
                    # 顯示 maxB 與 t
                    cv2.putText(img, f"B:{int(maxB)}  t:{t}", (10, 60), cv2.FONT_HERSHEY_DUPLEX, 0.8, (0,0,0), 4)
                    cv2.putText(img, f"B:{int(maxB)}  t:{t}", (10, 60), cv2.FONT_HERSHEY_DUPLEX, 0.8, (255,255,255), 1)

                    fps = "fps: " + str(int(1 / max(1e-6, (time.time() - fps_start))))
                    elapsed = "time: " + str(int(time.time() - pTimer)) + "s"
                    cv2.putText(img, fps,    (500, 30), cv2.FONT_HERSHEY_DUPLEX, 1, (0,0,0), 4)
                    cv2.putText(img, elapsed,(10,  30), cv2.FONT_HERSHEY_DUPLEX, 1, (0,0,0), 4)
                    cv2.putText(img, fps,    (500, 30), cv2.FONT_HERSHEY_DUPLEX, 1, (255,255,255), 1)
                    cv2.putText(img, elapsed,(10,  30), cv2.FONT_HERSHEY_DUPLEX, 1, (255,255,255), 1)

                    cv2.imshow("jetson_debug", img)
                    if cv2.waitKey(1) == ord('q'):
                        stop_car()
                        break

                prevAngle = angle
                tSignal = False
                prevError = error

        except HaltRun:
            # t 已在 inc_t() 達標後觸發停車，這裡只做收尾離開
            pass

        cap.release()
        cv2.destroyAllWindows()
    finally:
        if bno_bus:
            bno_bus.close()
        ws_hub.stop()