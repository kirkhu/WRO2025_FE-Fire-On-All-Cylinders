from machine import Pin, PWM, ADC, time_pulse_us, UART
import time, uos, ujson as json

UART_ID = 1      # Usually use UART 1 (or 0)
TX_PIN = 8       # Pico W GPIO Pin for TX (Connects to Jetson's RX)
RX_PIN = 9       # Pico W GPIO Pin for RX (Connects to Jetson's TX)
BAUD_RATE = 115200 # Recommend using a higher speed, please ensure Jetson's setting is consistent
DEBUG = True # Set to False if you want it to be quieter
MECH_SIGN      = +1 # Mechanical sign (for steering direction)
CENTER_TRIM_DEG  = 0 # Center trim in degrees
SERVO_MIN_US     = 1000 # Minimum pulse width in microseconds
SERVO_MAX_US     = 2000 # Maximum pulse width in microseconds
led = Pin("LED", Pin.OUT) # Onboard LED pin
A0PIN = 26  # Use ADC0, corresponding to GPIO26
A1PIN = 27  # Use ADC1, corresponding to GPIO27
A0 = ADC(Pin(A0PIN)) # Initialize ADC object for A0
A1 = ADC(Pin(A1PIN)) # Initialize ADC object for A1
TRIG_PIN1 = 2 # Trigger pin for ultrasonic sensor 1
ECHO_PIN1 = 3 # Echo pin for ultrasonic sensor 1
TRIG_PIN2 = 12 # Trigger pin for ultrasonic sensor 2
ECHO_PIN2 = 13 # Echo pin for ultrasonic sensor 2
trig1 = Pin(TRIG_PIN1, Pin.OUT) # Initialize trig1 as an output pin
echo1 = Pin(ECHO_PIN1, Pin.IN) # Initialize echo1 as an input pin
trig2 = Pin(TRIG_PIN2, Pin.OUT) # Initialize trig2 as an output pin
echo2 = Pin(ECHO_PIN2, Pin.IN) # Initialize echo2 as an input pin
servo_pin   = PWM(Pin(4), freq=50) # Initialize PWM for servo on GP4 at 50Hz
motor_in1   = Pin(21, Pin.OUT) # Motor driver input 1 on GP21
motor_in2   = Pin(20, Pin.OUT) # Motor driver input 2 on GP20
motor_pwm   = PWM(Pin(22), freq=1000) # Initialize PWM for motor speed on GP22 at 1000Hz
encoder_pin_A, encoder_pin_B = Pin(0, Pin.IN), Pin(1, Pin.IN) # Encoder pins A and B
encoder_count, last_state_A  = 0, encoder_pin_A.value() # Initialize encoder count and last state

RXBUF = ""           # Buffer for parsing JSON / M / STOP messages
LAST_COLOR = 0       # Stores any color received early in any state
magArea, magCX, magCY = 0, -1, -1 # Area, center X, and center Y of magenta object

UART_RECV_TIMEOUT = 0 

USE_ACTIVE_BRAKE = True # Flag to use active braking

def motor_brake():
    motor_in1.high() # Set motor direction pin 1 to HIGH
    motor_in2.high() # Set motor direction pin 2 to HIGH
    try:
        motor_pwm.duty_u16(65535) # Set PWM duty cycle to maximum for full brake
    except:
        pass # Ignore errors if PWM fails

def motor_coast():
    try:
        motor_pwm.duty_u16(0) # Set PWM duty cycle to zero
    except:
        pass # Ignore errors if PWM fails
    motor_in1.low() # Set motor direction pin 1 to LOW
    motor_in2.low() # Set motor direction pin 2 to LOW

def _clamp(v, lo, hi):
    return lo if v < lo else (hi if v > hi else v) # Clamps a value 'v' between 'lo' and 'hi'

def _map_servo_us(abs_deg_0_180):
    abs_deg_0_180 = _clamp(int(abs_deg_0_180), 0, 180) # Clamp angle between 0 and 180 degrees
    return SERVO_MIN_US + (SERVO_MAX_US - SERVO_MIN_US) * abs_deg_0_180 / 180.0 # Map angle to pulse width (us)

def set_servo_rel_deg(rel_deg):
    try:
        rel = int(rel_deg) # Convert relative angle to integer
    except:
        rel = 0 # Default to 0 if conversion fails
    rel = _clamp(rel, -180, 180) # Clamp relative angle
    abs_deg = 90 + CENTER_TRIM_DEG + MECH_SIGN * rel # Calculate absolute angle (0-180)
    abs_deg = _clamp(int(abs_deg), 0, 180) # Clamp absolute angle
    duty_us = _map_servo_us(abs_deg) # Map absolute angle to pulse width in us
    servo_pin.duty_u16(int(duty_us * 65535 / 20000)) # Set PWM duty cycle (u16 based on 20ms period)

def set_servo_angle(angle_in):
    set_servo_rel_deg(angle_in) # Public function to set servo angle

def control_motor(speed):
    try:
        sp = int(speed) # Convert speed to integer
    except:
        sp = 0 # Default to 0 if conversion fails
    sp = _clamp(sp, -100, 100) # Clamp speed between -100 (reverse) and 100 (forward)

    if sp == 0:
        if USE_ACTIVE_BRAKE:
            motor_brake() # Apply active brake
        else:
            motor_coast() # Coast the motor
        return # Exit the function if speed is 0

    try:
        motor_pwm.duty_u16(0) # Temporarily set PWM to 0 before changing direction
    except:
        pass # Ignore errors

    if sp > 0:
        motor_in1.high(); motor_in2.low() # Set direction for forward
    else:
        motor_in1.low(); motor_in2.high() # Set direction for reverse

    try:
        motor_pwm.duty_u16(int(abs(sp) * 65535 / 100)) # Set PWM duty cycle based on absolute speed
    except:
        pass # Ignore errors

def encoder_interrupt(pin):
    global encoder_count, last_state_A # Access global variables
    state_a = encoder_pin_A.value() # Read current state of pin A
    if state_a != last_state_A: # Check if pin A state has changed (rising or falling edge)
        state_b = encoder_pin_B.value() # Read current state of pin B
        encoder_count += 1 if state_a == state_b else -1 # Increment/decrement count based on direction
        last_state_A = state_a # Update last state of pin A

encoder_pin_A.irq(trigger=Pin.IRQ_RISING | Pin.IRQ_FALLING, handler=encoder_interrupt) # Attach interrupt handler to pin A

def run_encoder_Auto(motor_angle, speed, steer_deg):
    global encoder_count # Access global encoder count
    encoder_count = 0 # Reset encoder count
    set_servo_angle(steer_deg) # Set the steering angle
    while abs(encoder_count) < motor_angle: # Loop until target encoder count is reached
        control_motor(speed) # Control the motor speed
        time.sleep(0.01) # Small delay for control loop
    control_motor(0) # Stop the motor
    set_servo_angle(0) # Reset servo angle to center

def measure_distance(trig, echo):
    trig.value(0); time.sleep_us(2) # Set trigger low for 2us
    trig.value(1); time.sleep_us(10); trig.value(0) # Send 10us pulse
    duration = time_pulse_us(echo, 1) # Measure the pulse width on the echo pin
    if duration <= 0:
        return 9999 # Return a large value if measurement fails
    distance = (duration / 2) * 0.0343 # Calculate distance in cm (speed of sound: 0.0343 cm/us)
    return distance # Return the measured distance

def connect_uart():
    """Initialize and connect UART"""
    try:
        uart = UART(UART_ID, baudrate=BAUD_RATE, tx=Pin(TX_PIN), rx=Pin(RX_PIN), timeout=0)
        if DEBUG:
            print(f"UART {UART_ID} Initialized (TX:GP{TX_PIN}, RX:GP{RX_PIN}, Baud:{BAUD_RATE})") # Debug print: UART setup success
        return uart # Return the UART object
    except Exception as e:
        print(f"UART connect failed: {e}") # Print error if UART initialization fails
        raise OSError("UART Init failed") # Raise OSError to indicate failure
        
def uart_send(uart_obj, text):
    """Send text over UART"""
    try:
        uart_obj.write(text.encode('utf-8')) # Encode text to bytes and write to UART
    except Exception as e:
        if DEBUG:
            print(f"UART send error: {e}") # Debug print: UART send error

def uart_recv_chunk(uart_obj, timeout=UART_RECV_TIMEOUT):
    """Non-blocking read of data chunk from UART"""
    try:
        if uart_obj.any(): # Check if any data is available
            received = uart_obj.read() # Read all available bytes
            if received:
                if DEBUG:
                    print(f"[Pico W] Received raw bytes: {received}") # ★ Debug: Show raw received data
                return received.decode('utf-8') # Decode to string and return
    except Exception as e:
        if DEBUG:
            print(f"UART read error: {e}") # Debug print: UART read error
    return None # Return None if no data or error

def parse_json_msg(s):
    try:
        obj = json.loads(s) # Attempt to parse JSON string
        return obj if isinstance(obj, dict) else None # Return dictionary if successful, else None
    except Exception:
        return None # Return None on parsing error

def parse_m_line(s):
    if not s.startswith("M,"): # Check for "M," prefix
        return None # Not an M command
    parts = s.strip().split(",") # Split the line by comma
    if len(parts) >= 2: # Must have at least two parts
        try:
            val1 = int(parts[1]) # First value (signal or angle)
            val2 = int(parts[2]) if len(parts) >= 3 else 0 # Second value (speed, default to 0)
            
            # Assume val1 is angle/signal, val2 is speed
            if len(parts) == 2: # M,<signal>
                 # If it's a start/color signal (1~6), speed is 0
                 if 1 <= val1 <= 6:
                     return _clamp(val1, 1, 6), 0 # Return (signal, 0)
                 # If not a signal, treat as M,<angle>,0
                 return _clamp(val1, -180, 180), 0
                 
            # M,<angle>,<speed>
            return _clamp(val1, -180, 180), _clamp(val2, -100, 100) # Return (angle, speed)
            
        except Exception as e:
            if DEBUG: print(f"M parse error: {e}, raw: {s}") # Debug print: M parsing error
            return None # Return None on parsing error
    return None # Return None if not enough parts


def extract_magenta_from_json(obj):
    global magArea, magCX, magCY # Access global magenta data
    if not obj:
        return # Exit if object is None
    try:
        if "magArea" in obj: magArea = int(obj["magArea"]) # Update magenta area
        if "magCX"   in obj: magCX   = int(obj["magCX"]) # Update magenta center X
        if "magCY"   in obj: magCY   = int(obj["magCY"]) # Update magenta center Y
    except:
        pass # Ignore errors during type conversion

def pump_uart(uart_obj):
    """
    Non-blocking read from UART, parsing JSON / M / STOP commands.
    Returns (json_obj, m_tuple, got_stop)
    """
    global RXBUF # Access global receive buffer
    json_obj = None # Initialize parsed JSON object
    m_tuple = None # Initialize parsed M command tuple
    got_stop = False # Initialize STOP flag

    msg = uart_recv_chunk(uart_obj, timeout=UART_RECV_TIMEOUT) # Get raw data chunk
    if msg:
        RXBUF += msg # Append to global buffer
        
    if len(RXBUF) > 4096:
        RXBUF = RXBUF[-1024:] # Truncate buffer to prevent overflow

    idx_stop = RXBUF.find("STOP") # Find "STOP" in buffer
    if idx_stop != -1:
        end = idx_stop + 4 # End of "STOP"
        if end < len(RXBUF) and RXBUF[end:end+1] == "\n": # Check for newline after STOP
            end += 1 # Include newline if present
        RXBUF = RXBUF[:idx_stop] + RXBUF[end:] # Remove "STOP" and any following newline from buffer
        got_stop = True # Set stop flag
        if DEBUG:
            print("[PICO] GOT STOP SIGNAL") # Debug print: STOP received
            
    for _ in range(12): # Limit parsing iterations per call
        if not RXBUF:
            break # Break if buffer is empty

        idx_json = RXBUF.find("{") # Find start of JSON
        idx_m    = RXBUF.find("M,") # Find start of M command

        if idx_json == -1 and idx_m == -1:
            if RXBUF.strip() and not (RXBUF.startswith("M,") or RXBUF.startswith("{")):
                if DEBUG: print(f"[PICO] Cleared junk: {RXBUF.strip()[:10]}...") # Debug print: cleared junk
                RXBUF = "" # Clear junk data
            break # No command starters found

        if idx_json != -1 and (idx_m == -1 or idx_json < idx_m):
            # Process JSON (Telemetry data from Jetson, including magenta info)
            end = RXBUF.find("}", idx_json) # Find end of JSON
            if end == -1:
                break # JSON incomplete, break and wait for more data
            candidate = RXBUF[idx_json:end+1] # Extract the JSON candidate string
            next_idx = end + 1 # Index after '}'
            if next_idx < len(RXBUF) and RXBUF[next_idx] == "\n":
                next_idx += 1 # Skip newline if present
            RXBUF = RXBUF[next_idx:] # Update buffer
            
            obj = parse_json_msg(candidate) # Parse the JSON message
            
            if obj:
                json_obj = obj # Store the parsed object
                if DEBUG: print("PARSED_JSON:", obj) # Debug print: parsed JSON
                extract_magenta_from_json(obj) # Extract magenta data
                continue # Continue to check for next command
            else:
                continue # JSON parsing failed, continue to check next part of buffer
        else:
            # Process M command (Control command or signal from Jetson)
            nl = RXBUF.find("\n", idx_m) # Find newline after M command
            if nl == -1:
                # If M command has no newline, process the part starting with M and truncate
                # This handles cases where 'M,angle,speed\n' is received as 'M,angle,speed'
                candidate = RXBUF[idx_m:].strip() # Get remaining part
                RXBUF = RXBUF[:idx_m] # Clear M part (will likely be re-appended if partial)
            else:
                candidate = RXBUF[idx_m:nl].strip() # Extract the M command line
                RXBUF = RXBUF[nl+1:] # Update buffer by skipping the M command and newline

            parsed = parse_m_line(candidate) # Parse the M command
            if parsed:
                m_tuple = parsed # Store the parsed M tuple
                if DEBUG: print("PARSED_M:", m_tuple, "RAW=", candidate) # Debug print: parsed M
                
                # ★ Execute control command
                # The first value in M format can be a signal or an angle
                if len(m_tuple) == 2:
                    val1, speed = m_tuple # Unpack tuple
                    if 1 <= val1 <= 6:
                        # This is a signal (color or start signal)
                        pass # Signal processing is usually handled outside
                    else:
                        # This is a control command (angle, speed)
                        set_servo_angle(val1) # Set servo angle
                        control_motor(speed) # Control motor speed
                
                continue # Continue to check for next command
            else:
                continue # M parsing failed, continue to check next part of buffer

    return json_obj, m_tuple, got_stop # Return results

# =============== Main ===============
def run():
    global LAST_COLOR, encoder_count, mag_area, mag_cx, mag_cy # Access global variables
    motor_in1.off() # Ensure motor direction pin 1 is off
    motor_in2.off() # Ensure motor direction pin 2 is off
    control_motor(0) # Stop motor
    set_servo_angle(0) # Center servo
    led.off() # Turn off LED
    
    # Initialize UART
    try:
        uart_port = connect_uart() # Connect to UART
    except OSError:
        # If UART fails during initial connect, don't enter the main loop immediately
        time.sleep(1)
        return

    while True:
        try:
            print("UART Port Ready. Waiting for commands...") # Status message
            s = uart_port # Alias for UART object
            
            print("Pico W initialized.") # Status message
            
            # Send Pico Ready message to Jetson
            uart_send(s, json.dumps({"from":"pico","status":"ready"}) + "\n") # Send ready signal as JSON
            print("[Pico W] Sent ready signal to Jetson.") # Confirmation message
            
            led.on() # Turn on LED to indicate ready state

            mode = 0 # Current mode of operation
            turn = 0 # Starting direction (turn)
            color = 0 # Detected color signal
            count = 0 # General counter
            yaw = 0 # Yaw angle from Jetson (e.g., IMU)
            angle_from_jetson = 0 # Steering angle from Jetson (if M command not used)
            speed_from_jetson = 0 # Speed from Jetson (if M command not used)
            leftArea = 0 # Left area value (e.g., from sensor)
            rightArea = 0 # Right area value (e.g., from sensor)
            LAST_COLOR = 0 # Reset last received color
            aDiff = 0 # Area difference
            deg = 0 # Angle variable
            prevDiff = 0 # Previous difference for PID
            error = 0 # Current error for PID
            error1 = 0 # Previous error for PID
            Servo_angle = 0 # Calculated servo angle
            
            # --- mode 0: Get Starting Direction ---
            print("Entering mode=0 (Get Starting Direction), waiting for Jetson's M,<turn>,* ...") # Status message
            while mode == 0 and turn == 0: # Loop until turn direction is set
                json_obj, m_tuple, got_stop = pump_uart(s) # Pump UART for data
                
                if got_stop:
                    control_motor(0) # Stop motor
                    set_servo_angle(0) # Center servo
                    print("[HALT] STOP received (mode0)") # Halt message
                    return # Exit run() function

                if json_obj:
                    # Only update telemetry data here
                    try:
                        if "color" in json_obj:
                            LAST_COLOR = int(json_obj["color"]) # Update last color
                            if DEBUG: print("[LATCH] JSON color ->", LAST_COLOR) # Debug print
                        elif "c" in json_obj:
                            LAST_COLOR = int(json_obj["c"]) # Update last color (short key)
                            if DEBUG: print("[LATCH] JSON c ->", LAST_COLOR) # Debug print
                        extract_magenta_from_json(json_obj) # Update magenta data
                    except:
                        pass # Ignore errors
                    try:
                        if "yaw" in json_obj:
                            yaw = float(json_obj.get("yaw", yaw)) # Update yaw
                        if "angle" in json_obj:
                            angle_from_jetson = int(json_obj.get("angle", angle_from_jetson)) # Update angle
                        if "speed" in json_obj:
                            speed_from_jetson = int(json_obj.get("speed", speed_from_jetson)) # Update speed
                        if "leftArea" in json_obj:
                            leftArea = int(json_obj.get("leftArea", leftArea)) # Update left area
                        if "rightArea" in json_obj:
                            rightArea = int(json_obj.get("rightArea", rightArea)) # Update right area
                    except:
                        pass # Ignore errors

                if m_tuple:
                    candidate = m_tuple[0] # First value of M command
                    # Starting signal is 1 or 2
                    if candidate in (1, 2):
                        turn = candidate # Set turn direction
                        print("Set turn =", turn) # Confirmation message
                    else:
                        if DEBUG: print("[SKIP] M in mode0 (not turn):", m_tuple) # Debug print: skip M

                if json_obj is None and m_tuple is None:
                    time.sleep(0.01) # Sleep if no new data

            # --- Execute rotation based on turn ---
            if turn == 1:
                print("Turning right") # Right turn message
                run_encoder_Auto(500, 45, 180) # Move with encoder and turn
            else:
                print("Turning left") # Left turn message
                run_encoder_Auto(1550, 45, -200) # Move with encoder and turn

            # --- mode 1: Color Decision ---
            mode = 1 # Change mode
            LAST_COLOR = 0 # Reset last color
            color = 0 # Reset color
            print(mode, color) # Debug print
            print('Waiting for color (M,<1..6>[,<...>] or JSON {"color":n})...') # Status message

            while mode == 1 and color == 0: # Loop until color is detected
                json_obj, m_tuple, got_stop = pump_uart(s) # Pump UART for data

                if json_obj:
                    v = None # Value variable
                    try:
                        if "color" in json_obj:
                            v = int(json_obj["color"]) # Get color from JSON
                        elif "c" in json_obj:
                            v = int(json_obj["c"]) # Get color from JSON (short key)
                    except:
                        v = None # Set to None on error
                    if v is not None:
                        if 1 <= v <= 6:
                            color = v # Set color
                            LAST_COLOR = color # Update last color
                            print("[JSON] color =", color) # Confirmation message
                            break # Break the loop
                        else:
                            if DEBUG: print("[IGNORE] JSON color out of range:", v) # Debug print: ignore out of range
                    extract_magenta_from_json(json_obj) # Update magenta data

                if m_tuple:
                    first = m_tuple[0] # First value of M command
                    if 1 <= first <= 6:
                        color = first # Set color
                        LAST_COLOR = color # Update last color
                        print("[M] color =", color, "raw:", m_tuple) # Confirmation message
                        break # Break the loop
                    else:
                        if DEBUG: print("[IGNORE] M packet in mode1 (not color):", m_tuple) # Debug print: ignore M packet

                if json_obj is None and m_tuple is None:
                    time.sleep(0.002) # Short sleep if no new data
            
            # --- Color-based actions (Skipped for brevity, same as original) ---
            if color == 1:
                print("Color=1") # Status message
                run_encoder_Auto(1900, 70, 0) # Encoder move
                run_encoder_Auto(1500, 70, 180) # Encoder move
                run_encoder_Auto(1200, -45, 0) # Encoder move
            elif color == 2:
                print("Color=2") # Status message
                run_encoder_Auto(1700, 70, 0) # Encoder move
                run_encoder_Auto(1150, -50, -180) # Encoder move
            elif color == 3:
                print("Color=3") # Status message
                run_encoder_Auto(1700, 70, 0) # Encoder move
                run_encoder_Auto(1150, -50, -180) # Encoder move
            elif color == 4:
                print("Color=4") # Status message
                run_encoder_Auto(600, 40, 180) # Encoder move
                run_encoder_Auto(400, 50, 0) # Encoder move
                run_encoder_Auto(1100, 40, -180) # Encoder move
                run_encoder_Auto(800, 50, 0) # Encoder move
            elif color == 5:
                print("Color=5") # Status message
                run_encoder_Auto(600, 40, 180) # Encoder move
                run_encoder_Auto(2200, 60, 0) # Encoder move
                run_encoder_Auto(1400, 40, -180) # Encoder move
                run_encoder_Auto(500, 50, 0) # Encoder move
            elif color == 6:
                print("Color=6") # Status message
                run_encoder_Auto(600, 40, 180) # Encoder move
                run_encoder_Auto(400, 50, 0) # Encoder move
                run_encoder_Auto(1400, 40, -180) # Encoder move
                run_encoder_Auto(800, 50, 0) # Encoder move

            control_motor(0) # Stop motor
            set_servo_angle(0) # Center servo

            # --- mode 2: General Control (Synchronous magenta info reception) ---
            # Control commands are executed inside pump_uart, only update telemetry and check STOP here
            mode = 2 # Change mode
            print("Entering mode=2 (General Control), waiting for M,<rel>,<spd> ...") # Status message
            while mode == 2: # Loop for general control
                json_obj, m_tuple, got_stop = pump_uart(s) # Pump UART for data
                
                if got_stop:
                    control_motor(0) # Stop motor
                    set_servo_angle(0) # Center servo
                    print("[HALT] STOP received (mode2)") # Halt message
                    mode = 3 # Jump out of mode 2
                    continue # Continue to check outer loop condition
                
                # M format control command is executed inside pump_uart
                
                if json_obj:
                    extract_magenta_from_json(json_obj) # Update magenta data 
                    # Update telemetry data (if needed for subsequent modes)
                    try:
                        if "yaw" in json_obj:
                            yaw = float(json_obj.get("yaw", yaw)) # Update yaw
                        if "leftArea" in json_obj:
                            leftArea = int(json_obj.get("leftArea", leftArea)) # Update left area
                        if "rightArea" in json_obj:
                            rightArea = int(json_obj.get("rightArea", rightArea)) # Update right area
                    except:
                        pass # Ignore errors


                if json_obj is None and m_tuple is None:
                    time.sleep(0.001) # Very short sleep for fast loop
            
            # --- mode 3 ~ 10 (Rest of the logic, with pump_ws replaced by pump_uart) ---
            
            # --- mode 3 Example ---
            while mode == 3:
                json_obj, _, got_stop = pump_uart(s) # Pump UART for data
                extract_magenta_from_json(json_obj) # Update magenta data
                while abs(yaw) < 85: # Loop while yaw is less than 85 degrees
                    json_obj, _, got_stop = pump_uart(s) # Pump UART for data
                    if json_obj:
                        if "yaw" in json_obj:
                            try:
                                yaw = float(json_obj["yaw"]) # Update yaw
                            except:
                                pass
                        extract_magenta_from_json(json_obj) # Update magenta data
                    if turn == 2: # Turn 2 (e.g., Left start)
                        set_servo_angle(45) # Set servo angle
                        control_motor(35) # Set motor speed
                    else: # Turn 1 (e.g., Right start)
                        set_servo_angle(-40) # Set servo angle
                        control_motor(35) # Set motor speed                 
                motor_brake() # Stop motor
                set_servo_angle(0) # Center servo
                mode = 4 # Change mode
                
            
            while mode == 4:
                a0_value = A0.read_u16() # Read ADC A0 value
                time_a0=time.time() # Record start time
                while a0_value > 64800 and time.time()- time_a0 < 5: # Loop while A0 value is high and time limit not reached
                    a0_value = A0.read_u16() # Read ADC A0 value
                    extract_magenta_from_json(json_obj) # Update magenta data 
                    json_obj, _, got_stop = pump_uart(s) # Pump UART for data
                    if json_obj:
                        if "yaw" in json_obj:
                            try:
                                yaw = float(json_obj["yaw"]) # Update yaw
                            except:
                                pass
                        extract_magenta_from_json(json_obj) # Update magenta data  
                    set_servo_angle(0) # Center servo
                    control_motor(30) # Drive motor forward
                control_motor(-40) # Drive motor backward
                time.sleep(0.1) # Wait for a short time
                control_motor(0) # Stop motor
                mode = 5 # Change mode

            while mode == 5:
                json_obj, _, got_stop = pump_uart(s) # Pump UART for data
                while abs(yaw) < 177: # Loop while yaw is less than 177 degrees
                    extract_magenta_from_json(json_obj) # Update magenta data
                    json_obj, _, got_stop = pump_uart(s) # Pump UART for data
                    if json_obj:
                        if "yaw" in json_obj:
                            try:
                                yaw = float(json_obj["yaw"]) # Update yaw
                            except:
                                pass
                    if turn == 2: # Turn 2
                        set_servo_angle(-180) # Set servo angle
                        control_motor(-40) # Drive motor backward
                    else: # Turn 1
                        set_servo_angle(180) # Set servo angle
                        control_motor(-40) # Drive motor backward                  
                motor_brake() # Stop motor
                set_servo_angle(0) # Center servo
                mode = 6 # Change mode
                
            while mode == 6:
                json_obj, m_tuple, got_stop = pump_uart(s) # Pump UART for data
                extract_magenta_from_json(json_obj) # Update magenta data
                while magArea > 70: # Loop while magenta area is greater than 70
                    extract_magenta_from_json(json_obj) # Update magenta data
                    json_obj, m_tuple, got_stop = pump_uart(s) # Pump UART for data
                    if json_obj:
                        try:
                            if "leftArea" in json_obj:
                                leftArea = int(json_obj.get("leftArea", leftArea)) # Update left area
                            if "rightArea" in json_obj:
                                rightArea = int(json_obj.get("rightArea", rightArea)) # Update right area
                        except:
                            pass
                    if turn ==2: # Turn 2
                        if magArea > 3000:
                            error = magCX - 202 # Calculate error based on CX
                            Servo_angle = int(error*0.15 + (error - error1)*0.2) # PD control
                            error1 = error # Update previous error
                            set_servo_angle(Servo_angle) # Set servo angle
                            control_motor(40) # Drive motor forward
                        else:
                            error = leftArea - 6500 # Calculate error based on left area
                            Servo_angle = int(error*0.005 + (error - error1)*0.01) # PD control
                            error1 = error # Update previous error
                            set_servo_angle(Servo_angle) # Set servo angle
                            control_motor(40) # Drive motor forward
                    else: # Turn 1
                        if magArea > 3000:
                            error = magCX - 490 # Calculate error based on CX
                            Servo_angle = int(error*0.13 + (error - error1)*0.2) # PD control
                            error1 = error # Update previous error
                            set_servo_angle(Servo_angle) # Set servo angle
                            control_motor(40) # Drive motor forward
                        else:
                            error = 7000 - rightArea # Calculate error based on right area
                            Servo_angle = int(error*0.005 + (error - error1)*0.008) # PD control
                            error1 = error # Update previous error
                            set_servo_angle(Servo_angle) # Set servo angle
                            control_motor(40) # Drive motor forward
                control_motor(-50) # Drive motor backward
                time.sleep(0.1) # Wait for a short time
                control_motor(0) # Stop motor
                time.sleep(0.5) # Wait for a short time
                mode = 7 # Change mode

            while mode == 7:
                json_obj, _, got_stop = pump_uart(s) # Pump UART for data
                while abs(yaw) > 110: # Loop while yaw is greater than 110 degrees
                    json_obj, _, got_stop = pump_uart(s) # Pump UART for data
                    if json_obj:
                        if "yaw" in json_obj:
                            try:
                                yaw = float(json_obj["yaw"]) # Update yaw
                            except:
                                pass
                    if turn == 2: # Turn 2  
                        set_servo_angle(-180) # Set servo angle
                        control_motor(-38) # Drive motor backward
                    else: # Turn 1
                        set_servo_angle(180) # Set servo angle
                        control_motor(-38) # Drive motor backward
                control_motor(50) # Drive motor backward
                time.sleep(0.1) # Wait for a short time
                control_motor(0) # Stop motor
                mode =8 # Change mode 
            while mode == 8:
                json_obj, _, got_stop = pump_uart(s) # Pump UART for data
                a1_value = A1.read_u16() # Read ADC A1 value
                while abs(yaw) < 140 and a1_value > 64800: # Loop while yaw < 140 and A1 is high
                    a1_value = A1.read_u16() # Read ADC A1 value
                    json_obj, _, got_stop = pump_uart(s) # Pump UART for data
                    if json_obj:
                        if "yaw" in json_obj:
                            try:
                                yaw = float(json_obj["yaw"]) # Update yaw
                            except:
                                pass
                    if turn == 2: # Turn 2  
                        set_servo_angle(180) # Set servo angle
                        control_motor(-35) # Drive motor backward
                    else: # Turn 1
                        set_servo_angle(-180) # Set servo angle
                        control_motor(-35) # Drive motor backward  
                control_motor(40) # Drive motor forward
                time.sleep(0.1) # Wait for a short time
                control_motor(0) # Stop motor
                set_servo_angle(0) # Center servo
                mode =9 # Change mode
            while mode == 9:
                json_obj, _, got_stop = pump_uart(s) # Pump UART for data
                a0_value = A0.read_u16() # Read ADC A0 value
                while abs(yaw) < 160 : # Loop while yaw is less than 160 degrees
                    a0_value = A0.read_u16() # Read ADC A0 value
                    json_obj, _, got_stop = pump_uart(s) # Pump UART for data
                    if json_obj:
                        if "yaw" in json_obj:
                            try:
                                yaw = float(json_obj["yaw"]) # Update yaw
                            except:
                                pass
                    if turn == 2: # Turn 2  
                        set_servo_angle(-180) # Set servo angle
                        control_motor(35) # Drive motor forward
                    else: # Turn 1
                        set_servo_angle(180) # Set servo angle
                        control_motor(35) # Drive motor forward  
                control_motor(-40) # Drive motor backward
                time.sleep(0.1) # Wait for a short time
                control_motor(0) # Stop motor
                set_servo_angle(0) # Center servo
                mode =10 # Change mode 
            while mode == 10:
                json_obj, _, got_stop = pump_uart(s) # Pump UART for data
                a0_value = A0.read_u16() # Read ADC A0 value
                while abs(yaw) < 177 : # Loop while yaw is less than 177 degrees
                    a0_value = A0.read_u16() # Read ADC A0 value
                    json_obj, _, got_stop = pump_uart(s) # Pump UART for data
                    if json_obj:
                        if "yaw" in json_obj:
                            try:
                                yaw = float(json_obj["yaw"]) # Update yaw
                            except:
                                pass
                    if turn == 2: # Turn 2  
                        set_servo_angle(180) # Set servo angle
                        control_motor(-35) # Drive motor backward
                    else: # Turn 1
                        set_servo_angle(-180) # Set servo angle
                        control_motor(-35) # Drive motor backward  
                control_motor(40) # Drive motor backward
                time.sleep(0.1) # Wait for a short time
                control_motor(0) # Stop motor
                set_servo_angle(0) # Center servo
                mode =11 # Change mode
            while mode == 11:
                motor_brake() # Apply motor brake
                
        except OSError as e: # Catch UART Init failed
            print("UART error/initialization failed:", e) # Print error
            print("Retrying UART initialization in 3s...") # Status message
            time.sleep(3) # Wait before retrying
        except Exception as e:
            print("Unexpected error:", e) # Print unexpected error
            print("Re-initializing UART in 3s...") # Status message
            time.sleep(3) # Wait before re-initializing

try:
    run() # Start the main program loop
except KeyboardInterrupt:
    control_motor(0) # Stop motor on interruption
    set_servo_angle(0) # Center servo on interruption
    print("Program terminated by user") # Termination message

