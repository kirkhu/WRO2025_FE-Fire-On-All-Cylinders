import time  # Provides time-related functions such as sleep and current time
import json  # Used for encoding and decoding JSON data
import threading  # Used to create and manage threads for concurrent execution
import queue  # Provides thread-safe queues for inter-thread communication
import cv2  # OpenCV library for image processing and computer vision
import numpy as np  # NumPy for numerical operations and array handling
import serial  # pySerial library for serial (UART) communication
from masks import rBlack, rMagenta, rRed, rGreen, rBlue, rOrange  # Import predefined LAB color ranges for different colors

# ========= UART serial port settings =========  # Section header for UART serial configuration
SERIAL_PORT_NAME = "/dev/ttyTHS4"  # Device name of the UART port on Jetson
BAUD_RATE = 115200  # UART baud rate (bits per second)

# ========= Servo center / internal steering angle & speed state =========  # Section header for steering and speed state
straight_const = 87  # Center reference value for steering angle from vision algorithm

_last_speed_pct = 0  # Stores the last commanded motor speed in percentage
_last_angle_deg = 0  # Stores the last commanded steering angle in degrees (Pico convention)

# ========= UART =========  # Section header for UART communication class
class _UartBus:
    def __init__(self, port: str, baudrate: int):  # Initialize UART bus object with port and baudrate
        self.port = port  # Save serial port name
        self.baudrate = baudrate  # Save serial baud rate
        self.ser: serial.Serial | None = None  # Serial object, initially None until connected
        self.rx_q: "queue.Queue[str]" = queue.Queue()  # Queue to store received lines as strings
        self._thread = None  # Background thread handler for UART loop
        self._stop = threading.Event()  # Event flag used to stop the UART thread
        self.ready = False  # Indicates whether UART is ready and has exchanged messages
        self._lock = threading.Lock()  # Lock to protect concurrent writes to UART

    def start(self):  # Start background thread to handle UART receive loop
        if self._thread and self._thread.is_alive():  # If thread already running, do nothing
            return  # Exit without starting a new thread
        self._thread = threading.Thread(target=self._run_loop, daemon=True)  # Create daemon thread running _run_loop
        self._thread.start()  # Start the UART background thread

    def stop(self):  # Stop the UART thread and close the serial port
        self._stop.set()  # Signal the thread to stop
        if self._thread:  # If thread exists
            self._thread.join(timeout=2)  # Wait up to 2 seconds for thread to finish
        if self.ser and self.ser.is_open:  # If serial port exists and is open
            self.ser.close()  # Close the serial port

    def send_str(self, s: str):  # Send a string over UART with newline termination
        with self._lock:  # Acquire lock to prevent concurrent writes
            if self.ser and self.ser.is_open:  # Only send if serial port is open
                try:
                    self.ser.write((s + '\n').encode('utf-8'))  # Encode string as UTF-8 with newline and send
                except serial.SerialException as e:  # Handle serial write errors
                    print(f"[UART] Write error: {e}")  # Print error message
                    self.ready = False  # Mark UART as not ready on error
                except Exception:  # Catch any other unexpected exception
                    pass  # Ignore unknown send errors

    def recv_str(self, timeout: float | None = None) -> str | None:  # Receive one line from queue with optional timeout
        try:
            return self.rx_q.get(timeout=timeout)  # Get next line from receive queue
        except queue.Empty:  # If no data within timeout
            return None  # Return None to indicate no message

    def wait_until_any_message(self, timeout_sec=5.0) -> bool:  # Wait until any UART message arrives or timeout
        t0 = time.time()  # Record start time
        while time.time() - t0 < timeout_sec:  # Loop until timeout reached
            if self.ready:  # If already marked ready
                return True  # Return immediately
            msg = self.recv_str(timeout=0.2)  # Try to receive a line with short timeout
            if msg:  # If a message is received
                self.ready = True  # Mark UART as ready
                return True  # Return success
        return False  # Return False if no message within timeout

    # ----- Threading internals -----  # Section header for internal thread loop implementation
    def _run_loop(self):  # Background thread method to handle UART connection and reading
        while not self._stop.is_set():  # Continue running until stop flag is set
            if not self.ser or not self.ser.is_open:  # If serial not connected or closed
                self.ready = False  # Mark UART as not ready
                try:
                    self.ser = serial.Serial(  # Try to open serial port
                        port=self.port,  # Use configured port name
                        baudrate=self.baudrate,  # Use configured baud rate
                        timeout=0.01  # Set short read timeout for non-blocking behavior
                    )
                    print(f"[UART] Connected to {self.port} at {self.baudrate} bps.")  # Log successful connection
                    time.sleep(1.0)  # Wait briefly after opening to stabilize
                    self.send_str(json.dumps({"cmd": "ping"}))  # Send initial ping command to Pico
                    self.ready = True  # Mark UART as ready after successful send
                except serial.SerialException as e:  # If connection fails
                    time.sleep(1.0)  # Wait before retrying connection
                    continue  # Skip to next loop iteration and retry

            try:
                if self.ser.in_waiting > 0:  # Check if there is incoming data in buffer
                    line = self.ser.readline().decode('utf-8').strip()  # Read one line, decode and strip whitespace
                    if line:  # If line is not empty
                        self.ready = True  # Mark UART as ready, since data is flowing
                        try:
                            self.rx_q.put_nowait(line)  # Put received line into queue without blocking
                        except queue.Full:  # If queue is full
                            pass  # Drop oldest lines silently
                else:
                    time.sleep(0.005)  # If no data, sleep briefly to reduce CPU usage
            except serial.SerialException as e:  # Handle read errors
                if self.ser:  # If serial object exists
                    self.ser.close()  # Close serial port due to error
                time.sleep(1.0)  # Wait before attempting to reconnect
            except Exception:  # Catch any other unexpected exception
                time.sleep(1.0)  # Sleep and continue loop on unknown errors

_uart = _UartBus(SERIAL_PORT_NAME, BAUD_RATE)  # Create a global UART bus instance using specified port and baud
_uart.start()  # Start UART background thread immediately

# ========= Angle/speed conversion =========  # Section header for conversion helper functions
def _pwm_to_speed_percent(pwm: int) -> int:  # Convert PWM value to speed percentage
    pct = int(round((pwm - 1500) / 180.0 * 100.0))  # Map PWM offset from 1500 into approximate -100~100 range
    return max(-100, min(100, pct))  # Clamp the speed percentage to [-100, 100]

def _algo_to_pico_angle(raw_angle: int) -> int:  # Convert algorithm steering angle to Pico steering angle
    delta = raw_angle - straight_const  # Compute offset from center reference value
    pico_deg = -delta  # Invert direction to match Pico steering convention
    if pico_deg > 80: pico_deg = 80  # Limit maximum right turn to +80 degrees
    if pico_deg < -80: pico_deg = -80  # Limit maximum left turn to -80 degrees
    return int(pico_deg)  # Return final integer steering angle

# ========= Single entry point to Pico =========  # Section header for functions that send motion commands
def _send_motion(angle_deg: int, speed_pct: int):  # Send steering angle and speed to Pico as JSON commands
    _uart.send_str(json.dumps({"cmd": "steer", "angle": int(angle_deg)}))  # Send steering command with angle
    _uart.send_str(json.dumps({"cmd": "motor", "speed": int(speed_pct)}))  # Send motor command with speed

# ========= Public API =========  # Section header for functions used by other modules
def write(value):  # Unified write function to send angle or speed or delay based on value
    global _last_speed_pct, _last_angle_deg  # Use global variables to remember last speed and angle

    if isinstance(value, (int, float)) and value < 5:  # Treat small numeric values as delay seconds
        time.sleep(float(value))  # Sleep for the given number of seconds
        return  # Return without sending any UART command

    if value >= 1000:  # If value looks like a PWM speed command
        _last_speed_pct = _pwm_to_speed_percent(int(value))  # Convert PWM to speed percentage and store
    else:  # Otherwise treat value as a steering angle from algorithm
        _last_angle_deg = _algo_to_pico_angle(int(value))  # Convert algorithm angle to Pico angle and store

    _send_motion(_last_angle_deg, _last_speed_pct)  # Send combined steering and speed command to Pico

def multi_write(sequence):  # Execute a sequence of actions (angles, speeds, or delays) in order
    for action in sequence:  # Iterate through each action in the provided sequence
        if isinstance(action, (int, float)) and action < 5:  # If item is a small number, treat as delay
            time.sleep(float(action))  # Sleep for the specified duration
        else:
            write(action)  # Otherwise delegate to write() for angle/speed handling

def stop_car():  # Immediately stop the car and reset internal motion state
    _uart.send_str(json.dumps({"cmd": "motor", "speed": 0}))  # Send motor stop command (speed 0)
    _uart.send_str(json.dumps({"cmd": "steer", "angle": 0}))  # Send steering reset command (angle 0)
    global _last_speed_pct, _last_angle_deg  # Access global state variables
    _last_speed_pct = 0  # Reset last speed percentage to 0
    _last_angle_deg = 0  # Reset last steering angle to 0

def wait_for_start(timeout=None):  # Wait for start signal from Pico or host, with optional timeout
    start_t = time.time()  # Record the time when waiting starts
    if timeout is None:  # If no timeout is provided
        timeout = 9999999  # Use a very large timeout as effectively infinite

    if not _uart.ready:  # If UART is not yet marked ready
        _uart.wait_until_any_message(timeout_sec=min(timeout, 3.0))  # Wait briefly for any message to set ready

    while True:  # Keep checking for start signal until timeout
        msg = _uart.recv_str(timeout=0.2)  # Try to read one message with short timeout
        if msg:  # If a message is received
            s = msg.strip()  # Strip whitespace from the message
            try:
                j = json.loads(s)  # Try to parse message as JSON
            except Exception:
                j = None  # If parsing fails, treat as non-JSON

            if s == "START":  # If message is literal "START"
                return True  # Indicate that start signal has been received

            if j and (j.get("from") == "pico" or j.get("status") == "ready"):  # If JSON indicates Pico or ready status
                return True  # Treat this as a start/ready signal

        if timeout is not None and (time.time() - start_t) > timeout:  # Check if overall waiting time exceeded timeout
            return False  # Return False to indicate wait timed out

# ========= Image utility functions =========  # Section header for image processing helper functions
def display_roi(img, ROIs, color):  # Draw rectangles for all ROIs on an image
    for ROI in ROIs:  # Loop through each ROI in the list
        img = cv2.line(img, (ROI[0], ROI[1]), (ROI[2], ROI[1]), color, 4)  # Draw top edge of ROI rectangle
        img = cv2.line(img, (ROI[0], ROI[1]), (ROI[0], ROI[3]), color, 4)  # Draw left edge of ROI rectangle
        img = cv2.line(img, (ROI[2], ROI[3]), (ROI[2], ROI[1]), color, 4)  # Draw right edge of ROI rectangle
        img = cv2.line(img, (ROI[2], ROI[3]), (ROI[0], ROI[3]), color, 4)  # Draw bottom edge of ROI rectangle
    return img  # Return image with ROI rectangles drawn

def find_contours(img_lab, lab_range, ROI):  # Find contours of a LAB color range inside a given ROI
    x1, y1, x2, y2 = ROI  # Unpack ROI coordinates
    seg = img_lab[y1:y2, x1:x2]  # Crop image region corresponding to ROI
    lo = np.array(lab_range[0]); hi = np.array(lab_range[1])  # Convert LAB lower and upper bounds to NumPy arrays
    mask = cv2.inRange(seg, lo, hi)  # Create binary mask for pixels within LAB range
    k = np.ones((5,5), np.uint8)  # Define 5x5 kernel for morphological operations
    mask = cv2.erode(mask, k, iterations=1)  # Erode mask to remove small noise
    mask = cv2.dilate(mask, k, iterations=1)  # Dilate mask to restore main regions
    contours = cv2.findContours(mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)[-2]  # Find external contours in mask
    return contours  # Return the list of found contours

def max_contour(contours, ROI):  # Find contour with maximum area and compute its position
    maxArea = 0; maxY = 0; maxX = 0; mCnt = 0  # Initialize maximum area and corresponding coordinates/contour
    for cnt in contours:  # Iterate through all contours
        area = cv2.contourArea(cnt)  # Compute area of current contour
        if area > 100:  # Ignore very small areas as noise
            approx = cv2.approxPolyDP(cnt, 0.01*cv2.arcLength(cnt, True), True)  # Approximate contour polygon
            x,y,w,h = cv2.boundingRect(approx)  # Get bounding rectangle of the contour
            x += ROI[0] + w//2  # Convert local x to global and shift to center of bounding box
            y += ROI[1] + h  # Convert local y to global and shift to bottom of bounding box
            if area > maxArea:  # If this contour is larger than previous maximum
                maxArea = area; maxY = y; maxX = x; mCnt = cnt  # Update maximum area and corresponding data
    return [maxArea, maxX, maxY, mCnt]  # Return maximum area and position and contour

def pOverlap(img_lab, ROI, add=False):  # Compute overlapping/combined mask of black and magenta in an ROI
    x1, y1, x2, y2 = ROI  # Unpack ROI coordinates
    seg = img_lab[y1:y2, x1:x2]  # Crop LAB image to ROI region
    from masks import rBlack, rMagenta  # Import black and magenta LAB ranges locally
    loB, hiB = np.array(rBlack[0]),   np.array(rBlack[1])  # Convert black lower/upper LAB bounds to arrays
    loM, hiM = np.array(rMagenta[0]), np.array(rMagenta[1])  # Convert magenta lower/upper LAB bounds to arrays
    mB = cv2.inRange(seg, loB, hiB)  # Mask for black region in ROI
    mM = cv2.inRange(seg, loM, hiM)  # Mask for magenta region in ROI
    if add:  # If we want union of black and magenta
        mask = cv2.add(mB, mM)  # Combine masks by addition (logical OR)
    else:
        mask = cv2.bitwise_and(mB, cv2.bitwise_not(mM))  # Remove magenta from black using AND with NOT magenta
    k_open  = np.ones((3,3), np.uint8)  # Kernel for morphological opening
    k_close = np.ones((7,7), np.uint8)  # Kernel for morphological closing
    mask = cv2.morphologyEx(mask, cv2.MORPH_OPEN,  k_open,  iterations=1)  # Opening to remove small noise
    mask = cv2.morphologyEx(mask, cv2.MORPH_CLOSE, k_close, iterations=1)  # Closing to fill small holes
    contours = cv2.findContours(mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)[-2]  # Find external contours
    return contours  # Return contours obtained from combined mask

def display_variables(variables):  # Nicely print multiple variable names and values in terminal
    names = list(variables.keys())  # Get list of variable names (keys)
    for name in names:  # Iterate through all variable names
        print(f"{name}: {variables[name]}", end="\r\n")  # Print each variable name and its value on its own line
    print("\033[F" * len(names), end="")  # Move cursor up to overwrite lines on next call (console trick)

def get_last_speed_pct() -> int:  # Getter to return last commanded speed percentage
    return _last_speed_pct  # Return the global last speed percentage

def is_moving(threshold: int = 3) -> bool:  # Check whether the car is currently considered moving
    return abs(_last_speed_pct) > threshold  # Return True if absolute speed exceeds threshold