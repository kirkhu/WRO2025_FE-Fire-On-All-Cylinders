<div align=center> <img src="../../../other/img/logo.png" width = 300 alt=" logo"> </div>

## <div align="center">Open Challenge Code Overview</div> 
  Based on the characteristics of each control board, we distributed the complex operations required for the race vehicle:
   <ol>
   <li>
    The Nvidia Nvidia Jetson Orin Nano is primarily responsible for image recognition and driving direction determination, leveraging its powerful computational capabilities to perform real-time image analysis.     
   </li>
   <li>
    The Raspberry Pi Pico W handles the motor drive and vehicle steering, utilizing its efficient GPIO control functions to achieve precise hardware management.
   </li>
   <li>
    This specialized division of labor architecture maximizes the unique strengths of each control board, resulting in a system that operates with enhanced stability and efficiency.
   </li>
   </ol>

 - ### Nvidia Jetson Orin nano library 
    The core functions for image recognition and ground line color recognition have been fully integrated into the [function.py](../common/function.py) module and can be directly imported and called for use. The specific functions of these modules are listed as follows:
    - `find_contours()`: Process image data to identify objects or features of specific colors in the scene.

      ```python
      def find_contours(img_lab, lab_range, ROI):
        x1, y1, x2, y2 = ROI
        seg = img_lab[y1:y2, x1:x2]
        lo = np.array(lab_range[0]); hi = np.array(lab_range[1])
        mask = cv2.inRange(seg, lo, hi)
        k = np.ones((5,5), np.uint8)
        mask = cv2.erode(mask, k, iterations=1)
        mask = cv2.dilate(mask, k, iterations=1)
        contours = cv2.findContours(mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)[-2]
        return contours
      ```
    - `max_contour()`: This function filters the input list of contours by selecting those with an area greater than a specific threshold, then identifies the largest contour among them, calculates its centroid coordinates,and finally returns this largest contour's area, coordinates, and the contour itself.
    
      ```python
      def max_contour(contours, ROI):
          maxArea = 0; maxY = 0; maxX = 0; mCnt = 0
          for cnt in contours:
              area = cv2.contourArea(cnt)
              if area > 150:
                  approx = cv2.approxPolyDP(cnt, 0.01*cv2.arcLength(cnt, True), True)
                  x,y,w,h = cv2.boundingRect(approx)
                  x += ROI[0] + w//2
                  y += ROI[1] + h
                  if area > maxArea:
                      maxArea = area; maxY = y; maxX = x; mCnt = cnt
          return [maxArea, maxX, maxY, mCnt]
      ```             

 - ### Nvidia Jetson Orin Nano Open Challenge Code Overview 
   - #### Nvidia Jetson Orin Nano Core Library Open Challenge Code Plan 
    
    ```python
    import os, sys                                                                 
    sys.path.append(os.path.abspath(os.path.dirname(__file__)))                      
    import cv2, time, math, sys, numpy as np                                         
    from masks import rMagenta, rRed, rGreen, rBlue, rOrange, rBlack                 
    from functions_jetson import * 
    ```  

   - #### Introduction to running programs on the Nvidia Jetson Orin nano controller: 

      - ##### [jetson_orin_nano_main.py](./jetson_orin_nano_main.py)
      
      - The `jetson_nano_main.py` primary program is responsible for controlling the overall mission flow, encompassing core functions such as wall avoidance navigation, steering control, and lap counting.
      - System Startup Process: After the Nvidia Jetson Orin Nano boots up, the Raspberry Pi Pico W enters a waiting state. Upon the user pressing the physical start switch, the Nvidia Jetson Orin Nano receives the activation signal and immediately transmits a high-level signal to initiate the `jetson_nano_main.py` main program. Once running, the main program continuously sends servo motor (steering) and DC motor (drive) data to the Raspberry Pi Pico W via the UART interface for execution.
      - Straight Driving Mode (Wall Following): When the program starts, the vehicle defaults to the straight driving mode. In this mode, the system converts the calculated side wall range into a precise steering angle for the servo motor, utilizing a PD control algorithm to ensure stable tracking and prevent collisions with the walls.
      - Curve Mode Transition (Curve Detection): As the vehicle approaches a curve, the system detects the blue or orange lines on the track. Once these lines are detected, the system automatically switches to the turning mode.
      - Turning and Mode Return: In the turning mode, the servo motor angle remains fixed, and the vehicle still uses visual wall perception for auxiliary judgment. The turning is deemed complete when the system confirms that the inner wall area is greater than 4000, upon which the vehicle immediately returns to the straight driving mode.

      ### Nvidia Jetson Orin Nano Program Execution Flow
      
       - Upon execution, the `jetson_nano_main.py` program first initializes all system variables. Subsequently, the program enters a Main Loop, where it continuously calls the `find_contours()` and `max_contour()` functions to acquire real-time visual data. The system then branches into different conditional blocks based on the current vehicle status to execute the corresponding control operations.At the conclusion of each cycle, the program packages the calculated DC motor values, servo motor angles, and the current operating status into a binary data format. This package is then transmitted via the UART interface to the Raspberry Pi Pico W for low-level hardware control.

   - ##### Nvidia Jetson Orin Nano Controller Main Program Flowchart 
     ![flowchart_open](./img/open_challange_Jetson_nano.jpg)
     ![flowchart_open](./img/Chinese_Qualifying_Tournament_Operation_Flowchart.jpg)

 - ### Raspberry Pi Pico W Open Challenge Code Overview 
   - #### Raspberry Pi Pico W Core Library / Module Program Plan for the Open Challenge 
    
      ```python
      from machine import Pin, PWM, UART,I2C,time_pulse_us
      import time
      import struct
      ```  
     
   - #### Raspberry Pi Pico W Controller Program Operation Overview

      - ##### [pico_main.py](./pico_main.py)
      
      - The pico_main.py program runs on the Raspberry Pi Pico W controller, functioning as the intermediate control system for the self-driving vehicle. It is primarily responsible for managing the operation of both the DC driving motor and the servo steering motor. The program receives calculation results from the Nvidia Jetson Orin Nano controller via the UART interface, using this data to control the rotational speed of the rear DC motor and the angle of the front servo motor, while simultaneously monitoring vehicle status parameters.
      - To control the rear DC motor, we regulate the voltage by adjusting the PWM duty cycle, utilizing the L293D driver chip to manage the motor's speed. Furthermore, setting the high/low logic levels on the two control pins (20, 21) of the L293D chip allows for precise control over the rear DC motor's forward and reverse rotation.
      - For steering control with the front servo motor, we directly utilize the PWM signal's duty cycle to adjust the output, thereby commanding the servo motor's turning angle. The variation in the PWM duty cycle corresponds to different angle settings of the servo motor, which enables highly accurate steering.
      

      - ##### Program Operation flowchart of the Raspberry Pi Pico W controller
        ![flowchart_open](./img/open_challange_Pico.jpg)
        ![flowchart_open](./img/Chinese_pico_operation_flowchart.jpg)
        
      - #### 1. `set_servo_angle()`: Servo Motor Angle Setting
        * **Function:** Responsible for calculating and **converting** the human-readable **angle value (typically within the $\pm 180^\circ$ range)** into the required **PWM duty cycle range (0 to 65535)** for the servo motor.
        * **Output:** Outputs the calculated PWM signal precisely to the **front servo motor** to control its steering angle for accurate turning.

      - #### 2. `control_motor()`: DC Motor Speed and Direction Control
        * **Function:** Accepts a numerical value ranging from **-100 to 100** as input to control both speed and direction simultaneously.
        * **PWM Conversion:** Takes the **absolute value** of the input number and converts it into the **PWM duty cycle for the DC motor** (representing the rotational speed).
        * **Direction Control:** Based on the **sign (positive/negative)** of the input value, it sets the **high/low state of the two control pins on the L293D driver chip** to achieve **forward rotation, reverse rotation, or motor stop**.

      - #### 3. `pump_uart()`: UART Data Transmission Management (Jetson Side)
        * **Function:** This function executes on the **Nvidia Jetson Orin Nano controller**. Its responsibility is to transmit the latest control parameters, including the **updated mode**, **servo angle**, and **DC motor speed** values, to an **output queue** via the **UART protocol**.
        * **Purpose:** Ensures the control process runs continuously, maintaining **real-time data updates** and synchronization between the Jetson and the Pico W.
 

# <div align="center">![HOME](../../../other/img/home.png)[Return Home](../../../)</div>  
