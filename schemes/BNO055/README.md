，<div align="center"><img src="../../other/img/logo.png" width="300" alt=" logo"></div>

## <div align="center">Gyroscope orientation sensor Introduction-陀螺儀方向感測器簡介：</div> 

- ### __Instruction to BNO055 Gyroscope orientation sensor-BNO055 陀螺儀方向感測器使用說明：__
    <div align="center">
    <table>
    <tr>  
    <td>
    <ol>

    ### 中文:
    1. BNO055 陀螺儀方向感測器是由 Bosch Sensortec 開發的高精度九軸絕對方向感測器。它整合了加速度計、陀螺儀與磁力計，並內建用於感測器融合的微處理器，可提供即時的姿態與方向資訊。其主要特點是具備自動校準功能，能夠直接輸出三維空間中的絕對方向數據。
  
    2. BNO055 陀螺儀方向感測器能提供方位角、傾斜角、加速度、角速度與磁場強度等數據，非常適用於需要高精度姿態與方向感測的應用場景，例如自動駕駛、機器人導航、虛擬實境（VR）裝置及各類工業控制系統。由於其內建的感測器融合技術，可大幅簡化系統設計，讓開發者無需自行處理複雜的數據融合工作。
    3. 此感測器支援多種通訊介面（如 I2C、UART），便於整合至各種嵌入式系統中。BNO055 陀螺儀方向感測器的內建演算法會自動調整參數，能在不同環境中穩定輸出數據，因此特別適用於對穩定性與精準度要求極高的應用場景。
   
    ### 英文
    1. The BNO055 gyroscope orientation sensor is a high-precision nine-axis absolute orientation sensor developed by Bosch Sensortec. It integrates an accelerometer, gyroscope, and magnetometer and has a built-in microprocessor for sensor fusion algorithms, providing real-time attitude and orientation information. Its primary feature is automatic sensor calibration, enabling it to directly output absolute orientation data in three-dimensional space.

    2. The BNO055 gyroscope orientation sensor can provide data on azimuth, tilt angle, acceleration, angular velocity, and magnetic field strength, making it ideal for applications that require precise attitude and orientation sensing, such as autonomous driving, robotic navigation, virtual reality (VR) devices, and various industrial control systems. With its built-in sensor fusion technology, the BNO055 gyroscope orientation sensor simplifies system design, relieving developers from handling complex data fusion.
    
    3. This sensor supports multiple interfaces (e.g., I2C, UART), allowing for easy integration into different embedded systems. The BNO055 gyroscope orientation sensor’s built-in algorithm automatically adjusts to provide stable readings across different environments, making it suitable for applications requiring high stability and accuracy.
    </ol>
    </td>
    <td width=300 align="center">
      <img src="./img/BNO055up.png" alt="BNO055up" width="250" />
      <img src="./img/BNO055.png" alt="BNO055" width="250" />

    </td>
    </tr>
    </table>
    </div>

    ### 中文:
    - 我們將 BNO055 陀螺儀方向感測器安裝於車體上，並透過 I2C 模式將其與 Nvidia Jetson Nano 控制器連接。該配置用於讀取車輛的即時方向資訊，並將獲得的方向數據傳送至主程序進行運算與分析，作為車輛轉向決策的依據。
    ### 英文:
    - We installed the BNO055 gyroscope orientation sensor on the vehicle and connected it to the Nvidia Jetson Nano controller, using I2C mode for data transmission. This setup is used to read the vehicle's current orientation, and the obtained orientation data is transmitted to the main program for calculation and analysis, serving as a basis for the vehicle's steering decisions.
 

  - #### Hardware Connection:
    **Power Supply:**
    ### 中文:
    - 將BNO055的VIN腳位接入到Jetson Orin Nano的3.3V腳位(Pin 1)。BNO055的工作電壓範圍是2.4V ~ 3.6V，而Jetson Orin Nano可以提供穩定的3.3V輸出，因此可作為其電源供應。

    - 將BNO055的GND腳位接至Jetson Orin Nano的GND腳位(Pin 6)。這樣以確保BNO055形成正確的電壓迴路。
    ### 英文:
    - Connect VDD (BNO055) to the 3.3V pin on the Raspberry Pi Pico (pin 36). The BNO055 operates within a voltage range of 2.4V to 3.6V, and the Raspberry Pi Pico’s 3.3V pin provides a stable 3.3V voltage, making it suitable for powering the BNO055.
    - Connect GND (BNO055) to one of the GND pins on the Raspberry Pi Pico(pin 8) to ensure a common ground between the two devices.
     
    **I²C Communication:**
    ### 中文:
    - 將 BNO055 的 VDD 腳位 接至 Raspberry Pi Pico 的 3.3V 腳位（第 36 腳）。BNO055 的工作電壓範圍為 2.4V 至 3.6V，而 Raspberry Pi Pico 提供穩定的 3.3V 輸出，因此可作為其電源供應。
    - 將 BNO055 的 GND 腳位 接至 Raspberry Pi Pico 的其中一個 GND 腳位（第 8 腳），以確保兩個裝置之間的共地連接。

    ### 英文:
    - Connect SDA (BNO055) to the SDA pin on the Jetson Nano (pin 3 on header J41).
    - Connect SCL (BNO055) to the SCL pin on the Jetson Nano (pin 5 on header J41).
    - Connect both PS0 and PS1 pins (BNO055) to ground (GND) to set the device to I²C mode.
    - Connect the ADD pin (BNO055) to ground (GND) to set the I²C address to 0x28.

- 以下是 Python 程式碼，使用 類別方式 在 Nvidia Jetson Nano 上從 BNO055 陀螺儀感測器 實作方向偵測功能。
   
- The following is __Python__ code that implements orientation detection functionality from the __BNO055 gyroscope sensor__ on an __Nvidia Jetson Nano__ using a class-based approach.

    - ####  Python code-Python 程式碼



            import time
            from Adafruit_BNO055 import BNO055
            class BNO055Sensor:
                def __init__(self, i2c_address=0x28):
                    # Initialize BNO055 sensor with the specified I2C address
                    self.bno = BNO055.BNO055(i2c_address=i2c_address)
                    
                    # Check if the sensor was initialized successfully
                    if not self.bno.begin():
                        raise RuntimeError("Failed to initialize BNO055. Please check the connection.")
                    else:
                        print("BNO055 initialized successfully.")

                def get_orientation(self):
                    # Read orientation (Heading, Roll, Pitch) from the sensor
                    heading, roll, pitch = self.bno.read_euler()
                    return {
                        "heading": heading,
                        "roll": roll,
                        "pitch": pitch
                    }

                def get_calibration_status(self):
                    # Retrieve calibration status for the system, gyroscope, accelerometer, and magnetometer
                    sys, gyro, accel, mag = self.bno.get_calibration_status()
                    return {
                        "system": sys,
                        "gyroscope": gyro,
                        "accelerometer": accel,
                        "magnetometer": mag
                    }


    - #### Example usage-範例用法
            sensor = BNO055Sensor()
            while True:
                # Get orientation data
                orientation = sensor.get_orientation()
                print("Orientation - Heading: {heading}°, Roll: {roll}°, Pitch: {pitch}°".format(**orientation))

                # Get calibration status
                calibration_status = sensor.get_calibration_status()
                print("Calibration Status:", calibration_status)

                time.sleep(1)

   - #### Explanation-說明    
        <p>
        <ol>
        <li><strong>__init__ method:</strong> Initializes the BNO055 Gyroscope orientation Sensor class, setting the I2C address and verifying the sensor connection. If the connection fails, it raises an error.</li>
        <li><strong>get_orientation method:</strong> Retrieves orientation data from the sensor (Heading, Roll, and Pitch) and returns them in a dictionary.
        get_calibration_status method: Returns the calibration status for the system, gyroscope, accelerometer, and magnetometer, which is useful for ensuring accurate measurements.</li>
        </ol></p>

      __This code reads and prints the BNO055 Gyroscope orientation sensor's orientation data and calibration status every second.__

# <div align="center">![HOME](../../other/img/home.png)[Return Home](../../)</div>  
