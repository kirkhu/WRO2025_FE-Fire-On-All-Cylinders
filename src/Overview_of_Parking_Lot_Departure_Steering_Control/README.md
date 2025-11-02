<div align=center> <img src="../../other/img/logo.png" width=300 alt=" logo"> </div>

## <div align="center">Overview of Parking Lot Departure Steering Control-停車場出發轉向控制概述</div> 

- ### Determination of the Driving direction - 行車方向的判斷
    - 在車輛從停車區啟動之前，它會利用 CSI 鏡頭擷取的畫面，並結合感興趣區域 (ROI) 來預判行車方向。此判斷邏輯是透過比較 ROI_1 和 ROI_2 的面積：若 ROI_1 面積大於 ROI_2 面積，則判定本次行車方向為順時針方向；反之，若 ROI_2 面積大於 ROI_1 面積，則判定為逆時針方向。一旦行車方向確定，車輛隨即駛出停車區，之後系統會立即偵測車道上是否存在交通標誌積木 (即紅 、綠色交通標誌)，並根據偵測到的顏色執行相應的變道 (Lane Change) 決策。

    - Before the Vehicle departs from the parking lot, it utilizes the image captured by the CSI camera and applies the Region of Interest (ROI) technique to pre-determine the Driving direction. The determination logic is based on comparing the areas of `ROI_1` and `ROI_2`: if the area of `ROI_1` is greater than the area of `ROI_2`, the current Driving direction is determined to be the clockwise direction ; conversely, if the area of `ROI_2` is greater than the area of `ROI_1`, it is determined to be the Counterclockwise direction. Once the Driving direction is confirmed, the Vehicle exits the parking lot , and the system subsequently detects the presence of traffic signs blocks (red or green traffic signs) in the lane and executes the corresponding Lane Change decision based on the detected color.

  1. **ROI 面積讀取與牆面偵測**:
    - 我們使用 $pOverlap(img_{lab}, ROI_1)$ 和 $pOverlap(img_{lab}, ROI_2)$ 兩個函數，從 $LAB$ 色彩空間影像 $img_{lab}$ 中偵測出位於左右兩側 $ROI$ 區域內的黑色區域。$pOverlap()$ 函數會進一步判斷這些黑色區域是否與品紅色標記發生重疊。此步驟的主要目的在於辨識畫面左右兩側可能出現的牆面或立柱位置，從而為後續的輪廓擷取、面積分析以及路徑判斷提供堅實的基礎依據。
  2. **ROI 輪廓的最大面積擷取**:
    - 在左右兩側的 $ROI$ 區域中，我們使用 $max\_contour(contours_{left}, ROI_1)[0]$ 和 $max\_contour(contours_{right}, ROI_2)[0]$ 兩個函數。透過 $max\_contour()$ 函式，系統能夠分別從左右兩側偵測到的輪廓中，篩選出面積最大的黑牆輪廓區域，並取得其對應的面積值與中心點資訊。

  1. **ROI Area Reading and Wall Detection**:
    - We utilize the functions `pOverlap(img_{lab}, ROI_1)` and `pOverlap(img_{lab}, ROI_2)` to detect black regions within the left and right `ROI` areas, using the `LAB` color space image `img_{lab}`. The `pOverlap()` function further determines whether these black regions overlap with the magenta markings. The primary goal of this step is to identify the positions of walls or pillars that may appear on the left and right sides of the image, thereby providing a solid basis for subsequent contour extraction, area analysis, and path determination. 

  2. **ROI Maximum Contour Area Extraction**:
    - In the left and right `ROI` areas, we utilize the two functions `max\_contour(contours_{left}, ROI_1)[0]` and `max\_contour(contours_{right}, ROI_2)[0]`. Through the `max\_contour()` function, the system can filter out the contour area of the largest black wall from the contours detected on both sides, and retrieve its corresponding area value and center point information. 

<div align=center>

  |Counterclockwise direction(逆時針方向)|Clockwise direction(順時針方向)|
  |:---:|:---:|
  |<div align="center"> <img src="./img/Counterclockwise_direction.png" width="400"  alt="Detecting_nearby_obstacles"></div>|<div align="center"> <img src="./img/clockwise_direction.png" width="400" alt="Detecting_nearby_obstacles"></div>|

</div> 

- program code:
```
        a = 0
        start_turn = 0
        while a == 0:
            rightArea = leftArea = areaFront = tArea = 0
            ok, img = cap.read()
            if not ok:
                continue
            img_lab = cv2.cvtColor(img, cv2.COLOR_BGR2Lab)
            img_lab = cv2.GaussianBlur(img_lab, (3,3), 0)

            contours_left  = pOverlap(img_lab, ROI1)
            contours_right = pOverlap(img_lab, ROI2)
            leftArea  = max_contour(contours_left,  ROI1)[0]
            rightArea = max_contour(contours_right, ROI2)[0]

            if leftArea - rightArea > 0:
                print("右轉"); start_turn = 1; a = 1
            else:
                print("左轉"); start_turn = 2; a = 1

        write(start_turn)     
```

- ### Driving Route Decision Based on Color Recognition - 顏色判斷下的行駛路線決策
  ### 中文:
    - 逆時針方向:若行車方向為逆時針方向，當車輛偵測到綠柱，則行駛於車道內側；偵測到紅柱則行駛於車道外側；若未偵測到任何柱子，則預設行駛於車道外側。
    - 順時針方向:若行車方向為順時針方向，當車輛偵測到綠柱，則行駛於車道外側；偵測到紅柱則行駛於車道內側；若未偵測到任何柱子，則預設行駛於車道外側。

    - Counterclockwise direction : If the Driving direction is Counterclockwise direction , the Vehicle will drive on the inner wall of the lane when a green pillar is detected; it will drive on the exterior walls of the lane when a red pillar  is detected. If no pillar is detected, the default is to drive on the exterior walls  of the lane.
    - Clockwise direction : If the Driving direction is clockwise direction , the Vehicle will drive on the exterior walls of the lane when a green pillar is detected; it will drive on the inner wall of the lane when a red pillar  is detected. If no pillar is detected, the default is to drive on the exterior walls  of the lane.

  1. **顏色輪廓偵測**:
    - 我們使用 find\_contours(img_{lab}, r_{Red}, ROI_3) 和 find\_contours(img_{lab}, r_{Green}, ROI_3) 這兩行代碼。透過 find\_contours() 函式，系統能夠在指定的感興趣區域 ROI_3 內，從 LAB 色彩空間影像 img_{lab} 中，分別偵測出紅色區域（r_{Red}）與綠色區域（r_{Green}）的所有輪廓（contours）。每一次偵測的結果都是一組包含多個封閉區域的輪廓列表。
  2. **偵測最近的交通號誌**:
    - 接著，我們調用 find\_best\_pillar(contours_{red}, redTarget, "red", img_{lab}) 和 find\_best\_pillar(contours_{green}, greenTarget, "green", img_{lab}) 這兩行函式。find\_best\_pillar() 函式會根據每個輪廓的大小、位置以及與目標點（redTarget / greenTarget）的遠近等條件進行綜合評估。最終回傳的 best_{red} 和 best_{green} 分別是各自顏色中評分最高、最接近可通過路線的立柱。如果畫面中沒有找到符合條件的立柱，則函式可能會回傳 None 值。

  1. **Color Contour Detection**:
    - We use the two lines of code: `find\_contours(img_{lab}, r_{Red}, ROI_3)` and `find\_contours(img_{lab}, r_{Green}, ROI_3)`. Through the `find\_contours()` function, the system can detect all contours of the red region (`r_{Red}`) and the green region (`r_{Green}`) from the `LAB` color space image `img_{lab}` within the specified Region of Interest `ROI_3`. The result of each detection is a list of contours containing multiple closed areas.
  2. **Detecting the Nearest Traffic Sign**:
    - Subsequently, we call the functions `find\_best\_pillar(contours_{red}, redTarget, "red", img_{lab})` and `find\_best\_pillar(contours_{green}, greenTarget, "green", img_{lab})`. The `find\_best\_pillar()` function comprehensively evaluates each contour based on criteria such as size, position, and proximity to the target point (`redTarget` / `greenTarget`). The returned `best_{red}` and `best_{green}` are the pillars of their respective colors with the highest score and are closest to the passable route. If no suitable pillar is found, the function may return `None`.
  
  ### 英文: 
    <div align=center>
    <table>
    <tr>
    <th>Counterclockwise Direction, Green Signal(逆時針方向，綠色號誌)</th>
    <th>Drive on Inner Walls(行駛於車道內側)</th>
    </tr><tr>
    <td align=center><img src="./img/Counterclockwise_green.png" width=400 /></td>
    <td align=center><img src="./img/Counter-clockwise green route.png" width=400 /></td>
    </tr>
    </table>
    </div>

    <div align=center>
    <table>
    <tr>
    <th>Counterclockwise Direction, Red Signal(逆時針方向，紅色號誌)</th>
    <th>Drive on Exterior Walls(行駛於車道外側)</th>
    </tr><tr>
    <td align=center><img src="./img/Counterclockwise_red.png" width=400 /></td>
    <td align=center><img src="./img/Counter-clockwise red route.png" width=400 /></td>
    </tr>
    </table>
    </div>

    <div align=center>
    <table>
    <tr>
    <th>Counterclockwise Direction, No Signal(逆時針方向，沒有號誌)</th>
    <th>Drive on Exterior Walls(行駛於車道外側)</th>
    </tr><tr>
    <td align=center><img src="./img/Counterclockwise_NO.png" width=400 /></td>
    <td align=center><img src="./img/Counter-clockwise uncolored route.png" width=400 /></td>
    </tr>
    </table>
    </div>

    <div align=center>
    <table>
    <tr>
    <th>Clockwise Direction, Green Signal(順時針方向，綠色號誌)</th>
    <th>Drive on Exterior Walls(行駛於車道外側)</th>
    </tr><tr>
    <td align=center><img src="./img/Green in clockwise direction.png" width=400 /></td>
    <td align=center><img src="./img/Clockwise green route.png" width=400 /></td>
    </tr>
    </table>
    </div>

    <div align=center>
    <table>
    <tr>
    <th>Clockwise Direction, Red Signal(順時針方向，紅色號誌)</th>
    <th>Drive on Inner Wall(行駛於車道內側)</th>
    </tr><tr>
    <td align=center><img src="./img/Clockwise_red.png " width=400 /></td>
    <td align=center><img src="./img/Clockwise red route.png" width=400 /></td>
    </tr>
    </table>
    </div>

    <div align=center>
    <table>
    <tr>
    <th>Clockwise Direction, Green Signal(順時針方向，綠色號誌)</th>
    <th>Drive on Exterior Walls(行駛於車道外側)</th>
    </tr><tr>
    <td align=center><img src="./img/Clockwise the middle green.png " width=400 /></td>
    <td align=center><img src="./img/Clockwise green middle route.png" width=400 /></td>
    </tr>
    </table>
    </div>
    
    <div align=center>
    <table>
    <tr>
    <th>Clockwise Direction, Red Signal(順時針方向，紅色號誌)</th>
    <th>Drive on Inner Wall(行駛於車道內側)</th>
    </tr><tr>
    <td align=center><img src="./img/Clockwise the middle red.png " width=400 /></td>
    <td align=center><img src="./img/Clockwise red middle route.png" width=400 /></td>
    </tr>
    </table>
    </div>
- program code:
    ```
        color = 0
        detect_start = time.time()
        TIMEOUT = 2.0
        while a == 1:
            ok, img = cap.read()
            if not ok:
                continue
            img_lab = cv2.cvtColor(img, cv2.COLOR_BGR2Lab)
            img_lab = cv2.GaussianBlur(img_lab, (3,3), 0)

            contours_left  = pOverlap(img_lab, ROI1, True)
            contours_right = pOverlap(img_lab, ROI2, True)
            leftArea  = max_contour(contours_left,  ROI1)[0]
            rightArea = max_contour(contours_right, ROI2)[0]

            contours_red   = find_contours(img_lab, rRed,   ROI3)
            contours_green = find_contours(img_lab, rGreen, ROI3)
            best_red,   _ = find_best_pillar(contours_red,   redTarget,   "red",   img_lab)
            best_green, _ = find_best_pillar(contours_green, greenTarget, "green", img_lab)
            candidates = [p for p in (best_red, best_green) if p is not None]
            cPillar = min(candidates, key=lambda P: P.dist) if candidates else Pillar(0, 1000000, 0, 0, 0)
            seen_green_wait = (cPillar.target == greenTarget and cPillar.area > 0)
            seen_red_wait   = (cPillar.target == redTarget   and cPillar.area > 0)

            # === RGB：看到綠亮綠；看到紅亮紅；其他關燈（等待階段）===
            if seen_green_wait:
                rgb.show("green")
            elif seen_red_wait:
                rgb.show("red")
            else:
                rgb.off()

            if start_turn == 2:
                if seen_green_wait: color = 1; print("green"); a = 2
                elif seen_red_wait: color = 2; print("red"); a = 2
                elif time.time() - detect_start > TIMEOUT: color = 3; a = 2
            else:
                if seen_green_wait: color = 4; print("green"); a = 2
                elif seen_red_wait: color = 5; print("red"); a = 2
                elif time.time() - detect_start > TIMEOUT: color = 6; a = 2

        print(color)
        write(color)
        time2 = time.time()
    ```

# <div align="center">![HOME](../../other/img/home.png)[Return Home](../../)</div>  


