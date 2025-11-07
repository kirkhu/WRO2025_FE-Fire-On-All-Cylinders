<div align=center> <img src="../../../other/img/logo.png" width = 300 alt=" logo"> </div>

## <div align="center">Open Challenge Code Overview</div> 
  Based on the characteristics of each control board, we distributed the complex operations required for the race vehicle: - 考量到各控制板的運算特性與專長，我們對競賽車輛所需的複雜操作進行了專業的職責劃分：
  ### 中文:
   1. Jetson Orin Nano 核心處理影像辨識與行駛方向判斷，憑藉其強大的運算性能實現即時影像分析。
   2. 樹莓派 Pico W 則同步負責馬達驅動及車輛轉向，利用其高效的 GPIO 控制功能達成精準的硬體管理。
   3. 此種專業分工的架構能最大化各控制板的專長優勢，進而讓整個系統運行更為穩定且高效。
   ### 英文:
   <ol>
   <li>
    The Jetson Orin Nano is primarily responsible for image recognition and driving direction determination, leveraging its powerful computational capabilities to perform real-time image analysis.     
   </li>
   <li>
    The Raspberry Pi Pico W handles the motor drive and vehicle steering, utilizing its efficient GPIO control functions to achieve precise hardware management.
   </li>
   <li>
    This specialized division of labor architecture maximizes the unique strengths of each control board, resulting in a system that operates with enhanced stability and efficiency.
   </li>
   </ol>

 - ### Jetson Orin nano library - Jetson Orin nano庫
    The core functions for image recognition and ground line color recognition have been fully integrated into the [function.py](../common/function.py) module and can be directly imported and called for use. The specific functions of these modules are listed as follows:
    - `find_contours()`: Process image data to identify objects or features of specific colors in the scene.(處理影像資料以識別場景中的特定顏色物體或特徵。)
      ```
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
    - `max_contour()`: This function filters the input list of contours by selecting those with an area greater than a specific threshold, then identifies the largest contour among them, calculates its centroid coordinates,and finally returns this largest contour's area, coordinates, and the contour itself.(從輸入的輪廓列表中，篩選出面積大於特定閾值的輪廓，並找出其中面積最大的輪廓，計算其中心點座標，最終回傳此最大輪廓的面積、座標與輪廓本身。)
      ```
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

 - ### Jetson Orin Nano Open Challenge Code Overview - Jetson Orin nano 公開挑戰程式碼概述
   - #### Jetson Orin Nano Core Library Open Challenge Code Plan - Jetson Orin nano 函式庫的開放挑戰程式碼計劃
    
```
import os, sys                                                                 
sys.path.append(os.path.abspath(os.path.dirname(__file__)))                      
import cv2, time, math, sys, numpy as np                                         
from masks import rMagenta, rRed, rGreen, rBlue, rOrange, rBlack                 
from functions_jetson import * 
```  

   - #### Introduction to running programs on the Jetson Orin nano controller: - Jetson Orin Nano 控制器上程式運行之簡介:

      - ##### [jetson_orin_nano_main.py](./jetson_orin_nano_main.py)
      ### 中文:
      - `jetson_nano_main.py` 主程式負責掌控整體任務流程，包含避牆導航、轉向控制及圈數計數等核心功能。
      - 系統啟動流程： Jetson Orin Nano 啟動後，樹莓派 Pico W 會進入待命狀態。當使用者按下實體啟動開關後，Jetson Orin Nano 接收到啟動訊號，隨即發送高電平訊號來啟動 `jetson_nano_main.py` 主程式。主程式運行後，便透過 UART 介面持續將舵機（轉向）和直流馬達（驅動）的數據傳送給樹莓派 Pico W 執行。
      - 直線行駛模式 (Wall Following): 程式啟動時，車輛預設進入直線行駛模式。在此模式下，系統會將計算出的邊牆範圍轉換為伺服馬達的精確轉向角度，並利用 PD 控制演算法確保車輛能穩定循跡，避免碰撞牆壁。
      - 轉彎模式切換 (Curve Detection): 當車輛接近彎道時，系統會偵測賽道上的藍色或橘色線條，一旦偵測到這些線條，即自動切換至轉彎模式。
      - 轉彎與模式返回： 在轉彎模式下，伺服馬達的角度保持固定不變，車輛仍利用視覺看牆的方式進行輔助判斷。當系統確認內牆面積（inner wall area）大於 4000 時，即認定轉彎完成，隨即返回直線行駛模式。
      ### 英文:
      - The `jetson_nano_main.py` primary program is responsible for controlling the overall mission flow, encompassing core functions such as wall avoidance navigation, steering control, and lap counting.
      - System Startup Process: After the Jetson Orin Nano boots up, the Raspberry Pi Pico W enters a waiting state. Upon the user pressing the physical start switch, the Jetson Orin Nano receives the activation signal and immediately transmits a high-level signal to initiate the `jetson_nano_main.py` main program. Once running, the main program continuously sends servo motor (steering) and DC motor (drive) data to the Raspberry Pi Pico W via the UART interface for execution.
      - Straight Driving Mode (Wall Following): When the program starts, the vehicle defaults to the straight driving mode. In this mode, the system converts the calculated side wall range into a precise steering angle for the servo motor, utilizing a PD control algorithm to ensure stable tracking and prevent collisions with the walls.
      - Curve Mode Transition (Curve Detection): As the vehicle approaches a curve, the system detects the blue or orange lines on the track. Once these lines are detected, the system automatically switches to the turning mode.
      - Turning and Mode Return: In the turning mode, the servo motor angle remains fixed, and the vehicle still uses visual wall perception for auxiliary judgment. The turning is deemed complete when the system confirms that the inner wall area is greater than 4000, upon which the vehicle immediately returns to the straight driving mode.

      ### Jetson Orin Nano Program Execution Flow - Jetson Orin Nano程式運行流程
      ### 中文:
      - `jetson_nano_main.py` 程式啟動後，首先初始化所有系統變數。隨後，程式進入主循環 (Main Loop)，在循環中持續調用 `find_contours()`與 `max_contour()` 函式來獲取實時視覺數據。接著，系統會根據當前車輛狀態進入不同的條件分支，以執行相應的控制操作。在每個運行週期結束時，程式會將 Jetson Orin Nano 計算出的直流馬達驅動值、伺服馬達轉向角度以及當前運行狀態，打包成二進位數據格式，並透過 UART 介面發送給 Raspberry Pi Pico W，由其進行底層硬體控制。
      ### 英文:
       - Upon execution, the `jetson_nano_main.py` program first initializes all system variables. Subsequently, the program enters a Main Loop, where it continuously calls the `find_contours()` and `max_contour()` functions to acquire real-time visual data. The system then branches into different conditional blocks based on the current vehicle status to execute the corresponding control operations.At the conclusion of each cycle, the program packages the calculated DC motor values, servo motor angles, and the current operating status into a binary data format. This package is then transmitted via the UART interface to the Raspberry Pi Pico W for low-level hardware control.

   - ##### Jetson Orin Nano Controller Main Program Flowchart - Jetson Orin Nano控制器主程式流程圖
     ![flowchart_open](./img/open_challange_Jetson_nano.jpg)
     ![flowchart_open](./img/Chinese%20Qualifying%20Tournament%20Operation%20Flowchart.jpg)

 - ### Raspberry Pi Pico W Open Challenge Code Overview - 樹莓派 Pico W 公開挑戰代碼概述
   - #### Raspberry Pi Pico W Core Library / Module Program Plan for the Open Challenge - 樹莓派 Pico W 庫公開挑戰程式碼程序
    
      ```
      from machine import Pin, PWM, UART,I2C,time_pulse_us
      import time
      import struct
      ```  
     
   - #### Raspberry Pi Pico W Controller Program Operation Overview - 樹莓派 Pico W 控制器程式運作簡介:

      - ##### [pico_main.py](./pico_main.py)
      ### 中文:
      - 此`pico_main.py`程式運行於樹莓派 Pico W控制器上，作為自動駕駛車輛的中間控制系統，負責管理直流馬達和伺服馬達的運作。該程式透過 UART 介面接收來自 Jetson Orin Nano 控制器的計算結果，並控制後輪直流馬達的轉速、前輪伺服馬達的角度，同時監控車輛狀態參數。    
      - 在控制後輪直流馬達時，我們透過調節PWM的佔空比來控制電壓，並使用L293D驅動晶片來實現後輪直流馬達的速度控制。此外，透過設定L293D晶片上兩個控制引腳（20、21）的高低電平，我們可以控制後輪直流馬達的正反轉。
      - 在控制前輪伺服馬達時，我們直接利用PWM訊號的佔空比來調整輸出，進而控制伺服馬達的轉向角度，PWM訊號佔空比的變化對應於伺服馬達的不同角度設置，從而實現精確轉向。
      ### 英文:
      - The pico_main.py program runs on the Raspberry Pi Pico W controller, functioning as the intermediate control system for the self-driving vehicle. It is primarily responsible for managing the operation of both the DC driving motor and the servo steering motor. The program receives calculation results from the Jetson Orin Nano controller via the UART interface, using this data to control the rotational speed of the rear DC motor and the angle of the front servo motor, while simultaneously monitoring vehicle status parameters.
      - To control the rear DC motor, we regulate the voltage by adjusting the PWM duty cycle, utilizing the L293D driver chip to manage the motor's speed. Furthermore, setting the high/low logic levels on the two control pins (20, 21) of the L293D chip allows for precise control over the rear DC motor's forward and reverse rotation.
      - For steering control with the front servo motor, we directly utilize the PWM signal's duty cycle to adjust the output, thereby commanding the servo motor's turning angle. The variation in the PWM duty cycle corresponds to different angle settings of the servo motor, which enables highly accurate steering.
      

      - ##### Program Operation flowchart of the Raspberry Pi Pico W controller - 樹莓派 Pico W 控制器程式運作流程圖
        ![flowchart_open](./img/open_challange_Pico.jpg)
        ![flowchart_open](./img/Chinese%20pico%20operation%20flowchart.jpg)
        
      - #### 1. `set_servo_angle()`：伺服馬達角度設定
        * **功能：** 負責將人機可讀的**角度值（範圍通常為 $\pm 180$ 度）**，計算並**轉換**成伺服馬達所需的**PWM 佔空比範圍（0 到 65535）**。
        * **輸出：** 將計算出的 PWM 訊號精確地輸出到**前輪伺服馬達**，以控制其轉向角度，實現精準轉向。
                    
      - #### 2. `control_motor()`：直流馬達速度與方向控制
        * **功能：** 接收一個介於 **-100 到 100 之間**的數值作為輸入，用於同時控制速度和方向。
        * **PWM 轉換：** 取該數值的**絕對值**，將其轉換為**直流馬達的 PWM 佔空比**（代表轉速）。
        * **方向控制：** 根據輸入數值的**正負符號**，設定 **L293D 驅動晶片上兩個控制引腳的高低電平狀態**，以實現馬達的**正轉、反轉或停止**。

      - #### 3. `pump_uart()`：UART 資料傳輸管理 (Jetson 側)
        * **功能：** 此函式運行於 **Jetson Orin Nano 控制器**上，其職責是透過 **UART 協定**，將最新的控制參數，包括**更新後的模式 (mode)**、**伺服馬達角度 (servo angle)** 和**直流馬達速度 (DC motor speed)** 數值，**傳送到輸出佇列**。
        * **目的：** 確保控制流程持續運行，並維持資料在 Jetson 與 Pico W 之間的**即時更新**與同步。

      - #### 1. `set_servo_angle()`: Servo Motor Angle Setting
        * **Function:** Responsible for calculating and **converting** the human-readable **angle value (typically within the $\pm 180^\circ$ range)** into the required **PWM duty cycle range (0 to 65535)** for the servo motor.
        * **Output:** Outputs the calculated PWM signal precisely to the **front servo motor** to control its steering angle for accurate turning.

      - #### 2. `control_motor()`: DC Motor Speed and Direction Control
        * **Function:** Accepts a numerical value ranging from **-100 to 100** as input to control both speed and direction simultaneously.
        * **PWM Conversion:** Takes the **absolute value** of the input number and converts it into the **PWM duty cycle for the DC motor** (representing the rotational speed).
        * **Direction Control:** Based on the **sign (positive/negative)** of the input value, it sets the **high/low state of the two control pins on the L293D driver chip** to achieve **forward rotation, reverse rotation, or motor stop**.

      - #### 3. `pump_uart()`: UART Data Transmission Management (Jetson Side)
        * **Function:** This function executes on the **Jetson Orin Nano controller**. Its responsibility is to transmit the latest control parameters, including the **updated mode**, **servo angle**, and **DC motor speed** values, to an **output queue** via the **UART protocol**.
        * **Purpose:** Ensures the control process runs continuously, maintaining **real-time data updates** and synchronization between the Jetson and the Pico W.
 

# <div align="center">![HOME](../../../other/img/home.png)[Return Home](../../../)</div>  
