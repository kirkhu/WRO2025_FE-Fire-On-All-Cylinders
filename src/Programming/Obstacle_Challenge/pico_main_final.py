from machine import Pin, PWM, ADC, time_pulse_us
import time, network, usocket as socket, ubinascii, uos, ujson as json

# =============== Wi-Fi / WebSocket 設定 ===============
WIFI_SSID = "iPhone_ron"
WIFI_PASS = "ron0975750386"
JETSON_IP = "172.20.10.8"
WS_PORT  = 8765

# =============== 偵錯開關 ===============
DEBUG = True  # 想安靜一點就設 False

# =============== 舵機參數（可依實車調） ===============
MECH_SIGN        = +1
CENTER_TRIM_DEG  = 0
SERVO_MIN_US     = 1000
SERVO_MAX_US     = 2000

# =============== 硬體腳位 ===============
led = Pin("LED", Pin.OUT)

A0PIN = 26  # 使用 ADC0，對應 GPIO26
A1PIN = 27  # 使用 ADC1，對應 GPIO27
A0 = ADC(Pin(A0PIN))
A1 = ADC(Pin(A1PIN))

TRIG_PIN1 = 2
ECHO_PIN1 = 3
TRIG_PIN2 = 12
ECHO_PIN2 = 13
trig1 = Pin(TRIG_PIN1, Pin.OUT)
echo1 = Pin(ECHO_PIN1, Pin.IN)
trig2 = Pin(TRIG_PIN2, Pin.OUT)
echo2 = Pin(ECHO_PIN2, Pin.IN)

servo_pin   = PWM(Pin(4), freq=50)
motor_in1   = Pin(21, Pin.OUT)
motor_in2   = Pin(20, Pin.OUT)
motor_pwm   = PWM(Pin(22), freq=1000)
button      = Pin(18, Pin.IN, Pin.PULL_UP)

encoder_pin_A, encoder_pin_B = Pin(0, Pin.IN), Pin(1, Pin.IN)
encoder_count, last_state_A  = 0, encoder_pin_A.value()

# --------------- 全域 RX 緩衝與狀態 ---------------
RXBUF = ""           # 用來拆 JSON / M / STOP
LAST_COLOR = 0       # 任何階段提早收到的 color 都先暫存

# ====== 供外界使用的洋紅資料（ROI6） ======
magArea, magCX, magCY = 0, -1, -1

# 低延遲調校參數（非阻塞接收）
WS_RECV_TIMEOUT = 0  # 非阻塞；若想增穩可設 0.01~0.02

# ======== 主動煞車 / 漂停 ========
USE_ACTIVE_BRAKE = True

def motor_brake():
    motor_in1.high()
    motor_in2.high()
    try:
        motor_pwm.duty_u16(65535)
    except:
        pass

def motor_coast():
    try:
        motor_pwm.duty_u16(0)
    except:
        pass
    motor_in1.low()
    motor_in2.low()

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

    if sp == 0:
        if USE_ACTIVE_BRAKE:
            motor_brake()
        else:
            motor_coast()
        return

    try:
        motor_pwm.duty_u16(0)
    except:
        pass

    if sp > 0:
        motor_in1.high(); motor_in2.low()
    else:
        motor_in1.low();  motor_in2.high()

    try:
        motor_pwm.duty_u16(int(abs(sp) * 65535 / 100))
    except:
        pass

def encoder_interrupt(pin):
    global encoder_count, last_state_A
    state_a = encoder_pin_A.value()
    if state_a != last_state_A:
        state_b = encoder_pin_B.value()
        encoder_count += 1 if state_a == state_b else -1
        last_state_A = state_a

encoder_pin_A.irq(trigger=Pin.IRQ_RISING | Pin.IRQ_FALLING, handler=encoder_interrupt)

def run_encoder_Auto(motor_angle, speed, steer_deg):
    global encoder_count
    encoder_count = 0
    set_servo_angle(steer_deg)
    while abs(encoder_count) < motor_angle:
        control_motor(speed)
        time.sleep(0.01)
    control_motor(0)

def measure_distance(trig, echo):
    trig.value(0); time.sleep_us(2)
    trig.value(1); time.sleep_us(10); trig.value(0)
    duration = time_pulse_us(echo, 1)
    if duration <= 0:
        return 9999
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
            time.sleep(0.1)
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

# =============== 解析工具 ===============
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
    if len(parts) == 2:
        try:
            val = int(parts[1])
            return _clamp(val, -180, 180), 0
        except:
            return None
    if len(parts) >= 3:
        try:
            rel = int(parts[1])
            spd = int(parts[2])
        except:
            return None
        return _clamp(rel, -180, 180), _clamp(spd, -100, 100)
    return None

# ---- 把 JSON 內的洋紅欄位拉出來（ROI6） ----
def extract_magenta_from_json(obj):
    global magArea, magCX, magCY
    if not obj:
        return
    try:
        if "magArea" in obj: magArea = int(obj["magArea"])
        if "magCX"   in obj: magCX   = int(obj["magCX"])
        if "magCY"   in obj: magCY   = int(obj["magCY"])
    except:
        pass

# --------------- 流式拆 JSON / M 指令 / STOP（非阻塞） ---------------
def pump_ws(sock):
    """
    回傳 (json_obj, m_tuple, got_stop)
    """
    global RXBUF
    json_obj = None
    m_tuple = None
    got_stop = False

    msg = ws_recv_text(sock, timeout=WS_RECV_TIMEOUT)
    if msg:
        RXBUF += msg

    if len(RXBUF) > 4096:
        RXBUF = RXBUF[-1024:]

    idx_stop = RXBUF.find("STOP")
    if idx_stop != -1:
        end = idx_stop + 4
        if end < len(RXBUF) and RXBUF[end:end+1] == "\n":
            end += 1
        RXBUF = RXBUF[:idx_stop] + RXBUF[end:]
        got_stop = True
        if DEBUG:
            print("[PICO] GOT STOP SIGNAL")

    for _ in range(12):
        if not RXBUF:
            break

        idx_json = RXBUF.find("{")
        idx_m    = RXBUF.find("M,")

        if idx_json == -1 and idx_m == -1:
            break

        if idx_json != -1 and (idx_m == -1 or idx_json < idx_m):
            end = RXBUF.find("}", idx_json)
            if end == -1:
                break
            candidate = RXBUF[idx_json:end+1]
            RXBUF = RXBUF[end+1:]
            obj = parse_json_msg(candidate)
            if obj:
                json_obj = obj
                if DEBUG: print("PARSED_JSON:", obj)
                extract_magenta_from_json(obj)
                continue
            else:
                continue
        else:
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
    global LAST_COLOR, encoder_count, mag_area, mag_cx, mag_cy
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
            s.settimeout(0.05)
            s.connect((JETSON_IP, WS_PORT))
            ws_client_handshake(s, JETSON_IP, WS_PORT)
            print("WebSocket connected.")
            s.settimeout(0.01)

            ws_send_text(s, json.dumps({"from":"pico","status":"ready"}) + "\n")
            led.on()
            mode = 0
            turn = 0
            color = 0
            count = 0
            yaw = 0
            angle_from_jetson = 0
            speed_from_jetson = 0
            leftArea = 0
            rightArea = 0
            LAST_COLOR = 0
            aDiff = 0
            deg = 0
            prevDiff = 0
            error = 0
            error1 = 0
            Servo_angle = 0

            # --- mode 0：取起跑方向 ---
            print("進入 mode=0（取起跑方向），等待 Jetson 的 M,<turn>,* ...")
            while mode == 0 and turn == 0:
                json_obj, m_tuple, got_stop = pump_ws(s)
                if got_stop:
                    control_motor(0)
                    set_servo_angle(0)
                    print("[HALT] STOP received (mode0)")
                    return

                if json_obj:
                    try:
                        if "color" in json_obj:
                            LAST_COLOR = int(json_obj["color"])
                            if DEBUG: print("[LATCH] JSON color ->", LAST_COLOR)
                        elif "c" in json_obj:
                            LAST_COLOR = int(json_obj["c"])
                            if DEBUG: print("[LATCH] JSON c ->", LAST_COLOR)
                        # ★抽出洋紅欄位
                        extract_magenta_from_json(json_obj)
                    except:
                        pass
                    try:
                        if "yaw" in json_obj:
                            yaw = float(json_obj.get("yaw", yaw))
                        if "angle" in json_obj:
                            angle_from_jetson = int(json_obj.get("angle", angle_from_jetson))
                        if "speed" in json_obj:
                            speed_from_jetson = int(json_obj.get("speed", speed_from_jetson))
                        if "leftArea" in json_obj:
                            leftArea = int(json_obj.get("leftArea", leftArea))
                        if "rightArea" in json_obj:
                            rightArea = int(json_obj.get("rightArea", rightArea))
                    except:
                        pass

                if m_tuple:
                    candidate = m_tuple[0]
                    if candidate in (1, 2):
                        turn = candidate
                        print("設定 turn =", turn)
                    else:
                        if DEBUG: print("[SKIP] M in mode0 (not turn):", m_tuple)

                if json_obj is None and m_tuple is None:
                    time.sleep(0.01)

            # --- 根據 turn 執行旋轉 ---
            if turn == 1:
                print("右轉")
                run_encoder_Auto(500, 40, 180)
            else:
                print("左轉")
                run_encoder_Auto(1200, 40, -180)

            # --- mode 1：顏色決策 ---
            mode = 1
            LAST_COLOR = 0
            color = 0
            print(mode, color)
            print('等待 color（M,<1..6>[,<...>] 或 JSON {"color":n}）...')

            while mode == 1 and color == 0:
                json_obj, m_tuple, got_stop = pump_ws(s)

                if json_obj:
                    v = None
                    try:
                        if "color" in json_obj:
                            v = int(json_obj["color"])
                        elif "c" in json_obj:
                            v = int(json_obj["c"])
                    except:
                        v = None
                    if v is not None:
                        if 1 <= v <= 6:
                            color = v
                            LAST_COLOR = color
                            print("[JSON] color =", color)
                            break
                        else:
                            if DEBUG: print("[IGNORE] JSON color out of range:", v)
                    extract_magenta_from_json(json_obj)

                if m_tuple:
                    first = m_tuple[0]
                    if 1 <= first <= 6:
                        color = first
                        LAST_COLOR = color
                        print("[M] color =", color, "raw:", m_tuple)
                        break
                    else:
                        if DEBUG: print("[IGNORE] M packet in mode1 (not color):", m_tuple)

                if json_obj is None and m_tuple is None:
                    time.sleep(0.002)

            # --- 顏色對應動作（略，以你原本流程為準） ---
            if color == 1:
                print("顏色=1")
                run_encoder_Auto(2100, 60, 0)
                run_encoder_Auto(1400, 40, 180)
                run_encoder_Auto(1200, -45, 0)
            elif color == 2:
                print("顏色=2")
                run_encoder_Auto(1700, 60, 0)
                run_encoder_Auto(1150, -40, -180)
            elif color == 3:
                print("顏色=3")
                run_encoder_Auto(1700, 60, 0)
                run_encoder_Auto(1150, -40, -180)
            elif color == 4:
                print("顏色=4")
                run_encoder_Auto(600, 40, 180)
                run_encoder_Auto(400, 50, 0)
                run_encoder_Auto(1100, 40, -180)
                run_encoder_Auto(800, 50, 0)
            elif color == 5:
                print("顏色=5")
                run_encoder_Auto(600, 40, 180)
                run_encoder_Auto(2200, 60, 0)
                run_encoder_Auto(1150, 40, -180)
                run_encoder_Auto(800, 50, 0)
            elif color == 6:
                print("顏色=6")
                run_encoder_Auto(600, 40, 180)
                run_encoder_Auto(1500, 60, 0)
                run_encoder_Auto(1150, 40, -180)

            control_motor(0)
            set_servo_angle(0)

            # --- mode 2：一般控制（同步接收洋紅資訊） ---
            mode = 2
            print("進入 mode=2（一般控制），等待 M,<rel>,<spd> ...")
            while mode == 2:
                json_obj, m_tuple, got_stop = pump_ws(s)
                if got_stop:
                    control_motor(0)
                    set_servo_angle(0)
                    print("[HALT] STOP received (mode2)")
                    mode = 3
                if m_tuple:
                    rel, spd = m_tuple
                    set_servo_angle(rel)
                    control_motor(spd)
                if json_obj:
                    extract_magenta_from_json(json_obj) 

                if json_obj is None and m_tuple is None:
                    time.sleep(0.001)

            # --- mode 3 ~ 7（保留原本流程），期間也更新洋紅資訊 ---
            while mode == 3:
                json_obj, _, got_stop = pump_ws(s)
                extract_magenta_from_json(json_obj)
                while abs(yaw) < 73:
                    json_obj, _, got_stop = pump_ws(s)
                    if json_obj:
                        if "yaw" in json_obj:
                            try:
                                yaw = float(json_obj["yaw"])
                            except:
                                pass
                        extract_magenta_from_json(json_obj)
                    if turn == 2:    
                        set_servo_angle(50)
                        control_motor(35)
                    else:
                        set_servo_angle(-50)
                        control_motor(35)                        
                motor_brake()
                set_servo_angle(0)
                mode = 4

            while mode == 4:
                a0_value = A0.read_u16()
                time_a0=time.time()
                set_servo_angle(0)
                while a0_value > 64500 and time.time()- time_a0 < 6:
                    a0_value = A0.read_u16()
                    extract_magenta_from_json(json_obj) 
                    json_obj, _, got_stop = pump_ws(s)
                    if json_obj:
                        if "yaw" in json_obj:
                            try:
                                yaw = float(json_obj["yaw"])
                            except:
                                pass
                        extract_magenta_from_json(json_obj)  
                    set_servo_angle(0)
                    control_motor(30)
                control_motor(-40)
                time.sleep(0.15)
                control_motor(0)
                run_encoder_Auto(100, -35, 0)
                mode = 5

            while mode == 5:
                json_obj, _, got_stop = pump_ws(s)
                while abs(yaw) < 177:
                    extract_magenta_from_json(json_obj)
                    json_obj, _, got_stop = pump_ws(s)
                    if json_obj:
                        if "yaw" in json_obj:
                            try:
                                yaw = float(json_obj["yaw"])
                            except:
                                pass
                    if turn == 2:
                        set_servo_angle(-180)
                        control_motor(-35)
                    else:
                        set_servo_angle(180)
                        control_motor(-35)                        
                motor_brake()
                set_servo_angle(0)
                mode = 6
        
            while mode == 6:
                control_motor(38)
                json_obj, m_tuple, got_stop = pump_ws(s)
                extract_magenta_from_json(json_obj)
                while magArea > 100:
                    extract_magenta_from_json(json_obj)
                    json_obj, m_tuple, got_stop = pump_ws(s)
                    if json_obj:
                        try:
                            if "leftArea" in json_obj:
                                leftArea = int(json_obj.get("leftArea", leftArea))
                            if "rightArea" in json_obj:
                                rightArea = int(json_obj.get("rightArea", rightArea))
                        except:
                            pass
                    if turn ==2:
                        if magArea > 3000:
                            error = magCX - 150 
                            Servo_angle = int(error*0.15 + (error - error1)*0.2)
                            error1 = error
                            set_servo_angle(Servo_angle)
                        else:
                            error = leftArea - 6500
                            Servo_angle = int(error*0.003 + (error - error1)*0.008)
                            error1 = error
                            set_servo_angle(Servo_angle)
                    else:
                        if magArea > 3000:
                            error = magCX - 470
                            Servo_angle = int(error*0.13 + (error - error1)*0.2)
                            error1 = error
                            set_servo_angle(Servo_angle)
                        else:
                            error = 8000 - rightArea 
                            Servo_angle = int(error*0.003 + (error - error1)*0.008)
                            error1 = error
                            set_servo_angle(Servo_angle)
                control_motor(-30)
                time.sleep(0.1)
                control_motor(0)
                mode = 7
            while mode == 7:
                encoder_count = 0
                control_motor(38)
                json_obj, m_tuple, got_stop = pump_ws(s)
                extract_magenta_from_json(json_obj)
                while abs(encoder_count) < 100:
                    extract_magenta_from_json(json_obj)
                    json_obj, m_tuple, got_stop = pump_ws(s)
                    if json_obj:
                        try:
                            if "leftArea" in json_obj:
                                leftArea = int(json_obj.get("leftArea", leftArea))
                            if "rightArea" in json_obj:
                                rightArea = int(json_obj.get("rightArea", rightArea))
                        except:
                            pass
                    if turn == 2:
                        error = leftArea - 6500
                        Servo_angle = int(error*0.005 + (error - error1)*0.008)
                        error1 = error
                        set_servo_angle(Servo_angle)
                    else:
                        error = 3500 - rightArea
                        Servo_angle = int(error*0.005 + (error - error1)*0.01)
                        error1 = error
                        set_servo_angle(Servo_angle)
                mode = 8
            while mode == 8:
                json_obj, _, got_stop = pump_ws(s)
                while abs(yaw) > 123:
                    json_obj, _, got_stop = pump_ws(s)
                    if json_obj:
                        if "yaw" in json_obj:
                            try:
                                yaw = float(json_obj["yaw"])
                            except:
                                pass
                    if turn == 2:     
                        set_servo_angle(-180)
                        control_motor(-37)
                    else:
                        set_servo_angle(180)
                        control_motor(-37)
                motor_brake()
                set_servo_angle(0)
                mode =9 
            while mode == 9:
                json_obj, _, got_stop = pump_ws(s)
                a1_value = A1.read_u16()
                while abs(yaw) < 177 and a1_value > 64000:
                    a0_value = A0.read_u16()
                    json_obj, _, got_stop = pump_ws(s)
                    if json_obj:
                        if "yaw" in json_obj:
                            try:
                                yaw = float(json_obj["yaw"])
                            except:
                                pass
                    if turn == 2:     
                        set_servo_angle(180)
                        control_motor(-35)
                    else:
                        set_servo_angle(-180)
                        control_motor(-35)   
                control_motor(40)
                time.sleep(0.15)
                control_motor(0)
                set_servo_angle(0)
                mode =10 
            while mode == 10:
                motor_brake()
                
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



