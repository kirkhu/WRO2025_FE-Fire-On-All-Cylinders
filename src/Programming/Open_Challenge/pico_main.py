from machine import Pin, PWM, I2C, UART
import struct
import time

servo_pin = PWM(Pin(28), freq=50)
motor_in1 = Pin(3, Pin.OUT)
motor_in2 = Pin(2, Pin.OUT)
button_out = Pin(15, Pin.OUT)
motor_pwm = PWM(Pin(22), freq=1000)
encoder_pin_A = Pin(0, Pin.IN)
encoder_pin_B = Pin(1, Pin.IN)
button = Pin(18, Pin.IN, Pin.PULL_UP)
data_value = [0] * 3  # Initialize the data list
value = [0] * 3
encoder_count = 0  # Initialize encoder count
last_state_A = encoder_pin_A.value()  # Initialize encoder status
jetson_nano_return_last = 0
# Configuring UART
uart = UART(0, baudrate=115200, tx=Pin(16), rx=Pin(17))

def jetson_nano_return(number):
    global data_value
    HEADER = b"A"  # Header Definition
    HEADER_SIZE = len(HEADER)
    DATA_SIZE = 12 # 5 integers, 4 bytes each, 20 bytes in total
    TOTAL_SIZE = HEADER_SIZE + DATA_SIZE  # Total length of header + data
    if uart.any():
        data = uart.read(TOTAL_SIZE)
        
        # Check if a complete packet is received
        if len(data) == TOTAL_SIZE:
            # Find the header
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
    print(value[0], value[1], value[2])

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
        combined_control_signal = jetson_nano_return(0)
        
        # Use the control signal to adjust the servo
        set_servo_angle(combined_control_signal)
        control_motor(speed)        
        print(f"Encoder count: {encoder_count}, combined_control_signal: {combined_control_signal}")
        jetson_all()
        time.sleep(0.01)
    control_motor(0)

# GPIO interrupt setup
encoder_pin_A.irq(trigger=Pin.IRQ_RISING | Pin.IRQ_FALLING, handler=encoder_interrupt)

# Define motor control function
def control_motor(speed):
    if speed > 0:
        motor_in1.high()
        motor_in2.low()
    elif speed < 0:
        motor_in1.low()
        motor_in2.high()
    else:
        motor_in1.low()
        motor_in2.low()
    motor_pwm.duty_u16(int(abs(speed) * 65535 / 100))  # Set PWM duty cycle

# Set servo angle
def set_servo_angle(angle):
    min_duty = 1000  # Corresponds to 1ms duty cycle
    max_duty = 2000  # Corresponds to 2ms duty cycle
    duty = int(min_duty + (angle-15 + 180) * (max_duty - min_duty) / 360)
    duty_u16 = int(duty * 65535 / 20000)
    servo_pin.duty_u16(duty_u16)

try:
    motor_in1.off()
    motor_in2.off()
    set_servo_angle(0)
    button_out.low()
    while button.value() == 1:
        time.sleep(0.1)
        print(jetson_nano_return(0), jetson_nano_return(1), jetson_nano_return(2))
    button_out.high()
    control_motor(60)
    for a in range(3):
        for b in range(4):
            jetson_all()
            while not value[1] == 2:
                jetson_all()
                control_motor(value[2])
                set_servo_angle(value[0])
            run_encoder(3500, 60) 
except KeyboardInterrupt:
    motor_in1.off()
    motor_in2.off()
    set_servo_angle(0)
    print("Program interrupted")  