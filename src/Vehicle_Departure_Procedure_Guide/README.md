<div align="center"><img src="../../other/img/logo.png" width="300" alt=" logo"></div>

## <div align="center">Operational Procedure Guide for Vehicle Departure from the Parking Zone</div>
  **Parking Lot Exit Overview**
- ### Parking Lot Exit program
    1.  **System Startup and Direction Determination (Jetson Orin Nano Responsibility)**
    - * When the vehicle starts, the **main control system (Jetson Orin Nano)** performs image recognition via the camera to first **determine the vehicle's default driving direction** (Counter-Clockwise or Clockwise). Subsequently, it identifies and locks onto the **color of the target track line**, which serves as the basis for the entire mission.

    2.  **Counter-Clockwise (CCW) Driving Logic**
    - * **Upon detecting a Green Pillar:** The vehicle executes a **90-degree turn to the left** for a lane change, **driving forward to the inner side of the Green Pillar**. Subsequently, the vehicle **turns 90 degrees to the right** and **reverses to a predetermined position** (completing the inner lane change).
    - * **Upon detecting a Red Pillar:** The vehicle **drives forward**, then **turns 90 degrees to the left**, **driving forward to the outer side of the Red Pillar**. Subsequently, the vehicle **reverses, turns 90 degrees to the right**, and **reverses to a predetermined position** (completing the outer lane change or avoidance).
    - * **When no pillars are detected:** The system defaults the vehicle to **drive on the outer side of the lane**.

    3.  **Clockwise (CW) Driving Logic**
    - * **Upon detecting a Green Pillar:** The vehicle executes a **90-degree turn to the right** for a lane change, **driving forward to the outer side of the Green Pillar**. Subsequently, the vehicle **turns 90 degrees to the left** and **drives forward to a predetermined position** (completing the outer lane change).
    - * **Upon detecting a Red Pillar:** The vehicle executes a **90-degree turn to the right** for a lane change, **driving forward to the inner side of the Red Pillar**. Subsequently, the vehicle **turns 90 degrees to the left** and **drives forward to a predetermined position** (completing the inner lane change).
    - * **When no pillars are detected:** The system defaults the vehicle to **drive on the outer side of the lane**.
- **Code running on the Raspberry Pi Pico W controller.**
    ```python
    if turn in (1, 2):
        if turn == 1:
            print("right")
            run_encoder_Auto(500, 40, 180)
        else:
            print("left")
            run_encoder_Auto(1200, 40, -180)

        mode = 1
    else:

        mode = 2

    LAST_COLOR = 0
    color = 0
    print(mode, color)
    print(' color（M,<1..6>[,<...>]  {"color":n}）...')

    while mode == 1 and color == 0:
        json_obj, m_tuple, got_stop = pump_uart()

        if json_obj:
            v = None
            try:
                if "color" in json_obj:
                    v = int(json_obj["color"])
                elif "c" in json_obj:
                    v = int(json_obj["c"])
            except:
                v = None
            
            if v is not None:
                if 1 <= v <= 6:
                    color = v
                    LAST_COLOR = color
                    print("[JSON] color =", color)
                    break 
                else:
                    if DEBUG: print("[IGNORE] JSON color out of range:", v)
            
            extract_magenta_from_json(json_obj)

        if m_tuple:
            first = m_tuple[0]
            if 1 <= first <= 6:
                color = first
                LAST_COLOR = color
                print("[M] color =", color, "raw:", m_tuple)
                break 
            else:
                if DEBUG: print("[IGNORE] M packet in mode1 (not color):", m_tuple)

        if json_obj is None and m_tuple is None:
            import time 
            time.sleep(0.002)

    if mode == 1 and color != 0: 
        if color == 1:
            print("1")
            run_encoder_Auto(2100, 60, 0)
            run_encoder_Auto(1400, 40, 180)
            run_encoder_Auto(1200, -45, 0)
        elif color == 2:
            print("2")
            run_encoder_Auto(1700, 60, 0)
            run_encoder_Auto(1150, -40, -180)
        elif color == 3:
            print("3")
            run_encoder_Auto(1700, 60, 0)
            run_encoder_Auto(1150, -40, -180)
        elif color == 4:
            print("4")
            run_encoder_Auto(600, 40, 180)
            run_encoder_Auto(400, 50, 0)
            run_encoder_Auto(1100, 40, -180)
            run_encoder_Auto(800, 50, 0)
        elif color == 5:
            print("5")
            run_encoder_Auto(600, 40, 180)
            run_encoder_Auto(2200, 60, 0)
            run_encoder_Auto(1150, 40, -180)
            run_encoder_Auto(800, 50, 0)
        elif color == 6:
            print("6")
            run_encoder_Auto(600, 40, 180)
            run_encoder_Auto(1500, 60, 0)
            run_encoder_Auto(1150, 40, -180)

    control_motor(0)
    set_servo_angle(0)

    ```
## <div align=center>Counter-clockwise green departure process</div>
<div align=center>
<table>
<tr>
<th width="50%">Step-1: Preparing to turn left</th>
<th width="50%">Step-2: Start_reversing</th>
</tr><tr align=center>
<td width="50%"><img src="./img/Start_in_green_counterclockwise-1.png"  /></td>
<td width="50%"><img src="./img/Start_in_green_counterclockwise-2.png" /></td>
</tr>

<tr>
<th width="50%">Step-3: Reparing to turn right</th>
<th width="50%">Step-4: Preparing to retreat</th>
</tr><tr align=center>
<td width="50%"><img src="./img/Start_in_green_counterclockwise-3.png" /></td>
<td width="50%"><img src="./img/Start_in_green_counterclockwise-4.png"  /></td>
</tr>

<tr>
<th>Step-5: Arrive at the designated location</th>
<th>Video Recording of the Vehicle's Actual Run</th>
</tr><tr align=center>
<td><img src="./img/Start_in_green_counterclockwise-5.png" /></td>
<td><a href="" ><img src="./img/" /></a></td>
</tr>
</table>
</div>

## <div align="center">Counter-clockwise red departure process</div>
<div align=center>
<table>
<tr>
<th width="50%">Step-1: Preparing to turn left</th>
<th width="50%">Step-2: Start_reversing</th>
</tr><tr align=center>
<td width="50%"><img src="./img/Start_in_red_counterclockwise-1.png"  /></td>
<td width="50%"><img src="./img/Start_in_red_counterclockwise-2.png" /></td>
</tr>

<tr>
<th width="50%">Step-3: Prepare to back up and turn left</th>
<th width="50%">Step-4: Arrive at the designated location</th>
</tr><tr align=center>
<td width="50%"><img src="./img/Start_in_red_counterclockwise-3.png"  /></td>
<td width="50%"><img src="./img/Start_in_red_counterclockwise-4.png"  /></td>
</tr>

<tr>
<th colspan=2>Video Recording of the Vehicle's Actual Run</th>
</tr>
<tr align=center>
<td colspan=2><a href="" ><img src="./img/" /></a></td>
</tr>
</table>
</div>

## <div align="center">Counter-clockwise, no color starting process</div>
<div align=center>
<table>
<tr>
<th width="50%">Step-1: Preparing to turn left</th>
<th width="50%">Step-2: Start_reversing</th>
</tr><tr align=center>
<td width="50%"><img src="./img/Start_in_no_counterclockwise-1.png"  /></td>
<td width="50%"><img src="./img/Start_in_no_counterclockwise-2.png"  /></td>
</tr>

<tr>
<th width="50%">Step-3: Prepare to back up and turn left</th>
<th width="50%">Step-4: Arrive at the designated location</th>
</tr><tr align=center>
<td width="50%"><img src="./img/Start_in_no_counterclockwise-3.png"  /></td>
<td width="50%"><img src="./img/Start_in_no_counterclockwise-4.png"  /></td>
</tr>

<tr>
<th colspan=2>Video Recording of the Vehicle's Actual Run</th>
</tr><tr align=center>
<td colspan=2><a href="" ><img src="./img/" /></a></td>
</tr>
</table>
</div>

## <div align="center">Clockwise Green Departure Process</div>
<div align=center>
<table>
<tr>
<th width="50%">Step-1: Preparing to turn right</th>
<th width="50%">Step-2: Ready to move forward</th>
</tr><tr align=center>
<td width="50%"><img src="./img/Clockwise Green Departure Process-1.png"  /></td>
<td width="50%"><img src="./img/Clockwise Green Departure Process-2.png"  /></td>
</tr>

<tr>
<th width="50%">Step-3: Preparing to turn left</th>
<th width="50%">Step-4: Ready to move forward</th>
</tr><tr align=center>
<td width="50%"><img src="./img/Clockwise Green Departure Process-3.png"  /></td>
<td width="50%"><img src="./img/Clockwise Green Departure Process-4.png"  /></td>
</tr>

<tr>
<th width=50%>Step-5: Arrive at the designated location</th>
<th width=50%>Video Recording of the Vehicle's Actual Run</th>
</tr><tr align=center>
<td width=50%><img src="./img/Clockwise Green Departure Process-5.png" /></td>
<td width=50%><a href=""><img src="" /></a></td>
</tr>
</table>
</div>

## <div align="center">Clockwise Red Departure Process</div>
<div align=center>
<table>
<tr>
<th width="50%">Step-1: Preparing to turn right</th>
<th width="50%">Step-2: Ready to move forward</th>
</tr><tr align=center>
<td width="50%"><img src="./img/Clockwise red Departure Process-1.png"  /></td>
<td width="50%"><img src="./img/Clockwise red Departure Process-2.png"  /></td>
</tr>

<tr>
<th width="50%">Step-3: Preparing to turn left</th>
<th width="50%">Step-4: Ready to move forward</th>
</tr><tr align=center>
<td width="50%"><img src="./img/Clockwise red Departure Process-3.png"  /></td>
<td width="50%"><img src="./img/Clockwise red Departure Process-4.png"  /></td>
</tr>

<tr>
<th>Step-5: Arrive at the designated location</th>
<th>Video Recording of the Vehicle's Actual Run</th>
</tr><tr align=center>
<td><img src="./img/Clockwise red Departure Process-5.png"  width=80% /></td>
<td><a href=""><img src="" /></a></td>
</tr>
</table>
</div>

## <div align="center">Clockwise green center departure process</div>
<div align=center>
<table>
<tr>
<th width="50%">Step-1: Preparing to turn right</th>
<th width="50%">Step-2: Preparing to turn left</th>
</tr><tr align=center>
<td width="50%"><img src="./img/Clockwise green center departure process-1.png"  /></td>
<td><img src="./img/Clockwise green center departure process-2.png"  /></td>
</tr>

<tr>
<th width="50%">Step-3: Ready to move forward</th>
<th width="50%">Step-4: Arrive at the designated location</th>
</tr>
<tr>
<td width="50%"><img src="./img/Clockwise green center departure process-3.png" /></td>
<td width="50%"><img src="./img/Clockwise green center departure process-4.png" /></td>
</tr>

<tr>
<th colspan=2>Video Recording of the Vehicle's Actual Run</th>
</tr>
<tr align=center>
<td colspan=2><a href="" ><img src="./img/" /></a></td>
</tr>
</table>
</div>

## <div align="center">Clockwise red center departure process</div>
<div align=center>
<table>
<tr>
<th width="50%">Step-1: Preparing to turn right</th>
<th width="50%">Step-2: Ready to move forward</th>
</tr><tr>
<td width="50%"><img src="./img/Clockwise red center departure process-1.png"  /></td>
<td width="50%"><img src="./img/Clockwise red center departure process-2.png"  /></td>
</tr

<tr>
<th width="50%">Step-3: Preparing to turn left</th>
<th width="50%">Step-4: Ready to move forward</th>
</tr><tr>
<td width="50%"><img src="./img/Clockwise red center departure process-3.png"  /></td>
<td width="50%"><img src="./img/Clockwise red center departure process-4.png"  /></td>
</tr>

<tr>
<th>Step-5: Arrive at the designated location</th>
<th>Video Recording of the Vehicle's Actual Run</th>
</tr>
<tr align=center>
<td><img src="./img/Clockwise red center departure process-5.png" /></td>
<td><a href="" ><img src="./img/" /></a></td>
</tr>

</table>
</div>

# <div align="center">![HOME](../../other/img/home.png)[Return Home](../../)</div>  
