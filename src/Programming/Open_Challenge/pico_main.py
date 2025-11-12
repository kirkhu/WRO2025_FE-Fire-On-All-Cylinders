from machine import Pin, PWM # Import Pin and PWM classes from machine module
import time # Import time module
import uos # Import uos module
import ujson as json # Import ujson module as json
from machine import UART # Import UART class from machine module

UART_ID = 1      # Usually use UART 1 (or 0)
TX_PIN = 8       # Pico W GPIO Pin for TX (Connects to Jetson's RX)
RX_PIN = 9       # Pico W GPIO Pin for RX (Connects to Jetson's TX)
BAUD_RATE = 115200 # Set the baud rate
DEBUG = True # Enable debug output

RXBUF = ""           # Global RX buffer
UART_RECV_TIMEOUT = 0 # Non-blocking read timeout (0)
USE_ACTIVE_BRAKE = True # Assume active braking is used (Consistent with 2.py)

servo_pin = PWM(Pin(4), freq=50) # Initialize PWM for servo on GP4 at 50Hz
motor_in1 = Pin(21, Pin.OUT) # Motor driver input 1 on GP21
motor_in2 = Pin(20, Pin.OUT) # Motor driver input 2 on GP20
motor_pwm = PWM(Pin(22), freq=1000) # Initialize PWM for motor speed on GP22 at 1000Hz
encoder_pin_A = Pin(0, Pin.IN) # Encoder pin A on GP0
encoder_pin_B = Pin(1, Pin.IN) # Encoder pin B on GP1
button = Pin(18, Pin.IN, Pin.PULL_UP) # Button pin on GP18 with pull-up

encoder_count = 0 # Initialize encoder count
last_state_A = encoder_pin_A.value() # Get initial state of encoder pin A
_prev_speed_abs = 0  # Previous actual output absolute speed (%)
led = Pin("LED", Pin.OUT) # Onboard LED pin


def _clamp(v, lo, hi):
    return lo if v < lo else (hi if v > hi else v) # Clamps a value 'v' between 'lo' and 'hi'


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

def set_servo_angle(angle_rel_deg):
    """Converts a relative angle from -180 to 180 to an absolute pulse for the servo"""

    rel = _clamp(int(angle_rel_deg), -180, 180) # Clamp relative angle
    
    # Use Pico W's pulse range of 1000us ~ 2000us
    SERVO_MIN_US     = 1000 # Minimum pulse width in microseconds
    SERVO_MAX_US     = 2000 # Maximum pulse width in microseconds
    CENTER_TRIM_DEG  = 0 # Center trim in degrees
    MECH_SIGN        = +1 # Assume positive mechanical sign
    
    abs_deg = 90 + CENTER_TRIM_DEG + MECH_SIGN * rel # Calculate absolute angle (0-180)
    abs_deg = _clamp(int(abs_deg), 0, 180) # Clamp absolute angle
    
    duty_us = SERVO_MIN_US + (SERVO_MAX_US - SERVO_MIN_US) * abs_deg / 180.0 # Map angle to pulse width (us)
    servo_pin.duty_u16(int(duty_us * 65535 / 20000)) # Set PWM duty cycle (u16 based on 20ms period)

def control_motor(speed):
    """speed: -100 ~ 100 (Retains pico.py's startup pulse and minimum speed logic)"""
    global _prev_speed_abs # Access global previous absolute speed
    sp = _clamp(int(speed), -100, 100) # Clamp input speed
    abs_speed = abs(sp) # Calculate absolute speed

    if sp == 0:
        if USE_ACTIVE_BRAKE:
            motor_brake() # Apply active brake
        else:
            motor_coast() # Coast the motor
        _prev_speed_abs = 0 # Reset previous absolute speed
        return # Exit function
    if abs_speed > 0 and abs_speed < 20: # If speed is low but non-zero
        abs_speed = 20 # Set minimum speed to 20%
    if _prev_speed_abs == 0 and abs_speed > 0: # If motor is starting up
        motor_pwm.duty_u16(int(65535 * 0.6))  # Apply momentary startup pulse (60% duty)
        time.sleep(0.02) # Short delay for pulse effect
    _prev_speed_abs = abs_speed # Update previous absolute speed

    if sp > 0:
        motor_in1.high() # Set direction for forward
        motor_in2.low()
    elif sp < 0:
        motor_in1.low() # Set direction for reverse
        motor_in2.high()
    
    motor_pwm.duty_u16(int(abs_speed * 65535 / 100)) # Set PWM duty cycle based on speed


def encoder_interrupt(pin):
    global encoder_count, last_state_A # Access global variables
    state_a = encoder_pin_A.value() # Read current state of pin A
    if state_a != last_state_A: # Check for change in state A
        state_b = encoder_pin_B.value() # Read current state of pin B
        encoder_count += 1 if state_a == state_b else -1 # Increment/decrement count based on direction
        last_state_A = state_a # Update last state A

encoder_pin_A.irq(trigger=Pin.IRQ_RISING | Pin.IRQ_FALLING, handler=encoder_interrupt) # Attach interrupt handler

def connect_uart():
    """Initialize and connect UART"""
    try:
        # Set up UART, note that timeout is set to 0 for non-blocking read
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
                    print(f"[Pico W] Received raw bytes: {received}") # Debug print: Show raw received data
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
    # M,<signal>[,<speed>] or M,<angle>,<speed>
    if len(parts) >= 2: # Must have at least two parts
        try:
            val1 = int(parts[1]) # First value (angle)
            val2 = int(parts[2]) if len(parts) >= 3 else 0 # Second value (speed, default to 0)
            
            # Here we only process M,<angle>,<speed> control commands, ignoring other signals
            return _clamp(val1, -180, 180), _clamp(val2, -100, 100) # Return (angle, speed)
            
        except Exception as e:
            if DEBUG: print(f"M parse error: {e}, raw: {s}") # Debug print: M parsing error
            return None # Return None on parsing error
    return None # Return None if not enough parts

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
        RXBUF = RXBUF[:idx_stop] + RXBUF[end:] # Remove "STOP" and following newline
        got_stop = True # Set stop flag
        if DEBUG:
            print("[PICO] GOT STOP SIGNAL") # Debug print: STOP received

    for _ in range(12): # Limit parsing iterations per call
        if not RXBUF:
            break # Break if buffer is empty

        idx_json = RXBUF.find("{") # Find start of JSON
        idx_m    = RXBUF.find("M,") # Find start of M command

        # Prioritize M command (This is the control command)
        if idx_m != -1 and (idx_json == -1 or idx_m < idx_json):
            nl = RXBUF.find("\n", idx_m) # Find newline after M command
            if nl == -1:
                break # M command incomplete, break and wait for more data
            
            candidate = RXBUF[idx_m:nl].strip() # Extract the M command line
            RXBUF = RXBUF[nl+1:] # Update buffer by skipping M command and newline

            parsed = parse_m_line(candidate) # Parse the M command
            if parsed:
                m_tuple = parsed # Store the parsed M tuple
                if DEBUG: print("PARSED_M:", m_tuple, "RAW=", candidate) # Debug print: parsed M
                
                if len(m_tuple) == 2:
                    angle, speed = m_tuple # Unpack tuple
                    set_servo_angle(angle) # Set servo angle
                    control_motor(speed) # Control motor speed
                
                continue # Continue to check for next command
            else:
                continue # M parsing failed, continue to check next part of buffer
        elif idx_json != -1:
            end = RXBUF.find("}", idx_json) # Find end of JSON
            if end == -1:
                break # JSON incomplete, break and wait for more data
            candidate = RXBUF[idx_json:end+1] # Extract the JSON candidate string
            next_idx = end + 1 # Index after '}'
            if next_idx < len(RXBUF) and RXBUF[next_idx] == "\n": # Skip newline if present
                next_idx += 1
            RXBUF = RXBUF[next_idx:] # Update buffer
            
            obj = parse_json_msg(candidate) # Parse the JSON message
            if obj:
                json_obj = obj # Store the parsed object
                if DEBUG: print("PARSED_JSON:", obj) # Debug print: parsed JSON
    
                continue # Continue to check for next command
            else:
                continue # JSON parsing failed, continue to check next part of buffer
        break # Break if neither M nor JSON start found
    
    return json_obj, m_tuple, got_stop # Return results

# ===================== Main =====================
try:
    motor_in1.off() # Ensure motor inputs are off
    motor_in2.off() # Ensure motor inputs are off
    control_motor(0) # Stop motor
    set_servo_angle(0) # Center servo
    
    uart_port = connect_uart() # Connect to UART
    led.off() # Turn off LED

    while True:
        s = uart_port # Alias for UART object
        try:
            print("UART Port Ready. Starting communication...") # Status message
            uart_send(s, json.dumps({"from": "pico", "status": "ready"}) + "\n") # Send ready signal as JSON
            print("[Pico W] Sent ready signal to Jetson.") # Confirmation message
            led.on() # Turn on LED to indicate ready state

            while True:
                json_obj, m_tuple, got_stop = pump_uart(s) # Pump UART for data
                
                if got_stop:
                    print(" Received STOP -> Stopping Vehicle") # Status message
                    control_motor(0) # Stop motor
                    set_servo_angle(0) # Center servo
                    raise KeyboardInterrupt # Raise interrupt to exit loop/program

                if m_tuple:
                    # m_tuple = (angle, speed)
                    angle, speed = m_tuple # Unpack tuple
                    
                    # Display real-time control values (Retains original pico.py display logic)
                    print(" Angle = {:>4d}, Speed = {:>4d}, Encoder = {:>6d}".format(
                        angle, speed, encoder_count
                    )) # Print control and encoder values
                
                time.sleep(0.01) # Rest CPU for a short time

        except KeyboardInterrupt:
            control_motor(0) # Stop motor
            set_servo_angle(0) # Center servo
            print("Program Interrupted") # Termination message
            break # Exit the inner loop

        except OSError as e: # Catch UART Init failed
            print("UART error:", e) # Print error
            print(" Reconnecting in 3s...") # Status message
            time.sleep(3) # Wait before retrying
        
        except Exception as e:
            print("Unexpected error:", e) # Print unexpected error
            print(" Reconnecting in 3s...") # Status message
            time.sleep(3) # Wait before reconnecting


except KeyboardInterrupt:
    control_motor(0) # Stop motor on external interruption
    set_servo_angle(0) # Center servo on external interruption
    print(" Program Interrupted (Outer Level)") # Termination message
