import sys, cv2, time, json, queue, threading, asyncio, websockets, numpy as np
import Jetson.GPIO as GPIO
from functions_jetson import find_contours, max_contour
from masks import rOrange, rBlack, rBlue


class WsServer:
    def __init__(self, host="0.0.0.0", port=8765):
        self.host = host
        self.port = port
        self.clients = set()
        self._thread = None
        self._loop = None
        self._stop_evt = threading.Event()

    def start(self):
        self._thread = threading.Thread(target=self._run, daemon=True)
        self._thread.start()

    def stop(self):
        self._stop_evt.set()
        if self._loop:
            try:
                for ws in list(self.clients):
                    asyncio.run_coroutine_threadsafe(ws.close(code=1001, reason="server stop"), self._loop)
            except RuntimeError:
                pass
        if self._thread:
            self._thread.join(timeout=2)

    async def _handler(self, ws):
        peer = getattr(ws.remote_address, "host", None) or str(ws.remote_address)
        self.clients.add(ws)
        try:
            await ws.send('{"from":"jetson","status":"ready"}')
            async for msg in ws:
                dead = []
                for cli in self.clients:
                    if cli is ws:
                        continue
                    try:
                        await cli.send(msg)
                    except Exception:
                        dead.append(cli)
                for d in dead:
                    self.clients.discard(d)
        except Exception as e:
            print("WS error:", e)
        finally:
            self.clients.discard(ws)
            print("Client disconnected:", peer)

    async def _main(self):
        async with websockets.serve(
            self._handler, self.host, self.port,
            ping_interval=None, compression=None, max_size=None, close_timeout=1.5
        ):
            while not self._stop_evt.is_set():
                await asyncio.sleep(0.5)

    def _run(self):
        self._loop = asyncio.new_event_loop()
        asyncio.set_event_loop(self._loop)
        try:
            self._loop.run_until_complete(self._main())
        finally:
            self._loop.close()

WS_SERVER_URL = "ws://127.0.0.1:8765"
class WsBus:
    def __init__(self, url: str):
        self.url = url
        self.tx_q: "queue.Queue[str]" = queue.Queue()
        self.rx_q: "queue.Queue[str]" = queue.Queue()
        self._thread = None
        self._loop = None
        self._ws = None
        self._stop = threading.Event()
        self.ready = False

    def start(self):
        self._thread = threading.Thread(target=self._run_loop, daemon=True)
        self._thread.start()

    def stop(self):
        self._stop.set()
        if self._loop:
            try:
                asyncio.run_coroutine_threadsafe(self._async_close(), self._loop)
            except RuntimeError:
                pass
        if self._thread:
            self._thread.join(timeout=2)

    def send(self, obj: dict):
        try:
            self.tx_q.put_nowait(json.dumps(obj))
        except queue.Full:
            pass

    def get(self, timeout=0.0):
        try:
            return self.rx_q.get(timeout=timeout)
        except queue.Empty:
            return None

    def wait_until_ready(self, timeout_sec=5.0):
        t0 = time.time()
        while time.time() - t0 < timeout_sec:
            if self.ready:
                return True
            msg = self.get(timeout=0.2)
            if msg:
                self.ready = True
                return True
        return False

    def _run_loop(self):
        self._loop = asyncio.new_event_loop()
        asyncio.set_event_loop(self._loop)
        self._loop.run_until_complete(self._main())

    async def _main(self):
        while not self._stop.is_set():
            try:
                async with websockets.connect(self.url, ping_interval=None) as ws:
                    self._ws = ws
                    await self._safe_send(json.dumps({"cmd": "ping"}))
                    rx_task = asyncio.create_task(self._rx_loop(ws))
                    tx_task = asyncio.create_task(self._tx_loop(ws))
                    done, pending = await asyncio.wait(
                        {rx_task, tx_task}, return_when=asyncio.FIRST_EXCEPTION
                    )
                    for t in pending: t.cancel()
            except Exception as e:
                await asyncio.sleep(1.0)

    async def _rx_loop(self, ws):
        while not self._stop.is_set():
            msg = await ws.recv()
            if isinstance(msg, (bytes, bytearray)):
                msg = msg.decode("utf-8", errors="ignore")
            self.ready = True
            try:
                self.rx_q.put_nowait(msg)
            except queue.Full:
                pass

    async def _tx_loop(self, ws):
        while not self._stop.is_set():
            try:
                msg = self.tx_q.get(timeout=0.2)
            except queue.Empty:
                await asyncio.sleep(0.01)
                continue
            await self._safe_send(msg)

    async def _safe_send(self, msg: str):
        try:
            await self._ws.send(msg)
        except Exception as e:
            print("[WS] send error:", e)

    async def _async_close(self):
        try:
            if self._ws:
                await self._ws.close()
        except:
            pass

# ===================== IMU Stub =====================
def read_imu_angle():
    return 0

# ===================== GStreamer =====================
def gstreamer_pipeline(sensor_id=0, capture_width=640, capture_height=480,
                       display_width=640, display_height=480,
                       framerate=30, flip_method=0):
    return (
        f"nvarguscamerasrc sensor-id={sensor_id} ! "
        f"video/x-raw(memory:NVMM), width={capture_width}, height={capture_height}, "
        f"format=NV12, framerate={framerate}/1 ! "
        f"nvvidconv flip-method={flip_method} ! "
        f"video/x-raw, width={display_width}, height={display_height}, format=BGRx ! "
        f"videoconvert ! "
        f"video/x-raw, format=BGR ! appsink"
    )

# ===================== LED =====================
GPIO.setmode(GPIO.BCM)
GPIO.setwarnings(False)
LED_PIN = 21  
BUTTON_PIN = 18  
GPIO.setup(LED_PIN, GPIO.OUT)
GPIO.setup(BUTTON_PIN, GPIO.IN, pull_up_down=GPIO.PUD_DOWN)

def led_on(): GPIO.output(LED_PIN, GPIO.HIGH)
def led_off(): GPIO.output(LED_PIN, GPIO.LOW)

def wait_for_button_press():
    led_on()
    print("Please press the button to begin.！")
    while GPIO.input(BUTTON_PIN) == GPIO.LOW:
        time.sleep(0.05)
    print(" The button was pressed, and execution began.！")
    
    time.sleep(0.3)

ws_server = WsServer(host="0.0.0.0", port=8765)
ws_bus = WsBus(WS_SERVER_URL)

def send_motor(angle: int, speed: int):
    ws_bus.send({"cmd": "steer", "angle": int(angle)})
    ws_bus.send({"cmd": "motor", "speed": int(speed)})

def stop_car():
    ws_bus.send({"cmd": "motor", "speed": 0})
    ws_bus.send({"cmd": "steer", "angle": 0})
    led_off()


def display_roi_with_contours(img, rois, color=(255, 204, 0)):
    preview = img.copy()
    for roi in rois:
        x1, y1, x2, y2 = roi
        cv2.rectangle(preview, (x1, y1), (x2, y2), color, 2)
    return preview

def draw_contours_in_roi(preview_img, contours, roi, draw_color=(0, 255, 0)):
    for contour in contours:
        offset_contour = contour + np.array([[roi[0], roi[1]]])
        cv2.drawContours(preview_img, [offset_contour], -1, draw_color, 2)      


if __name__ == '__main__':
    global leftArea, rightArea, orangeArea, blueArea
    led_off()
    ws_server.start()
    ws_bus.start()
    
    ws_bus.wait_until_ready(timeout_sec=5.0)

    cap = cv2.VideoCapture(gstreamer_pipeline(flip_method=0), cv2.CAP_GSTREAMER)
    if not cap.isOpened():
        print("NO CSI camera")
        ws_bus.stop()
        ws_server.stop()
        sys.exit(1)

    ROI1, ROI2, ROI3 = [0,180,330,245], [330,180,640,245], [50,300,580,345]


    kp, kd, speed = 0.01, 0.015, 70
    turnThresh, exitThresh = 100, 0
    aDiff = prevDiff = prevAngle = 0
    lTurn = rTurn = False
    t = 0
    started = False
    turnDir = "none"
    blueLineThreshold = 90
    blueLineDetected = False
    lastBlueDetectTime = 0
    blueLineCooldown = 2.0

    leftArea = rightArea = blueArea = orangeArea = 0


    try:
        count = 0
        start_time = 0
        angle = 120
        error = 0
        time1 = 0

        wait_for_button_press()
        started = True

        while True:
            ret, img = cap.read()
            if not ret:
        
                break

            preview_img = display_roi_with_contours(img.copy(), [ROI1, ROI2, ROI3], (255, 204, 0))

            if started:
                img_lab = cv2.cvtColor(img, cv2.COLOR_BGR2Lab)
                img_lab = cv2.GaussianBlur(img_lab, (7, 7), 0)

                cListLeft   = find_contours(img_lab, rBlack,  ROI1)
                cListRight  = find_contours(img_lab, rBlack,  ROI2)
                cListOrange = find_contours(img_lab, rOrange, ROI3)
                cListBlue   = find_contours(img_lab, rBlue,   ROI3)
                  
                leftArea   = max_contour(cListLeft,  ROI1)[0]
                rightArea  = max_contour(cListRight, ROI2)[0]
                orangeArea = max_contour(cListOrange, ROI3)[0]
                blueArea   = max_contour(cListBlue,   ROI3)[0]

                draw_contours_in_roi(preview_img, cListLeft,  ROI1, (0,255,0))
                draw_contours_in_roi(preview_img, cListRight, ROI2, (0,255,0))
                draw_contours_in_roi(preview_img, cListOrange, ROI3, (0,140,255))
                draw_contours_in_roi(preview_img, cListBlue,   ROI3, (255,0,0))

                cv2.putText(preview_img, f"L:{leftArea}",  (ROI1[0], ROI1[1]-10), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0,255,0), 2)
                cv2.putText(preview_img, f"R:{rightArea}", (ROI2[0], ROI2[1]-10), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0,255,0), 2)
                cv2.putText(preview_img, f"Diff:{rightArea-leftArea}", (10,30), cv2.FONT_HERSHEY_SIMPLEX,0.7,(255,255,255),2)
                 
        
                if orangeArea > 100 and turnDir=="none" and time.time() - time1 > 1.5 and rightArea < 1600:
                    turnDir="right"
                    rTurn = True
                    print("right")
                elif blueArea > 100 and turnDir=="none" and time.time() - time1 > 1.5 and leftArea < 100:
                    turnDir="left"
                    lTurn = True
                    print("left")
              
                currentTime = time.time()
                if blueArea > blueLineThreshold:
                    if not blueLineDetected and (currentTime - lastBlueDetectTime) > blueLineCooldown:
                        t += 1
                        blueLineDetected = True
                        lastBlueDetectTime = currentTime
                        print(f"t +1， t={t}")
                else:
                    blueLineDetected = False


                if lTurn:
                    angle = -60
                    print(leftArea,rightArea,angle)
                    send_motor(int(angle), speed)
                    error = 3000
                    exitThresh = 4000
                if rTurn:
                    angle = 75
                    print(leftArea,rightArea,angle)
                    send_motor(int(angle), speed)
                    error = -11000
                    exitThresh = 5000
                if not lTurn and not rTurn:
                    aDiff = (leftArea - rightArea) - error
                    angle = aDiff * kp + (aDiff - prevDiff) * kd
                    angle = max(min(angle, 70), -70)
                    print("Forword",angle)
                    send_motor(int(angle), speed)
                    
 
                if (rightArea > exitThresh and rTurn) or (leftArea > exitThresh and lTurn):
                    turnDir = "none"
                    lTurn = rTurn = False
                    error = 0
                    print("Turn_end")
                    time1 = time.time()
                prevDiff = aDiff
                prevAngle = int(angle)
                
                if t >= 12:
                    
                    if count == 0:
                        start_time = time.time()
                        count = count + 1
                        
                if time.time() - start_time > 1.7 and count != 0:

                    stop_car()
                    break

            cv2.imshow("finalColor", preview_img)
            if cv2.waitKey(1) & 0xFF == ord('q'):
                stop_car()
                break

    finally:
        cap.release()
        cv2.destroyAllWindows()
        ws_bus.stop()
        ws_server.stop()
