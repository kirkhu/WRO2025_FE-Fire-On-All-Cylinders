from machine import Pin, PWM, time_pulse_us
import time, network, usocket as socket, ubinascii, uos, ujson as json

# =============== Wi-Fi / WebSocket 設定 ===============
WIFI_SSID = "iPhone_ron"
WIFI_PASS = "ron0975750386"
JETSON_IP = "172.20.10.8"
WS_PORT   = 8765

# =============== 偵錯開關 ===============
DEBUG = True  # 想安靜一點就設 False

# =============== 舵機參數（可依實車調） ===============
MECH_SIGN        = +1
CENTER_TRIM_DEG  = 0
SERVO_MIN_US     = 1000
SERVO_MAX_US     = 2000

# =============== 硬體腳位 ===============
led = Pin("LED", Pin.OUT)

TRIG_PIN1 = 8
ECHO_PIN1 = 9
TRIG_PIN2 = 12
ECHO_PIN2 = 13
TRIG_PIN3 = 4
ECHO_PIN3 = 5
trig1 = Pin(TRIG_PIN1, Pin.OUT)
echo1 = Pin(ECHO_PIN1, Pin.IN)
trig2 = Pin(TRIG_PIN2, Pin.OUT)
echo2 = Pin(ECHO_PIN2, Pin.IN)
trig3 = Pin(TRIG_PIN3, Pin.OUT)
echo3 = Pin(ECHO_PIN3, Pin.IN)

servo_pin   = PWM(Pin(28), freq=50)
motor_in1   = Pin(21, Pin.OUT)
motor_in2   = Pin(20, Pin.OUT)
motor_pwm   = PWM(Pin(22), freq=1000)
button      = Pin(18, Pin.IN, Pin.PULL_UP)

encoder_pin_A, encoder_pin_B = Pin(0, Pin.IN), Pin(1, Pin.IN)
encoder_count, last_state_A  = 0, encoder_pin_A.value()

# --------------- 全域 RX 緩衝與狀態 ---------------
RXBUF = ""           # 用來拆 JSON / M / STOP
LAST_COLOR = 0       # 任何階段提早收到的 color 都先暫存

# 低延遲調校參數（非阻塞接收）
WS_RECV_TIMEOUT = 0.05  # 先用 50ms 提高穩定度；穩定後可改回 0.0~0.02

# =============== 小工具 ===============
def _clamp(v, lo, hi):
    return lo if v < lo else (hi if v > hi else v)

def _map_servo_us(abs_deg_0_180):
    abs_deg_0_180 = _clamp(int(abs_deg_0_180), 0, 180)
    return SERVO_MIN_US + (SERVO_MAX_US - SERVO_MIN_US) * abs_deg_0_180 / 180.0

def set_servo_rel_deg(rel_deg):
    try:
        rel = int(rel_deg)
    except:
        rel = 0
    rel = _clamp(rel, -180, 180)
    abs_deg = 90 + CENTER_TRIM_DEG + MECH_SIGN * rel
    abs_deg = _clamp(int(abs_deg), 0, 180)
    duty_us = _map_servo_us(abs_deg)
    servo_pin.duty_u16(int(duty_us * 65535 / 20000))

def set_servo_angle(angle_in):
    set_servo_rel_deg(angle_in)

def control_motor(speed):
    try:
        sp = int(speed)
    except:
        sp = 0
    sp = _clamp(sp, -100, 100)
    if sp > 0:
        motor_in1.high(); motor_in2.low()
    elif sp < 0:
        motor_in1.low(); motor_in2.high()
    else:
        motor_in1.low(); motor_in2.low()
    motor_pwm.duty_u16(int(abs(sp) * 65535 / 100))

def encoder_interrupt(pin):
    global encoder_count, last_state_A
    state_a = encoder_pin_A.value()
    if state_a != last_state_A:
        state_b = encoder_pin_B.value()
        encoder_count += 1 if state_a == state_b else -1
        last_state_A = state_a

encoder_pin_A.irq(trigger=Pin.IRQ_RISING | Pin.IRQ_FALLING, handler=encoder_interrupt)

def run_encoder_Auto(motor_angle, speed, string):
    global encoder_count
    encoder_count = 0
    while abs(encoder_count) < motor_angle:
        set_servo_angle(string)
        control_motor(speed)
        time.sleep(0.01)
    control_motor(0)

def measure_distance(trig, echo):
    trig.value(0)
    time.sleep_us(2)
    trig.value(1)
    time.sleep_us(10)
    trig.value(0)
    duration = time_pulse_us(echo, 1)
    distance = (duration / 2) * 0.0343
    return distance

# =============== Wi-Fi ===============
def connect_wifi():
    wlan = network.WLAN(network.STA_IF)
    wlan.active(True)
    if not wlan.isconnected():
        print("Connecting WiFi...")
        wlan.connect(WIFI_SSID, WIFI_PASS)
        t0 = time.time()
        while not wlan.isconnected():
            if time.time() - t0 > 20:
                raise OSError("WiFi connect timeout")
            time.sleep(0.2)
    print("WiFi:", wlan.ifconfig())
    return wlan

# =============== WebSocket 基本函數 ===============
def ws_client_handshake(sock, host, port):
    key_b64 = ubinascii.b2a_base64(uos.urandom(16)).strip().decode()
    req = (
        "GET / HTTP/1.1\r\n"
        "Host: {}:{}\r\n"
        "Upgrade: websocket\r\n"
        "Connection: Upgrade\r\n"
        "Sec-WebSocket-Key: {}\r\n"
        "Sec-WebSocket-Version: 13\r\n\r\n"
    ).format(host, port, key_b64)
    sock.send(req.encode())
    resp = b""
    sock.settimeout(5)
    while b"\r\n\r\n" not in resp:
        part = sock.recv(256)
        if not part: break
        resp += part
    if b"101 Switching Protocols" not in resp:
        raise OSError("WS handshake failed")

def _recvn(sock, n):
    data = b""
    while len(data) < n:
        chunk = sock.recv(n - len(data))
        if not chunk: raise OSError("socket closed")
        data += chunk
    return data

def ws_send_text(sock, text):
    payload = text.encode("utf-8")
    plen = len(payload)
    header = bytearray([0x81])
    mask_bit = 0x80
    if plen <= 125:
        header.append(mask_bit | plen)
    elif plen <= 65535:
        header.append(mask_bit | 126); header.extend(bytes([(plen>>8)&0xFF, plen&0xFF]))
    else:
        raise ValueError("payload too long")
    mask_key = uos.urandom(4); header.extend(mask_key)
    masked = bytearray(plen)
    for i in range(plen): masked[i] = payload[i] ^ mask_key[i%4]
    sock.send(header + masked)

def ws_recv_text(sock, timeout=WS_RECV_TIMEOUT):
    sock.settimeout(timeout)
    try:
        b1b2 = _recvn(sock, 2)
    except OSError:
        return None
    b1, b2 = b1b2[0], b1b2[1]
    plen = (b2 & 0x7F)
    if plen == 126:
        plen = int.from_bytes(_recvn(sock, 2), "big")
    elif plen == 127:
        _ = _recvn(sock, 8)
        raise ValueError("Too long frame")
    masked = (b2 & 0x80) != 0
    if masked:
        mask_key = _recvn(sock, 4)
    payload = _recvn(sock, plen) if plen else b""
    if masked:
        payload = bytes([payload[i] ^ mask_key[i % 4] for i in range(plen)])
    text = payload.decode("utf-8")
    if DEBUG and text:
        print("RX_FRAME:", text)
    return text

# =============== 解析工具（支援 M,<val>；允許無換行；另支援 STOP） ===============
def parse_json_msg(s):
    try:
        obj = json.loads(s)
        return obj if isinstance(obj, dict) else None
    except Exception:
        return None

def parse_m_line(s):
    if not s.startswith("M,"):
        return None
    parts = s.strip().split(",")
    # 兩段：M,<val> -> (rel=<val>, spd=0)
    if len(parts) == 2:
        try:
            val = int(parts[1])
            return _clamp(val, -180, 180), 0
        except:
            return None
    # 三段：M,<rel>,<spd>
    if len(parts) >= 3:
        try:
            rel = int(parts[1])
            spd = int(parts[2])
        except:
            return None
        return _clamp(rel, -180, 180), _clamp(spd, -100, 100)
    return None

def wait_for_button_and_send_start(sock):
    print("等待按鍵啟動...")
    while button.value() == 1:
        time.sleep(0.05)
    print("按鍵已按下，發送 START")
    try:
        ws_send_text(sock, "START\n")
    except Exception as e:
        print("送 START 失敗：", e)

# --------------- 流式拆 JSON / M 指令 / STOP（非阻塞） ---------------
def pump_ws(sock):
    """
    回傳 (json_obj, m_tuple, got_stop)
    - json_obj: 最近解析到的一個 JSON 物件（可能含 yaw/angle/speed/leftArea/rightArea/color/c）
    - m_tuple:  最近解析到的一個 M 指令 (rel, spd)
    - got_stop: 是否收到了 'STOP'（Jetson 三圈結束會廣播）
    """
    global RXBUF
    json_obj = None
    m_tuple = None
    got_stop = False

    # 拉一個 frame 進來（可能沒有）
    msg = ws_recv_text(sock, timeout=WS_RECV_TIMEOUT)
    if msg:
        RXBUF += msg

    # 避免無限制成長
    if len(RXBUF) > 4096:
        RXBUF = RXBUF[-1024:]

    # 優先處理 STOP（不一定有換行）
    idx_stop = RXBUF.find("STOP")
    if idx_stop != -1:
        # 將 STOP 以及可能的尾隨換行剔除
        end = idx_stop + 4
        if end < len(RXBUF) and RXBUF[end:end+1] == "\n":
            end += 1
        RXBUF = RXBUF[:idx_stop] + RXBUF[end:]
        got_stop = True
        if DEBUG:
            print("[PICO] GOT STOP SIGNAL")

    # 盡可能多拆（但不阻塞）
    for _ in range(12):
        if not RXBUF:
            break

        idx_json = RXBUF.find("{")
        idx_m    = RXBUF.find("M,")

        if idx_json == -1 and idx_m == -1:
            break

        # --- 先處理較前面的片段 ---
        if idx_json != -1 and (idx_m == -1 or idx_json < idx_m):
            end = RXBUF.find("}", idx_json)
            if end == -1:
                break  # JSON 尚未完整
            candidate = RXBUF[idx_json:end+1]
            RXBUF = RXBUF[end+1:]
            obj = parse_json_msg(candidate)
            if obj:
                json_obj = obj
                if DEBUG: print("PARSED_JSON:", obj)
                continue
            else:
                continue
        else:
            # 嘗試以換行切；若沒有換行，視為「到緩衝結尾就是完整一條」；支援 'M,3' 無 \n
            nl = RXBUF.find("\n", idx_m)
            if nl == -1:
                candidate = RXBUF[idx_m:].strip()
                RXBUF = RXBUF[:idx_m]
            else:
                candidate = RXBUF[idx_m:nl].strip()
                RXBUF = RXBUF[nl+1:]

            parsed = parse_m_line(candidate)
            if parsed:
                m_tuple = parsed
                if DEBUG: print("PARSED_M:", m_tuple, "RAW=", candidate)
                continue
            else:
                continue

    return json_obj, m_tuple, got_stop

# =============== 主程式 ===============
def run():
    global LAST_COLOR
    motor_in1.off()
    motor_in2.off()
    control_motor(0)
    set_servo_angle(0)
    led.off()

    connect_wifi()
    while True:
        s = None
        try:
            print("Connecting TCP to {}:{}".format(JETSON_IP, WS_PORT))
            s = socket.socket()
            s.settimeout(5)
            s.connect((JETSON_IP, WS_PORT))
            ws_client_handshake(s, JETSON_IP, WS_PORT)
            print("WebSocket connected.")
            s.settimeout(0.5)

            ws_send_text(s, json.dumps({"from":"pico","status":"ready"}) + "\n")
            led.on()
            wait_for_button_and_send_start(s)
            time.sleep(5)
            mode = 0
            turn = 0

            yaw = 0.0
            angle_from_jetson = 0
            speed_from_jetson = 0
            leftArea = 0
            rightArea = 0

            # --- 流程 0：取起跑方向（只讀 turn = 1/2），但提早到的 color 會先暫存 ---
            print("進入 mode=0（取起跑方向），等待 Jetson 的 M,<turn>,* ...")
            while mode == 0 and turn == 0:
                json_obj, m_tuple, got_stop = pump_ws(s)
                if got_stop:
                    control_motor(0)
                    set_servo_angle(0)
                    print("[HALT] STOP received (mode0)")
                    return

                if json_obj:
                    # 提早收到 color 也先暫存
                    if "color" in json_obj:
                        try:
                            LAST_COLOR = int(json_obj["color"])
                            if DEBUG: print("[LATCH] JSON color ->", LAST_COLOR)
                        except: pass
                    if "c" in json_obj:
                        try:
                            LAST_COLOR = int(json_obj["c"])
                            if DEBUG: print("[LATCH] JSON c ->", LAST_COLOR)
                        except: pass
                    if "yaw" in json_obj:
                        try: yaw = float(json_obj.get("yaw", yaw))
                        except: pass
                    if "angle" in json_obj:
                        try: angle_from_jetson = int(json_obj.get("angle", angle_from_jetson))
                        except: pass
                    if "speed" in json_obj:
                        try: speed_from_jetson = int(json_obj.get("speed", speed_from_jetson))
                        except: pass
                    if "leftArea" in json_obj:
                        try: leftArea = int(json_obj.get("leftArea", leftArea))
                        except: pass
                    if "rightArea" in json_obj:
                        try: rightArea = int(json_obj.get("rightArea", rightArea))
                        except: pass

                if m_tuple:
                    candidate = m_tuple[0]
                    # 先緩存 color（若提前送到）
                    if 1 <= candidate <= 6:
                        LAST_COLOR = candidate
                        if DEBUG: print("[LATCH] M color ->", LAST_COLOR)
                    # 只接受 1 或 2 當作 turn
                    if candidate in (1, 2):
                        turn = candidate
                        print("設定 turn =", turn)

                if json_obj is None and m_tuple is None:
                    time.sleep(0.002)

            # --- 根據 turn 執行旋轉（只靠陀螺儀，條件達成立即跳出） ---
            if turn == 1:
                # 右轉
                print("右轉")
                set_servo_angle(180)
                control_motor(30)
                while True:
                    json_obj, _, got_stop = pump_ws(s)
                    if got_stop:
                        control_motor(0)
                        set_servo_angle(0)
                        print("[HALT] STOP received (right turn 1)")
                        return
                    if json_obj and ("yaw" in json_obj):
                        try: yaw = float(json_obj["yaw"])
                        except: pass
                        if yaw >= 13:
                            break
                control_motor(-15)
                set_servo_angle(0)
                time.sleep(0.5)
                set_servo_angle(-180)
                control_motor(-30)
                while True:
                    json_obj, _, got_stop = pump_ws(s)
                    if got_stop:
                        control_motor(0)
                        set_servo_angle(0)
                        print("[HALT] STOP received (right turn 2)")
                        return
                    if json_obj and ("yaw" in json_obj):
                        try: yaw = float(json_obj["yaw"])
                        except: pass
                        if yaw >= 25:
                            break
                control_motor(15)
                set_servo_angle(0)
                time.sleep(0.5)
                set_servo_angle(180)
                control_motor(35)
                while True:
                    json_obj, _, got_stop = pump_ws(s)
                    if got_stop:
                        control_motor(0)
                        set_servo_angle(0)
                        print("[HALT] STOP received (right turn 3)")
                        return
                    if json_obj and ("yaw" in json_obj):
                        try: yaw = float(json_obj["yaw"])
                        except: pass
                        if yaw >= 90:
                            break
                control_motor(-15)
                set_servo_angle(0)

            else:
                # 左轉
                print("左轉")
                set_servo_angle(-180)
                control_motor(30)
                while True:
                    json_obj, _, got_stop = pump_ws(s)
                    if got_stop:
                        control_motor(0)
                        set_servo_angle(0)
                        print("[HALT] STOP received (left turn 1)")
                        return
                    if json_obj and ("yaw" in json_obj):
                        try: yaw = float(json_obj["yaw"])
                        except: pass
                        if yaw <= -13:
                            break
                control_motor(-15)
                set_servo_angle(0)
                time.sleep(0.01)
                set_servo_angle(180)
                control_motor(-30)
                while True:
                    json_obj, _, got_stop = pump_ws(s)
                    if got_stop:
                        control_motor(0)
                        set_servo_angle(0)
                        print("[HALT] STOP received (left turn 2)")
                        return
                    if json_obj and ("yaw" in json_obj):
                        try: yaw = float(json_obj["yaw"])
                        except: pass
                        if yaw <= -25:
                            break
                control_motor(15)
                set_servo_angle(0)
                time.sleep(0.01)
                set_servo_angle(-180)
                control_motor(35)
                while True:
                    json_obj, _, got_stop = pump_ws(s)
                    if got_stop:
                        control_motor(0)
                        set_servo_angle(0)
                        print("[HALT] STOP received (left turn 3)")
                        return
                    if json_obj and ("yaw" in json_obj):
                        try: yaw = float(json_obj["yaw"])
                        except: pass
                        if yaw <= -100:
                            break
                control_motor(-15)
                set_servo_angle(0)
                print("左轉：完成")

            # --- 流程1：顏色決策（同時接受 M 與 JSON，並吃掉先前緩存） ---
            mode = 1
            color = LAST_COLOR if (1 <= LAST_COLOR <= 6) else 0
            print(mode, color)
            print("等待 color（M,<1..6> 或 JSON {\"color\":n}）... 先前緩存 =", LAST_COLOR)
            while mode == 1 and color == 0:
                json_obj, m_tuple, got_stop = pump_ws(s)
                if got_stop:
                    control_motor(0)
                    set_servo_angle(0)
                    print("[HALT] STOP received (mode1 waiting color)")
                    return

                # A. JSON 欄位 color / c
                if json_obj:
                    if "color" in json_obj:
                        try:
                            color = int(json_obj["color"])
                            LAST_COLOR = color
                            print("[JSON] color =", color)
                        except:
                            pass
                    elif "c" in json_obj:
                        try:
                            color = int(json_obj["c"])
                            LAST_COLOR = color
                            print("[JSON] c -> color =", color)
                        except:
                            pass

                # B. M 指令：M,<val> 或 M,<rel>,<spd>
                if m_tuple:
                    candidate = m_tuple[0]
                    if 1 <= candidate <= 6:
                        color = candidate
                        LAST_COLOR = color
                        print("[M] color =", color)

                if json_obj is None and m_tuple is None:
                    time.sleep(0.002)

            # --- 顏色對應動作 ---
            if color == 1:
                print("顏色=1（綠色：範例組合）")
                run_encoder_Auto(2000, 40, 0)
                run_encoder_Auto(2900, 40, -180)
            elif color == 2:
                print("顏色=2（紅色）")
                run_encoder_Auto(1700, 50, 0)
                run_encoder_Auto(1400, -40, -180)
            elif color == 3:
                print("顏色=3（NO）")
                run_encoder_Auto(500, 40, -180)
                run_encoder_Auto(1300, 40, 180)
            elif color == 4:
                print("顏色=4（綠色）")
                run_encoder_Auto(300, 40, 180)
                run_encoder_Auto(600, 70, 0)
                run_encoder_Auto(900, 30, -180)
            elif color == 5:
                print("顏色=5（紅色）")
                run_encoder_Auto(1000, 40, 180)
                run_encoder_Auto(1000, 70, 0)
                run_encoder_Auto(1800, 40, -180)
            elif color == 6:
                print("顏色=6（NO）")
                run_encoder_Auto(300, 40, 180)
                run_encoder_Auto(600, 70, 0)
                run_encoder_Auto(900, 30, -180)

            control_motor(-10)
            set_servo_angle(0)

            # --- 流程2：一般控制（持續接收 M,<rel>,<spd>；同時可隨時收到 STOP） ---
            mode = 2
            print("進入 mode=2（一般控制），等待 M,<rel>,<spd> ...")
            while True:
                json_obj, m_tuple, got_stop = pump_ws(s)

                if got_stop:
                    control_motor(0)
                    set_servo_angle(0)
                    print("[HALT] STOP received (mode2)")
                    return

                if json_obj:
                    # 這裡也允許隨時更新 color 緩存（不影響當前控制邏輯）
                    if "color" in json_obj:
                        try: LAST_COLOR = int(json_obj["color"])
                        except: pass
                    elif "c" in json_obj:
                        try: LAST_COLOR = int(json_obj["c"])
                        except: pass

                if m_tuple:
                    rel, spd = m_tuple
                    set_servo_angle(rel)
                    control_motor(spd)

                if json_obj is None and m_tuple is None:
                    time.sleep(0.002)

        except Exception as e:
            print("WS error:", e)
            try:
                if s: s.close()
            except: pass
            print("Reconnecting in 3s...")
            time.sleep(3)

# 進入程式
try:
    run()
except KeyboardInterrupt:
    control_motor(0)
    set_servo_angle(0)
    print("程式中斷")

