<div align="center"><img src="../../other/img/logo.png" width="300" alt=" logo"></div>

## <div align="center">Vehicle Power Supply System Introduction</div> 
- ###  Power Supply Operation System Overview Diagram
  <div align="center"><img src="./img/Power_supply_system.png" ></div>

- ###  Physical Connection Diagram of Power Supply System
  <div align="center"><img src="./img/Power_supply_system of Summary diagram.png" ></div>

- ### Power Supply System Operation Instructions
  Each electronic component requires a specific operating voltage to function properly, and the configuration is as follows:
    - The 3S Li-Polymer battery provides 11.1V, which powers the buck converter module and the L293D motor control chip to drive the 12V DC motor.
    - The 5A constant voltage and constant current buck power module steps down the 11.1V to 5V, supplying power to components requiring a 5V operating voltage, including the Nvidia Jetson Nano, Raspberry Pi Pico, L293D dual H-bridge DC motor driver IC, BNO055 gyroscope orientation sensor, and the MG90S front steering servo motor.
    - The Nvidia Jetson Nano control board further supplies 3.3V to the camera module.
    - The Raspberry Pi Pico control board provides 3.3V to the HC-SR04 ultrasonic distance sensor.
  
  This configuration ensures all components operate stably at their required working voltages.


# <div align="center">![HOME](../../other/img/home.png)[Return Home](../../)</div>  

