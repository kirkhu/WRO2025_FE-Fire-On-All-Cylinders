from machine import Pin, PWM
import time
import network
import usocket as socket
import uos, ubinascii
import ujson as json


SSID = "iPhone_ron"
PASSWORD = "ron0975750386"
JETSON_IP = "172.20.10.8"
PORT = 8765


servo_pin = PWM(Pin(4), freq=50)
motor_in1 = Pin(21, Pin.OUT)
motor_in2 = Pin(20, Pin.OUT)
button_out = Pin(15, Pin.OUT)

motor_pwm = PWM(Pin(22), freq=1000)
encoder_pin_A = Pin(0, Pin.IN)
encoder_pin_B = Pin(1, Pin.IN)
button = Pin(18, Pin.IN, Pin.PULL_UP)

encoder_count = 0
last_state_A = encoder_pin_A.value()
_prev_speed_abs = 0 
led = Pin("LED", Pin.OUT)

def set_servo_angle(angle):
    min_duty = 1000  
    max_duty = 2000  
    duty = int(min_duty + (angle - 15 + 180) * (max_duty - min_duty) / 360)
    duty_u16 = int(duty * 65535 / 20000)
    servo_pin.duty_u16(duty_u16)

def control_motor(speed):
    """speed: -100 ~ 100"""
    global _prev_speed_abs
    abs_speed = abs(speed)

    if abs_speed > 0 and abs_speed < 20:
        abs_speed = 20
    if _prev_speed_abs == 0 and abs_speed > 0:
        motor_pwm.duty_u16(int(65535 * 0.6))  
    _prev_speed_abs = abs_speed

    if speed > 0:
        motor_in1.high()
        motor_in2.low()
    elif speed < 0:
        motor_in1.low()
        motor_in2.high()
    else:
        motor_in1.low()
        motor_in2.low()

    motor_pwm.duty_u16(int(abs_speed * 65535 / 100))


def encoder_interrupt(pin):
    global encoder_count, last_state_A
    state_a = encoder_pin_A.value()
    if state_a != last_state_A:
        state_b = encoder_pin_B.value()
        encoder_count += 1 if state_a == state_b else -1
        last_state_A = state_a

encoder_pin_A.irq(trigger=Pin.IRQ_RISING | Pin.IRQ_FALLING, handler=encoder_interrupt)


def connect_wifi():
    wlan = network.WLAN(network.STA_IF)
    wlan.active(True)
    if not wlan.isconnected():
        print("Connecting WiFi...")
        wlan.connect(SSID, PASSWORD)
        t0 = time.time()
        while not wlan.isconnected():
            if time.time() - t0 > 20:
                raise OSError("WiFi connect timeout")
            time.sleep(0.2)
    print(" WiFi ", wlan.ifconfig())
    return wlan


def _recvn(sock, n):
    data = b""
    while len(data) < n:
        chunk = sock.recv(n - len(data))
        if not chunk:
            raise OSError("socket closed")
        data += chunk
    return data

def ws_client_handshake(sock, host, port):
    key_b64 = ubinascii.b2a_base64(uos.urandom(16)).strip().decode()
    req = (
        "GET / HTTP/1.1\r\n"
        "Host: {}:{}\r\n"
        "Upgrade: websocket\r\n"
        "Connection: Upgrade\r\n"
        "Sec-WebSocket-Key: {}\r\n"
        "Sec-WebSocket-Version: 13\r\n"
        "\r\n"
    ).format(host, port, key_b64)
    sock.send(req.encode())
    resp = b""
    sock.settimeout(5)
    while b"\r\n\r\n" not in resp:
        part = sock.recv(256)
        if not part:
            break
        resp += part
    if b"101 Switching Protocols" not in resp:
        raise OSError("WS handshake failed")

def ws_send_text(sock, text):
    payload = text.encode("utf-8")
    plen = len(payload)
    header = bytearray([0x81])
    mask_bit = 0x80
    if plen <= 125:
        header.append(mask_bit | plen)
    elif plen <= 65535:
        header.append(mask_bit | 126)
        header.extend(bytes([(plen >> 8) & 0xFF, plen & 0xFF]))
    else:
        raise ValueError("payload too long")
    mask_key = uos.urandom(4)
    header.extend(mask_key)
    masked = bytearray(plen)
    for i in range(plen):
        masked[i] = payload[i] ^ mask_key[i % 4]
    sock.send(header + masked)

def ws_recv_text(sock, timeout=0.2):
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
        _ = _recvn(sock, 4)
    payload = _recvn(sock, plen) if plen else b""
    return payload.decode("utf-8") if payload else ""


try:
    motor_in1.off(); motor_in2.off()
    control_motor(0)
    set_servo_angle(0)
    wlan = connect_wifi()
    led.off()

    while True:
        s = None
        try:
            print("Connecting TCP to {}:{}".format(JETSON_IP, PORT))
            s = socket.socket()
            s.connect((JETSON_IP, PORT))
            ws_client_handshake(s, JETSON_IP, PORT)
            print(" WebSocket Connected!")
            s.settimeout(0.1)

            ws_send_text(s, json.dumps({"from": "pico", "status": "ready"}))
            led.on()

            while True:
                msg = ws_recv_text(s, timeout=0.01)
                if not msg:
                    continue
                for line in msg.split("\n"):
                    line = line.strip()
                    if not line:
                        continue

                    if line == "STOP":
                        print("  STOP")
                        control_motor(0)
                        set_servo_angle(0)
                        raise KeyboardInterrupt

                    if line.startswith("M,"):
                        try:
                            _, angle_str, speed_str = line.split(",")
                            angle = int(angle_str)
                            speed = int(speed_str)
                            set_servo_angle(angle)
                            control_motor(speed)

                           
                            print(" 角度 = {:>4d}, 速度 = {:>4d}, 編碼器 = {:>6d}".format(
                                angle, speed, encoder_count
                            ))
                        except ValueError:
                            print("指令解析失敗:", line)
                        continue

                    if line.startswith("{"):
                        try:
                            j = json.loads(line)
                            if j.get("cmd") == "motor":
                                spd = int(j.get("speed", 0))
                                control_motor(spd)
                                print(" JSON 馬達速度:", spd)
                            elif j.get("cmd") == "steer":
                                ang = int(j.get("angle", 90))
                                set_servo_angle(ang)
                                print("JSON 舵機角度:", ang)
                            elif j.get("cmd") == "stop":
                                control_motor(0)
                                set_servo_angle(0)
                                raise KeyboardInterrupt
                        except Exception:
                            pass
                time.sleep(0.01)

        except KeyboardInterrupt:
            control_motor(0)
            set_servo_angle(0)
            print("程式中斷")
            break

        except Exception as e:
            print("WS error:", e)
            if s:
                try: s.close()
                except: pass
            print(" Reconnecting in 3s...")
            time.sleep(3)

except KeyboardInterrupt:
    control_motor(0)
    set_servo_angle(0)
    print(" 程式中斷(外層)")




