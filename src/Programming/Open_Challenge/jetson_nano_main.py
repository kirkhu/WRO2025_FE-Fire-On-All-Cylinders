import cv2
import numpy as np
import serial as AC
import struct
import Adafruit_BNO055.BNO055 as BNO055
import time
from function import process_roi, detect_color, pd_control
import Jetson.GPIO as GPIO

# Define sensing areas
rois = [
    (370, 100, 640, 150),  # Large right sensing area
    (0, 100, 270, 150),  # Large left sensing area
]
GPIO.setmode(GPIO.BOARD)  # Use pin numbering
target_heading = [0] * 4
left_heading = [-90,-180,90,0]
right_heading = [90,180,-90,0]
turn_side = 0
kp_roi = 0.008  # Default data column proportional gain
kd_roi = 0.01  # Default data column differential gain
combined_control_signal = 0
count = 0
PWM = 100
round_number = 0
data_to_send = 0
output_pin = 40
GPIO.setup(output_pin, GPIO.OUT)
# Load calibration data
calibration_data = np.load('calibration_data.npz')
camera_matrix = calibration_data['camera_matrix']
distortion_coefficients = calibration_data['distortion_coefficients']

# Try opening the serial port
try:
    ser = AC.Serial('/dev/ttyTHS1', 115200, timeout=1)  # Adjust the baud rate as needed
except AC.SerialException as e:
    print(f"Error: Could not open serial port: {e}")
    exit()


def main():
    global turn_side
    global target_heading
    global left_heading
    global right_heading
    global count
    global PWM
    global round_number
    global data_to_send
    current_last = 0  # Initialize the current_last variable
    window_name = "Camera Preview"
    binary_window_name = "Binary Preview"
    
    # Open the camera
    cap = cv2.VideoCapture('nvarguscamerasrc ! video/x-raw(memory:NVMM), width=640, height=480, format=(string)NV12, framerate=12/1 ! nvvidconv ! video/x-raw, format=BGRx ! videoconvert ! video/x-raw, format=BGR ! appsink drop=true sync=false', cv2.CAP_GSTREAMER)

    if not cap.isOpened():
        print("Error: Could not open video stream.")
        return
    bno = BNO055.BNO055(busnum=1)

    if not bno.begin():
        raise RuntimeError('Failed to initialize BNO055!')

    GPIO.output(output_pin, GPIO.HIGH)
    combined_control_signal = 0
    while True:
        ret, frame = cap.read()
        if not ret:
            break
        # Read BNO055 sensor data
        heading, roll, pitch = bno.read_euler()
        accel_x, accel_y, accel_z = bno.read_linear_acceleration()
        if heading > 180:
            heading -= 360
        # Correct distortion of the image using calibration parameters
        h, w = frame.shape[:2]
        new_camera_matrix, roi = cv2.getOptimalNewCameraMatrix(camera_matrix, distortion_coefficients, (w, h), 0.12, (w, h))
        undistorted_frame = cv2.undistort(frame, camera_matrix, distortion_coefficients, None, new_camera_matrix)

        # Create a binarized copy
        gray = cv2.cvtColor(undistorted_frame, cv2.COLOR_BGR2GRAY)
        _, binary_frame = cv2.threshold(gray, 105, 255, cv2.THRESH_BINARY)
        binary_frame = cv2.cvtColor(binary_frame, cv2.COLOR_GRAY2BGR)

        roi_values = []
        for i, (x1, y1, x2, y2) in enumerate(rois):
            processed_roi, black_pixels = process_roi(undistorted_frame, x1, y1, x2, y2)  # Get the number of black pixels
            roi_values.append(black_pixels)
            binary_frame[y1:y2, x1:x2] = processed_roi

        # Color detection, return Y coordinates
        color_y_positions = detect_color(undistorted_frame)
        

        # Straight
        if turn_side == 0 or turn_side == 2:
            PWM = 50
            if color_y_positions[0] > color_y_positions[1]:     
                if target_heading == [0] * 4:
                    target_heading = right_heading
                if color_y_positions[0] > 270:
                    turn_side = 1
            elif color_y_positions[0] < color_y_positions[1]:
                if target_heading == [0] * 4:
                    target_heading = left_heading
                if color_y_positions[1] > 270:
                    turn_side = 1    
            else:
                turn_side = 0
            # Select PD control signal according to data_mode
            if roi_values[0] >= roi_values[1]:
                if roi_values[0] >= 4500:
                    print("right")
                    combined_control_signal = pd_control(4500, roi_values[0], kp_roi, kd_roi)
            else:
                if roi_values[1] >= 4500:
                    print("left")
                    combined_control_signal = -pd_control(4500, roi_values[1], kp_roi, kd_roi)
            start_time = time.time()  # Get the current time (seconds)
        
        # Turn
        if turn_side == 1:
            PWM = 50
            # Select PD control signal according to data_mode
            if target_heading == left_heading or target_heading:
                    if roi_values[0] >= 8500:
                        combined_control_signal = pd_control(8500, roi_values[0], kp_roi, kd_roi)
                    else:
                        combined_control_signal = -90
            else:
                    if roi_values[1] >= 8500:
                        combined_control_signal = -pd_control(8500, roi_values[1], kp_roi, kd_roi)
                    else:
                        combined_control_signal = 75
            current_time = time.time()
            elapsed_time = current_time - start_time
            if elapsed_time >= 1 and heading < target_heading[count] + 35 and heading > target_heading[count] - 35 and color_y_positions[0] ==0 and color_y_positions[1] == 0:
                turn_side = 2
                if count >= 3:
                    count = 0
                    round_number +=1
                else:
                    count += 1
                combined_control_signal = 0
                    
        # String limit
        if combined_control_signal > 180:
            combined_control_signal=180
        if combined_control_signal < -180:
            combined_control_signal=-180

        # Prepare the data to be sent
        data_to_send = (int(combined_control_signal), int(turn_side),int(PWM))
        # Print the data being sent for debugging
        print("Sent: ", data_to_send)

        # Add the header "A" to the front of the data packet
        header = b"A"
        send_data_value = struct.pack('3i', *data_to_send)  # Ensure packing 3 integers
        send_data_value = header + send_data_value

        # Send the data with header
        ser.write(send_data_value)

        # Display two windows
        cv2.imshow(window_name, undistorted_frame)
        cv2.imshow(binary_window_name, binary_frame)
        
        if cv2.waitKey(1) == ord('q'):
            break

    cap.release()
    cv2.destroyAllWindows()

if __name__ == "__main__":
    main()
