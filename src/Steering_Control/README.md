<div align=center> <img src="../../other/img/logo.png" width=300 alt=" logo"> </div>

## <div align="center">Steering Control Overview-轉向控制概述</div> 

 - ### Vehicle steering control-車輛轉向控制
    ### 中文:
    1. **方向判斷**:
        * 系統使用 **Jetson Orin Nano 控制板**讀取 **CSI 攝影鏡頭的影像畫面**，並透過設定的**感興趣區域 (ROI4)** 來偵測賽道上的**橘線與藍線**，進而決定車輛應執行**左轉或右轉**。
        * **右轉決策：** 若偵測到**橘線的輪廓面積 (maxO)** **超過預設閾值 (> 110)**，系統則判斷需要執行**右轉 ("right")**。
        * **左轉決策：** 若偵測到**藍線的輪廓面積 (maxB)** **超過預設閾值 (> 110)**，系統則判斷需要執行**左轉 ("left")**。
    2. **彎道進入訊號**:
        * **條件判斷：** 一旦系統**確認了預定的轉向方向**，並且**偵測到對應的轉彎標線**（例如，若決定執行右轉，則需滿足 **`maxO > 100`** 的條件），系統即判定需進入轉彎。
        * **旗標設置：** 隨後，系統會設置主要的**轉向訊號旗標 (`tSignal = True`)**，同時根據方向設置 **`rTurn`（右轉）或 `lTurn`（左轉）旗標**，以通知控制邏輯開始執行轉彎操作。
    3. **轉彎輔助偵測與避障機制**:
        * **觸發條件：** 當**任一側牆壁輪廓面積**（**`leftArea` (來自 ROI1) 或 `rightArea` (來自 ROI2)**）**超過預設閾值 1000** 時，系統判斷車輛過於靠近牆壁。
        * **動態 ROI 調整：** 系統會自動啟動一個**較小的、高靈敏度的感興趣區域 (ROI5)**，其座標為 `[270, 110, 370, 150]`，專門用於**強化偵測黑色與洋紅色輪廓**。
        * **外牆接觸反應：** 一旦 **ROI5 偵測到與外牆接觸**時，系統會立即**增大轉向角度**，使車輛更快速地轉彎，以**防止車體與外牆發生碰撞**。
    ### 英文:
    1. **Direction Determination**:
        * The system uses the **Jetson Orin Nano controller** to read the image stream from the **CSI camera**. It then utilizes the designated **Region of Interest (ROI4)** to detect the **orange and blue lines** on the track, thereby determining whether the vehicle should execute a **left turn or a right turn**.
        * **Right Turn Decision:** If the **contour area of the detected orange line (maxO)** **exceeds the preset threshold (> 110)**, the system decides that a **right turn ("right")** is required.
        * **Left Turn Decision:** If the **contour area of the detected blue line (maxB)** **exceeds the preset threshold (> 110)**, the system decides that a **left turn ("left")** is required.
    2. **Curve Entry Signal**:
        * **Condition Check:** Once the system **confirms the intended turning direction** and **detects the corresponding turn line marker** (e.g., if a right turn is intended, the condition **`maxO > 100`** must be met), the system determines that curve entry is necessary.
        * **Flag Setting:** Subsequently, the system sets the primary **turning signal flag (`tSignal = True`)**, and simultaneously sets the **`rTurn` (right turn) or `lTurn` (left turn) flag** according to the direction, signaling the control logic to begin the turning maneuver.
    3. **Curve Auxiliary Detection and Avoidance Mechanism**:
        * **Trigger Condition:** When the **contour area of the wall on either side** (**`leftArea` (from ROI1) or `rightArea` (from ROI2)**) **exceeds the preset threshold of 1000**, the system determines that the vehicle is too close to the wall.
        * **Dynamic ROI Adjustment:** The system automatically activates a **smaller, high-sensitivity Region of Interest (ROI5)**, with coordinates `[270, 110, 370, 150]`, specifically designed to **enhance the detection of black and magenta contours**.
        * **Outer Wall Contact Reaction:** As soon as **ROI5 detects contact with the outer wall**, the system immediately **increases the steering angle**, causing the vehicle to turn more sharply to **prevent the vehicle body from colliding with the outer wall**.
    - program code:
    ```
    if turnDir == "none":
      if maxO > 110:
        turnDir = "right"
      elif maxB > 110:
        turnDir = "left"
    if (turnDir == "right" and maxO > 100) or (turnDir == "left" and maxB > 100):
      t2 = t
      if t2 == 7 and not pillarAtStart:
        ROI3[1] = 110
      if cPillar.area != 0 and ((leftArea > 1000 and turnDir == "left") or (rightArea > 1000 and turnDir == "right")):
        ROI5 = [270, 110, 370, 150]
      if turnDir == "right":
        rTurn = True
    else:
      lTurn = True
      if t == 0 and pillarAtStart == -1:
        pillarAtStart = True if ((startArea > 2000 and startTarget == greenTarget) or (startArea > 1500 and startTarget == redTarget)) else False
        tSignal = True
      elif (turnDir == "left" and maxO > 100) or (turnDir == "right" and maxB > 100):
        if t2 == 11:
          s = 2
          sTime = time.time()
    ```
     <div align=center>
        <table>
        <tr>
        <th>Blue Line Detected in ROI4(ROI4偵測到藍線)</th>
        <th>Orange Line Detected in ROI4(ROI4偵測到橘線)</th>
        </tr><tr>
        <td><img src="./img/Blue_Line_Recognition.png" width=400 height="400"></td>
        <td><img src="./img/Orange_Line_Recognition.png" width="400" height="395" ></td>
        </tr>
        </table>
        </div>
     <div align=center>
        <table>
        <tr>
        <th>Performing Avoidance Maneuvers Upon Traffic Signal Detection(偵測到交通號誌後執行規避操作)</th>
        <th>Performing Turns Without Traffic Signal Detection(無偵測交通號誌即可進行轉彎)</th>
        </tr><tr>
        <td><img src="./img/Traffic_Signal_Evaluation_and_Steering_Control.png" width=400 height="400"></td>
        <td><img src="./img/Unsignalized_Intersection_Steering_Control.png" width="400" height="400"></td>
        </tr>
        </table>
        </div>
     <div align=center>
        <table>
        <tr>
        <th>Activation of Auxiliary ROI5 Triggered by Inner Wall Detection During Turning Mode(轉彎模式下，內壁偵測觸發輔助 ROI5 開啟)</th>
        <th>Executing Evasion Maneuver Upon Outer Wall Detection by ROI5(ROI5 偵測到外牆後執行規避動作)</th>
        </tr><tr>
        <td><img src="./img/Inner_Side_Obstacle_Avoidance_and_Steering_Control.png" width="400" height="400"></td>
        <td><img src="./img/ROI_5_assisted_turning_detection.png" width=400 height="400"></td>
        </tr>
        </table>
        </div>   

  
</div> 

- ### Vehicle Obstacle Avoidance Control - 車輛避障控制

  ### 中文:
   * 根據任務需求，當車輛偵測到**紅色交通號誌**或**紅色障礙物**時，系統將觸發**向右繞行機動 (Right Evasion Maneuver)**。相反，當偵測到**綠色障礙物**時，系統會觸發**向左繞行機動 (Left Evasion Maneuver)**。 
   * 當車輛移動時，**攝影機**會將**視訊流**傳輸到主控制器（**Jetson Orin Nano**）。控制器隨後進行**影像處理**，以確定**目標柱子**在畫面中的**理想 X 座標位置**。這些視覺數據（特別是 X 座標）能夠協助控制器**確定物體在空間中的位置和距離**，從而實現**精確的導航和避障**。
   * 在拍攝的影像上，系統利用 **`boundingRect()` 函式**在目標輪廓周圍**繪製一個矩形**。該函式會傳回矩形**左上角的 X 和 Y 座標**。將其應用於訊號柱的輪廓時，這些座標即可用於**確定該柱子在畫面中的精確位置**。

  - 車輛透過以下步驟完成避開交通號誌的操作：
    1. 如果螢幕上出現兩根或多根柱子，我們會計算螢幕底部中心點到柱子底部中心點的距離。我們使用距離最近的柱子來計算伺服角度。
    2. 根據柱子的 x 座標與目標 x 座標的差值進行 PD 控制計算。綠色立柱的目標 x 座標設定 430，紅色立柱的目標 x 座標設定 110。
    3. 在偵測到柱子的同時，若左側或右側牆壁的面積過大，我們會取消當前柱子的選擇，改由牆壁面積決定轉向角度。這樣可以讓車子朝中間轉動，避免撞上牆壁。

  - 車輛透過以下三個主要步驟，完成避開交通號誌（色柱）的精確操作：
    1.  **目標柱子選擇與距離計算：**
        * 如果攝影機畫面中出現**兩根或多根柱子**，系統會計算**螢幕底部中心點**到**每根柱子底部中心點**的距離。
        * 系統將選定**距離車輛最近的柱子**作為當前避障的目標，並以此柱子的數據來計算伺服馬達所需的轉向角度。
    2.  **基於 PD 控制的轉向決策：**
        * 轉向控制採用 **PD 控制演算法**。系統根據**柱子的 X 座標**與**預設目標 X 座標**之間的差值（即誤差 `error`）進行計算。
        * **目標 X 座標設定：**
          * **綠色立柱**的目標 X 座標設定為 **430**。
          * **紅色立柱**的目標 X 座標設定為 **110**。
    3.  **安全避牆優先級機制：**
        * **優先級判斷：** 在偵測到柱子的同時，系統會**持續監測左側或右側牆壁的輪廓面積**。
        * **安全接管：** 若任一側牆壁的面積**過大**（達到危險閾值），系統會**取消當前柱子的選擇**，將控制優先級**切換至牆壁避障**。轉向角度將改由牆壁面積的偏差量決定，使車輛**朝向車道中心轉動**，以**避免撞上牆壁**，確保安全。
   ### 英文:
  * According to the mission requirements, when the vehicle detects a **Red Traffic Sign/Obstacle**, the system triggers a **Right Evasion Maneuver**.Conversely, when a **Green Obstacle** is encountered, the system triggers a **Left Evasion Maneuver**.
  * As the vehicle moves, the **camera** transmits the **video stream** to the main controller (**Jetson Orin Nano**).The controller then performs **image processing** to determine the **ideal X-coordinate position** of the **target pillar** within the image frame.This visual data (specifically the X-coordinate) assists the controller in **determining the object's spatial position and distance**, enabling **precise navigation and obstacle avoidance**.
  * On the captured image, the system uses the **`boundingRect()` function** to **draw a rectangle** around the target contour.This function returns the **X and Y coordinates of the rectangle's top-left corner**. When applied to the signal pillar's contour, these coordinates are then used to **determine its precise position** within the frame.
  
- The vehicle completes the precise maneuver to avoid traffic signals (colored pillars) through the following three main steps:
    
    1.  **Target Pillar Selection and Distance Calculation:**
        * If **two or more pillars** appear on the camera screen, the system calculates the distance from the **center point of the screen's bottom edge** to the **center point of the bottom of each pillar**.
        * The system selects the **pillar closest to the vehicle** as the current avoidance target, using its data to calculate the required servo motor steering angle.
    2.  **PD Control-Based Steering Decision:**
        * Steering control employs a **PD Control Algorithm**. The system calculates the angle based on the difference (error) between the **pillar's X-coordinate** and its **predetermined target X-coordinate**.
        * **Target X-coordinate Settings:**
          * The target X-coordinate for the **Green Pillar** is set to **430**.
          * The target X-coordinate for the **Red Pillar** is set to **110**.
    3.  **Safety Wall Avoidance Priority Mechanism:**
        * **Priority Check:** Simultaneously while detecting pillars, the system **continuously monitors the contour area of the left or right side walls**.
        * **Safety Override:** If the area of either side wall is **excessively large** (reaching a critical threshold), the system **cancels the current pillar selection** and **switches the control priority to wall avoidance**. The steering angle is then determined by the wall area deviation, causing the vehicle to **steer towards the center of the lane** to **prevent collision with the walls**, thereby ensuring safety.
    
<div align=center>

  |Recognize the color of traffic signal blocks.|The color and X, target coordinates of traffic signal blocks.|
  |:---:|:---:|
  |<div align="center"> <img src="./img/Detecting_nearby_obstacles.png"  alt="Detecting_nearby_obstacles"></div>|<div align="center"> <img src="./img/Obstacle_XY_coordinates.png"  alt="Obstacle_XY_coordinates"></div>|

# <div align="center">![HOME](../../other/img/home.png)[Return Home](../../)</div>  


