# Import the time module for delays.
import time
# Import standard system, math, and concurrency libraries.
import os, sys, math, json, threading, asyncio
# Import the OpenCV library for computer vision.
import cv2
# Import NumPy for numerical operations.
import numpy as np
# Import the serial library for UART communication.
import serial 
# Import SMBus for I2C communication (used for BNO055).
from smbus2 import SMBus
# Import Jetson.GPIO for hardware pin control.
import Jetson.GPIO as GPIO
# Import custom functions from function.py (aliased as fj, though fj is not used).
import function as fj

# -------------------- Path and Utilities --------------------
# Add the current script's directory to the system path.
sys.path.append(os.path.abspath(os.path.dirname(__file__)))
# Import color range masks from the 'masks.py' file.
from masks import rMagenta, rRed, rGreen, rBlue, rOrange, rBlack
# Import all functions from 'function.py' (e.g., find_contours, max_contour).
from function import *

# =================== BNO055 (IMU) Constants ===================
# I2C address of the BNO055 sensor.
BNO055_ADDRESS = 0x28
# Register address for setting the operation mode.
BNO055_OPR_MODE_ADDR = 0x3D
# Register address for setting the power mode.
BNO055_PWR_MODE_ADDR = 0x3E
# Expected Chip ID value for BNO055.
BNO055_ID = 0xA0
# Register address for reading the Chip ID.
BNO055_CHIP_ID_ADDR = 0x00
# Register address for reading the calibration status.
BNO055_CALIB_STAT_ADDR = 0x35
# Operation mode for configuration.
OPERATION_MODE_CONFIG = 0x00
# Operation mode for 9-axis fusion (NDOF).
OPERATION_MODE_NDOF = 0x0C
# Register address for the start of Euler Heading data (LSB).
BNO055_EULER_H_LSB = 0x1A
# I2C bus number on the Jetson (Bus 7 for 40-pin header).
BNO055_BUS = 7 

# ====== Angle and Clamping Utilities ======
# Utility function to constrain a value 'v' between 'lo' and 'hi'.
def clamp(v, lo, hi):
    # Return the clamped value.
    return lo if v < lo else (hi if v > hi else v)

# Mechanical sign for steering (e.g., +1 if positive angle means right).
MECH_SIGN = +1
# The servo value (0-180) that corresponds to driving straight.
straight_const = 90

# Convert a relative angle (-90 to +90) to a servo angle (0-180).
def rel_to_servo_deg(rel_deg: int) -> int:
    # Calculate the servo angle based on the straight constant and mechanical sign.
    servo = int(round(straight_const + MECH_SIGN * rel_deg))
    # Return the clamped servo value.
    return clamp(servo, 0, 180)

# Helper function to define a relative LEFT turn angle.
def LEFT(deg=60):   return -abs(int(deg))
# Helper function to define a relative RIGHT turn angle.
def RIGHT(deg=60):  return +abs(int(deg))

# Calculate the shortest difference between two angles (e.g., target and current).
def ang_diff_deg(target_deg: float, current_deg: float) -> float:
    # Use modulo arithmetic to find the shortest path (-180 to 180).
    return ((target_deg - current_deg + 180.0) % 360.0) - 180.0

# ---- Prebuilt morphology kernels ----
# A 5x5 rectangular kernel for morphological operations.
K5 = cv2.getStructuringElement(cv2.MORPH_RECT, (5,5))
# A 3x3 rectangular kernel.
K3 = cv2.getStructuringElement(cv2.MORPH_RECT, (3,3))

# Define the serial port device name for UART.
UART_PORT = "/dev/ttyTHS0"
# Define the baud rate for UART communication.
UART_BAUDRATE = 115200

# Function to convert a PWM signal (1000-2000) to a percentage (-100 to 100).
def pwm_to_percent(pwm: int) -> int:
    # Calculate the percentage (assuming 1500 is center, 180 is the range).
    pct = round((pwm - 1500) / 180 * 100)
    # Return the clamped percentage value.
    return max(-100, min(100, pct))

# Define a class to manage UART communication (sending and receiving).
class UartHub:
    # Initialize the UartHub instance.
    def __init__(self, port=UART_PORT, baudrate=UART_BAUDRATE):
        # Store the port name.
        self.port = port
        # Store the baud rate.
        self.baudrate = baudrate
        # Initialize the serial object as None.
        self.ser = None
        # Initialize the reader thread object as None.
        self._thread = None
        # Create a threading event to signal the reader thread to stop.
        self._stop_evt = threading.Event()
        # Create an event to signal when the Pico W is ready.
        self.started_evt = threading.Event()
        # Store the last commanded steering angle.
        self._last_angle_rel = 0
        # Store the last commanded speed percentage.
        self._last_speed_pct = 0
        # Store a pending turn/color signal command.
        self._pending_turn_signal = None
        # Create a lock to ensure thread-safe writes to the serial port.
        self.lock = threading.Lock()

    # Define the method to start the UART connection and reader thread.
    def start(self):
        # Start a try-except block to handle potential serial errors.
        try:
            # Attempt to open the serial port.
            self.ser = serial.Serial(self.port, self.baudrate, timeout=0.1)
            # Print a success message.
            print(f"UART opened on {self.port} at {self.baudrate} baud.")
        # Handle exceptions if the serial port fails to open.
        except serial.SerialException as e:
            # Print the failure message.
            print(f"Failed to open serial port {self.port}: {e}")
            # Print a help message suggesting a permission fix.
            print("Please check the port name and permissions (e.g. sudo usermod -a -G dialout $USER)")
            # Exit the script with an error code.
            sys.exit(1)

        # Create the background reader thread.
        self._thread = threading.Thread(target=self._read_loop, daemon=True)
        # Start the reader thread.
        self._thread.start()
        
    # Define the private method for the background thread to read UART data.
    def _read_loop(self):
        # Loop continuously until the stop event is set.
        while not self._stop_evt.is_set():
            # Start a try block for reading operations.
            try:
                # Check if the serial port is open and has data waiting.
                if self.ser and self.ser.in_waiting > 0:
                    # Read a line, decode it, and strip whitespace.
                    line = self.ser.readline().decode('utf-8', errors='ignore').strip()
                    # If a non-empty line was read:
                    if line:
                        # Print the received line to the console.
                        print(f"[UART RECV] {line}")
                        # Check if the line is the 'ready' signal from the Pico.
                        if line.startswith('{"from":"pico","status":"ready"}'):
                            # Print a confirmation message.
                            print("Received Pico W Ready signal via UART.")
                            # Set the 'started' event to unblock 'wait_for_start'.
                            self.started_evt.set()
                # Sleep briefly to prevent high CPU usage.
                time.sleep(0.01)
            # Handle any exceptions during the read loop.
            except Exception as e:
                # If the stop was not intentional, note it (or just pass).
                if not self._stop_evt.is_set():
                    # Ignore read errors if not stopping.
                    pass
                # Sleep longer after an error.
                time.sleep(0.1)

    # Define the method to stop the UART hub.
    def stop(self):
        # Signal the reader thread to stop.
        self._stop_evt.set()
        # If the thread exists:
        if self._thread:
            # Wait for the thread to terminate (with a timeout).
            self._thread.join(timeout=1)
        # If the serial port is open:
        if self.ser and self.ser.is_open:
            # Close the serial port.
            self.ser.close()
            # Print a confirmation message.
            print("UART closed.")

    # Define a method to block until the Pico 'ready' signal is received.
    def wait_for_start(self, timeout=None):
        # Print a status message.
        print("Waiting for Pico W Ready signal / Button...")
        # Wait for the 'started' event to be set, with an optional timeout.
        return self.started_evt.wait(timeout)

    # Define a private, thread-safe method to send data over UART.
    def _send(self, text):
        # Acquire the lock to prevent concurrent writes.
        with self.lock:
            # Check if the serial port is open.
            if self.ser and self.ser.is_open:
                # Start a try block for the write operation.
                try:
                    # Encode the text and write it to the serial port.
                    self.ser.write(text.encode('utf-8'))
                # Handle potential write errors.
                except Exception as e:
                    # Ignore write errors.
                    pass

    # Define the main public method for sending commands (motor, angle, sleep, signals).
    def write(self, value):
        # If the value is a small float, treat it as a sleep duration.
        if isinstance(value, float) and value < 10.0:
            # Pause execution for that duration.
            time.sleep(float(value))
            # Exit the function.
            return
        
        # Handle speed commands
        # If the value is a tuple like ("S", speed), update speed.
        if isinstance(value, tuple) and len(value) == 2 and value[0] == "S":
            # Store the speed percentage directly.
            self._last_speed_pct = int(value[1])
        # If the value is an integer >= 1000, treat it as PWM speed.
        elif isinstance(value, int) and value >= 1000:
            # Convert PWM to percentage and store it.
            self._last_speed_pct = pwm_to_percent(value)
        
        # Handle angle commands
        # If the value is an integer (and not PWM), treat it as an angle.
        elif isinstance(value, int):
            # Cast the value to an integer.
            rel = int(value)
            # Clamp the angle value.
            rel = clamp(rel, -180, 180)
            # Store the angle.
            self._last_angle_rel = rel
        
        # Handle start or color signals
        # If the value is a string of digits, treat it as a signal.
        elif isinstance(value, str) and value.isdigit():
            # Store it as a pending signal.
            self._pending_turn_signal = value
        
        # If there is a pending signal, send it immediately.
        if self._pending_turn_signal:
            # Format the signal command (M,signal,0). (Comment translated)
            text = f"M,{self._pending_turn_signal},0\n" # Send M,<signal>,0
            # Send the command.
            self._send(text)
            # Print the sent signal command.
            print(f"[UART SEND] Signal: {text.strip()}")
            # Clear the pending signal.
            self._pending_turn_signal = None

    # Define a method to execute a sequence of 'write' commands.
    def multi_write(self, seq):
        # Iterate through each item in the sequence.
        for v in seq:
            # Call the 'write' method for each item.
            self.write(v)

    # Define a method to stop the car.
    def stop_car(self):
        # Reset the internal angle state to 0.
        self._last_angle_rel = 0
        # Reset the internal speed state to 0.
        self._last_speed_pct = 0
        # Send the specific "STOP" command string.
        self._send("STOP\n")

    # Method to broadcast JSON data and send a control command.
    def broadcast_json(self, leftArea, rightArea, yaw, angle, speed, magArea, magCX, magCY, **extra):
        # Create a dictionary for magenta (obstacle) data.
        mag_data = json.dumps({
            # Current yaw (heading) from IMU.
            "yaw": round(yaw, 2),
            # Detected left wall area.
            "leftArea": int(leftArea),
            # Detected right wall area.
            "rightArea": int(rightArea),
            # Detected magenta area.
            "magArea": int(magArea),
            # Detected magenta center X.
            "magCX": int(magCX),
            # Detected magenta center Y.
            "magCY": int(magCY)
        })
        # Send the JSON data string.
        self._send(mag_data + "\n")

        # Use the last stored angle as default.
        angle_to_send = self._last_angle_rel
        # Use the last stored speed as default.
        speed_to_send = self._last_speed_pct
        
        # If a new angle is provided, update the value to be sent.
        if angle is not None:
             # Set the angle to send.
             angle_to_send = angle
             
        # If a new speed is provided, update the value to be sent.
        if speed is not None:
             # Set the speed to send.
             speed_to_send = speed

        # Format the standard motion control command (M,angle,speed).
        control_cmd = f"M,{int(angle_to_send)},{int(speed_to_send)}\n"
        # Send the motion command.
        self._send(control_cmd) 

# Instantiate the UartHub class.
uart_hub = UartHub(UART_PORT, UART_BAUDRATE)
# Start the UART hub (opens port, starts reader thread).
uart_hub.start()
# Create a global alias for the 'write' method.
write          = uart_hub.write
# Create a global alias for the 'multi_write' method.
multi_write    = uart_hub.multi_write
# Create a global alias for the 'wait_for_start' method.
wait_for_start = uart_hub.wait_for_start
# Create a global alias for the 'stop_car' method.
stop_car       = uart_hub.stop_car


# ===== Helper for quick stops (using an Exception) =====
# Initialize lap counter 't'.
t = 0
# Define a custom exception to halt the main loop.
class HaltRun(Exception): pass
# Function to increment the global lap counter 't'.
def inc_t():
    # Access the global variable 't'.
    global t
    # Increment 't'.
    t += 1
    # Print the new lap count.
    print(f"[t++] -> {t}")

# Define a function to generate the GStreamer pipeline string...
def gstreamer_csi_pipeline(sensor_id=0, capture_width=640, capture_height=480,
                           # ...for capturing from the Jetson's CSI camera.
                           display_width=640, display_height=480,
                           # (Function signature continues).
                           framerate=30, flip_method=0):
    # Return the formatted string.
    return (
        # NVIDIA camera source element.
        f"nvarguscamerasrc sensor-id={sensor_id} ! "
        # Set camera properties (NVMM memory).
        f"video/x-raw(memory:NVMM), width={capture_width}, height={capture_height}, "
        # Set format and framerate.
        f"format=NV12, framerate={framerate}/1 ! "
        # NVIDIA video converter for flipping/conversion.
        f"nvvidconv flip-method={flip_method} ! "
        # Set output format to BGRx.
        f"video/x-raw, width={display_width}, height={display_height}, format=BGRx ! "
        # Software video converter.
        f"videoconvert ! video/x-raw, format=BGR ! "
        # Final format BGR for OpenCV, sent to appsink.
        f"appsink max-buffers=1 drop=true sync=false"
    # End of string.
    )

# Define a class to store information about a detected pillar.
class Pillar:
    # Initialize the Pillar object.
    def __init__(self, area, dist, x, y, target):
        # Area of the pillar's contour.
        self.area = area
        # Distance to the pillar (heuristic).
        self.dist = dist
        # Center X coordinate.
        self.x = x
        # Center Y coordinate (bottom).
        self.y = y
        # Target X coordinate for this pillar (e.g., redTarget).
        self.target = target
        # Width of the bounding box (initialized to 0).
        self.w = 0
        # Height of the bounding box (initialized to 0).
        self.h = 0
    # Method to set the bounding box dimensions.
    def setDimentions(self, w, h):
        # Set width.
        self.w = w
        # Set height.
        self.h = h

# Helper function to convert a list of contours into a binary mask.
def _contours_to_mask(contours, size):
    # Create a black mask of the given size.
    mask = np.zeros(size, dtype=np.uint8)
    # If contours were provided:
    if contours:
        # Draw the contours filled in white (255) on the mask.
        cv2.drawContours(mask, contours, -1, 255, thickness=cv2.FILLED)
    # Return the mask.
    return mask

# Helper function to filter contours based on geometry (area, tilt, edge proximity).
def _geom_filter(contours, w, *, edge_margin=18, min_area=110, max_tilt=26):
    # List to store contours that pass the filter.
    kept = []
    # Iterate through each contour.
    for c in contours:
        # Calculate the contour area.
        area = cv2.contourArea(c)
        # Filter 1: Minimum area.
        if area < min_area: continue
        # Get the minimum area rectangle (center, size, angle).
        (cx, _), (cw, ch), theta = cv2.minAreaRect(c)
        # Calculate the tilt (angle from vertical).
        tilt = abs(theta)
        # Normalize tilt to be between 0 and 45 degrees.
        tilt = (90 - tilt) if tilt > 45 else tilt
        # Check if the contour is near the left or right edge.
        near_edge = (cx < edge_margin) or (cx > (w - edge_margin))
        # Filter 2: Keep if near edge and not tilted too much.
        if near_edge and tilt <= max_tilt:
            # Add to the list of kept contours.
            kept.append(c)
    # Return the filtered list.
    return kept

# Function to find wall contours (black) but ignore lines (magenta).
def wall_contours_no_lines(img_lab, ROI, img_bgr=None):
    # Unpack ROI coordinates.
    x1, y1, x2, y2 = ROI
    # Get ROI dimensions.
    h, w = y2 - y1, x2 - x1
    # Find black contours in the ROI.
    c_black = find_contours(img_lab, rBlack, ROI)
    # Create a mask from the black contours.
    m_black = _contours_to_mask(c_black, (h, w))
    # Perform morphological closing to fill gaps.
    m = cv2.morphologyEx(m_black, cv2.MORPH_CLOSE, K5, iterations=1)
    # Perform morphological opening to remove noise.
    m = cv2.morphologyEx(m,      cv2.MORPH_OPEN,  K3, iterations=1)
    # Find contours in the cleaned mask.
    contours, _ = cv2.findContours(m, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
    # Apply the geometric filter.
    kept = _geom_filter(contours, w)
    # Return the final contours.
    return kept

# Function to find the area of the most dominant *vertical* contour.
def dominant_vertical_area(contours, ROI, max_tilt=26):
    # If no contours, return 0.
    if not contours: return 0
    # Initialize best area.
    best = 0
    # Iterate through contours.
    for c in contours:
        # Get contour area.
        area = cv2.contourArea(c)
        # Skip if area is 0.
        if area <= 0: continue
        # Get the minimum area rectangle.
        _, (w, h), theta = cv2.minAreaRect(c)
        # Calculate the tilt (angle from vertical).
        tilt = abs(theta)
        # Normalize tilt to be between 0 and 45 degrees.
        tilt = (90 - tilt) if tilt > 45 else tilt
        # If the tilt is within the allowed maximum:
        if tilt <= max_tilt: 
            # Update the best area found so far.
            best = max(best, area)
    # Return the largest vertical area.
    return best

# Function to find the best (closest) pillar from a list of contours.
def find_best_pillar(contours, target, colour, img_lab):
    # Access global variables (used for logic).
    global s, leftArea, rightArea, maxDist, tempParking, speed, endConst
    # Initialize number of pillars, best pillar object, and best distance.
    num_p, best, best_dist = 0, None, math.inf
    # Iterate through all provided contours.
    for cnt in contours:
        # Calculate contour area.
        area = cv2.contourArea(cnt)
        # Apply area filtering based on color and state.
        if ((area > 150 and colour == "red") or
            (area > 200 and colour == "green") or
            (area > 100 and colour == "red" and tempParking)):
            # Get a polygon approximation of the contour.
            approx = cv2.approxPolyDP(cnt, 0.01 * cv2.arcLength(cnt, True), True)
            # Get the bounding box.
            x, y, w, h = cv2.boundingRect(approx)
            # Calculate center X (relative to full image).
            x += ROI3[0] + w // 2
            # Calculate bottom Y (relative to full image).
            y += ROI3[1] + h
            # Calculate distance from bottom-center of image (heuristic).
            temp_dist = round(math.dist([x, y], [320, 480]), 0)
            # Count if it's within a reasonable distance range.
            if 160 < temp_dist < 380: num_p += 1
            # Emergency stop/reverse logic if pillar is too large (too close).
            if (((area > 6500 and target == redTarget) or (area > 8000 and target == greenTarget))
                and (not tempParking) and is_moving()):
                # Send commands to reverse and turn.
                multi_write([0, 0.1, -40, 0.5, ("S", speed)])
                # Increment 's' state variable.
                if s != 0: s += 1.5
            # Skip this pillar if walls are too close or distance is too large.
            if((target == greenTarget and (leftArea > 13000 or rightArea > 13000 or temp_dist > maxDist)) or
               (target == redTarget  and (leftArea > 13000 or rightArea > 15000 or temp_dist > maxDist))):
                # Go to the next contour.
                continue
            # If this pillar is closer than the previous best:
            if temp_dist < best_dist:
                # Update the best distance.
                best_dist = temp_dist
                # Create a new Pillar object for this best one.
                best = Pillar(area, temp_dist, x, y, target)
                # Store its dimensions.
                best.setDimentions(w, h)
    # Return the best Pillar object found and the count of pillars.
    return best, num_p

# Helper function to draw ROI boxes on an image.
def draw_roi_boxes(img, rois, color=(255, 204, 0), thickness=2):
    # Iterate through ROIs with an index (starting from 1).
    for i, R in enumerate(rois, 1):
        # Skip if ROI is None or invalid.
        if R is None or len(R) != 4:
            # Continue to next ROI.
            continue
        # Unpack coordinates.
        x1, y1, x2, y2 = R
        # Skip if ROI is empty (all zeros).
        if x1 == x2 == y1 == y2 == 0:
            # Continue to next ROI.
            continue
        # Draw the rectangle.
        cv2.rectangle(img, (int(x1), int(y1)), (int(x2), int(y2)), color, thickness)
        # Put the text label (e.g., "ROI1").
        cv2.putText(img, f"ROI{i}", (int(x1) + 4, int(y1) + 18),
            cv2.FONT_HERSHEY_SIMPLEX, 0.6, color, 2)

# Helper function to draw a list of contours, offset by their ROI.
def draw_contours_list(img, contours, roi, color, label=None, thickness=2, show_bbox=True):
    # Skip if inputs are invalid.
    if contours is None or len(contours) == 0 or roi is None or len(roi) != 4:
        # Do nothing.
        return
    # Get the top-left offset of the ROI.
    ox, oy = int(roi[0]), int(roi[1])
    # Iterate through all contours.
    for c in contours:
        # Create a new contour array, offset by (ox, oy).
        c2 = c + np.array([[[ox, oy]]])
        # Draw the offset contour.
        cv2.drawContours(img, [c2], -1, color, thickness)
        # If requested, draw the bounding box.
        if show_bbox:
            # Get the bounding box of the offset contour.
            x, y, w, h = cv2.boundingRect(c2)
            # Draw the bounding rectangle.
            cv2.rectangle(img, (x, y), (x + w, y + h), color, 1)
    # If a label is provided:
    if label:
        # Draw the text label near the top-left of the ROI.
        cv2.putText(img, label, (ox + 4, oy + 16), cv2.FONT_HERSHEY_SIMPLEX, 0.5, color, 2)

# ---- Print text within an ROI (black border + specified color) ----
def _put_text_in_roi(img, roi, text, line_idx=0, color=(255, 255, 255)):
    # Unpack ROI coordinates.
    x1, y1, x2, y2 = map(int, roi)
    # Calculate X position.
    x = x1 + 8
    # Calculate Y position based on line index.
    y = y1 + 24 + 22 * int(line_idx)
    # Draw the black border (outline).
    cv2.putText(img, text, (x, y), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 0, 0), 3)
    # Draw the colored text.
    cv2.putText(img, text, (0 + x, y), cv2.FONT_HERSHEY_SIMPLEX, 0.6, color, 1)

# ---- Get area/center/bbox of the largest magenta contour in an ROI ----
def _largest_magenta_in_roi(img_lab, roi):
    # Check for invalid ROI.
    if roi is None or len(roi) != 4:
        # Return empty values.
        return 0, None, None
    # Unpack ROI coordinates.
    x1, y1, x2, y2 = map(int, roi)
    # Find all magenta contours in the specified ROI.
    contours = find_contours(img_lab, rMagenta, roi)
    # If no contours were found:
    if not contours:
        # Return empty values.
        return 0, None, None
    # Find the contour with the largest area.
    c = max(contours, key=cv2.contourArea)
    # Get the area of the largest contour.
    area = int(cv2.contourArea(c))
    # Calculate moments to find the centroid.
    M = cv2.moments(c)
    # If moments are valid:
    if M["m00"] > 0:
        # Calculate centroid X (local to ROI).
        cx_local = int(M["m10"] / M["m00"])
        # Calculate centroid Y (local to ROI).
        cy_local = int(M["m01"] / M["m00"])
    # If moments are invalid (e.g., straight line):
    else:
        # Use the center of the bounding box instead.
        x, y, w, h = cv2.boundingRect(c)
        # Calculate local center X.
        cx_local = x + w // 2
        # Calculate local center Y.
        cy_local = y + h // 2
    # Convert local centroid X to global image coordinate.
    cx = cx_local + x1
    # Convert local centroid Y to global image coordinate.
    cy = cy_local + y1
    # Get the bounding box (local coordinates).
    x, y, w, h = cv2.boundingRect(c)
    # Create the bounding box tuple (global coordinates).
    bbox = (x + x1, y + y1, w, h)
    # Return the area, global center (cx, cy), and global bbox.
    return area, (cx, cy), bbox

# ---------- BNO055 I2C (IMU Functions) ----------
# Function to write a single byte to an I2C register.
def write_byte(bus, reg, value):
    # Use smbus to write byte data.
    bus.write_byte_data(BNO055_ADDRESS, reg, value)

# Function to read a block of bytes from an I2C register.
def read_bytes(bus, reg, length):
    # Use smbus to read a block of data.
    return bus.read_i2c_block_data(BNO055_ADDRESS, reg, length)

# Function to read the chip ID from the BNO055.
def read_chip_id(bus):
    # Read a single byte from the CHIP_ID register.
    return bus.read_byte_data(BNO055_ADDRESS, BNO055_CHIP_ID_ADDR)

# Function to read the calibration status.
def read_calibration_status(bus):
    # Read the calibration status register.
    calib = bus.read_byte_data(BNO055_ADDRESS, BNO055_CALIB_STAT_ADDR)
    # Parse the system calibration bits (0-3).
    sys_cal = (calib >> 6) & 0x03
    # Parse the gyroscope calibration bits.
    gyro_cal = (calib >> 4) & 0x03
    # Parse the accelerometer calibration bits.
    accel_cal = (calib >> 2) & 0x03
    # Parse the magnetometer calibration bits.
    mag_cal = calib & 0x03
    # Return all four calibration statuses.
    return sys_cal, gyro_cal, accel_cal, mag_cal

# Function to initialize the BNO055 sensor.
def init_bno055(bus, wait_for_calibration=True):
    # Turn off the LED during initialization.
    led_off()
    # Print status message.
    print("🔧 Initializing BNO055...")
    # Start try-except block for I2C communication.
    try:
        # Read the chip ID.
        chip_id = read_chip_id(bus)
        # Check if the chip ID matches the expected value.
        if chip_id != BNO055_ID:
            # Print error message if ID doesn't match.
            print(f" Could not find BNO055 (ID: 0x{chip_id:X}, Expected: 0x{BNO055_ID:X})")
            # Return failure.
            return False
        # Print success message.
        print(f" Found BNO055 (ID: 0x{chip_id:X})")
    # Handle exceptions (e.g., I2C connection error).
    except Exception as e:
        # Print the exception.
        print(f" Failed to read chip ID: {e}")
        # Print troubleshooting tips.
        print(f"   Please check if the I2C bus number is correct (Current: {BNO055_BUS})")
        # Return failure.
        return False
    # Switch to CONFIG mode to make changes.
    write_byte(bus, BNO055_OPR_MODE_ADDR, OPERATION_MODE_CONFIG)
    # Wait for the mode switch.
    time.sleep(0.025)
    # Set power mode to NORMAL.
    write_byte(bus, BNO055_PWR_MODE_ADDR, 0x00)
    # Wait.
    time.sleep(0.01)
    # Switch to NDOF (9-axis fusion) mode.
    write_byte(bus, BNO055_OPR_MODE_ADDR, OPERATION_MODE_NDOF)
    # Print status.
    print(" Waiting for sensor to stabilize...")
    # Wait for the sensor to stabilize after mode switch.
    time.sleep(0.5)
    # If calibration is requested:
    if wait_for_calibration:
        # Print status.
        print(" Waiting for gyroscope calibration...")
        # Set a timeout for calibration.
        timeout = 2
        # Record the start time.
        start_time = time.time()
        # Loop until timeout.
        while time.time() - start_time < timeout:
            # Read the calibration status.
            sys_cal, gyro_cal, accel_cal, mag_cal = read_calibration_status(bus)
            # Print the current status.
            print(f"   Calibration status - Sys:{sys_cal} Gyro:{gyro_cal} Accel:{accel_cal} Mag:{mag_cal}")
            # Check if the gyroscope is at least partially calibrated (>=1).
            if gyro_cal >= 1:
                # Print success.
                print(" Gyroscope calibration complete")
                # Exit the calibration loop.
                break
            # Wait before checking again.
            time.sleep(0.1)
        # If the loop finished without breaking (timeout).
        else:
            # Print a warning.
            print(" Gyroscope calibration timed out, but continuing anyway")
    # Print final initialization success message.
    print(" BNO055 initialization complete")
    # Return success.
    return True

# Function to read the heading (Yaw) from the BNO055.
def read_heading(bus, samples=1):
    # List to store multiple readings (for averaging).
    readings = []
    # Loop for the requested number of samples.
    for _ in range(samples):
        # Start try block for I2C read.
        try:
            # Read 2 bytes (LSB, MSB) from the Euler H register.
            data = read_bytes(bus, BNO055_EULER_H_LSB, 2)
            # Convert the 2 bytes to a signed integer (16-bit).
            heading = int.from_bytes(data, byteorder='little', signed=True) / 16.0
            # Append the heading (in degrees) to the list.
            readings.append(heading)
            # Short delay between samples.
            time.sleep(0.005)
        # Handle I2C read errors.
        except Exception:
            # Skip this sample on error.
            continue
    # If any readings were successful:
    if readings:
        # Return the average of all readings.
        return sum(readings) / len(readings)
    # If all readings failed, return 0.0.
    return 0.0

# ---- IMU background updater ----
# Global variable to store the latest relative heading.
relative_heading = 0.0
# Function to be run in a background thread to continuously update the heading.
def imu_loop(bus, zero, dt=0.05):
    # Access the global variable.
    global relative_heading
    # Loop indefinitely.
    while True:
        # Read the current absolute heading.
        h = read_heading(bus, samples=1)
        # Calculate the heading relative to the initial zero point.
        rel = h - zero
        # Wrap the relative angle to the -180 to +180 range.
        if rel > 180: rel -= 360
        # Wrap the relative angle.
        elif rel < -180: rel += 360
        # Update the global variable.
        relative_heading = rel
        # Wait for the specified time delta (dt).
        time.sleep(dt)

# =================== RGB LED Control ===================
# Class to control a common-cathode or common-anode RGB LED.
class RgbLED:
    # Initialize the RGB LED pins.
    def __init__(self, pin_r=13, pin_g=12, pin_b=22, common_anode=False):
        # Store the pin numbers.
        self.r, self.g, self.b = pin_r, pin_g, pin_b
        # Store the LED type (common anode or cathode).
        self.common_anode = common_anode
        # Setup Red pin as output, initial state OFF.
        GPIO.setup(self.r, GPIO.OUT, initial=self._logic(False))
        # Setup Green pin as output, initial state OFF.
        GPIO.setup(self.g, GPIO.OUT, initial=self._logic(False))
        # Setup Blue pin as output, initial state OFF.
        GPIO.setup(self.b, GPIO.OUT, initial=self._logic(False))

    # Private helper to determine the correct logic (HIGH/LOW) for "ON".
    def _logic(self, on: bool):
        # If common anode, LOW is ON.
        if self.common_anode:
            # Return LOW if 'on' is True, HIGH if False.
            return GPIO.LOW if on else GPIO.HIGH
        # If common cathode, HIGH is ON.
        else:
            # Return HIGH if 'on' is True, LOW if False.
            return GPIO.HIGH if on else GPIO.LOW

    # Private helper to drive the pins.
    def _drive(self, r, g, b):
        # Set the Red pin state.
        GPIO.output(self.r, self._logic(bool(r)))
        # Set the Green pin state.
        GPIO.output(self.g, self._logic(bool(g)))
        # Set the Blue pin state.
        GPIO.output(self.b, self._logic(bool(b)))

    # Public method to show a color by name.
    def show(self, color: str):
        # Normalize the color string.
        c = (color or "off").lower()
        # Color name lookup table.
        table = {
            "off": (0,0,0),    # All off
            "red": (1,0,0),    # Red on
            "green": (0,1,0),  # Green on
            "blue": (0,0,1),   # Blue on
            "orange": (1,1,1), # R+G+B = White (used as Orange indicator?)
        }
        # Get the (r,g,b) tuple from the table, default to (0,0,0).
        self._drive(*table.get(c, (0,0,0)))

    # Public method to turn the LED off.
    def off(self):
        # Drive all pins to OFF state.
        self._drive(0,0,0)

#===========================================================
# Set the GPIO pin numbering mode to BCM.
GPIO.setmode(GPIO.BCM)
# Disable GPIO warnings.
GPIO.setwarnings(False)
# Define the GPIO pin number for the single (status) LED.
LED_PIN = 21
# Define the GPIO pin number for the start button.
BUTTON_PIN = 18
# Set the LED pin as an output.
GPIO.setup(LED_PIN, GPIO.OUT)
# Set the button pin as an input with a pull-down resistor.
GPIO.setup(BUTTON_PIN, GPIO.IN, pull_up_down=GPIO.PUD_DOWN)

# === Initialize RGB LED ===
# Instantiate the RgbLED class.
rgb = RgbLED(pin_r=13, pin_g=12, pin_b=22, common_anode=False)

# Helper function to turn the single (status) LED on.
def led_on(): GPIO.output(LED_PIN, GPIO.HIGH)
# Helper function to turn the single (status) LED off.
def led_off(): GPIO.output(LED_PIN, GPIO.LOW)

# Function to block execution until the button is pressed.
def wait_for_button_press():
    # Turn the status LED on to indicate it's ready.
    led_on()
    # Prompt the user to press the button.
    print(" Please press the button to start!")
    # Loop while the button is not pressed (reading LOW).
    while GPIO.input(BUTTON_PIN) == GPIO.LOW:
        # Sleep briefly to poll the button.
        time.sleep(0.05)
    # Confirm the button press.
    print(" Button pressed, starting execution!")
    # A short delay for debouncing.
    time.sleep(0.3)


# ======================================================
# Main
# ======================================================
# Standard Python entry point.
if __name__ == "__main__":
    # Initialize I2C bus variable.
    bno_bus = None
    # Initialize camera capture variable.
    cap = None
    # Start the main try-finally block to ensure cleanup.
    try:
        # [1] IMU Initialization
        # Initialize the SMBus object for I2C.
        bno_bus = SMBus(BNO055_BUS)
        # Attempt to initialize the BNO055 sensor.
        if not init_bno055(bno_bus, wait_for_calibration=True):
            # Print error messages if initialization fails.
            print(" BNO055 initialization failed, please check:")
            print("   1. I2C bus number (Current: BNO055_BUS = 7)")
            print("   2. Hardware wiring is correct")
            print("   3. Use 'sudo i2cdetect -y -r 7' to check the device")
            # Exit the script with an error code.
            sys.exit(2)
        # Print status.
        print(" Waiting for data to fully stabilize...")
        # Wait for sensor readings to settle.
        time.sleep(1)
        # Read the initial heading to use as the "zero" reference.
        zero_heading = read_heading(bno_bus, samples=3)
        # Print the zero offset.
        print(f" Zeroing complete, initial heading: {zero_heading:.2f}° (Will be used as 0° reference)")
        # Start the background thread for continuous IMU updates.
        threading.Thread(target=imu_loop, args=(bno_bus, zero_heading, 0.05), daemon=True).start()

        # [2] Camera Capture Initialization (Moved up)
        # Initialize the video capture with the GStreamer pipeline.
        cap = cv2.VideoCapture(gstreamer_csi_pipeline(), cv2.CAP_GSTREAMER)
        # Check if the camera failed to open.
        if not cap.isOpened():
            # Print error.
            print("Camera open failed")
            # Exit the script.
            sys.exit(1)
        # Try to set the camera buffer size to 1 (to get the latest frame).
        try:
            # Set property.
            cap.set(cv2.CAP_PROP_BUFFERSIZE, 1)
        # Catch exceptions if this property is not supported.
        except Exception:
            # Ignore the error.
            pass

        # ---- State / Parameter Initialization ----
        # (This variable seems unused).
        eTurnMethod = ""
        # Flag for lap completion.
        lapsComplete = False
        # Target X-coordinates for red and green pillars.
        redTarget, greenTarget = 110, 540
        # Store the last seen pillar target.
        lastTarget = 0
        # Flag for temporary parking state.
        tempParking = False
        # Timestamp for 's' state.
        sTime = 0
        # State variable 's' (used in pillar logic).
        s = 0
        # (This variable seems unused).
        endConst = 50
        # (This variable seems unused).
        lotType = "light"
        # Current turning direction state ("none", "left", "right").
        turnDir = "none"
        # Flag for pillar detection at the start.
        pillarAtStart = -1
        # Lap counter 't' (re-initialized, global 't' is also used by inc_t()).
        t = 0
        # Secondary lap counter 't2'.
        t2 = 0
        # (This variable seems unused).
        B = 0
        # Flag for being in a right turn.
        rTurn = False
        # Flag for being in a left turn.
        lTurn = False
        # Flag for signaling a turn (?).
        tSignal = False

        # Define ROI1 (Left wall).
        ROI1 = [0, 180, 330, 245]
        # Define ROI2 (Right wall).
        ROI2 = [330, 180, 640, 245]
        # Define ROI3 (Pillars).
        ROI3 = [redTarget - 100, 45, greenTarget + 100, 360]
        # Define ROI4 (Front obstacle / Lap lines).
        ROI4 = [200, 305, 440, 350]
        # Define ROI5 (Turn helper), initially empty.
        ROI5 = [0, 0, 0, 0]
        # Define ROI6 (Magenta obstacle), initially empty.
        ROI6 = [0, 0, 0, 0]
        # Area from ROI5.
        tArea = 0
        # Magenta area from ROI6.
        mag6_area = 0
        # Magenta center from ROI6.
        mag6_center = 0
        # Magenta bounding box from ROI6.
        mag6_bbox = 0

        # PD gains for wall following.
        kp, kd = 0.02, 0.03
        # PD gains for pillar following.
        cKp, cKd, cy = 0.2, 0.3, 0.28

        # Initialize steering angle.
        angle = 0
        # Store previous angle.
        prevAngle = angle
        # Define max turn deviation.
        tDeviation = 50
        # Set sharp left angle.
        sharpLeft = LEFT(tDeviation)
        # Set sharp right angle.
        sharpRight = RIGHT(tDeviation)
        # Set forward and reverse speeds.
        speed, reverseSpeed = 60, -40
        # Initial area of the start pillar.
        startArea = 4000
        # PD differential for wall following.
        aDiff = 0
        # Previous differential (for derivative term).
        prevDiff = 0
        # Previous error (for derivative term) for pillar following.
        prevError = 0
        # Maximum distance (heuristic) to consider a pillar.
        maxDist = 370
        # Left wall area.
        leftArea = 0
        # Right wall area.
        rightArea = 0
        # Pillar following error (x - target_x).
        error= 0
        # (These variables seem unused).
        ERROR = 0
        ERROR_1 = 0
        # Counter 'count' (used for post-lap logic).
        count = 0
        # (This variable seems unused).
        c = 0
        
        # Check if "debug" is in the command-line arguments.
        debug = ("debug" in "".join(sys.argv).lower())


        # ===== Lap Line Thresholds =====
        # Area threshold to trigger blue line detection.
        BLUE_ON_THRESH      = 90
        # Area threshold to re-arm blue line detection.
        BLUE_OFF_THRESH     = 60
        # Cooldown period (seconds) after blue line detection.
        BLUE_COOLDOWN_SEC = 2
        # Timestamp when blue line detection is allowed again.
        blue_next_allowed_time = 0
        # Flag to indicate if blue detection is armed (ready).
        blue_armed = True

        # Area threshold to trigger orange line detection.
        ORANGE_ON_THRESH      = 90
        # Area threshold to re-arm orange line detection.
        ORANGE_OFF_THRESH     = 60
        # Cooldown period (seconds) after orange line detection.
        ORANGE_COOLDOWN_SEC = 2
        # Timestamp when orange line detection is allowed again.
        orange_next_allowed_time = 0
        # Flag to indicate if orange detection is armed (ready).
        orange_armed = True
        
        # Print status message. (Translated from Chinese, adapted)
        print(" Please press the button to start! Debug window is active (if 'debug' arg was passed).")
        # Turn on status LED to indicate waiting. (Comment translated)
        led_on() # Light on means waiting for button
        
        # ===== Wait for Button Press Loop =====
        # Loop while the button is not pressed.
        while GPIO.input(BUTTON_PIN) == GPIO.LOW:
            # Read a frame from the camera.
            ok, img = cap.read()
            # If frame read failed, skip.
            if not ok:
                # Wait briefly.
                time.sleep(0.01)
                # Retry loop.
                continue
            
            # If in debug mode:
            if debug:
                # Show a "waiting" message on the screen. (Comment translated)
                # Display waiting message on the image
                cv2.putText(img, "WAITING FOR BUTTON PRESS...", (10, 470),
                    cv2.FONT_HERSHEY_DUPLEX, 0.8, (0, 0, 0), 4)
                # White text overlay.
                cv2.putText(img, "WAITING FOR BUTTON PRESS...", (10, 470),
                    cv2.FONT_HERSHEY_DUPLEX, 0.8, (255, 255, 255), 1)
                # Display debug label.
                cv2.putText(img, "jetson_debug", (10, 30), cv2.FONT_HERSHEY_DUPLEX, 1, (255,255,255), 1)

                # Show the image in the debug window.
                cv2.imshow("jetson_debug", img)
                # Check for 'q' key to quit.
                if cv2.waitKey(1) == ord('q'):
                    # Raise the HaltRun exception to exit cleanly. (Comment translated)
                    raise HaltRun # Allow exit
            
            # Prevent high CPU usage while polling. (Comment translated)
            time.sleep(0.05) # Avoid using too much CPU

        # Print confirmation.
        print(" Button pressed, starting execution!")
        # Debounce delay.
        time.sleep(0.3)
        # Turn off status LED to indicate running. (Comment translated)
        led_off() # Light off means running

        # Send initial command to set speed.
        write(("S", speed))
        # Send initial command to set angle to 0 (straight).
        write(0)
        # Wait for car to start moving.
        time.sleep(0.5)

        # Record the main loop start time.
        pTimer = time.time()
        # Flag to indicate if first command has been sent.
        start = False

        # Set the period for sending UART data (0.05s = 20Hz).
        TX_PERIOD      = 0.05  # 20Hz
        # Timestamp of the last UART transmission.
        last_tx        = 0.0

        # Frequency for logging (log every 10 frames).
        log_every = 10
        # Frame counter.
        frame_id = 0

        # ===== LED State (Blue/Orange) + Hysteresis =====
        # Current color state of the RGB LED.
        led_state = "off"   # "blue" / "orange" / "green" / "red" / "off"
        # Hysteresis flag for blue line.
        blue_seen = False
        # Hysteresis flag for orange line.
        orange_seen = False
        # Timestamp of the last LED log message.
        last_led_log = 0.0

        # ==== Starting Direction Judgment ====
        # Loop control variable.
        a = 0
        # Variable to store start turn direction (1=right, 2=left).
        start_turn = 0
        # Loop until direction is determined.
        while a == 0:
            # Reset area variables.
            rightArea = leftArea = areaFront = tArea = 0
            # Read a frame.
            ok, img = cap.read()
            # Skip if frame failed.
            if not ok:
                # Retry loop.
                continue
            # Convert to LAB color space.
            img_lab = cv2.cvtColor(img, cv2.COLOR_BGR2Lab)
            # Apply blur.
            img_lab = cv2.GaussianBlur(img_lab, (3,3), 0)

            # Find left wall contours (using pOverlap).
            contours_left   = pOverlap(img_lab, ROI1)
            # Find right wall contours.
            contours_right = pOverlap(img_lab, ROI2)
            # Get max area for left wall.
            leftArea    = max_contour(contours_left,  ROI1)[0]
            # Get max area for right wall.
            rightArea = max_contour(contours_right, ROI2)[0]

            # Compare areas to decide start direction.
            if leftArea - rightArea > 0:
                # Print and set direction to right.
                print("Turning Right"); start_turn = 1; a = 1
            # Otherwise, turn left.
            else:
                # Print and set direction to left.
                print("Turning Left"); start_turn = 2; a = 1
            
            # Ensure the frame is shown even while waiting. (Comment translated)
            # Ensure image is visible during waiting phase
            if debug:
                # Show the debug image.
                cv2.imshow("jetson_debug", img)
                # Check for 'q' to quit.
                if cv2.waitKey(1) == ord('q'):
                    # Halt execution.
                    raise HaltRun

        # Send the start turn signal ('1' or '2') to Pico W.
        write(str(start_turn)) 
        # Print confirmation.
        print(f"Sending start signal: {start_turn}")

        # Set the color to use for lap counting based on the start turn.
        use_color_for_lap = "orange" if start_turn == 1 else "blue"
        # Print the selected lap counter color.
        print("[LapCounter] using:", use_color_for_lap)

        # ==== Wait for Pillar Color Judgment ====
        # Variable to store the detected color signal (1-6).
        color = 0
        # Record the start time for this detection phase.
        detect_start = time.time()
        # Set a timeout for color detection.
        TIMEOUT = 2.0
        # Loop while 'a' is 1 (detection phase).
        while a == 1:
            # Read a frame.
            ok, img = cap.read()
            # Skip if frame failed.
            if not ok:
                # Retry loop.
                continue
            # Convert to LAB and blur.
            img_lab = cv2.cvtColor(img, cv2.COLOR_BGR2Lab)
            # Apply blur.
            img_lab = cv2.GaussianBlur(img_lab, (3,3), 0)

            # Find wall contours (using 'add=True' for pOverlap).
            contours_left   = pOverlap(img_lab, ROI1, True)
            # Find right wall contours.
            contours_right = pOverlap(img_lab, ROI2, True)
            # Get max area for left wall.
            leftArea    = max_contour(contours_left,  ROI1)[0]
            # Get max area for right wall.
            rightArea = max_contour(contours_right, ROI2)[0]

            # Find red pillar contours in ROI3.
            contours_red   = find_contours(img_lab, rRed,   ROI3)
            # Find green pillar contours in ROI3.
            contours_green = find_contours(img_lab, rGreen, ROI3)
            # Find the best (closest) red pillar.
            best_red,   _ = find_best_pillar(contours_red,   redTarget,   "red",   img_lab)
            # Find the best (closest) green pillar.
            best_green, _ = find_best_pillar(contours_green, greenTarget, "green", img_lab)
            # Create a list of valid (non-None) candidates.
            candidates = [p for p in (best_red, best_green) if p is not None]
            # Select the closest pillar from the candidates, or create a dummy far-away pillar.
            cPillar = min(candidates, key=lambda P: P.dist) if candidates else Pillar(0, 1000000, 0, 0, 0)
            # Check if the closest pillar is green.
            seen_green_wait = (cPillar.target == greenTarget )
            # Check if the closest pillar is red.
            seen_red_wait   = (cPillar.target == redTarget)

            # === RGB: Green if green seen; Red if red seen; Off otherwise ===
            # If green is seen:
            if seen_green_wait:
                # Show green on RGB LED.
                rgb.show("green")
            # If red is seen:
            elif seen_red_wait:
                # Show red on RGB LED.
                rgb.show("red")
            # Otherwise:
            else:
                # Turn RGB LED off.
                rgb.off()

            # Determine the color signal code based on start_turn and detected color.
            if start_turn == 2: # Left start
                # If green seen:
                if seen_green_wait: color = 1; print("green"); a = 2
                # If red seen:
                elif seen_red_wait: color = 2; print("red"); a = 2
                # If timeout:
                elif time.time() - detect_start > TIMEOUT: color = 3; a = 2
            # If start_turn == 1 (Right start)
            else:
                # If green seen:
                if seen_green_wait: color = 4; print("green"); a = 2
                # If red seen:
                elif seen_red_wait: color = 5; print("red"); a = 2
                # If timeout:
                elif time.time() - detect_start > TIMEOUT: color = 6; a = 2

            # If in debug mode:
            if debug:
                # Draw the ROI boxes.
                draw_roi_boxes(img, [ROI1, ROI2, ROI3], color=(255, 204, 0), thickness=2)
                # Show the debug image.
                cv2.imshow("jetson_debug", img)
                # Check for 'q' to quit.
                if cv2.waitKey(1) == ord('q'):
                    # Halt execution.
                    raise HaltRun

        # Print the color signal code to be sent.
        print(f"Sending color signal: {color}")
        # Send the color signal ('1' - '6') to Pico W.
        write(str(color)) 

        # Record a timestamp for the final wait.
        time2 = time.time()
        # Loop while 'a' is 2 (final wait phase).
        while a == 2:
            # Wait until 4.5 seconds have passed.
            while time.time() - time2 < 4.5:
                # Print the elapsed time.
                print(time.time() - time2)
            # Exit the loop.
            a=3

        # =================== Main Loop ===================
        try:
            # Start the main processing loop.
            while True:
                # Record frame start time for FPS calculation.
                fps_start = time.time()

                # Get image
                # Read a frame.
                ok, img = cap.read()
                # If frame read failed, skip.
                if not ok:
                    # Retry loop.
                    continue
                # Convert to LAB color space.
                img_lab = cv2.cvtColor(img, cv2.COLOR_BGR2Lab)
                # Apply blur.
                img_lab = cv2.GaussianBlur(img_lab, (3,3), 0)
                
                # ROI5 Turn reinforcement
                # Initialize turn contour lists.
                contours_turn, contours_turn_m = [], []
                # If ROI5 is active (not all zeros):
                if ROI5[0] != 0:
                    # Find black contours in ROI5.
                    contours_turn   = find_contours(img_lab, rBlack,   ROI5)
                    # Find magenta contours in ROI5.
                    contours_turn_m = find_contours(img_lab, rMagenta, ROI5)
                    # Sum the areas from both black and magenta contours.
                    tArea = max_contour(contours_turn, ROI5)[0] + max_contour(contours_turn_m, ROI5)[0]

                # Left/Right walls
                # Find left wall contours (using pOverlap with add=True).
                contours_left   = pOverlap(img_lab, ROI1, True)
                # Find right wall contours.
                contours_right = pOverlap(img_lab, ROI2, True)
                # Get max area for left wall.
                leftArea    = max_contour(contours_left, ROI1)[0]
                # Get max area for right wall.
                rightArea = max_contour(contours_right, ROI2)[0]

                # Front black (for parking)
                # Find black contours in ROI4 (front).
                contours_parking = find_contours(img_lab, rBlack, ROI4)
                # Get max area of front black.
                areaFront = max_contour(contours_parking, ROI4)[0]

                # Red/Green pillars
                # Find red pillar contours in ROI3.
                contours_red   = find_contours(img_lab, rRed,   ROI3)
                # Find green pillar contours in ROI3.
                contours_green = find_contours(img_lab, rGreen, ROI3)

                # Corner Blue/Orange lines
                # Find blue line contours in ROI4.
                contours_blue   = find_contours(img_lab, rBlue,   ROI4)
                # Find orange line contours in ROI4.
                contours_orange = find_contours(img_lab, rOrange, ROI4)
                # Get max area of orange line.
                maxO = max_contour(contours_orange,  ROI4)[0]
                # Get max area of blue line.
                maxB = max_contour(contours_blue,    ROI4)[0]

                # ★ Lap counting based on start turn (using selected color)
                # Get the current timestamp.
                now_ts = time.time()
                # If we are looking for the blue line:
                if use_color_for_lap == "blue":
                    # If area is below OFF threshold, re-arm.
                    if maxB <= BLUE_OFF_THRESH and not blue_armed:
                        # Set armed flag to true.
                        blue_armed = True
                    # If area is above ON threshold, and armed, and cooldown passed:
                    if maxB >= BLUE_ON_THRESH and blue_armed and now_ts >= blue_next_allowed_time:
                        # Disarm (to prevent re-triggering).
                        blue_armed = False
                        # Set the next allowed time.
                        blue_next_allowed_time = now_ts + BLUE_COOLDOWN_SEC
                        # Increment the lap counter.
                        inc_t()
                # If we are looking for the orange line:
                else:
                    # If area is below OFF threshold, re-arm.
                    if maxO <= ORANGE_OFF_THRESH and not orange_armed:
                        # Set armed flag to true.
                        orange_armed = True
                    # If area is above ON threshold, and armed, and cooldown passed:
                    if maxO >= ORANGE_ON_THRESH and orange_armed and now_ts >= orange_next_allowed_time:
                        # Disarm (to prevent re-triggering).
                        orange_armed = False
                        # Set the next allowed time.
                        orange_next_allowed_time = now_ts + ORANGE_COOLDOWN_SEC
                        # Increment the lap counter.
                        inc_t()

                # Check if 13 laps are completed (entering obstacle phase).
                if t >= 13:
                    # ===== ROI6 Magenta Detection =====
                    # Activate ROI6 (full bottom area).
                    ROI6 = [0, 45, 640, 480]
                    # Find the largest magenta obstacle in ROI6.
                    mag6_area, mag6_center, mag6_bbox = _largest_magenta_in_roi(img_lab, ROI6)
                    # If this is the first frame after 13 laps:
                    if count == 0:
                        # Stop the car.
                        stop_car()
                        # Turn off the status LED.
                        led_off()

                # ========== Regular Pillar/Wall Following Calculation ==========
                # Find the best red pillar.
                best_red,   _ = find_best_pillar(contours_red,   redTarget,   "red",   img_lab)
                # Find the best green pillar.
                best_green, _ = find_best_pillar(contours_green, greenTarget, "green", img_lab)
                # Create a list of valid (non-None) candidates.
                candidates = [p for p in (best_red, best_green) if p is not None]
                # Select the closest pillar from the candidates, or create a dummy far-away pillar.
                cPillar = min(candidates, key=lambda P: P.dist) if candidates else Pillar(0, 1000000, 0, 0, 0)

                # At t=0, capture the area of the first pillar seen.
                if t == 0 and cPillar.area > startArea:
                    # Store its area.
                    startArea = cPillar.area
                    # Store its target type.
                    startTarget = cPillar.target

                # If not currently in a turn, check for new turn signals (lines).
                if turnDir == "none":
                    # If orange line is seen, start a right turn.
                    if maxO > 100:
                        # Set turn direction.
                        turnDir = "right"
                    # If blue line is seen, start a left turn.
                    elif maxB > 100:
                        # Set turn direction.
                        turnDir = "left"

                # If a turn is active and the correct line is still visible:
                if (turnDir == "right" and maxO > 100) or (turnDir == "left" and maxB > 100):
                    # Record the lap count when the turn started.
                    t2 = t
                    # Special case for lap 7 (adjust ROI3).
                    if t2 == 7 and not pillarAtStart:
                        # Move ROI3 (pillars) up.
                        ROI3[1] = 110
                    # If a pillar is visible during the turn:
                    if cPillar.area != 0 and turnDir == "left" or cPillar.area != 0 and turnDir == "right":#cPillar.area != 0 and ((leftArea > 1000 and turnDir == "left") or (rightArea > 1000 and turnDir == "right"))
                        # Activate ROI5 (turn helper).
                        ROI5 = [270, 110, 370, 150]
                    # If it's a right turn:
                    if turnDir == "right":
                        # Set the right turn flag.
                        rTurn = True
                    # If it's a left turn:
                    else:
                        # Set the left turn flag.
                        lTurn = True
                    # At t=0, check if there was a pillar at the start line.
                    if t == 0 and pillarAtStart == -1:
                        # Set the pillarAtStart flag.
                        pillarAtStart = True if ((startArea > 2000 and startTarget == greenTarget) or (startArea > 1500 and startTarget == redTarget)) else False
                    # Set the signal flag.
                    tSignal = True
                # Check for "wrong" line detection (e.g., blue during a right turn).
                elif (turnDir == "left" and maxO > 100) or (turnDir == "right" and maxB > 100):
                    # Special case for lap 11 (related to 's' state).
                    if t2 == 11:
                        # Set 's' state.
                        s = 2
                        # Record timestamp for 's' state.
                        sTime = time.time()

                # Steering Angle.
                # If not in post-lap obstacle mode (count == 0):
                if count == 0:
                    # If no pillar is visible AND no turn helper (ROI5) is active:
                    if cPillar.area == 0 and tArea < 100:
                        # --- Wall Following ---
                        # Calculate PD error (difference in wall areas).
                        aDiff = leftArea-rightArea
                        # Calculate PD control output (angle).
                        angle = int(aDiff*kp + (aDiff - prevDiff)*kd)
                        # Clamp the angle to limits.
                        angle = clamp(angle, sharpLeft, sharpRight)
                        # Store the current error for the next derivative calculation.
                        prevDiff = aDiff
                    # If ROI5 (turn helper) is not active (but pillar *is* visible):
                    elif tArea < 100:
                        # --- Pillar Following ---
                        # Calculate PD error (pillar_x - target_x).
                        error = cPillar.x - cPillar.target
                        # Calculate PD control output (angle).
                        angle = int(0 + error*cKp + (error - prevError)*cKd)
                        # Clamp the angle to limits.
                        angle = clamp(angle, sharpLeft, sharpRight)
                        # Store the last seen pillar type (if it's on the correct side).
                        if cPillar.target == greenTarget and cPillar.x > 320 and cPillar.area > 1000:
                            # Store green target.
                            lastTarget = greenTarget
                        # Store the last seen pillar type.
                        elif cPillar.target == redTarget and cPillar.x < 320 and cPillar.area > 1000:
                            # Store red target.
                            lastTarget = redTarget
                        # Store the current error for the next derivative calculation.
                        prevError = error
        
                        
                    # If a hard turn (lTurn or rTurn) is active:
                    if rTurn or lTurn == True:
                        # --- Turn Helper (ROI5) --- (Comment translated)
                        # ROI5 Turn reinforcement
                        # If ROI5 detects a strong line (black/magenta):
                        if ((tArea > 1000 and turnDir == "left") or (tArea > 1000 and turnDir == "right")):
                            # If a pillar is *also* visible (over 3000 area):
                            if cPillar.area > 3000:
                                # Go straight (override turn).
                                angle = 0
                            # If it's a right turn (and no pillar):
                            elif turnDir == "right":
                                # Turn hard right.
                                angle = sharpRight
                                # Print debug message.
                                print("right")
                            # If it's a left turn (and no pillar):
                            else:
                                # Turn hard left.
                                angle = sharpLeft
                                # Print debug message.
                                print("left")

                        # If no pillar is visible AND ROI5 is also clear:
                        if ((cPillar.area == 0 and tArea < 100)):#abs(leftArea - rightArea) > 1000 and tArea > 1000)
                            # Reset the turn helper area.
                            tArea = 0
                            # Deactivate ROI5.
                            ROI5 = [0,0,0,0]

                    # Increment the frame counter.
                    frame_id += 1
                    # If it's time to log:
                    if frame_id % log_every == 0:
                        # Print a comprehensive debug log.
                        print(t, lTurn, rTurn, leftArea, rightArea, cPillar.target, angle, f"{relative_heading:.2f}",
                              "mag6:", mag6_area, mag6_center)

                # Send the first motor command (one time).
                if not start:
                    # Send speed, wait, then send angle.
                    multi_write([("S", speed), 0.03, angle])
                    # Set the flag to true.
                    start = True

                # ====== Transmit Control Data ====== (
                # Get the current time.
                now = time.time()
                
                # Check if it's time to send the next UART packet.
                if now - last_tx >= TX_PERIOD:
                    # Call the broadcast function to send JSON and control command.
                    uart_hub.broadcast_json( 
                        # Wall areas.
                        leftArea=leftArea,
                        rightArea=rightArea,
                        # IMU heading.
                        yaw=relative_heading,
                        # Commanded angle.
                        angle=angle,
                        # Commanded speed.
                        speed=speed,
                        # Magenta obstacle area.
                        magArea=mag6_area, 
                        # Magenta obstacle center X.
                        magCX=mag6_center[0] if mag6_center else 0,
                        # Magenta obstacle center Y.
                        magCY=mag6_center[1] if mag6_center else 0
                    )
                    # Update the last transmission time.
                    last_tx = now
                
                # ====== RGB: Line Priority + Hysteresis ======
                # Check if blue line is seen (above ON threshold).
                if maxB >= BLUE_ON_THRESH:
                    # Set hysteresis flag.
                    blue_seen = True
                # Check if blue line is unseen (below OFF threshold).
                elif maxB <= BLUE_OFF_THRESH:
                    # Clear hysteresis flag.
                    blue_seen = False

                # Check if orange line is seen.
                if maxO >= ORANGE_ON_THRESH:
                    # Set hysteresis flag.
                    orange_seen = True
                # Check if orange line is unseen.
                elif maxO <= ORANGE_OFF_THRESH:
                    # Clear hysteresis flag.
                    orange_seen = False

                # Determine the target LED color (lines have priority).
                if blue_seen:
                    # Set target to blue.
                    target_led = "blue"
                # Else if orange is seen:
                elif orange_seen:
                    # Set target to orange.
                    target_led = "orange"
                # If no lines are seen:
                else:
                    # Check for pillars.
                    seen_green = (best_green is not None and best_green.area > 0)
                    # Check for red pillar.
                    seen_red   = (best_red   is not None and best_red.area   > 0)
                    # If green is seen:
                    if seen_green:
                        # Set target to green.
                        target_led = "green"
                    # Else if red is seen:
                    elif seen_red:
                        # Set target to red.
                        target_led = "red"
                    # If nothing is seen:
                    else:
                        # Set target to off.
                        target_led = "off"

                # If the target state is different from the current state:
                if target_led != led_state:
                    # Update the physical RGB LED.
                    rgb.show(target_led if target_led != "off" else "off")
                    # Store the new state.
                    led_state = target_led

                # Log the LED state periodically.
                if now - last_led_log > 1.0:
                    # Print the log message.
                    print(f"[LED] B:{int(maxB)} O:{int(maxO)} -> {led_state}")
                    # Update the log timestamp.
                    last_led_log = now
                
                # If in debug mode:
                if debug:
                    # Draw all active ROI boxes.
                    draw_roi_boxes(img, [ROI1, ROI2, ROI3, ROI4, ROI5, ROI6], color=(255, 204, 0), thickness=2)
                    # Define colors for debug drawing.
                    COLOR_BLUE    = (255 , 0 , 0)
                    COLOR_ORANGE  = (0, 165, 255)
                    COLOR_LWALL   = (0, 255, 0)
                    COLOR_RWALL   = (0, 255, 255)
                    COLOR_RED     = (0, 0, 255)
                    COLOR_GREEN   = (0, 255, 0)
                    COLOR_FRONT   = (200, 200, 200)
                    COLOR_TURN    = (128, 128, 255)
                    COLOR_MAGENTA = (255, 0, 255)

                    # Start try block for drawing (in case contours are invalid).
                    try:
                        # Draw left wall contours.
                        draw_contours_list(img, contours_left, ROI1, COLOR_LWALL,  label="Lwall",  thickness=2)
                        # Draw right wall contours.
                        draw_contours_list(img, contours_right,ROI2, COLOR_LWALL,  label="Rwall",  thickness=2)
                        # Draw red pillar contours.
                        draw_contours_list(img, contours_red,  ROI3, COLOR_RED,    label="pillar(R)", thickness=2)
                        # Draw green pillar contours.
                        draw_contours_list(img, contours_green,ROI3, COLOR_GREEN,  label="pillar(G)", thickness=2)
                        # Draw blue line contours.
                        draw_contours_list(img, contours_blue, ROI4, COLOR_BLUE,   label="blue",  thickness=2)
                        # Draw orange line contours.
                        draw_contours_list(img, contours_orange,ROI4,COLOR_ORANGE, label="orange",thickness=2)
                        # Draw front (parking) contours.
                        draw_contours_list(img, contours_parking,ROI4,COLOR_FRONT, label="front", thickness=2)
                        # If ROI5 is active:
                        if ROI5[0] != 0:
                            # Draw black turn helper contours.
                            draw_contours_list(img, contours_turn,  ROI5, COLOR_TURN, label="turn(B)", thickness=2)
                            # Draw magenta turn helper contours.
                            draw_contours_list(img, contours_turn_m,ROI5, COLOR_TURN, label="turn(M)", thickness=2)
                        # If ROI6 is active and magenta obstacle is found:
                        if ROI6[1] != 0 and mag6_area > 0 and mag6_center is not None and mag6_bbox is not None:
                            # Get the bounding box.
                            x, y, w, h = mag6_bbox
                            # Draw the bounding box.
                            cv2.rectangle(img, (x, y), (x + w, y + h), COLOR_MAGENTA, 2)
                            # Draw the center point.
                            cv2.circle(img, (mag6_center[0], mag6_center[1]), 5, COLOR_MAGENTA, -1)

                    # Catch any drawing errors.
                    except Exception:
                        # Ignore them.
                        pass

                    # Display blue line area and lap count (t).
                    cv2.putText(img, f"B:{int(maxB)}  t:{t}", (10, 60),  cv2.FONT_HERSHEY_DUPLEX, 0.8, (0,0,0), 4)
                    # White text overlay.
                    cv2.putText(img, f"B:{int(maxB)}  t:{t}", (10, 60),  cv2.FONT_HERSHEY_DUPLEX, 0.8, (255,255,255), 1)

                    # Calculate FPS.
                    fps = "fps: " + str(int(1 / max(1e-6, (time.time() - fps_start))))
                    # Calculate elapsed time.
                    elapsed = "time: " + str(int(time.time() - pTimer)) + "s"
                    # Draw FPS (black outline).
                    cv2.putText(img, fps,     (500, 30), cv2.FONT_HERSHEY_DUPLEX, 1, (0,0,0), 4)
                    # Draw elapsed time (black outline).
                    cv2.putText(img, elapsed, (10,  30), cv2.FONT_HERSHEY_DUPLEX, 1, (0,0,0), 4)
                    # Draw FPS (white text).
                    cv2.putText(img, fps,     (500, 30), cv2.FONT_HERSHEY_DUPLEX, 1, (255,255,255), 1)
                    # Draw elapsed time (white text).
                    cv2.putText(img, elapsed, (10,  30), cv2.FONT_HERSHEY_DUPLEX, 1, (255,255,255), 1)

                    # If a valid pillar is found:
                    if cPillar and cPillar.area > 0:
                        # Draw a circle at its base-center.
                        cv2.circle(img, (int(cPillar.x), int(cPillar.y)), 6, (0, 0, 255), -1)
                        # Display its area and distance.
                        cv2.putText(img, f"Pillar a:{int(cPillar.area)} d:{int(cPillar.dist)}",
                                    # Position the text next to the circle.
                                    (int(cPillar.x)+6, int(cPillar.y)-8),
                                    # Font settings.
                                    cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0,0,255), 2)

                    # Show the final debug image.
                    cv2.imshow("jetson_debug", img)
                    # Check for 'q' key to quit.
                    if cv2.waitKey(1) == ord('q'):
                        # Stop the car.
                        stop_car()
                        # Break out of the main loop.
                        break

                # Store the current angle for the next PD loop.
                prevAngle = angle
                # Reset the turn signal flag.
                tSignal = False
                # Store the current error for the next PD loop.
                prevError = error

        # Catch the custom HaltRun exception (e.g., from pressing 'q').
        except HaltRun:
            # Just pass, will proceed to finally block.
            pass

    # This block runs no matter how the program exits (error, 'q', or normal end).
    finally:
        # Send a final stop command to the car.
        stop_car()
        # If the camera was opened:
        if cap:
            # Release the camera resource.
            cap.release()
        # If the I2C bus was opened:
        if bno_bus:
            # (No explicit close needed for smbus2, but good practice).
            pass
        # If the UART hub was initialized:
        if 'uart_hub' in locals() and uart_hub:
            # Stop the UART thread and close the port.
            uart_hub.stop()
        # Clean up all GPIO pins.
        GPIO.cleanup()
        # Exit the script.
        sys.exit(0)