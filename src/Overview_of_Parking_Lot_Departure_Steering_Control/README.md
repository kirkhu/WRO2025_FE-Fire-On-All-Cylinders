<div align=center> <img src="../../other/img/logo.png" width=300 alt=" logo"> </div>

## <div align="center">Overview of Parking Lot Departure Steering Control</div> 

- ### Determination of the Driving direction
  - Before the Vehicle departs from the parking lot, it utilizes the image captured by the CSI camera and applies the Region of Interest (ROI) technique to pre-determine the Driving direction. The determination logic is based on comparing the areas of `ROI_1` and `ROI_2`: if the area of `ROI_1` is greater than the area of `ROI_2`, the current Driving direction is determined to be the clockwise direction ; conversely, if the area of `ROI_2` is greater than the area of `ROI_1`, it is determined to be the Counterclockwise direction. Once the Driving direction is confirmed, the Vehicle exits the parking lot , and the system subsequently detects the presence of traffic signs blocks (red or green traffic signs) in the lane and executes the corresponding Lane Change decision based on the detected color.
    1. **ROI Area Reading and Wall Detection:**
      We utilize the functions `pOverlap(img_{lab}, ROI_1)` and `pOverlap(img_{lab}, ROI_2)` to detect black regions within the left and right `ROI` areas, using the `LAB` color space image `img_{lab}`. The `pOverlap()` function further determines whether these black regions overlap with the magenta markings. The primary goal of this step is to identify the positions of walls or pillars that may appear on the left and right sides of the image, thereby providing a solid basis for subsequent contour extraction, area analysis, and path determination. 

    2. **ROI Maximum Contour Area Extraction:**
      In the left and right `ROI` areas, we utilize the two functions `max\_contour(contours_{left}, ROI_1)[0]` and `max\_contour(contours_{right}, ROI_2)[0]`. Through the `max\_contour()` function, the system can filter out the contour area of the largest black wall from the contours detected on both sides, and retrieve its corresponding area value and center point information. 

<div align=center>

  |Counterclockwise direction|Clockwise direction|
  |:---:|:---:|
  |<div align="center"> <img src="./img/Counterclockwise_direction.png" width="400"  alt="Detecting_nearby_obstacles"></div>|<div align="center"> <img src="./img/clockwise_direction.png" width="400" alt="Detecting_nearby_obstacles"></div>|

</div> 

- ### program code: ###

```python
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
                print("Turn Right"); start_turn = 1; a = 1
            else:
                print("Turn Left"); start_turn = 2; a = 1

        write(start_turn)     
```

- ### Driving Route Decision Based on Color Recognition 
    - Counterclockwise direction : If the Driving direction is Counterclockwise direction , the Vehicle will drive on the inner wall of the lane when a green pillar is detected; it will drive on the exterior walls of the lane when a red pillar  is detected. If no pillar is detected, the default is to drive on the exterior walls  of the lane.
    - Clockwise direction : If the Driving direction is clockwise direction , the Vehicle will drive on the exterior walls of the lane when a green pillar is detected; it will drive on the inner wall of the lane when a red pillar  is detected. If no pillar is detected, the default is to drive on the exterior walls  of the lane.

  1. **Color Contour Detection**:
    We use the two lines of code: `find\_contours(img_{lab}, r_{Red}, ROI_3)` and `find\_contours(img_{lab}, r_{Green}, ROI_3)`. Through the `find\_contours()` function, the system can detect all contours of the red region (`r_{Red}`) and the green region (`r_{Green}`) from the `LAB` color space image `img_{lab}` within the specified Region of Interest `ROI_3`. The result of each detection is a list of contours containing multiple closed areas.
  2. **Detecting the Nearest Traffic Sign**:
    Subsequently, we call the functions `find\_best\_pillar(contours_{red}, redTarget, "red", img_{lab})` and `find\_best\_pillar(contours_{green}, greenTarget, "green", img_{lab})`. The `find\_best\_pillar()` function comprehensively evaluates each contour based on criteria such as size, position, and proximity to the target point (`redTarget` / `greenTarget`). The returned `best_{red}` and `best_{green}` are the pillars of their respective colors with the highest score and are closest to the passable route. If no suitable pillar is found, the function may return `None`.
    
  
    <div align=center>
    <table>
    <tr>
    <th>Counterclockwise Direction, Green Signal</th>
    <th>Drive on Inner Walls</th>
    </tr><tr>
    <td align=center><img src="./img/Counterclockwise_green.png" width=400 /></td>
    <td align=center><img src="./img/Counter-clockwise green route.png" width=400 /></td>
    </tr>
    </table>
    </div>

    <div align=center>
    <table>
    <tr>
    <th>Counterclockwise Direction, Red Signal</th>
    <th>Drive on Exterior Walls</th>
    </tr><tr>
    <td align=center><img src="./img/Counterclockwise_red.png" width=400 /></td>
    <td align=center><img src="./img/Counter-clockwise red route.png" width=400 /></td>
    </tr>
    </table>
    </div>

    <div align=center>
    <table>
    <tr>
    <th>Counterclockwise Direction, No Signal</th>
    <th>Drive on Exterior Walls</th>
    </tr><tr>
    <td align=center><img src="./img/Counterclockwise_NO.png" width=400 /></td>
    <td align=center><img src="./img/Counter-clockwise uncolored route.png" width=400 /></td>
    </tr>
    </table>
    </div>

    <div align=center>
    <table>
    <tr>
    <th>Clockwise Direction, Green Signal</th>
    <th>Drive on Exterior Walls</th>
    </tr><tr>
    <td align=center><img src="./img/Green in clockwise direction.png" width=400 /></td>
    <td align=center><img src="./img/Clockwise green route.png" width=400 /></td>
    </tr>
    </table>
    </div>

    <div align=center>
    <table>
    <tr>
    <th>Clockwise Direction, Red Signal</th>
    <th>Drive on Inner Wall</th>
    </tr><tr>
    <td align=center><img src="./img/Clockwise_red.png " width=400 /></td>
    <td align=center><img src="./img/Clockwise red route.png" width=400 /></td>
    </tr>
    </table>
    </div>

    <div align=center>
    <table>
    <tr>
    <th>Clockwise Direction, Green Signal</th>
    <th>Drive on Exterior Walls</th>
    </tr><tr>
    <td align=center><img src="./img/Clockwise the middle green.png " width=400 /></td>
    <td align=center><img src="./img/Clockwise green middle route.png" width=400 /></td>
    </tr>
    </table>
    </div>
    
    <div align=center>
    <table>
    <tr>
    <th>Clockwise Direction, Red Signal</th>
    <th>Drive on Inner Wall</th>
    </tr><tr>
    <td align=center><img src="./img/Clockwise the middle red.png " width=400 /></td>
    <td align=center><img src="./img/Clockwise red middle route.png" width=400 /></td>
    </tr>
    </table>
    </div>

- ### program code: ###
    ```python
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


