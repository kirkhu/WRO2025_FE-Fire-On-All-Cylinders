<div align="center"><img src="../../other/img/logo.png" width="300" alt=" logo"></div>

## <div align="center">Introduction to TCRT5000 Infrared Line Tracking Sensor</div>

- ### __Introduction to TCRT5000 Infrared Line Tracking Sensor__

TCRT5000是一款常見的反射型紅外線感測器( Infrared Reflective Sensor )，內部由紅外線發射二極體( IR LED )與光電晶體( Phototransistor )組成。它的工作原理是透過紅外線發射端發出不可見光，當光線遇到前方物體表面時，會反射回感測器的接收器。若接收端偵測到反射光，即可判斷前方是否有物體存在。

The TCRT5000 is a prevalent Infrared Reflective Sensor that integrates an Infrared Emitting Diode (IR LED) and a Phototransistor. Its operation involves the IR LED transmitting invisible light. When this light reflects off a nearby object's surface and is detected by the receiver, the sensor determines the presence of the object.

<div align="center" width=100%>
<table  align="center">
  <tr>
  <TH>Top View
  </TH>
  <TH>Bottom View
  </TH>
  </tr>
  <tr>
  <td align=left width=500>
    <img src="./img/TCRT5000_front.png" width="50%" />
  </td>
  <td align=center width=500>
  <img src="./img/TCRT5000_back.png" width="50%" />
  </td>
   </tr>
  </table>
</div>

<div align=center width=100%>
    <table  align="center">
        <tr align=center>
            <th colspan=2>TCRT5000 Infrared Sensor Placement Diagram on Vehicle</th>
        </tr>
        <tr align=center>
            <th>Front</th>
            <th>Rear</th>
        </tr>
        <tr>
            <td align=center><img src="./img/Car_Front_TCRT5000.png" width=500 /></td>
            <td align=center><img src="./img/Car_Back_TCRT5000.png" width=500 /></td>
        </tr>
    </table>
</div>

- ### Wiring steps for connecting the TCRT5000 to the Raspberry Pi Pico W:
    - TCRT5000 的 GND 腳位連接到 Raspberry Pi Pico W 的接地腳位。
    - TCRT5000 的 A0 腳位連接到 Raspberry Pi Pico W 的 GPIO 腳位：
        - 腳位26(前方)
        - 腳位27(後方)，用於輸出紅外反射量的電壓訊號。
    - 以下是 MicroPython 撰寫的程式碼，以類別形式呈現，能透過 Raspberry Pi Pico W 讀取 TCRT5000 紅外線循線感測器的紅外反射量電壓訊號。

- ### The following are the wiring and programming details for the TCRT5000:

* The **GND** pin of the TCRT5000 is connected to a **Ground (GND) pin** on the Raspberry Pi Pico W.
* The **A0** (Analog Output) pin of the TCRT5000 is connected to the following **GPIO pins** on the Raspberry Pi Pico W:
    * **GPIO 26 (Front)**
    * **GPIO 27 (Rear)**
    * *(Note: The A0 pin provides the voltage signal representing the amount of infrared reflection.)*
* The following code is written in **MicroPython** and presented in a **class structure** to allow the Raspberry Pi Pico W to read the **infrared reflection voltage signal** from the TCRT5000 line-following sensor.

- ### MicroPython Code
    ```python
    class TCRT5000:
        def __init__(self, adc_pin):
            try:
                self.adc = ADC(Pin(adc_pin))
            except:
                self.adc = None

        def read_raw(self):
            try:
                return self.adc.read_u16()
            except:
                return -1

        def read_percentage(self):
            try:
                raw = self.read_raw()
                if raw == -1:
                    return -1
                percentage = (raw / 65535) * 100
                return round(percentage, 1)
            except:
                return -1
    ```

- ### Example usage
    ```python
    if __name__ == "__main__":
        sensor = TCRT5000(adc_pin=26)
        while True:
            raw_val = sensor.read_raw()
            percent = sensor.read_percentage()
            print("Raw ADC:", raw_val, " 反射強度百分比:", percent, "%")
            time.sleep(0.2)
    ```

- ### Explanation
    此程式碼包含一個名為 TCRT5000 的類別，透過定義模擬輸出（A0）腳位來測量紅外線反射強度。read_raw() 方法會回傳原始 ADC 數值，read_percentage() 方法會回傳反射強度的百分比（0~100%），可用於判斷黑線或白線。若讀取過程發生錯誤，則可回傳 -1。

# <div align="center">![HOME](../../other/img/home.png)[Return Home](../../)</div> 