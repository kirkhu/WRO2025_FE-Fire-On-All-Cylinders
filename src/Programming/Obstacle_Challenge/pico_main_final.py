from machine import Pin, PWM, I2C, UART, time_pulse_us
import struct
import time

# Set the pin position of ultrasound module 9
TRIG_PIN1 = 8  # Corresponds to the Trig pin of the first ultrasound module
ECHO_PIN1 = 9  # Corresponds to the Echo pin of the first ultrasound module
TRIG_PIN2 = 12  # Corresponds to the Trig pin of the second ultrasound module
ECHO_PIN2 = 13  # Corresponds to the Echo pin of the second ultrasound module

# Ultrasonic initialization pin
trig1 = Pin(TRIG_PIN1, Pin.OUT)
echo1 = Pin(ECHO_PIN1, Pin.IN)
trig2 = Pin(TRIG_PIN2, Pin.OUT)
echo2 = Pin(ECHO_PIN2, Pin.IN)

servo_pin = PWM(Pin(28), freq=50)
motor_in1 = Pin(21, Pin.OUT)
motor_in2 = Pin(20, Pin.OUT)
button_out = Pin(15, Pin.OUT)
motor_pwm = PWM(Pin(22), freq=1000)
encoder_pin_A = Pin(0, Pin.IN)
encoder_pin_B = Pin(1, Pin.IN)
button = Pin(18, Pin.IN, Pin.PULL_UP)
data_value = [0] * 3  # Initialize data list
value = [0] * 3
encoder_count = 0  # Initialize encoder count
last_state_A = encoder_pin_A.value()  # Initialize encoder status
jetson_nano_return_last = 0
# Configure UART
uart = UART(0, baudrate=115200, tx=Pin(16), rx=Pin(17))

def jetson_nano_return(number):
    global data_value
    HEADER = b"A"  # Baotou definition
    HEADER_SIZE = len(HEADER)
    DATA_SIZE = 12 # 5 integers, 4 bytes each, 20 bytes in total
    TOTAL_SIZE = HEADER_SIZE + DATA_SIZE  # Header + total length of data

    if uart.any():
        data = uart.read(TOTAL_SIZE)
        
        # Check if complete packet is received
        if len(data) == TOTAL_SIZE:
            # Find Baotou
            header_index = data.find(HEADER)
            if header_index != -1:
                # If a header is found, remove the header and extract the data
                start_index = header_index + HEADER_SIZE
                data = data[start_index:] + data[:start_index]
                data_value = struct.unpack('3i', data[:DATA_SIZE])
                return data_value[number]
            else:
                print("Error: Incorrect header received.")
        else:
            print("Error: Incomplete data received.")
    return data_value[number]
def jetson_all():
    global value
    value[0] = jetson_nano_return(0)
    value[1] = jetson_nano_return(1)
    value[2] = jetson_nano_return(2)
    print(value[0],value[1],value[2])


def encoder_interrupt(pin):
    global encoder_count, last_state_A
    state_A = encoder_pin_A.value()
    state_B = encoder_pin_B.value()
    if state_A != last_state_A:
        encoder_count += 1 if state_B != state_A else -1
    last_state_A = state_A

def run_encoder(motor_angle, speed):
    global encoder_count
    encoder_count = 0  # Reset the encoder count to zero before running
    while abs(encoder_count) < motor_angle:
        # Select PD control signal according to data_mode
        combined_control_signal = value[0]
        
        # Use control signals to adjust the servo
        set_servo_angle(combined_control_signal)
        control_motor(speed)
        
        print(f"编码器计数: {encoder_count}, combined_control_signal: {combined_control_signal}")
        jetson_all()
        time.sleep(0.01)
    control_motor(0)
    
    
def approach_until(trig, echo, threshold, operator):
    dist = measure_distance(trig, echo)
    while (dist > threshold if operator == '>' else dist < threshold):
        jetson_all()
        dist = measure_distance(trig, echo)
        control_motor(value[2])
        set_servo_angle(value[0])
        time.sleep(0.05)

def run_encoder_Auto(motor_angle, speed, string):
    global encoder_count
    encoder_count = 0  #Reset the encoder count to zero before running
    while abs(encoder_count) < motor_angle:
        # Select PD control signal according to data_mode
        combined_control_signal = string
        
        # Use control signals to adjust the servo
        set_servo_angle(combined_control_signal)
        control_motor(speed)
        
        time.sleep(0.01)
    control_motor(0)
# GPIO interrupt settings
encoder_pin_A.irq(trigger=Pin.IRQ_RISING | Pin.IRQ_FALLING, handler=encoder_interrupt)
# Define the motor control function
def control_motor(speed):
    if speed > 0:
        motor_in1.high()
        motor_in2.low()
    elif speed < 0:
        motor_in1.low()
        motor_in2.high()
    else:
        motor_in1.high()
        motor_in2.high()
    motor_pwm.duty_u16(int(abs(speed) * 65535 / 100))  # Setting the PWM duty cycle
# Set the servo angle
def set_servo_angle(angle):
    min_duty = 1000  #Corresponding to a duty cycle of 1ms
    max_duty = 2000  # Corresponding to a duty cycle of 2ms
    duty = int(min_duty + (angle-15 + 180) * (max_duty - min_duty) / 360)
    duty_u16 = int(duty * 65535 / 20000)
    servo_pin.duty_u16(duty_u16)

def measure_distance(trig, echo):
    # Send trigger pulse
    trig.value(0)
    time.sleep_us(2)
    trig.value(1)
    time.sleep_us(10)
    trig.value(0)

    # Read Echo pulse width
    duration = time_pulse_us(echo, 1)

    # Calculate distance (speed of sound is approximately 343 m/s)
    distance = (duration / 2) * 0.0343

    return distance
    

try:
    motor_in1.off()
    motor_in2.off()
    set_servo_angle(0)
    button_out.high()
    while button.value() == 1:
        time.sleep(0.1)
#         print(jetson_nano_return(0),jetson_nano_return(1),jetson_nano_return(2))
        distance2 = measure_distance(trig2, echo2)
        print(distance2)
    
    control_motor(60)

    while value[1] != 5 :
        jetson_all()
        control_motor(value[2])
        set_servo_angle(value[0])
        time.sleep(0.05)
        if value[1] == 6:
            run_encoder(3500, 60)
            control_motor(0)
            time.sleep(3)

    
    control_motor(35)
    time.sleep(0.4)
    control_motor(0)
    distance2 = measure_distance(trig2, echo2)
    distance1 = measure_distance(trig1, echo1)
    if distance1 > distance2:  # Right-side parking
        approach_until(trig2, echo2, 15, '>')
        approach_until(trig2, echo2, 20, '<')
        approach_until(trig2, echo2, 15, '>')
     # Reverse parking.
        run_encoder_Auto(300, 10, 0)
        run_encoder_Auto(1500, -45, 175)
        run_encoder_Auto(30, -10, -190)
        run_encoder_Auto(1400, -25, -190)
        run_encoder_Auto(480, 30, 180)
        run_encoder_Auto(10, 10, 0)
    # (Continue with the rest of the reverse parking sequence)
    else:  # Left-side parking
        approach_until(trig1, echo1, 15, '>')
        approach_until(trig1, echo1, 20, '<')
        approach_until(trig1, echo1, 15, '>')
    # Reverse parking.
        run_encoder_Auto(400, 10, 0)
        run_encoder_Auto(1620, -45, -190)
        run_encoder_Auto(30, -10, 180)
        run_encoder_Auto(1330, -25, 180)
        run_encoder_Auto(470, 30, -180)
        run_encoder_Auto(10, 10, 0)
    # (Continue with the rest of the reverse parking sequence)
            
    control_motor(-25)
    time.sleep(0.35)
    control_motor(0)
    button_out.low()
            
        
except KeyboardInterrupt:
    motor_in1.off()
    motor_in2.off()
    set_servo_angle(0)
    print("Program interruption")









