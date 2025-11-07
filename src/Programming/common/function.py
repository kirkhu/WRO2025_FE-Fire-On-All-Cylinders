# functions_jetson.py  — WebSocket 版本（取代 UART）
import time
import json
import asyncio
import threading
import queue
import cv2
import numpy as np
import websockets
from masks import rBlack, rMagenta, rRed, rGreen, rBlue, rOrange

WS_SERVER_URL = "ws://127.0.0.1:8765"

straight_const = 87

_last_speed_pct = 0     
_last_angle_deg = 0     

class _WsBus:
    def __init__(self, url: str):
        self.url = url
        self.tx_q: "queue.Queue[str]" = queue.Queue()
        self.rx_q: "queue.Queue[str]" = queue.Queue()
        self._loop = None
        self._ws = None
        self._thread = None
        self._stop = threading.Event()
        self.ready = False

    def start(self):
        if self._thread and self._thread.is_alive():
            return
        self._thread = threading.Thread(target=self._run_loop, daemon=True)
        self._thread.start()

    def stop(self):
        self._stop.set()
        if self._loop:
            try:
                asyncio.run_coroutine_threadsafe(self._async_close(), self._loop)
            except Exception:
                pass
        if self._thread:
            self._thread.join(timeout=2)

    def send_obj(self, obj: dict):
        try:
            self.tx_q.put_nowait(json.dumps(obj))
        except queue.Full:
            pass

    def recv_str(self, timeout: float | None = None) -> str | None:
        try:
            return self.rx_q.get(timeout=timeout)
        except queue.Empty:
            return None

    def wait_until_any_message(self, timeout_sec=5.0) -> bool:

        t0 = time.time()
        while time.time() - t0 < timeout_sec:
            if self.ready:
                return True
            msg = self.recv_str(timeout=0.2)
            if msg:
                self.ready = True
                return True
        return False

    # ----- asyncio internals -----
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
                    rx = asyncio.create_task(self._rx_loop(ws))
                    tx = asyncio.create_task(self._tx_loop(ws))
                    done, pending = await asyncio.wait(
                        {rx, tx}, return_when=asyncio.FIRST_EXCEPTION
                    )
                    for t in pending:
                        t.cancel()
            except Exception as e:
                # print("[WS] reconnect in 1s", e)
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
                s = self.tx_q.get(timeout=0.2)
            except queue.Empty:
                await asyncio.sleep(0.01)
                continue
            await self._safe_send(s)

    async def _safe_send(self, s: str):
        try:
            await self._ws.send(s)
        except Exception:
            pass

    async def _async_close(self):
        try:
            if self._ws:
                await self._ws.close()
        except Exception:
            pass

_ws = _WsBus(WS_SERVER_URL)
_ws.start()


def _pwm_to_speed_percent(pwm: int) -> int:

    pct = int(round((pwm - 1500) / 180.0 * 100.0))
    return max(-100, min(100, pct))

def stop_car():

    _ws.send_obj({"cmd": "motor", "speed": 0})
    _ws.send_obj({"cmd": "steer", "angle": 0})

def wait_for_start(timeout=None):

    start_t = time.time()

    if timeout is None:
        timeout = 9999999


    _ws.wait_until_any_message(timeout_sec=min(timeout, 3.0))

    while True:
        msg = _ws.recv_str(timeout=0.2)
        if msg:
            s = msg.strip()
            try:
                j = json.loads(s)
            except Exception:
                j = None

            if s == "START":
                return True

            if j and (j.get("from") == "pico" or j.get("status") == "ready"):
                return True

        if timeout is not None and (time.time() - start_t) > timeout:
            return False


def display_roi(img, ROIs, color):
    for ROI in ROIs:
        img = cv2.line(img, (ROI[0], ROI[1]), (ROI[2], ROI[1]), color, 4)
        img = cv2.line(img, (ROI[0], ROI[1]), (ROI[0], ROI[3]), color, 4)
        img = cv2.line(img, (ROI[2], ROI[3]), (ROI[2], ROI[1]), color, 4)
        img = cv2.line(img, (ROI[2], ROI[3]), (ROI[0], ROI[3]), color, 4)
    return img

def find_contours(img_lab, lab_range, ROI):
    x1, y1, x2, y2 = ROI
    seg = img_lab[y1:y2, x1:x2]
    lo = np.array(lab_range[0]); hi = np.array(lab_range[1])
    mask = cv2.inRange(seg, lo, hi)
    k = np.ones((5,5), np.uint8)
    mask = cv2.erode(mask, k, iterations=1)
    mask = cv2.dilate(mask, k, iterations=1)
    contours = cv2.findContours(mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)[-2]
    return contours

def max_contour(contours, ROI):
    maxArea = 0; maxY = 0; maxX = 0; mCnt = 0
    for cnt in contours:
        area = cv2.contourArea(cnt)
        if area > 150:
            approx = cv2.approxPolyDP(cnt, 0.01*cv2.arcLength(cnt, True), True)
            x,y,w,h = cv2.boundingRect(approx)
            x += ROI[0] + w//2
            y += ROI[1] + h
            if area > maxArea:
                maxArea = area; maxY = y; maxX = x; mCnt = cnt
    return [maxArea, maxX, maxY, mCnt]

def pOverlap(img_lab, ROI, add=False):
    x1, y1, x2, y2 = ROI
    seg = img_lab[y1:y2, x1:x2]
    from masks import rBlack, rMagenta
    loB, hiB = np.array(rBlack[0]),   np.array(rBlack[1])
    loM, hiM = np.array(rMagenta[0]), np.array(rMagenta[1])
    mB = cv2.inRange(seg, loB, hiB)
    mM = cv2.inRange(seg, loM, hiM)
    if add:
        mask = cv2.add(mB, mM)
    else:
        mask = cv2.bitwise_and(mB, cv2.bitwise_not(mM))
    k_open  = np.ones((3,3), np.uint8)
    k_close = np.ones((7,7), np.uint8)
    mask = cv2.morphologyEx(mask, cv2.MORPH_OPEN,  k_open,  iterations=1)
    mask = cv2.morphologyEx(mask, cv2.MORPH_CLOSE, k_close, iterations=1)
    contours = cv2.findContours(mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)[-2]
    return contours

def display_variables(variables):
    names = list(variables.keys())
    for name in names:
        print(f"{name}: {variables[name]}", end="\r\n")
    print("\033[F" * len(names), end="")


def get_last_speed_pct() -> int:

    return _last_speed_pct

def is_moving(threshold: int = 3) -> bool:
    return abs(_last_speed_pct) > threshold
