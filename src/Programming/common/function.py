import time # Import the time module
import json # Import the json module
import threading # Import the threading module
import queue # Import the queue module
import cv2 # Import the OpenCV module
import numpy as np # Import the numpy module, aliased as np
import serial # <-- UART serial port communication library
from masks import rBlack, rMagenta, rRed, rGreen, rBlue, rOrange # Import color range constants from masks

# ========= UART Serial Port Settings =========
SERIAL_PORT_NAME = "/dev/ttyTHS4" # Serial port name
BAUD_RATE = 115200 # Baud rate

straight_const = 87 # Raw angle constant when driving straight

_last_speed_pct = 0 # Last set speed percentage
_last_angle_deg = 0 # Last set angle

# ========= Angle/Speed Conversion =========
def _pwm_to_speed_percent(pwm: int) -> int:
    # Convert PWM value (1000~2000) to speed percentage (-100~100)
    pct = int(round((pwm - 1500) / 180.0 * 100.0))
    # Limit speed percentage between -100 and 100
    return max(-100, min(100, pct))

def _algo_to_pico_angle(raw_angle: int) -> int:
    # Convert raw angle from algorithm to pico's desired servo angle (-80~80)
    delta = raw_angle - straight_const # Calculate the difference from the straight constant
    pico_deg = -delta # Invert the sign to match the control direction
    if pico_deg > 80: pico_deg = 80 # Limit maximum angle
    if pico_deg < -80: pico_deg = -80 # Limit minimum angle
    return int(pico_deg) # Return integer angle

# ========= External API =========
def write(value):
    # Set the vehicle's speed or angle, or pause
    global _last_speed_pct, _last_angle_deg # Declare use of global variables

    if isinstance(value, (int, float)) and value < 5:
        # If value is less than 5, treat it as pause time (seconds)
        time.sleep(float(value)) # Pause
        return

    if value >= 1000:
        # If value >= 1000, treat it as PWM speed input
        _last_speed_pct = _pwm_to_speed_percent(int(value)) # Convert and set speed percentage
    else:
        # Otherwise, treat it as algorithm raw angle input
        _last_angle_deg = _algo_to_pico_angle(int(value)) # Convert and set pico angle

    _send_motion(_last_angle_deg, _last_speed_pct) # Send motion command via UART

def multi_write(sequence):
    # Execute a sequence of actions (speed, angle, or pause) sequentially
    for action in sequence:
        if isinstance(action, (int, float)) and action < 5:
            # If it's a pause time
            time.sleep(float(action)) # Pause
        else:
            # Otherwise execute the write action
            write(action)

def stop_car():
    # Stop the vehicle's motor and steering servo
    _uart.send_str(json.dumps({"cmd": "motor", "speed": 0})) # Send command for motor speed 0
    _uart.send_str(json.dumps({"cmd": "steer", "angle": 0})) # Send command for steering angle 0
    global _last_speed_pct, _last_angle_deg # Declare use of global variables
    _last_speed_pct = 0 # Reset last speed to 0
    _last_angle_deg = 0 # Reset last angle to 0

def wait_for_start(timeout=None):
    # Wait for the vehicle to receive a start signal
    start_t = time.time() # Record start time
    if timeout is None:
        timeout = 9999999 # Use a large value if timeout is not set

    if not _uart.ready:
        # If UART is not ready, wait until it is
        _uart.wait_until_any_message(timeout_sec=min(timeout, 3.0))

    while True:
        msg = _uart.recv_str(timeout=0.2) # Receive UART message
        if msg:
            s = msg.strip() # Remove whitespace
            try:
                j = json.loads(s) # Try to parse as JSON
            except Exception:
                j = None # Parse failed

            if s == "START":
                # If "START" signal is received
                return True # Return True for start
            
            if j and (j.get("from") == "pico" or j.get("status") == "ready"):
                # If JSON message is from pico or status is "ready"
                return True # Return True for start

        if timeout is not None and (time.time() - start_t) > timeout:
            # If timeout
            return False # Return False for timeout

# ========= Image Tools =========
def display_roi(img, ROIs, color):
    # Draw Region of Interest (ROI) bounding boxes on the image
    for ROI in ROIs:
        # Iterate through all ROIs
        # ROI format: [x1, y1, x2, y2]
        img = cv2.line(img, (ROI[0], ROI[1]), (ROI[2], ROI[1]), color, 4) # Top line
        img = cv2.line(img, (ROI[0], ROI[1]), (ROI[0], ROI[3]), color, 4) # Left line
        img = cv2.line(img, (ROI[2], ROI[3]), (ROI[2], ROI[1]), color, 4) # Right line
        img = cv2.line(img, (ROI[2], ROI[3]), (ROI[0], ROI[3]), color, 4) # Bottom line
    return img # Return the image with drawings

def find_contours(img_lab, lab_range, ROI):
    # Find contours in ROI using LAB color range
    x1, y1, x2, y2 = ROI # Unpack ROI coordinates
    seg = img_lab[y1:y2, x1:x2] # Crop the image to the ROI area
    lo = np.array(lab_range[0]); hi = np.array(lab_range[1]) # Get color low and high thresholds
    mask = cv2.inRange(seg, lo, hi) # Create color mask
    k = np.ones((5,5), np.uint8) # 5x5 rectangular kernel
    mask = cv2.erode(mask, k, iterations=1) # Erode operation
    mask = cv2.dilate(mask, k, iterations=1) # Dilate operation
    contours = cv2.findContours(mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)[-2] # Find external contours
    return contours # Return found contours

def max_contour(contours, ROI):
    # Find the largest contour by area and its center point
    maxArea = 0; maxY = 0; maxX = 0; mCnt = 0 # Initialize max area, center coordinates, and max contour
    for cnt in contours:
        area = cv2.contourArea(cnt) # Calculate contour area
        if area > 100: # Only consider contours with area greater than 100
            approx = cv2.approxPolyDP(cnt, 0.01*cv2.arcLength(cnt, True), True) # Polygon approximation
            x,y,w,h = cv2.boundingRect(approx) # Get bounding box
            x += ROI[0] + w//2 # Calculate center point X (relative to original image)
            y += ROI[1] + h # Calculate bottom center point Y (relative to original image)
            if area > maxArea:
                # If current contour area is larger
                maxArea = area; maxY = y; maxX = x; mCnt = cnt # Update maximum values
    return [maxArea, maxX, maxY, mCnt] # Return max area, center X, center Y, and max contour

def pOverlap(img_lab, ROI, add=False):
    # Process contours for black and magenta overlapping regions
    x1, y1, x2, y2 = ROI # Unpack ROI coordinates
    seg = img_lab[y1:y2, x1:x2] # Crop the image to the ROI area
    from masks import rBlack, rMagenta # Re-import color ranges to ensure availability
    loB, hiB = np.array(rBlack[0]),   np.array(rBlack[1]) # Black range
    loM, hiM = np.array(rMagenta[0]), np.array(rMagenta[1]) # Magenta range
    mB = cv2.inRange(seg, loB, hiB) # Black mask
    mM = cv2.inRange(seg, loM, hiM) # Magenta mask
    if add:
        mask = cv2.add(mB, mM) # If add is True, add them (Union)
    else:
        mask = cv2.bitwise_and(mB, cv2.bitwise_not(mM)) # Else, Black AND (NOT Magenta) (Difference)
    k_open  = np.ones((3,3), np.uint8) # Kernel for opening
    k_close = np.ones((7,7), np.uint8) # Kernel for closing
    mask = cv2.morphologyEx(mask, cv2.MORPH_OPEN,  k_open,  iterations=1) # Perform Opening
    mask = cv2.morphologyEx(mask, cv2.MORPH_CLOSE, k_close, iterations=1) # Perform Closing
    contours = cv2.findContours(mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)[-2] # Return found contours

def display_variables(variables):
    # Display variables and their values, using \r\n for new line
    names = list(variables.keys()) # Get all variable names
    for name in names:
        print(f"{name}: {variables[name]}", end="\r\n") # Print variable name and value
    print("\033[F" * len(names), end="") # Move cursor up to achieve overwrite display

# === External Access to Recent Speed Information ===
def get_last_speed_pct() -> int:
    # Get the last set speed percentage
    return _last_speed_pct # Return speed percentage

def is_moving(threshold: int = 3) -> bool:
    # Check if the vehicle is moving (absolute value of speed percentage > threshold)
    return abs(_last_speed_pct) > threshold # Return boolean indicating if moving