<div align="center"><img src="../../other/img/logo.png" width="300" alt=" logo"></div>

## <div align="center">Vehicle Power Supply System Introduction-車輛電源系統介紹</div> 
- ###  Power Supply Operation System Overview Diagram-電源系統運作概覽圖
  <div align="center"><img src="./img/Power_supply_system.png" ></div>

- ###  Physical Connection Diagram of Power Supply System-電源系統實體連接示意圖
  <div align="center"><img src="./img/Power_supply_system of Summary diagram.png" ></div>

- ### Power Supply System Operation Instructions-電源系統操作說明
### 中文:
### 系統電源配置與電壓分配詳述
本系統的正常運作仰賴於對各電子元件提供其特定且穩定的工作電壓。整體電源架構配置如下：
  - __主電源輸入：__ 採用 3S 鋰聚合物電池作為主要供電來源，其輸出電壓為 12.6V。此電壓直接為降壓模組、Nvidia Jetson Orin Nano 控制板以及 L293D 馬達驅動晶片提供電力，以驅動後端的 12V 直流馬達。
  - __次級降壓與穩壓：__ 配置一個 5A 恆壓恆流降壓電源模組，負責將 12.6V 的輸入電壓精確降壓至 5V。此 5V 穩壓電源專門供給系統中多個需要此電壓運作的元件，包括：
    - Raspberry Pi Pico W
    - L293D 雙 H 橋直流馬達驅動 IC (部分供電或邏輯電平)
    - 超聲波距離感測模組
    - 紅外線感測模組
    - MG90S 前輪伺服馬達
  - __邏輯電壓輸出：__ Nvidia Jetson Orin Nano 控制板內建的穩壓機制，可提供 3.3V氶及5V電壓，專門用於驅動對電壓敏感的週邊設備，如：
    - BNO055 陀螺儀/慣性測量單元 (IMU)(5V)
    - 攝影機模組(3.3V)

__總結：__ 透過上述多層次的電壓轉換與分配，本系統設計確保了所有關鍵電子元件都能在最佳且匹配其規格的工作電壓下穩定、可靠地運行。

  ### 英文:
好的，這是一個專業的技術文件片段，我將依您提供的格式，將其翻譯成專業的英文版本，並使用 Markdown 輸出：

---

### Detailed Description of System Power Configuration and Voltage Distribution

The proper functioning of this system relies on supplying each electronic component with its **specific and stable operating voltage**. The overall power architecture is configured as follows:

* **Main Power Input:** A **3S Lithium Polymer (LiPo) battery** is employed as the primary power source, delivering an output voltage of **12.6V**. This voltage directly powers the step-down module, the **Nvidia Jetson Orin Nano** control board, and the **L293D motor driver IC** for actuating the downstream **12V DC motor**.

* **Secondary Step-Down and Regulation:** A **5V Constant Voltage/Constant Current (CV/CC) Buck Converter Module** is configured to precisely reduce the 12.6V input to **5V**. This **5V regulated power supply** is dedicated to components requiring this voltage, including:
    * Raspberry Pi Pico W
    * L293D Dual H-Bridge DC Motor Driver IC (for partial power supply or logic levels)
    * Ultrasonic Distance Sensor Module
    * Infrared (IR) Reflective Sensor Module
    * MG90S Front Wheel Servo Motor

* **Logic Voltage Output:** The integrated voltage regulation mechanism of the **Nvidia Jetson Orin Nano** control board provides both **3V and 5V** outputs, dedicated to driving voltage-sensitive peripherals, such as:
    * BNO055 Gyroscope/Inertial Measurement Unit (IMU) (5V)
    * Camera Module (3.3V)

**Conclusion:** Through this multi-layered voltage conversion and distribution scheme, the system design ensures that all critical electronic components operate stably and reliably at the **optimal voltage matching their specifications**.

---

# <div align="center">![HOME](../../other/img/home.png)[Return Home](../../)</div>  

