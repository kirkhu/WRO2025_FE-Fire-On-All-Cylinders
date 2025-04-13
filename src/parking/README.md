<div align="center"><img src="../../other/img/logo.png" width="300" alt=" logo"></div>

## <div align="center">Explanation of the parking method</div>
  **Below is the code for performing the parking task after completing three laps.**
- ### Parking program
    - When the vehicle is in motion, the system (Jetson Nano) first uses the camera to detect the pink square to identify the location of the parking lot. When the vehicle reaches the last turn of the third lap, it first proceeds to the end zone and pauses momentarily. The vehicle then completes another lap and, upon approaching the turn near the parking lot, reduces its speed to park precisely in the designated spot. At this point, the system uses the highlighted values from the camera to assess the distance between the vehicle and the front boundary wall, adjusting its direction toward the parking lot.

    - Upon entering the parking lot, the system (Jetson Nano) employs the camera’s side-highlight detection area to measure the distance between the vehicle and the side wall, ensuring the vehicle maintains an appropriate distance from the pink square marking the parking space. To confirm the vehicle’s arrival at the designated parking position, the system (Raspberry Pi Pico) utilizes ultrasonic sensors on both sides to detect the boundaries of the parking area as the vehicle advances. Once the vehicle detects the walls, it compares the left and right ultrasonic values: if the left value is greater than the right, it parks to the right; otherwise, it parks to the left.

    - After confirming the parking direction, the system applies a real-world parallel parking approach. First, it sets the steering angle for the servo motor and the angle needed for the motor to reach the target position. During the parking process, the system (Raspberry Pi Pico) controls the motor to achieve the target angle while simultaneously adjusting the servo motor, thereby completing the reverse parking maneuver.
    
  - **Code running on the Jetson Nano controller.**
    ```
        #parking area turn
        if turn_side == 4:
            if not ROI2:
                PWM = 25
                current_time = time.time()
                elapsed_time = current_time - start_time
                if elapsed_time != 0.8 and time_count > 0 or elapsed_time < 0.9:
                    if target_heading == left_heading or target_heading == red_left_heading:
                        if roi_values[0] > 6000:
                            combined_control_signal = -100
                        else:
                            combined_control_signal = 65
                    else:
                        if roi_values[1] > 5000:
                            combined_control_signal = 65
                        else:
                           combined_control_signal = -80
                    time_count = time_count-1
                    time.sleep(0.01)
                else:
                    if target_heading == left_heading or target_heading == red_left_heading:
                        combined_control_signal = pd_control(target_heading[count], heading, kp_heading, kd_heading)
                    else:
                        combined_control_signal = pd_control(target_heading[count], heading, kp_heading, kd_heading)
                if roi_values[2] >= 7500:
                    ROI2 = True
                    time_count = 0
            if ROI2:
                PWM = -35
                if target_heading == left_heading or target_heading == red_left_heading:
                        combined_control_signal = 180
                else:
                        combined_control_signal = -180
                if heading < target_heading[count+1] + 30 and heading > target_heading[count+1] - 30:
                    combined_control_signal = 0
                    turn_side = 5

        #parking area
        if turn_side == 5:
            PWM = 30
            if pink_positions[1] != 0:
                print("pink")
                if target_heading == left_heading or target_heading == red_left_heading: 
                    combined_control_signal = -pd_control(55, pink_green_x_diff, kp_X, kd_X)
                elif target_heading == right_heading or target_heading == red_right_heading:
                    combined_control_signal = pd_control(15, pink_red_x_diff, kp_X, kd_X)
            else:
                if target_heading == left_heading or target_heading == red_left_heading:
                    print("right")
                    combined_control_signal = pd_control(7500, roi_values[0], kp_roi, kd_roi)
                else:
                    print("left")
                    combined_control_signal = -pd_control(7500, roi_values[1], kp_roi, kd_roi)
    ```
  - **Code running on the Raspberry Pi Pico controller.**
    ``` 
        control_motor(35)
        time.sleep(0.4)
        control_motor(0)
        distance2 = measure_distance(trig2, echo2)
        distance1 = measure_distance(trig1, echo1)
        if distance1 > distance2:  # Right-side parking
            approach_until(trig2, echo2, 15, '>')
            approach_until(trig2, echo2, 20, '<')
            approach_until(trig2, echo2, 15, '>')
        # Reverse parking.
            run_encoder_Auto(300, 10, 0)
            run_encoder_Auto(1500, -45, 175)
            run_encoder_Auto(30, -10, -190)
            run_encoder_Auto(1400, -25, -190)
            run_encoder_Auto(480, 30, 180)
            run_encoder_Auto(10, 10, 0)
        # (Continue with the rest of the reverse parking sequence)
        else:  # Left-side parking
            approach_until(trig1, echo1, 15, '>')
            approach_until(trig1, echo1, 20, '<')
            approach_until(trig1, echo1, 15, '>')
        # Reverse parking.
            run_encoder_Auto(400, 10, 0)
            run_encoder_Auto(1620, -45, -190)
            run_encoder_Auto(30, -10, 180)
            run_encoder_Auto(1330, -25, 180)
            run_encoder_Auto(470, 30, -180)
            run_encoder_Auto(10, 10, 0)
        # (Continue with the rest of the reverse parking sequence)
                    
        control_motor(-25)
        time.sleep(0.35)
        control_motor(0)
        button_out.low()
                    
                
    except KeyboardInterrupt:
        motor_in1.off()
        motor_in2.off()
        set_servo_angle(0)
        print("Program interruption")
        
    ```
<div align=center>

  |Prepare_to_reverse|Start_reversing|Parking_ends|
  |:---:|:---:|:---:|
  |<div align="center"> <img src="./img/Prepare_to_reverse.png"  alt="Prepare_to_reverse"></div>|<div align="center"> <img src="./img/Start_reversing.png"  alt="Start_reversing"></div>|<div align="center"> <img src="./img/Parking_ends.png"  alt="Parking_ends"></div>|

- ### Parking test video
[![Parking @ Fire On All Cylinders](./img/parking.jpg)](https://youtu.be/zhCsoUZu6ao "Open Challange clockwise @ Fire On All Cylinders")

# <div align="center">![HOME](../../other/img/home.png)[Return Home](../../)</div>  
