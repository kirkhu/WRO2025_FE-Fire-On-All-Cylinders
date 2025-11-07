<div align=center> <img src="../../../other/img/logo.png" width = 300 alt=" logo"> </div>

## <div align="center">Obstacle_Challenge Code Overview</div> 

### **任務賽問題分解與控制器職責分配** ⚙️

根據 **Jetson Orin Nano** 與 **Raspberry Pi Pico W** 等控制器的技術特性，我們針對任務挑戰賽（Obstacle Challenge rounds）所面臨的問題進行了**功能分解及職責分配**。

#### **1. Jetson Orin Nano（主控單元）的職責**
這次，**Jetson Orin Nano** 除了具備**影像辨識**和**方向偵測**功能外，還**新增了障礙物辨識功能**。憑藉其強大的運算能力，Jetson Orin Nano 能夠：
* 進行**即時影像分析與處理**。
* **精準偵測車輛行駛方向**。
* **快速辨識並避開路徑上的障礙物**，進而提升自動駕駛的**穩定性與安全性**。

#### **2. Raspberry Pi Pico W（輔助單元）的職責**
此外，這次 **Raspberry Pi Pico W** 不僅要控制**直流馬達轉速**和**車輛轉向**，還新增了**使用紅外線感測器偵測車輛與牆壁距離**的功能。憑藉其**高效的 GPIO 控制能力**，樹莓派 Pico W 可以：
* 進行**精確的距離測量**和**硬體管理**。
* **確保車輛安全停放在停車場內**，並**保持適當的安全距離**。


### **Obstacle Challenge Problem Decomposition and Controller Responsibility Allocation** 

Based on the technical characteristics of controllers like the **Jetson Orin Nano** and the **Raspberry Pi Pico W**, we decomposed the problems faced in the Obstacle Challenge rounds and **allocated functional responsibilities**.

#### **1. Responsibilities of the Jetson Orin Nano (Main Control Unit)**
This time, the **Jetson Orin Nano** not only includes **image recognition** and **direction detection** capabilities but has also **added obstacle recognition functionality**. Leveraging its powerful computing capability, the Jetson Orin Nano can:
* Perform **real-time image analysis and processing**.
* **Precisely detect the vehicle's direction of travel**.
* **Quickly identify and avoid obstacles on the path**, thereby enhancing the **stability and safety** of autonomous driving.

#### **2. Responsibilities of the Raspberry Pi Pico W (Auxiliary Unit)**
Furthermore, this time the **Raspberry Pi Pico W** is not only tasked with controlling the **DC motor speed** and **vehicle steering** but also requires the use of **infrared sensors to detect the distance between the vehicle and the walls**. Leveraging its **efficient GPIO control capability**, the Raspberry Pi Pico W can:
* Perform **precise distance measurement** and **hardware management**.
* **Ensure the vehicle is safely parked within the parking lot** and **maintains an appropriate safe distance**.


 - ### Jetson Orin Nano library-Jetson Orin Nano 庫
    ### 中文:
    - 影像辨識、影像處理與視覺辨識函式等功能已整合到`functions.py`模組中，可直接導入使用。這些模組的功能如下：


    ### 英文:
    **All functions related to image recognition, image processing, and key visual identification** have been **highly integrated** into the **[function.py](../common/function.py) module** and can be directly **imported and called** by the higher-level program. The **specific functionalities** of these modules are outlined as follows:

    - `display_roi()`此函數的作用是在影像上繪製多個感興趣區域 (ROI) 的邊界框。它接收一個影像 (img)、一個包含多個 ROI 座標的列表 (ROIs)，以及繪製顏色 (color)。它透過繪製四條線段來組成每個 ROI 的矩形邊界，然後返回被標記過的影像。
    - The **`display_roi()` function** is designed to **visualize** multiple **Regions of Interest (ROIs)** on an image. It accepts the **source image (`img`)**, a **list containing the coordinates of multiple ROIs (`ROIs`)**, and the **drawing color (`color`)** for the boundary boxes as input parameters.Its mechanism involves **drawing four line segments** to form the **rectangular boundary** for each ROI. Upon completion, the function **returns** the processed image marked with the boundary boxes.
      ```
      def display_roi(img, ROIs, color):
      for ROI in ROIs:
          img = cv2.line(img, (ROI[0], ROI[1]), (ROI[2], ROI[1]), color, 4)
          img = cv2.line(img, (ROI[0], ROI[1]), (ROI[0], ROI[3]), color, 4)
          img = cv2.line(img, (ROI[2], ROI[3]), (ROI[2], ROI[1]), color, 4)
      ```
    - **`find_contours()` 函式**旨在**從影像中偵測特定色彩範圍的物體輪廓**。此函式首先**擷取**影像中的**感興趣區域 (ROI)**。接著，它利用 **LAB 顏色空間**與預設的 **`lab_range` 參數**進行**顏色閾值分割**，將該區域轉換為**二值遮罩 (mask)**。為**優化輪廓的精確度**，程式會對遮罩執行**形態學操作**，即**腐蝕 (erode)** 與**膨脹 (dilate)** 處理。最終，函式會從處理完成的遮罩中**提取外部輪廓**並將其**返回**。
    - The **`find_contours()` function** is used to **detect object contours** within a specific color range in an image.It first **extracts** the **Region of Interest (ROI)** portion of the image. It then performs **color thresholding** using the **LAB color space** and the predefined **`lab_range` parameters** to convert this area into a **binary mask**. To **enhance contour accuracy**, the function performs **morphological operations**—specifically **erosion** and **dilation**—on the mask. Finally, the function **extracts the external contours** from the processed mask and **returns** them.
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
    - `max_contour()` 函式旨在從輸入的輪廓列表 (contours) 中，識別並選取面積最大的有效目標輪廓。此函式首先**篩選**掉所有**面積小於 150 的雜訊輪廓**。對於符合標準的輪廓，它會計算其**面積**以及相對於**原始影像的中心底部座標 (`maxX`, `maxY`)**。最終，函式會**返回**最大面積的數值、其對應的校正座標，以及該**輪廓物件本身**，作為車輛進行**循跡導航或目標識別**的關鍵依據。
    - The **`max_contour()` function** is used to **identify and select the largest valid target contour** from an input **list of contours (`contours`)**.The function first **filters out** all **noise contours** with an **area less than 150**. For the qualified contours, it calculates their **area** and the **center-bottom coordinates (`maxX`, `maxY`)** relative to the original image. Finally, the function **returns** the value of the largest area, its corresponding corrected coordinates, and the **contour object itself**, serving as the key basis for the vehicle's **line following or target recognition**.
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
    - **`pOverlap()` 函式**用於在影像的**特定感興趣區域 (ROI)** 中，**偵測包含黑色和洋紅色組合的複合輪廓**，主要應用於牆壁或特殊標記的識別。此函式根據布林參數 `add` 的值，來決定如何處理這兩種顏色的區域：
      1.  **若 `add=True`：** 函式會將**黑色區域與洋紅色區域進行邏輯合併 (Union)**，以尋找融合後的複合輪廓。
      2.  **若 `add=False`：** 函式會尋找**純黑色區域**，即**從黑色區域中減去 (Subtract) 被洋紅色覆蓋的部分**。
    - 無論選擇哪種組合方式，函式都會對最終產生的遮罩執行**運算（通常指腐蝕和膨脹）**處理來**優化輪廓形狀**，最後**提取並返回外部輪廓**。
    - The **`pOverlap()` function** is used to **detect composite contours** that involve a combination of black and magenta within a **specific Region of Interest (ROI)** in an image, primarily intended for the detection of walls or special markers.The function determines how to combine these two color regions based on the boolean parameter `add`:
      1.  **If `add=True`:** The function **logically combines (Union)** the black and magenta areas to find the resulting composite contours.
      2.  **If `add=False`:** The function searches for the **pure black area**, which means **subtracting the portion covered by magenta from the black area**.
    - In either scenario, the function performs **morphological operations (implied erosion and dilation)** on the resulting mask to **optimize the contour shape**. Finally, it **extracts and returns the external contours**.
      ```
      def pOverlap(img_lab, ROI, add=False):
          x1, y1, x2, y2 = ROI
          seg = img_lab[y1:y2, x1:x2]
          from masks import rBlack, rMagenta
          loB, hiB = np.array(rBlack[0]),   np.array(rBlack[1])
          loM, hiM = np.array(rMagenta[0]), np.array(rMagenta[1])
          mB = cv2.inRange(seg, loB, hiB)
          mM = cv2.inRange(seg, loM, hiM)
          if add:
              mask = cv2.add(mB, mM)
          else:
              mask = cv2.bitwise_and(mB, cv2.bitwise_not(mM))
          k_open  = np.ones((3,3), np.uint8)
          k_close = np.ones((7,7), np.uint8)
          mask = cv2.morphologyEx(mask, cv2.MORPH_OPEN,  k_open,  iterations=1)
          mask = cv2.morphologyEx(mask, cv2.MORPH_CLOSE, k_close, iterations=1)
          contours = cv2.findContours(mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)[-2]
          return contours
      ```



 - ### Overview of the Jetson Orin Nano Obstacle Challenge Code - Jetson Orin Nano 障礙挑戰程式碼概述
   - #### Obstacle Challenge Code Jetson Orin Nano Library - 障礙挑戰程式碼程式 Jetson Orin Nano 函式庫
    
      ```
      import os, sys                                                          
      sys.path.append(os.path.abspath(os.path.dirname(__file__)))                      
      import cv2, time, math, sys, numpy as np                                         
      from masks import rMagenta, rRed, rGreen, rBlue, rOrange, rBlack                 
      from functions_jetson import * 
      ```  

   - #### Introduction to Running Programs on the Jetson Orin Nano Controller: - Jetson Orin Nano 控制器程式運作簡介：

      - ##### [jetson_Orin_Nano_final.py](./jetson_orin_nano_final.py)
      ### 中文:
        - 自駕車系統的啟動流程採**主從協作機制**：Jetson Orin Nano 啟動後，**樹莓派 Pico W** 即進入**硬體待命狀態**。當使用者按下**實體啟動開關**後，Jetson Orin Nano 接收到啟動訊號，並發送**高電平訊號**以啟動其核心程式 **`jetson_Orin_Nano_final.py`**。此主程式全面負責**綜觀調度**整個自動駕駛任務的執行流程。其核心功能涵蓋**避開牆壁（循牆導航）**、**精確的方向控制（轉向決策）**、**動態的障礙物躲避**以及**圈數計數**。程式運行後，便透過 **UART 介面**持續將計算出的**舵機（轉向）**和**直流馬達（驅動）**數據傳送給樹莓派 Pico W 執行，從而**保障行駛的穩定性與任務的完整性**，確保車輛按預定計畫完成所有競賽任務。

        - 程式啟動之初，車輛會優先執行**停車區出發模式 (Parking Lot Exit Mode)**。在此模式下，避障系統會**即時計算**偵測到的**柱子或邊牆範圍**，並將此範圍轉換為**伺服馬達的轉向角度**。隨後，系統利用此角度進行 **PD 轉向控制**，以確保車輛能**穩定地離開停車區**，並**避免與牆壁發生任何碰撞**。當車輛接近**轉彎區域**時，系統會**偵測賽道上的藍色或橘色線條**，以作為**切換至轉彎模式**的判斷依據。
        
        - 在**直線循跡模式 (Straight Line Following Mode)** 中，系統會優先以**紅色與綠色柱子**（透過 `detect_color_final()` 函式計算出的**中心偏差**）作為**主要的轉向校正依據**。僅當**未檢測到任何色塊**時（判斷條件為 `cPillar.area == 0`），系統才會啟用**兩側牆壁的輪廓面積差異**，將其作為**輔助性的循跡校正參考**。
        
        - 在**直線循跡模式**下，系統會持續監測**影像感興趣區域 (ROI4)**，一旦偵測到賽道上的**藍色或橘色線條**，即以此觸發訊號，**設定 `rTurn` 或 `lTurn` 旗標**，**進入轉彎模式**。轉彎模式啟動後，**伺服舵角即被鎖定於固定值**。而**判斷轉彎是否完成**並**切換回直線循跡模式**的完整依據是：車輛在轉彎期間持續利用**視覺看牆**的方式，確認**內牆的輪廓面積**是否**大於預設閾值**（例如：**4000**）。一旦內牆面積確認符合此條件，系統即判定轉彎結束，並**立即返回直線循跡模式**。
        ### 英文:
        - The startup process of the self-driving car system employs a **master-slave collaboration mechanism**: After the Jetson Orin Nano boots up, the **Raspberry Pi Pico W** immediately enters a **hardware standby state**. Upon the user pressing the **physical start switch**, the Jetson Orin Nano receives the activation signal and transmits a **high-level signal** to initiate its core program, **`jetson_Orin_Nano_final.py`**.This main program is entirely responsible for **supervising and coordinating** the execution flow of the entire autonomous driving mission. Its core functionalities encompass **wall avoidance (wall following navigation)**, **precise direction control (steering decision-making)**, **dynamic obstacle evasion**, and **lap counting**. Once running, the program continuously transmits the calculated **servo motor (steering)** and **DC motor (drive)** data to the Raspberry Pi Pico W via the **UART interface** for execution, thereby **guaranteeing driving stability and mission integrity** and ensuring the vehicle completes all competition tasks according to the predetermined plan.

        - Upon program startup, the vehicle first executes the **Parking Lot Exit Mode**. In this mode, the obstacle avoidance system **calculates in real-time** the range of the detected **pillars or side walls**, converting this range into a **steering angle for the servo motor**. Subsequently, this angle is used for **PD steering control** to ensure the vehicle **stably exits the parking zone** and **avoids any collision with the walls**. As the vehicle approaches a **turning area**, the system will **detect the blue or orange lines on the track** to serve as the criterion for **switching to the turning mode**.

        - In the **Straight Line Following Mode**, the system prioritizes using the **red and green pillars** (specifically, the **center deviation** calculated by the `detect_color_final()` function) as the **primary reference for steering correction**. Only when **no color blocks are detected** (under the condition `cPillar.area == 0`) does the system activate the **area difference of the side walls** as an **auxiliary reference for line following correction**.

        - While in **Straight Line Following Mode**, the system continuously monitors the **Region of Interest (ROI4)** for the detection of **blue or orange lines** on the track. This detection serves as the trigger signal, **setting the `rTurn` or `lTurn` flag to initiate the turning mode**.Once the turning mode is activated, the **servo steering angle is locked to a fixed value**. The complete criterion for **determining whether the turn is complete** and **switching back to the straight line following mode** is as follows: The vehicle continuously uses **visual wall perception** during the turn to confirm whether the **contour area of the inner wall** is **greater than a preset threshold** (e.g., **4000**). Once the inner wall area is confirmed to satisfy this condition, the system determines the turn is complete and **immediately returns to the straight line following mode**.

      __Program operation flow__ - 程式運行流程
        ### 中文:
        - `jetson_Orin_Nano_final.py` 程式啟動後，首先執行**系統變數的初始化**。隨後，程式進入**主循環 (Main Loop)**，在循環中持續調用 `find_contours` 與 `max_contour` 函式來**獲取實時的視覺感知數據**。接著，系統依據**當前的運行狀態**進入不同的**條件分支**，以執行相應的**控制邏輯與決策**。在每個運行週期結束時，程式會將 Jetson Orin Nano 計算出的**直流馬達驅動值**、**伺服馬達轉向角度**以及**當前車輛狀態**，**打包成二進位數據格式**，並透過 **UART 介面**發送給 Raspberry Pi Pico W，由其進行**底層的硬體驅動控制**。
        ### 英文:
        - Upon execution, the `jetson_Orin_Nano_final.py` program first performs the **initialization of all system variables**. Subsequently, the program enters a **Main Loop**, where it continuously calls the `find_contours` and `max_contour` functions to **acquire real-time visual perception data**. The system then branches into different **conditional blocks** based on the **current operating status** to execute the corresponding **control logic and decisions**.At the conclusion of each cycle, the program **packages** the calculated **DC motor drive values**, **servo motor steering angle**, and the **current vehicle status** into a **binary data format**. This package is then transmitted via the **UART interface** to the Raspberry Pi Pico W for **low-level hardware drive control**.

   - ##### Jetson Orin Nano Controller Main Program Flowchart Overview - Jetson Orin Nano控制器程式流程圖
     ![Obstacle_Challenge_Jetson_nano](./img/FE-obstacle_challenge_Jetson_nano.jpg)

 - ### Raspberry Pi Pico W Obstacle Challenge Code Overview - 樹莓派 Pico W 障礙挑戰代碼概述
   - ####  Raspberry Pi Pico W Function Library for the Obstacle Challenge Program - 障礙挑戰程式碼程式 Raspberry Pi Pico W函式庫
    
      ```
      from machine import Pin, PWM, UART,I2C,time_pulse_us
      import time
      import struct
      ```  
     
   - #### Introduction to running programs on the Raspberry Pi Pico W controller:-樹莓派 Pico W 控制器程式運作簡介：
      ### 中文:

      - **`pico_main_final.py` 程式**運行於 **Raspberry Pi Pico 控制器**上，擔任自駕車系統的**底層中間控制單元**，負責**管理直流馬達和伺服馬達的驅動與運行**。該程式透過 **UART 介面**接收來自 **Jetson Orin Nano** 控制器的**即時計算結果**，並依此**精確控制後輪直流馬達的轉速**及**前輪伺服馬達的轉向角度**，同時也負責**監控車輛狀態參數**。

      - 在控制後輪直流馬達時，我們選用 **L293D 驅動晶片**。系統透過**調節 PWM 訊號的佔空比**來精確控制電壓輸出，從而**實現後輪直流馬達的轉速控制**。此外，藉由設定 L293D 晶片上的**兩個控制引腳（20 和 21）的高低電平邏輯**，我們能進一步**控制後輪直流馬達的正向與反向轉動**。

      - 在控制前輪伺服馬達時，我們**直接利用 PWM 訊號的佔空比**來**調節輸出脈衝的寬度**，從而**精確控制伺服馬達的轉向角度**。PWM 訊號**佔空比的微小變化**與伺服馬達的**不同角度設定**直接對應，確保了**車輛轉向的精準度**。

      - 當程式運行至 **`mode=3`** 時，系統即取得直流馬達的控制權，開始**轉向前行**。車輛會持續前進，直到**紅外線感測器偵測到牆壁**，隨即切換至**後退轉彎**，並開始**循跡追蹤停車區域的洋紅色標記**。在洋紅色循跡過程中，車輛將持續沿著標記行駛，直到**洋紅色輪廓面積小於閾值 100**。此時，系統會利用**牆壁循跡機制向前移動一段距離**（例如：100 個單位），隨後運用**陀螺儀**進行**精確的角度轉彎**，最終駛入停車區，以**確保最終停車定位的精準性**。
      ### 英文:
      - ##### [pico_main_final.py](./pico_main_final.py)
        - The **`pico_main_final.py` program** runs on the **Raspberry Pi Pico W controller**, serving as the **low-level intermediate control unit** for the autonomous vehicle system. It is responsible for **managing the drive and operation of both the DC motor and the servo motor**. The program receives **real-time calculation results** from the **Jetson Orin Nano** controller via the **UART interface**, using this data to **precisely control the rotational speed of the rear DC motor** and the **steering angle of the front servo motor**, while also being responsible for **monitoring vehicle status parameters**.
        -  When controlling the rear DC motor, we utilize the **L293D driver chip**. The system achieves **rotational speed control of the rear DC motor** by precisely regulating the output voltage through **adjusting the PWM signal's duty cycle**. Furthermore, by setting the **high/low logic levels of the two control pins (20 and 21)** on the L293D chip, we can also control the **forward and reverse rotation of the rear DC motor**.
        - When controlling the front servo motor, we **directly utilize the PWM signal's duty cycle** to **adjust the width of the output pulse**, thereby **precisely controlling the servo motor's steering angle**. The **slight variation in the PWM signal's duty cycle** directly corresponds to **different angle settings** of the servo motor, which ensures the **accuracy of the vehicle's steering**.
        - When the program operates in **`mode=3`**, the system assumes control of the DC motor and initiates a **forward turn**. The vehicle continues its forward movement until the **infrared sensor detects a wall**, immediately switching to a **reverse turn** and commencing **line tracking of the magenta marker** for the parking zone.During magenta tracking, the vehicle persists in following the marker until the **magenta contour area is less than the threshold (100)**. At this point, the system utilizes the **wall-following mechanism to move forward by a set distance** (e.g., 100 units/steps), subsequently employing the **gyroscope** to execute a **precise angle turn** and finally entering the parking bay, thereby **ensuring the accuracy of the final parking position**.
      

      __Program operation flow__-程式運行流程
        ### 中文:
        - 當 **`pico_main_final.py` 程式啟動**時，它會立即進入**硬體等待模式**。程式將持續駐留於此狀態，直到**實體啟動按鈕被按下**。一旦按鈕觸發，**Jetson Orin Nano 控制板**隨即發送啟動訊號給 Pico W 控制板，此時 `pico_main_final.py` 便**進入主循環**，開始**持續接收** Jetson Orin Nano 透過 **UART 介面**傳送來的控制數據，並執行常規的馬達驅動任務。特別地，當接收到的**狀態參數為 `mode=3`** 時，**Pico W 將接手車輛的完整控制權**，並獨立執行**泊車（入庫）操作**。

        ### 英文:
        - Upon the **start of the `pico_main_final.py` program**, it immediately enters a **hardware waiting mode**. The program remains in this state until the **physical start button is pressed**. Once triggered, the **Jetson Orin Nano controller** sends an activation signal to the Pico W controller. At this point, `pico_main_final.py` **enters its main loop**, beginning to **continuously receive** control data transmitted by the Jetson Orin Nano via the **UART interface**, and executes routine motor driving tasks.Specifically, when the received **status parameter is `mode=3`**, the **Pico W takes over the vehicle's full control authority** and independently executes the **parking (bay entry) operation**.

    - ##### Raspberry Pi Pico W Controller Program Flowchart-樹莓派 Pico W 控制器的程式流程圖
        ![FE-obstacle_challenge_Pico](./img/FE-obstacle_challenge_Pico.jpg)

    - #### 1. `set_servo_angle()`：伺服馬達角度設定 (Pico W 職責)
      * **功能：** 負責將輸入的**角度值（範圍通常為 $\pm 180$ 度）**，計算並**轉換**成伺服馬達所需的 **PWM 佔空比範圍（0 到 65535）**。
      * **輸出：** 將計算出的 PWM 訊號精確地輸出到**前輪伺服馬達**，實現精準轉向。

    - #### 2. `control_motor()`：直流馬達速度與方向控制 (Pico W 職責)
      * **功能：** 接收一個介於 **-100 到 100 之間**的數值作為輸入，用於同時控制速度和方向。
      * **PWM 轉換：** 取該數值的**絕對值**，將其轉換為**直流馬達的 PWM 佔空比**（代表轉速）。
      * **方向控制：** 根據輸入數值的**正負符號**，設定驅動引腳的高低電平狀態，以實現馬達的**正轉、反轉或停止**。

    - #### 3. `run_encoder_Auto()`：編碼器輔助的自動運行 (Pico W 輔助)
      * **功能：** 在此函數中，系統通常呼叫 **`run_encoder()`** 執行基於編碼器計數的精確移動。
      * **控制穩定性：** 在此操作期間，**伺服馬達的角度會被設定為一個固定值**，以確保車輛在移動過程中，**位置和方向的穩定控制**。

    - #### 4. `pump_uart()`：UART 控制數據傳輸 (Jetson 職責)
      * **功能：** 此函式運行於 **Jetson Orin Nano 控制器**上，透過 **UART 協定**，將最新的控制參數，包括**更新後的模式 (mode)**、**伺服馬達角度** 和**直流馬達速度**數值，**傳送到輸出佇列**。
      * **目的：** 確保控制流程持續運行，並維持資料在 Jetson 與 Pico W 之間的**即時更新**與同步。

    - #### 5. `extract_magenta_from_json()`：洋紅色數據傳輸 (Jetson 職責)
      * **功能：** 此函式運行於 **Jetson Orin Nano 控制器**上，透過 **UART 協定**，將視覺系統擷取到的**洋紅色牆壁面積**、**X 座標**和**Y 座標**數值，**傳送到輸出佇列**。
      * **目的：** 確保流程持續運行，為 Pico W 執行複雜的**泊車入庫**或**視覺輔助**任務提供即時的數據輸入。

    - #### 1. `set_servo_angle()`: Servo Motor Angle Setting (Pico W Responsibility)
      * **Function:** Responsible for calculating and **converting** the input **angle value (typically within the $\pm 180^\circ$ range)** into the required **PWM duty cycle range (0 to 65535)** for the servo motor.
      * **Output:** Outputs the calculated PWM signal precisely to the **front servo motor** for accurate steering.

    - #### 2. `control_motor()`: DC Motor Speed and Direction Control (Pico W Responsibility)
      * **Function:** Accepts a numerical value ranging from **-100 to 100** as input, controlling both speed and direction simultaneously.
      * **PWM Conversion:** Takes the **absolute value** of the number and converts it into the **PWM duty cycle for the DC motor** (representing the rotational speed).
      * **Direction Control:** Based on the **sign (positive/negative)** of the input value, it sets the high/low state of the driver pins to achieve **forward rotation, reverse rotation, or motor stop**.

    - #### 3. `run_encoder_Auto()`: Encoder-Assisted Automatic Running (Pico W Support)
      * **Function:** Within this function, the system typically calls **`run_encoder()`** to execute precise movement based on encoder counts.
      * **Control Stability:** During this operation, the **servo motor angle is fixed to a set value** to ensure **stable control over the vehicle's position and direction**.

    - #### 4. `pump_uart()`: UART Control Data Transmission (Jetson Responsibility)
      * **Function:** This function executes on the **Jetson Orin Nano controller**. It utilizes the **UART protocol** to transmit the latest control parameters, including the **updated mode**, **servo angle**, and **DC motor speed** values, to an **output queue**.
      * **Purpose:** Ensures continuous control flow, maintaining **real-time data updates** and synchronization between the Jetson and the Pico W.

    - #### 5. `extract_magenta_from_json()`: Magenta Data Transmission (Jetson Responsibility)
      * **Function:** This function executes on the **Jetson Orin Nano controller**. It uses the **UART protocol** to transmit the visually acquired values for the **magenta wall area**, **X-coordinate**, and **Y-coordinate** to an **output queue**.
      * **Purpose:** Ensures continuous flow, providing real-time data input for the Pico W to execute complex **parking bay entry** or **visual assistance** tasks.

       </ol>
# <div align="center">![HOME](../../../other/img/home.png)[Return Home](../../../)</div>  
