# Import necessary standard libraries.
import sys, cv2, time, json, queue, threading, asyncio, numpy as np
# Import the Jetson.GPIO library for hardware pin control.
import Jetson.GPIO as GPIO
# Import custom computer vision functions from 'function.py'.
from function import find_contours, max_contour, pOverlap 
# Import color range constants (masks) for CV.
from masks import rOrange, rBlack, rBlue, rMagenta 
# Import the serial library for UART communication.
import serial 

# Define the serial port device name for UART.
UART_PORT = "/dev/ttyTHS0" 
# Define the baud rate for UART communication.
UART_BAUDRATE = 115200

# Define a utility function to constrain a value 'v' between 'lo' and 'hi'.
def clamp(v, lo, hi):
    # Return the clamped value.
    return lo if v < lo else (hi if v > hi else v)

# Define a function to convert a PWM signal (1000-2000) to a percentage (-100 to 100).
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
        # Store a pending turn signal command.
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
            print(f" UART opened on {self.port} at {self.baudrate} baud.")
        # Handle exceptions if the serial port fails to open.
        except serial.SerialException as e:
            # Print the failure message.
            print(f" Failed to open serial port {self.port}: {e}")
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
        print("Waiting for Pico W Ready signal...")
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

    # Define the main public method for sending commands (motor, angle, sleep).
    def write(self, value):
        # If the value is a small float, treat it as a sleep duration.
        if isinstance(value, float) and value < 10.0:
            # Pause execution for that duration.
            time.sleep(float(value))
            # Exit the function.
            return
        
        # If the value is a tuple like ("S", speed), update speed.
        if isinstance(value, tuple) and len(value) == 2 and value[0] == "S":
            # Store the speed percentage directly.
            self._last_speed_pct = int(value[1]) 
        # If the value is an integer >= 1000, treat it as PWM speed.
        elif isinstance(value, int) and value >= 1000:
            # Convert PWM to percentage and store it.
            self._last_speed_pct = pwm_to_percent(value)
        
        # If the value is an integer (and not PWM), treat it as an angle.
        elif isinstance(value, int):
            # Cast the value to an integer.
            rel = int(value)
            # Clamp the angle value.
            rel = clamp(rel, -180, 180)
            # Store the angle.
            self._last_angle_rel = rel
        
        # If the value is a string of digits, treat it as a turn signal command.
        elif isinstance(value, str) and value.isdigit():
            # Store it as a pending signal.
            self._pending_turn_signal = value
        
        # Get the last stored angle.
        angle_to_send = self._last_angle_rel
        # Get the last stored speed.
        speed_to_send = self._last_speed_pct
        
        # Check if there is a pending turn signal to send.
        if self._pending_turn_signal:
            # Format the turn signal command (M,signal_code,0).
            text = f"M,{self._pending_turn_signal},0\n"
            # Send the command.
            self._send(text)
            # Print the sent signal command.
            print(f"[UART SEND] Signal: {text.strip()}")
            # Clear the pending signal.
            self._pending_turn_signal = None
            # Exit the function (don't send a motion command this time).
            return 

        # Format the standard motion control command (M,angle,speed).
        control_cmd = f"M,{int(angle_to_send)},{int(speed_to_send)}\n"
        # Send the motion command.
        self._send(control_cmd) 

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


# Instantiate the UartHub class.
uart_hub = UartHub(UART_PORT, UART_BAUDRATE)
# Create a global alias for the 'write' method.
write          = uart_hub.write
# Create a global alias for the 'multi_write' method.
multi_write    = uart_hub.multi_write
# Create a global alias for the 'stop_car' method.
stop_car       = uart_hub.stop_car
# Create a global alias for the 'wait_for_start' method.
wait_for_start = uart_hub.wait_for_start


# ===================== IMU Stub =====================
# Define a placeholder (stub) function for reading an IMU.
def read_imu_angle():
    # Always return 0 as the IMU angle (not implemented).
    return 0

# ===================== GStreamer =====================
# Define a function to generate the GStreamer pipeline string...
def gstreamer_pipeline(sensor_id=0, capture_width=640, capture_height=480,
                       # ...for capturing from the Jetson's CSI camera.
                       display_width=640, display_height=480,
                       # (Function signature continues).
                       framerate=30, flip_method=0):
    # Return the formatted string.
    return (
        # NVIDIA camera source element.
        f"nvarguscamerasrc sensor-id={sensor_id} ! "
        # Set camera properties (NVMM memory).
        f"video/x-raw(memory:NVMM), width=640, height=480, "
        # Set format and framerate.
        f"format=NV12, framerate=30/1 ! "
        # NVIDIA video converter for flipping/conversion.
        f"nvvidconv flip-method={flip_method} ! "
        # Set output format to BGRx.
        f"video/x-raw, width=640, height=480, format=BGRx ! "
        # Software video converter.
        f"videoconvert ! "
        # Final format BGR for OpenCV, sent to appsink.
        f"video/x-raw, format=BGR ! appsink"
    # End of string.
    )

# ===================== LED =====================
# Set the GPIO pin numbering mode to BCM.
GPIO.setmode(GPIO.BCM)
# Disable GPIO warnings.
GPIO.setwarnings(False)
# Define the GPIO pin number for the LED.
LED_PIN = 21  
# Define the GPIO pin number for the button.
BUTTON_PIN = 18  
# Set the LED pin as an output.
GPIO.setup(LED_PIN, GPIO.OUT)
# Set the button pin as an input with a pull-down resistor.
GPIO.setup(BUTTON_PIN, GPIO.IN, pull_up_down=GPIO.PUD_DOWN)

# Define a helper function to turn the LED on.
def led_on(): GPIO.output(LED_PIN, GPIO.HIGH)
# Define a helper function to turn the LED off.
def led_off(): GPIO.output(LED_PIN, GPIO.LOW)

# Define a function to block execution until the button is pressed.
def wait_for_button_press():
    # Turn the LED on to indicate it's ready.
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

# ===================== UART Control =====================
# Define a helper function to send both angle and speed.
def send_motor(angle: int, speed: int):
    # Call 'write' for the angle (updates internal state).
    write(int(angle))
    # Call 'write' for the speed (updates state and sends the command).
    write(("S", int(speed)))


# ===================== ROI Display / Helper Functions =====================
# Define a function to draw ROI rectangles on a copy of the image.
def display_roi_with_contours(img, rois, color=(255, 204, 0)):
    # Create a copy of the image to draw on.
    preview = img.copy()
    # Iterate through the list of ROIs.
    for roi in rois:
        # Unpack the ROI coordinates.
        x1, y1, x2, y2 = roi
        # Draw the rectangle on the preview image.
        cv2.rectangle(preview, (x1, y1), (x2, y2), color, 2)
    # Return the image with ROIs drawn.
    return preview

# Define a function to draw detected contours, offset by their ROI.
def draw_contours_in_roi(preview_img, contours, roi, draw_color=(0, 255, 0)):
    # If no contours were found, do nothing.
    if not contours:
        # Exit the function.
        return
    # Iterate through all found contours.
    for contour in contours:
        # Add the ROI's top-left corner offset to the contour points.
        offset_contour = contour + np.array([[roi[0], roi[1]]])
        # Draw the offset contour on the preview image.
        cv2.drawContours(preview_img, [offset_contour], -1, draw_color, 2)      

# ===================== Main Program =====================
# Standard Python entry point.
if __name__ == '__main__':
    # Declare global variables (Note: this is unusual here, usually used inside functions).
    global leftArea, rightArea, orangeArea, blueArea
    # Ensure the LED is off at the start.
    led_off()
    # Start the UART hub (opens port, starts reader thread).
    uart_hub.start() 

    # Print a status message that UART is starting.
    print(f" UART starting on {UART_PORT} ...")
    
    # Initialize the video capture with the GStreamer pipeline.
    cap = cv2.VideoCapture(gstreamer_pipeline(flip_method=0), cv2.CAP_GSTREAMER)
    # Check if the camera failed to open.
    if not cap.isOpened():
        # Print an error message.
        print(" Cannot open CSI camera")
        # Stop the UART hub cleanly.
        uart_hub.stop()
        # Clean up GPIO resources.
        GPIO.cleanup()
        # Exit the script with an error code.
        sys.exit(1)

    # Define the Regions of Interest (ROI) for line detection [x1, y1, x2, y2].
    ROI1, ROI2, ROI3 = [0,180,330,245], [330,180,640,245], [100,300,530,345]

    # Initialize PD controller gains (Proportional, Derivative) and base speed.
    kp, kd, speed = 0.008, 0.015, 70
    # Initialize thresholds for turning (turnThresh seems unused).
    turnThresh, exitThresh = 200, 0
    # Initialize PD loop variables.
    aDiff = prevDiff = prevAngle = 0
    # Initialize turning state flags.
    lTurn = rTurn = False
    # Initialize lap counter 't'.
    t = 0
    # Initialize the main logic 'started' flag.
    started = False
    # Initialize turning direction state.
    turnDir = "none"
    # Set the contour area threshold for detecting the lap line.
    blueLineThreshold = 90
    # Initialize lap line detection flag.
    blueLineDetected = False
    # Initialize timestamp for lap line cooldown.
    lastBlueDetectTime = 0
    # Set a 2-second cooldown between lap detections.
    blueLineCooldown = 2.0
    
    # Flag to indicate if the lap line color has been determined.
    lap_color_locked = False
    # Variable to store which color ("blue" or "orange") is the lap line.
    use_color_for_lap = None # "blue" or "orange"
    
    # Initialize a counter for consecutive camera read failures.
    camera_error_count = 0 
    # Set the maximum number of allowed consecutive camera errors.
    MAX_CAMERA_ERRORS = 10 

    # Initialize area variables to zero.
    leftArea = rightArea = blueArea = orangeArea = 0

    # Start the main try-finally block to ensure cleanup.
    try:
        # Initialize a counter 'count' (used for post-lap wall following).
        count = 0
        # Initialize a timer 'start_time' (used for post-lap wall following).
        start_time = 0
        # Initialize 'angle' variable (seems to be overwritten soon).
        angle = 120
        # Initialize 'error' variable (PD controller error offset).
        error = 0
        # Initialize 'time1' (timestamp for turn logic cooldown).
        time1 = 0
        
            
        # Wait for the user to press the physical button to start.
        wait_for_button_press()
        
        # Set the 'started' flag to True to begin the main logic.
        started = True
        
        # Send the initial command to start moving forward.
        send_motor(angle=0, speed=speed)
        # A brief pause after starting.
        time.sleep(0.1)

        # Start the main camera processing loop.
        while True:
            # Read a frame from the camera.
            ret, img = cap.read()
            # Check if the frame was read successfully.
            if not ret:
                # Increment the camera error counter.
                camera_error_count += 1
                # Print a warning message.
                print(f"Camera read failed! Consecutive errors: {camera_error_count}")
                # Check if the error limit has been reached.
                if camera_error_count >= MAX_CAMERA_ERRORS:
                    # Print a fatal error message.
                    print(f" Exceeded {MAX_CAMERA_ERRORS} consecutive camera errors, exiting.")
                    # Break out of the main loop.
                    break
                # Wait a bit before retrying.
                time.sleep(0.1) 
                # Skip the rest of this loop iteration.
                continue 
            
            # Reset the error counter on a successful read.
            camera_error_count = 0

            
            # Create a preview image with ROIs drawn on it.
            preview_img = display_roi_with_contours(img.copy(), [ROI1, ROI2, ROI3], (255, 204, 0))

            # Check if the 'started' flag (from button press) is true.
            if started:
                # Start a try-except block for the image processing logic.
                try:
                    # Convert the image from BGR to LAB color space.
                    img_lab = cv2.cvtColor(img, cv2.COLOR_BGR2Lab)
                    # Apply a Gaussian blur to reduce noise.
                    img_lab = cv2.GaussianBlur(img_lab, (7, 7), 0)

                    # Find black contours in the left ROI (ROI1).
                    cListLeft   = find_contours(img_lab, rBlack,  ROI1) 
                    # Find black contours in the right ROI (ROI2).
                    cListRight  = find_contours(img_lab, rBlack,  ROI2)
                    
                    # Find orange contours in the center/lap ROI (ROI3).
                    cListOrange = find_contours(img_lab, rOrange, ROI3)
                    # Find blue contours in the center/lap ROI (ROI3).
                    cListBlue   = find_contours(img_lab, rBlue,   ROI3)

                      
                    # Get the area of the largest black contour on the left.
                    leftArea   = max_contour(cListLeft,  ROI1)[0]
                    # Get the area of the largest black contour on the right.
                    rightArea  = max_contour(cListRight, ROI2)[0]
                    # Get the area of the largest orange contour in the center.
                    orangeArea = max_contour(cListOrange, ROI3)[0]
                    # Get the area of the largest blue contour in the center.
                    blueArea   = max_contour(cListBlue,   ROI3)[0]

                    # Draw the left line contours on the preview.
                    draw_contours_in_roi(preview_img, cListLeft,  ROI1, (0,255,0))
                    # Draw the right line contours on the preview.
                    draw_contours_in_roi(preview_img, cListRight, ROI2, (0,255,0))
                    # Draw the orange contours on the preview.
                    draw_contours_in_roi(preview_img, cListOrange, ROI3, (0,140,255))
                    # Draw the blue contours on the preview.
                    draw_contours_in_roi(preview_img, cListBlue,   ROI3, (255,0,0))

                    # Display the left area value on the preview.
                    cv2.putText(preview_img, f"L:{leftArea}",  (ROI1[0], ROI1[1]-10), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0,255,0), 2)
                    # Display the right area value on the preview.
                    cv2.putText(preview_img, f"R:{rightArea}", (ROI2[0], ROI2[1]-10), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0,255,0), 2)
                    # Display the difference in area (for debugging).
                    cv2.putText(preview_img, f"Diff:{rightArea-leftArea}", (10,30), cv2.FONT_HERSHEY_SIMPLEX,0.7,(255,255,255),2)
                    
                    # If the lap line color hasn't been determined yet:
                    if not lap_color_locked:
                        # Check if a significant blue area is detected.
                        if blueArea > blueLineThreshold:
                            # Set the lap color to blue.
                            use_color_for_lap = "blue"
                            # Lock the lap color.
                            lap_color_locked = True
                            # Print a confirmation message.
                            print(f" Locked lap color: Blue Line (Blue)")
                        # Check if a significant orange area is detected (using the same threshold). (Comment translated)
                        elif orangeArea > blueLineThreshold: # Use the same threshold
                            # Set the lap color to orange.
                            use_color_for_lap = "orange"
                            # Lock the lap color.
                            lap_color_locked = True
                            # Print a confirmation message.
                            print(f" Locked lap color: Orange Line (Orange)")
                    
                    # If the lap color is blue:
                    if use_color_for_lap == "blue":
                        # Use the blue area for lap detection.
                        current_lap_area = blueArea
                    # If the lap color is orange:
                    elif use_color_for_lap == "orange":
                        # Use the orange area for lap detection.
                        current_lap_area = orangeArea
                    # Otherwise (if not locked yet):
                    else:
                        # Set current lap area to 0 (don't count). (Comment translated)
                        current_lap_area = 0 # Not locked yet, do not count laps

                    # Get the current time.
                    currentTime = time.time()
                    # Check if the detected lap line area exceeds the threshold.
                    if current_lap_area > blueLineThreshold:
                        # If it's a new detection and the cooldown has passed:
                        if not blueLineDetected and (currentTime - lastBlueDetectTime) > blueLineCooldown:
                            # Increment the lap counter 't'.
                            t += 1
                            # Set the flag to prevent re-counting.
                            blueLineDetected = True
                            # Reset the cooldown timer.
                            lastBlueDetectTime = currentTime
                            # Print a lap count update.
                            print(f" Detected {use_color_for_lap} line! Lap +1, current t={t}")
                    # If the lap line area is below the threshold:
                    else:
                        # Reset the detection flag.
                        blueLineDetected = False
                    
                    # Check conditions for a right turn (orange detected, not already turning, cooldown passed, right line is clear).
                    if orangeArea > 100 and turnDir=="none" and time.time() - time1 > 1.5 and rightArea < 1500:
                        # Set the turn direction state.
                        turnDir="right"
                        # Set the right turn flag.
                        rTurn = True
                        # Print "right".
                        print("right")
                    # Check conditions for a left turn (blue detected, not already turning, cooldown passed, left line is clear).
                    elif blueArea > 100 and turnDir=="none" and time.time() - time1 > 1.5 and leftArea < 1500:
                        # Set the turn direction state.
                        turnDir="left"
                        # Set the left turn flag.
                        lTurn = True
                        # Print "left".
                        print("left")
                         
                    # If in a left turn state:
                    if lTurn:
                        # Set a fixed hard left angle.
                        angle = -35
                        # Send the command.
                        send_motor(int(angle), speed)
                        # Set a large positive error offset (to steer right after the turn).
                        error = 3000
                        # Set the exit threshold (area of the *opposite* line).
                        exitThresh = 4000
                    # If in a right turn state:
                    if rTurn:
                        # Set a fixed hard right angle.
                        angle = 30
                        # Send the command.
                        send_motor(int(angle), speed)
                        # Set a large negative error offset (to steer left after the turn).
                        error = -8000
                        # Set the exit threshold (area of the *opposite* line).
                        exitThresh = 4000
                    # If not in a hard turn (i.e., normal lane following):
                    if not lTurn and not rTurn:
                        # Calculate the differential error (PD input).
                        aDiff = (leftArea - rightArea) - error
                        # Calculate the PD control output (angle).
                        angle = aDiff * kp + (aDiff - prevDiff) * kd
                        # Clamp the output angle.
                        angle = max(min(angle, 70), -70)
                        # Send the command.
                        send_motor(int(angle), speed)
                        
                    # Check for turn exit conditions (detecting the opposite line strongly).
                    if (rightArea > exitThresh and rTurn) or (leftArea > exitThresh and lTurn):
                        # Reset the turn direction state.
                        turnDir = "none"
                        # Reset the turn flags.
                        lTurn = rTurn = False
                        # Reset the error offset to 0.
                        error = 0
                        # Print a message.
                        print("Turn_end")
                        # Reset the turn cooldown timer.
                        time1 = time.time()
                    # Store the current error for the next derivative calculation.
                    prevDiff = aDiff
                    # Store the current angle (unused).
                    prevAngle = int(angle)
                    
                    # Check if 12 laps are completed.
                    if t >= 12:
                        # Print a status message. (Translated from Chinese, adapted to 2.5s)
                        print("Completed 12 laps, entering wall-following 2.5 sec mode")
                        # If this is the first time hitting 12 laps:
                        if count == 0:
                            # Start the wall-following timer.
                            start_time = time.time()
                            # Increment the counter to prevent re-starting the timer.
                            count = count + 1
                            
                    # Check if 2.5 seconds have passed since 12 laps were completed.
                    if time.time() - start_time > 2.5 and count != 0:
                        # Print a final message.
                        print(" Ending 2.5 second wall-following, stopping car")
                        # Send the stop command.
                        stop_car()
                        # Break out of the main 'while True' loop.
                        break
                        
                # Catch any unhandled exceptions in the processing logic.
                except Exception as e:
                    # Print the exception message.
                    print(f" An unhandled exception occurred in the tracking logic: {e}")
                    # Stop the car on error.
                    stop_car()
                    # Break out of the main loop.
                    break

            # Display the preview image in a window.
            cv2.imshow("finalColor", preview_img)
            # Check if the 'q' key was pressed.
            if cv2.waitKey(1) & 0xFF == ord('q'):
                # Stop the car.
                stop_car()
                # Break out of the main loop.
                break

    # This block will run no matter how the loop exits (break, error, etc.).
    finally:
        # Release the camera resource.
        cap.release()
        # Close all OpenCV windows.
        cv2.destroyAllWindows()
        # Check if the uart_hub was successfully initialized.
        if 'uart_hub' in locals() and uart_hub:
            # Stop the UART hub cleanly.
            uart_hub.stop()
        # Clean up GPIO resources.
        GPIO.cleanup()
        # Exit the script cleanly.
        sys.exit(0)