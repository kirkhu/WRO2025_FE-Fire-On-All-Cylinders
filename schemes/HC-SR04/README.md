<div align="center"><img src="../../other/img/logo.png" width="300" alt=" logo"></div>

## <div align="center">Ultrasonic rangefinder Introduction-超聲波測距儀簡介</div> 

- ### __Instruction to HC-SR04 ultrasonic distance sensor-HC-SR04 超聲波距離感測器說明__
    <div align="center">
    <table>
    <tr>  
    <td>
    <ol>

    ### 中文:
    1. HC-SR04 超聲波距離感測器是一種具成本效益且易於使用的距離測量方案。它透過發射超聲波脈衝並測量飛行時間來判斷物體距離。量測範圍為 2 公分到 400 公分，精度達 3 毫米，提供高度準確且可靠的距離資料，適用於避障、自主導航及物體偵測等多種應用。
    2. HC-SR04 超聲波距離感測器幫助我們在車輛進入停車區時偵測與側牆的距離，便利停車操作。透過根據偵測距離進行精確控制的程式設計，我們能順利引導車輛進入停車區，協助成功完成任務。
    ### 英文:
    1. The HC-SR04 ultrasonic distance sensor is a cost-effective and user-friendly solution for distance measurement. It operates by transmitting ultrasonic pulses and measuring the time of flight to determine the distance to an object. With a measurement range of 2cm to 400cm and a precision of 3mm, it provides highly accurate and reliable distance data, making it suitable for a wide range of applications including obstacle avoidance, autonomous navigation, and object detection.

    2. The HC-SR04 ultrasonic distance sensor helps us detect the distance between the vehicle and the side wall when entering the parking area, facilitating parking maneuvers. By programming precise control based on the detected distance, we can guide the vehicle into the parking area smoothly, helping us successfully complete the task.
        

    </ol>
    </td>
    <td width=300 align="center"><p>
    <strong>Supports 3.3V operating voltage-支援3.3伏特操作電壓</strong>
    </p>
        <img src="./img/HC-SR04.png" alt="HC-SR04" width="250" />
        <img src="./img/HC-SR04back.png" alt="HC-SR04" width="250" />
    </td>
    </tr>
    </table>
    </div>
   <ol>
    ### 中文:
    1. 我們在車輛的左側、右側及後方安裝了 HC-SR04 超聲波距離感測器，並將其連接到 Raspberry Pi Pico 控制器，以偵測車輛與側牆的距離。測得的距離資料會傳送到主程式進行處理，作為停車操作的依據。
    2. 需特別注意的是，Raspberry Pi Pico 控制器所能讀取的最高訊號電壓為 3.3V，而市售 HC-SR04 超聲波距離感測器通常輸出最高訊號電壓為 5V。因此，在選用或使用此感測器時，必須特別注意其操作電壓，以避免因電壓不符導致的操作問題或控制器損壞。
    ### 英文:
    1. We installed HC-SR04 ultrasonic distance sensors on the left, right, and rear of the vehicle and connected them to the Raspberry Pi Pico controller to detect the distance between the vehicle and the side walls. The measured distance data is transmitted to the main program for processing, serving as a basis for parking maneuvers.
   2. It is worth noting that the maximum signal voltage read by the Raspberry Pi Pico controller is 3.3V, while commercially available HC-SR04 ultrasonic distance sensors typically output a maximum signal voltage of 5V. Therefore, when selecting or using the sensor, special attention should be paid to its operating voltage to avoid operational issues or potential damage to the controller due to voltage mismatch.
    </ol>
<br>
    <div align="center" width=100%>
    <table >
    <tr align="center">
    <th colspan="2">HC-SR04 Ultrasonic Distance Sensor Placement Diagram on Vehicle-HC-SR04 超聲波距離感測器在車輛上的安裝位置示意圖

</th>
    </tr>
    <tr align="center">
      <th>Left(左側)</th>
      <th>Right(右側)</th>
      </tr>
    <tr>
      <td align=center><img src="./img/Car Left HC.png" alt="HC-SR04" width="250" /></td>
      <td align=center><img src="./img/Car Right HC.png" alt="HC-SR04" width="250" /></td>
      </tr>
    </table>
    </div>

- #### HC-SR04 連接至 Raspberry Pi Pico W的接線步驟：  
    - HC-SR04 的 VCC 連接到 Raspberry Pi Pico W的 3.3V（腳位 36）：為超聲波感測器提供電源。
    - HC-SR04 的 GND 連接到 Raspberry Pi Pico W的接地腳位：確保兩者共用接地。
    - HC-SR04 的 Trig 腳位連接到 Raspberry Pi Pico W的 GPIO 腳位：
        - 腳位 12（左側），
        - 腳位 13（右側），用於發送超聲波脈衝信號。
    - HC-SR04 的 Echo 腳位連接到 Raspberry Pi Pico W的 GPIO 腳位：
        - 腳位 8（左側），
        - 腳位 9（右側），用於接收回聲信號。
    - 以下是使用 MicroPython 撰寫的程式碼，以類別形式實現，能透過 Raspberry Pi Pico W讀取 HC-SR04 超聲波感測器的偵測距離。

- #### Wiring steps for connecting the HC-SR04 to the Raspberry Pi Pico:

    - VCC (HC-SR04) connects to the 3.3V (pin 36) on the Raspberry Pi Pico W: Provides power to the ultrasonic sensor.
    - GND (HC-SR04) connects to the GND pin on the Raspberry Pi Pico W: Ensures a common ground between both devices.
    - Trig (HC-SR04) connects to the GPIO pins on the Raspberry Pi Pico W:
         - pin 12 (left),
        - pin 13 (right), used for sending ultrasonic pulse signals.
    - Echo (HC-SR04) connects to the GPIO pins on the Raspberry Pi Pico W:
        - pin 8 (left),
        - pin 9 (right), used for receiving the echo signal.

    - Below is the code written in MicroPython, implemented as a class to read the detection distance from the HC-SR04 ultrasonic sensor using the Raspberry Pi Pico W.

   - #### MicroPython code-MicroPython 程式碼 
            from machine import Pin, time_pulse_us
            import time
            class HCSR04:
                def __init__(self, trigger_pin, echo_pin, echo_timeout_us=30000):
                    self.trigger = Pin(trigger_pin, Pin.OUT)
                    self.echo = Pin(echo_pin, Pin.IN)
                    self.echo_timeout_us = echo_timeout_us
                    self.trigger.low()
                    time.sleep(0.05)  # Stabilize the sensor

                def distance_cm(self):
                    # Send a 10us pulse to trigger the measurement
                    self.trigger.high()
                    time.sleep_us(10)
                    self.trigger.low()

                    # Wait for the echo response and measure its duration
                    try:
                        pulse_time = time_pulse_us(self.echo, 1, self.echo_timeout_us)
                    except OSError as ex:
                        pulse_time = -1

                    # Calculate distance in cm (pulse time in microseconds)
                    if pulse_time > 0:
                        distance = (pulse_time / 2) / 29.1  # Speed of sound ~343 m/s
                    else:
                        distance = -1  # Return -1 if timeout or error

                    return distance
  
   - #### Example usage-範例使用方法  

            sensor = HCSR04(trigger_pin=3, echo_pin=2)  # Assign pins accordingly
            while True:
                distance = sensor.distance_cm()
                if distance == -1:
                    print("Out of range or error")
                else:
                    print("Distance: {:.2f} cm".format(distance))
                time.sleep(1)
   - #### Explanation-說明  
        此程式碼包含一個名為 HC-SR04 的類別，透過定義觸發（trigger）和回聲（echo）腳位來測量距離。distance_cm() 方法會回傳以公分為單位的距離值，若發生測量錯誤或距離超出範圍，則會回傳 -1。


        This code includes a class named <strong>HC-SR04</strong> that measures distance by defining trigger and echo pins. The distance_cm() method returns the distance in centimeters, and if a measurement error occurs or the distance is out of range, it returns -1.


# <div align="center">![HOME](../../other/img/home.png)[Return Home](../../)</div>  
