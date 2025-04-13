<div align=center> <img src="../../../other/img/logo.png" width = 300 alt=" logo"> </div>

## <div align="center">Obstacle_Challenge Code Overview</div> 
Based on the characteristics of each control board, we distributed the complex operations required for the race vehicle:
   <ol>
   <li>
    This time, in addition to handling sidewall image recognition and direction detection, the Jetson Nano has added an obstacle block recognition feature. Leveraging its powerful computing capabilities, the Jetson Nano can perform real-time image analysis and processing, accurately detecting the vehicle's direction while also quickly recognizing and avoiding obstacles in its path, thereby enhancing the stability and safety of autonomous driving. 
   </li>
   <li>
    Additionally, this time, the Raspberry Pi Pico not only controls the DC motor speed and vehicle steering but also needs to detect the distance to the parking lot sidewall. Utilizing its efficient GPIO control capabilities, the Raspberry Pi Pico can perform precise distance measurements and hardware management, ensuring the vehicle parks safely in the lot while maintaining an appropriate distance.
   </li>
   </ol>

 - ### Jetson Nano library
    The functions for image recognition, front-wheel servo motor proportional steering control, and ground line color recognition have been integrated into the [function.py](../common/function.py) module and can be directly imported for use.
    The functions of these modules are as follows:
    - The explanations for `process_roi()` and `pd_control()` can be found in the **[Open Challenge Code Overview](../Open_Challenge/README.md) section**, so they will not be repeated here.

    - `detect_color_final()`: The system detects the color of ground lines to enable applications such as path or lane tracking. Additionally, the system detects the coordinates of traffic signs and records this coordinate data for further analysis and processing.
       ```
          def detect_color_final(undistorted_frame, last_diffs, start_points, end_points, slope_values, curvature_factors, colors):
              """Detect specific color regions, return the Y coordinates of color centers, and calculate X differences for red and green curves."""
              hsv_frame = cv2.cvtColor(undistorted_frame, cv2.COLOR_BGR2HSV)
              color_y_positions = []
              pink_positions = [0] * 4
              center_x, center_y = 0, 0
              diffs = {'Red': 0, 'Green': 0, 'Pink_Red': 0, 'Pink_Green': 0}

              for color, (lower, upper, bgr) in color_ranges_final.items():
                  lower = np.array(lower, dtype=np.uint8)
                  upper = np.array(upper, dtype=np.uint8)
                  color_mask = cv2.inRange(hsv_frame, lower, upper)
                  contours, _ = cv2.findContours(color_mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)

                  if contours:
                      if color == 'Pink':
                          sorted_contours = sorted(contours, key=cv2.contourArea, reverse=True)
                          top_two_contours = [cnt for cnt in sorted_contours[:2] if cv2.contourArea(cnt) > 500]
                          for i, cnt in enumerate(top_two_contours):
                              x, y, w, h = cv2.boundingRect(cnt)
                              center_x = x + w // 2
                              center_y = y + h // 2
                              pink_positions[2*i:2*i+2] = [center_x, center_y]
                              cv2.rectangle(undistorted_frame, (x, y), (x + w,  y + h), bgr, 2)
                              cv2.circle(undistorted_frame, (center_x, center_y), 5, bgr, -1)
                          else:
                              largest_contour = max(contours, key=cv2.contourArea)
                              if cv2.contourArea(largest_contour) > 600:
                                  x, y, w, h = cv2.boundingRect(largest_contour)
                                  center_x = x + w // 2
                                  center_y = y + h // 2
                                  color_y_positions.append(center_y)
                                  cv2.rectangle(undistorted_frame, (x, y), (x + w, y + h), bgr, 2)
                                  cv2.circle(undistorted_frame, (center_x, center_y), 5, bgr, -1)
                              else:
                                  color_y_positions.append(0)

                    red_curve_points, green_curve_points = draw_multiple_curves(undistorted_frame, start_points, end_points, slope_values, curvature_factors, colors)
            
                if color == 'Red':
                    diffs['Red'] = calculate_x_diff(center_x, center_y, red_curve_points, last_diffs['Red'], undistorted_frame, (0, 0, 255))
                elif color == 'Green':
                    diffs['Green'] = calculate_x_diff(center_x, center_y, green_curve_points, last_diffs['Green'], undistorted_frame, (0, 255, 0))
                elif color == 'Pink':
                    diffs['Pink_Red'] = calculate_x_diff(pink_positions[0], pink_positions[1], red_curve_points, last_diffs['Pink_Red'], undistorted_frame, (255, 192, 203))
                    diffs['Pink_Green'] = calculate_x_diff(pink_positions[0], pink_positions[1], green_curve_points, last_diffs['Pink_Green'], undistorted_frame, (255, 192, 203))
            else:
                color_y_positions.append(0)
                pink_positions[:] = [0, 0, 0, 0]
        
          return color_y_positions, pink_positions, diffs['Red'], diffs['Green'], diffs['Pink_Red'], diffs['Pink_Green']
        ```
     - `calculate_x_diff`: Using the coordinates of traffic signs along with **raw_multiple_curves**, calculate the current coordinates and the ideal coordinates to enable `pd_control()` for PD tracking.
        ```
            def calculate_x_diff(center_x, center_y, curve_points, last_diff, frame, color):
                """Calculate the X difference between the center point and curve point."""
                max_curve_y = max(pt[1] for pt in curve_points)
                if center_y < max_curve_y:
                    for curve_x, curve_y in curve_points:
                        if abs(curve_y - center_y) < 2:
                            cv2.circle(frame, (curve_x, curve_y), 6, color, -1)
                            return curve_x - center_x
                    return last_diff
                return 0
       ```

    - `draw_multiple_curves`: Use `detect_color_final()` to obtain and calculate the coordinates of the traffic sign blocks, then use Bézier curves to determine the x-values of the traffic sign blocks at the same y-coordinate. This will allow the calculation of deviation errors.
       ```
        def draw_multiple_curves(undistorted_frame, start_points, end_points, slope_values, curvature_factors, colors, thickness=2):
        """
        Draw multiple curves with different starting points, endpoints, slopes, and curvatures on the image, and return the coordinate list of the red curve.
        """
        red_curve_points = []  # store the coordinates of the points on the red curve.
        green_curve_points = []  # store the coordinates of the points on the green curve.


        for start_point, end_point, slope, curvature, color in zip(start_points, end_points, slope_values, curvature_factors, colors):
            x1, y1 = start_point
            x2, y2 = end_point

            # Calculate the position of the intermediate control points to control the curvature.
            mid_x = (x1 + x2) // 2
            mid_y = (y1 + y2) // 2
           control_x = mid_x
           control_y = int(mid_y - curvature * slope * (x2 - x1))  # Use curvature and slope to adjust the intermediate control points.

           # Draw using Bézier curves.
           curve_points = []
           for t in np.linspace(0, 1, 100):
               xt = (1 - t)**2 * x1 + 2 * (1 - t) * t * control_x + t**2 * x2
               yt = (1 - t)**2 * y1 + 2 * (1 - t) * t * control_y + t**2 * y2
               curve_points.append((int(xt), int(yt)))

           #  If it is a red curve, save the point coordinates.
           if color == (0, 0, 255):  # Red curve.
               red_curve_points = curve_points
           if color == (0, 255, 0):  # Green curve.
               green_curve_points = curve_points

           # Draw the curve.
           for i in range(len(curve_points) - 1):
               cv2.line(undistorted_frame, curve_points[i], curve_points[i + 1], color, thickness)

       return red_curve_points,green_curve_points  # Return the coordinates of the points on the red curve.

      ```


 - ### Obstacle_Challenge Code Overview of Jetson nano
   - #### Obstacle_Challenge Code Program Jetson nano Libraries
    
      ```
      import cv2
      import numpy as np
      import serial as AC
      import struct
      import Adafruit_BNO055.BNO055 as BNO055 
      # Program module for loading the BNO055 gyroscope orientation sensor
      
      import time
      from function import process_roi, detect_color, pd_control
      # Load custom program modules for image recognition, front-wheel servo
        motor steering ratio control, and ground line color recognition.

      import Jetson.GPIO as GPIO 
      # Enable GPIO pin control on the Jetson Nano.
      ```  

   - #### Introduction to running programs on the Jetson nano controller:

      - ##### [jetson_nano_main_final.py](./jetson_nano_main_final.py)
        - The `jetson_nano_main.py` program is primarily responsible for controlling the entire task flow, including avoiding walls, steering control, dodging block obstacles, and lap counting to ensure the vehicle completes all tasks as planned.

        - When the program starts, the vehicle is set to straight-driving mode by default. In this mode, the system converts the boundary range calculated by `process_roi()` into the angle for the servo motor and uses `pd_control()` to perform PD steering control to ensure the vehicle does not collide with the sidewall. As the vehicle approaches a turning area, the system uses `detect_color_final()` to detect blue or orange lines to determine whether to switch to turning mode.

        - **In straight-driving mode**, the system primarily uses the deviation of red and green blocks from the track curve, calculated by `detect_color_final()`, as a reference for correction, and uses the sidewall as a secondary correction reference when necessary.

        - **In turning mode**, the servo motor angle remains fixed. The system determines whether it has reached the next turning point based on changes in the gyroscope angle and elapsed time, allowing it to decide when to return to straight-driving mode and avoid repeated detection.

      __Program operation flow__
        - `jetson_nano_main_fianl.py` starts execution, initializes all variables, and enters a loop, continuously retrieving data from process_roi and detect_color, then entering different conditional branches based on the current state to perform the appropriate control actions. In each loop, `jetson_nano_main_final.py` packages the calculated DC motor value, servo motor angle, and current status into binary data and sends it to the Raspberry Pi Pico via UART. 

   - ##### Program Operation flowchart of the Jetson Nano controller
     ![Obstacle_Challenge_Jetson_nano](./img/FE-obstacle_challenge_Jetson_nano.jpg)

 - ### Obstacle_Challenge Code Overview of Raspberry Pi Pico
   - ####  Obstacle_Challenge Code Program Raspberry Pi Pico Libraries
    
      ```
      from machine import Pin, PWM, I2C, UART  
      # In MicroPython, you can import relevant modules to enable 
        GPIO pin control, Pulse Width Modulation (PWM), I2C, and 
        UART communication protocols on the Raspberry Pi Pico.

      import struct
      import time
      ```  
     
   - #### Introduction to running programs on the Raspberry Pi Pico controller:

      - ##### [pico_main_final.py](./pico_main_final.py)
        - The `pico_main_final.py` program runs on the Raspberry Pi Pico controller as an intermediary control system for an autonomous vehicle, managing the operation of the DC motor and servo motor. This program receives computation results from the Jetson Nano controller via UART and controls the speed of the rear-wheel DC motor, the angle of the front-wheel servo motor, while also monitoring vehicle status parameters.
        -  When the start switch is pressed, the Raspberry Pi Pico controller receives a start signal and sends a high-level signal to initiate the main program `jetson_nano_main_final.py` on the Jetson Nano.
        - When controlling the rear-wheel DC motor, we adjust the voltage through the duty cycle of PWM, using the L293D driver chip to achieve speed control of the rear-wheel DC motor. Additionally, by setting the high and low levels of the two control pins (20,21) on the L293D, we can control the forward and reverse rotation of the rear-wheel DC motor.
        - When controlling the front-wheel servo motor, we directly use the duty cycle of the PWM signal to adjust the output and control the steering angle of the servo motor, without the need for an L293D driver. Changes in the PWM signal’s duty cycle correspond to different angle settings for the servo motor, allowing for precise steering.
        - When the program reaches state five, the system takes over the control of the DC motor and begins tracking the pink sidewall of the parking area. During tracking, the ultrasonic distance sensor detects the parking area; when the sensor detects that the sidewall is pink, the system simultaneously takes control of both the servo motor and the DC motor. It then uses `run_encoder_Auto()` to adjust the forward angle of the DC motor to ensure precise parking.
      

      __Program operation flow__
      
        - When  `pico_main_final.py` starts, it sends a high-frequency signal to the Jetson Nano to trigger the execution of the `jetson_nano_main_final.py` program. Then, `pico_main_final.py` enters a waiting mode until the button is pressed. After pressing the button,`pico_main_final.py` enters the main loop, starts receiving data transmitted via UART from the Jetson Nano, and continues running. When it receives a status value of 5, the Pico takes over vehicle control and performs the parking operation.

    - ##### Program Operation flowchart of the Raspberry Pi Pico controller
        ![FE-obstacle_challenge_Pico](./img/FE-obstacle_challenge_Pico.jpg)

       **set_servo_angle():** <br>
           Calculate and convert the angle value from ±180 degrees to the PWM duty cycle range required by the servo motor (0 to 65535) and output it to the front-wheel servo motor.

        __control_motor():__<br>
           Take the absolute value of a number in the range of -100 to 100 and convert it to the PWM duty cycle. Meanwhile, set the high and low states of two pins based on the sign of the value to control forward and reverse rotation or to stop.

        __jetson_all():__<br>
           Receive updated data sent from the Jetson Nano controller via the UART protocol and store it in a queue, ensuring that this process runs continuously to maintain real-time data updates.

        __run_encoder():__<br>
           By reading the current value of the DC motor to calculate its rotation angle, conditions are set based on the calculation results to control the motor to move straight to the specified rotation angle. This design allows for precise motor adjustments, ensuring that the vehicle moves steadily during operation and accurately reaches the intended target angle.

        __run_encoder_Auto():__<br>
            In `run_encoder()`, the servo motor angle is set to a fixed value to maintain stable control of the vehicle's position and direction during the parking operation.
       </ol>
# <div align="center">![HOME](../../../other/img/home.png)[Return Home](../../../)</div>  
