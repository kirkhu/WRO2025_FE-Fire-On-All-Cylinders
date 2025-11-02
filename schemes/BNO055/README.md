，<div align="center"><img src="../../other/img/logo.png" width="300" alt=" logo"></div>

## <div align="center">Gyroscope orientation sensor Introduction</div> 

- #### __Instruction to BNO055 Gyroscope orientation sensor__

    1. The BNO055 gyroscope orientation sensor is a high-precision nine-axis absolute orientation sensor developed by Bosch Sensortec. It integrates an accelerometer, gyroscope, and magnetometer and has a built-in microprocessor for sensor fusion algorithms, providing real-time attitude and orientation information. Its primary feature is automatic sensor calibration, enabling it to directly output absolute orientation data in three-dimensional space.

    2. The BNO055 gyroscope orientation sensor can provide data on azimuth, tilt angle, acceleration, angular velocity, and magnetic field strength, making it ideal for applications that require precise attitude and orientation sensing, such as autonomous driving, robotic navigation, virtual reality (VR) devices, and various industrial control systems. With its built-in sensor fusion technology, the BNO055 gyroscope orientation sensor simplifies system design, relieving developers from handling complex data fusion.
    
    3. This sensor supports multiple interfaces (e.g., I2C, UART), allowing for easy integration into different embedded systems. The BNO055 gyroscope orientation sensor’s built-in algorithm automatically adjusts to provide stable readings across different environments, making it suitable for applications requiring high stability and accuracy.

    <div align="center">
    <table width="100%">
    <tr>  
    <th>Top View
    </th>
    <th>Bottom View
    </th>
    </tr>
    
    <tr>
    <td align="center"> <img src="./img/BNO055up.png" alt="BNO055 Top View" width="50%"    /> </td>
    <td align="center"> <img src="./img/BNO055.png" alt="BNO055 Bottom View  " width="50%"  /> </td>
    </tr>
    
    </table>
    </div>


    - To achieve precise steering control, the BNO055 Inertial Measurement Unit (IMU) / gyroscope orientation sensor was securely mounted onto the autonomous vehicle. - This sensor communicates with the NVIDIA Jetson Orin Nano controller via the I²C protocol, acquiring the vehicle's real-time directional data. 
    - This data is then transmitted to the main program for efficient computation and analysis, serving as a critical basis for the vehicle's autonomous steering decisions.

- #### Connection Guide for Gyroscope (BNO055) and Main Controller (NVIDIA Jetson Orin Nano)

    * **VCC (Power)**: Connect the VCC pin of the BNO055 to the **3.3V** pin (PIN 1) on the NVIDIA Jetson Orin Nano. This connection **provides the stable positive power supply** for the gyroscope.
    * **GND (Ground)**: Connect the GND pin of the BNO055 to the **GND** pin (PIN 6) on the NVIDIA Jetson Orin Nano. This connection **ensures a shared ground** between the two devices, completing the circuit loop.
    * **SDA (Data Line)**: Connect the SDA pin of the BNO055 to the **SDA** pin (PIN 3) on the NVIDIA Jetson Orin Nano. This line is used for **data transmission in the $I^2C$ protocol**.
    * **SCL (Clock Line)**: Connect the SCL pin of the BNO055 to the **SCL** pin (PIN 5) on the NVIDIA Jetson Orin Nano. This line is used for **clock signal synchronization in the $I^2C$ protocol**.


Here is the **Python code**, implemented using an **Object-Oriented Programming (OOP) approach (class-based)**, and deployed on an **NVIDIA Jetson Orin Nano** development board. This code is designed to read data from a **BNO055 Inertial Measurement Unit (IMU) gyroscope sensor** to accurately implement the **heading/orientation detection function** for a **vehicle**.

- ####  Python code
```python
     

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

```

- #### Example usage
```python
            sensor = BNO055Sensor()
            while True:
                # Get orientation data
                orientation = sensor.get_orientation()
                print("Orientation - Heading: {heading}°, Roll: {roll}°, Pitch: {pitch}°".format(**orientation))

                # Get calibration status
                calibration_status = sensor.get_calibration_status()
                print("Calibration Status:", calibration_status)

                time.sleep(1)
```

- #### Explanation      
    * **init method:** Initializes the BNO055 Gyroscope orientation Sensor class, setting the I2C address and verifying the sensor connection. If the connection fails, it raises an error.
    * **get_orientation method:** Retrieves orientation data from the sensor (Heading, Roll, and Pitch) and returns them in a dictionary.
    * **get_calibration_status method:** Returns the calibration status for the system, gyroscope, accelerometer, and magnetometer, which is useful for ensuring accurate measurements.

__This code reads and prints the BNO055 Gyroscope orientation sensor's orientation data and calibration status every second.__

# <div align="center">![HOME](../../other/img/home.png)[Return Home](../../)</div>  
