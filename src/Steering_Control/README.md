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
        <th>Blue Line Recognition(藍線偵測)</th>
        <th>Orange Line Recognition(橘線偵測)</th>
        </tr><tr>
        <td><img src="./img/Blue Line Recognition.png" width=400 height="400"></td>
        <td><img src="./img/Orange Line Recognition.png" width="400" height="395" ></td>
        </tr>
        </table>
        </div>
     <div align=center>
        <table>
        <tr>
        <th>Turning with traffic signals(有交通號誌轉彎)</th>
        <th>Turning without traffic signals(沒有交通號誌轉彎)</th>
        </tr><tr>
        <td><img src="./img/Traffic Signal Evaluation and Steering Control.png" width=400 height="400"></td>
        <td><img src="./img/Unsignalized Intersection Steering Control.png" width="400" height="400"></td>
        </tr>
        </table>
        </div>
     <div align=center>
        <table>
        <tr>
        <th>ROI5 assists in corner detection 
        before turning(轉彎前ROI5輔助轉彎偵測)</th>
        <th>ROI 5 assisted turning detection(ROI5輔助轉彎偵測)</th>
        </tr><tr>
        <td><img src="./img/Inner Side Obstacle Avoidance and Steering Control.png" width="400" height="400"></td>
        <td><img src="./img/ROI 5 assisted turning detection.png" width=400 height="400"></td>
        </tr>
        </table>
        </div>   

  
</div> 

- ### Vehicle block avoidance control-車輛避障控制

  ### 中文:
   - 根據任務需求，當車輛偵測到紅色交通號誌遮擋時，系統觸發向右繞行機動；當遇到綠色障礙物時，它會觸發向左繞行機動。 
   - 當車輛移動時，攝影機將視訊傳送到控制器（Jetson Orin Nano），然後控制器進行影像處理以目標柱子在畫面中的理想 X 座標位置。這些數據可協助控制器確定物體的位置和距離，從而實現精確導航和避障。
   - 在拍攝的影像上繪製一個矩形，boundingRect()並傳回該矩形左上角的 x 和 y 座標。將其應用於訊號柱的輪廓時，即可用於確定其位置。

  - 車輛透過以下步驟完成避開交通號誌的操作：
    1. 如果螢幕上出現兩根或多根柱子，我們會計算螢幕底部中心點到柱子底部中心點的距離。我們使用距離最近的柱子來計算伺服角度。
    2. 根據柱子的 x 座標與目標 x 座標的差值進行 PD 控制計算。綠色立柱的目標 x 座標設定在較右側，因為車輛需由左側通過，紅色立柱則相反，目標位置偏向左側。
    3. 在偵測到柱子的同時，若左側或右側牆壁的面積過大，我們會取消當前柱子的選擇，改由牆壁面積決定轉向角度。這樣可以讓車子朝中間轉動，避免撞上牆壁。
    
   ### 英文:
  - According to task requirements, when the vehicle detects a red traffic signal block, the system triggers a rightward bypass maneuver; when it encounters a green block, it triggers a leftward bypass maneuver.
  - As the vehicle moves, the camera transmits video to the controller (Jetson Orin Nano), which then performs image processing to obtain the X and Y coordinates and the area size of objects in the frame. This data helps the controller determine the position and distance of objects for accurate navigation and obstacle avoidance.
  - Quadratic Bézier curves in red and green are drawn on the captured image to guide the vehicle toward the traffic signal and accurately position the block along the curve.
  
- The vehicle completes the traffic signal block avoidance through the following steps:
    
    1. The system detects traffic signal blocks through the camera and uses image recognition to analyze the y-coordinate, area, and color of the blocks, thereby determining the position of the block closest to the vehicle.
    2. Next, the system obtains the X-coordinate of the nearest block and compares it with the corresponding X-coordinate on the Bézier curve to calculate the X-axis deviation. The deviation is then multiplied by a preset avoidance coefficient to determine the final error value.
    3. Finally, based on the calculated error value, the servo motor's turning direction is adjusted to steer the vehicle appropriately, effectively avoiding the block and ensuring the safety and stability of its driving path.
    
<div align=center>

  |Recognize the color of traffic signal blocks.|The color and X, target coordinates of traffic signal blocks.|
  |:---:|:---:|
  |<div align="center"> <img src="./img/Detecting_nearby_obstacles.png"  alt="Detecting_nearby_obstacles"></div>|<div align="center"> <img src="./img/Obstacle_XY_coordinates.png"  alt="Obstacle_XY_coordinates"></div>|

# <div align="center">![HOME](../../other/img/home.png)[Return Home](../../)</div>  


