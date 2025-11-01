<div align="center"><img src="../../other/img/logo.png" width="300" alt=" logo"></div>

## <div align="center">Hardware Fool-Proof Design-硬體防呆設計</div>
<div align="center">


</div>

### 中文:
- ####  Pin Header / Socket 
在硬體開發與整合的關鍵階段，我們經常面臨因電源或資料訊號線路誤接，對高價值的 NVIDIA Jetson Orin Nano 模組、Raspberry Pi Pico W 及相關積體電路（IC）造成不可逆轉的損壞風險。為有效規避此類人為操作失誤所帶來的嚴重後果與高昂成本損失，我們在設計中前瞻性地導入了關鍵的防護機制：
- 介面標準化與規範化（Connectorization）： 針對電源輸入及資料傳輸介面，全面採用標準化的公母插座(Pin Header/Socket)，以強制確保連接的方向性與正確性，杜絕因插拔錯誤導致的損壞。
- 核心電路固化設計： 關鍵電路元件直接焊裝於印刷電路板（PCB）上，實現了極致穩定、佈線規範化的管理，消除了外部線纜連接的潛在弱點。

此結構性設計優化，已顯著降低了 NVIDIA Jetson Orin Nano 及 Raspberry Pi Pi Pico W 核心元件因接線錯誤而發生故障的機率，從根本上提升了整體系統的運行穩定性、長期可靠性，並有效地延長了產品的平均使用壽命。

- #### pluggable terminal block
為確立 Jetson Orin Nano 的電源輸入方案，我們於主電路 PCB 板上新增了插拔式接線端子，作為其專用的電源供應介面。

此設計的決策依據如下：
- 供電路徑要求： Jetson Orin Nano 依賴 11.1V 鋰電池直接透過電源插座供電，不支持從其 5V 腳位進行反向供電。
- 連接穩定性： 直接將電源線連接至降壓模組存在接觸鬆脫的潛在風險，這可能導致電路供電不穩，進而造成電路板損壞。

綜上所述，採用插拔式接線端子作為電源供應線的連接介面，不僅能確保連接的穩固性與提升系統整體安全性，更便利了後續的維修與故障排除作業。

During critical phases of hardware development and integration, we frequently encounter the risk of irreversible damage to high-value modules such as the __NVIDIA Jetson Orin Nano__, __Raspberry Pi Pico W__, and related Integrated Circuits (ICs) due to incorrect wiring of power or data signal lines. To effectively mitigate the severe consequences and __high costs associated__ with such human operational errors, we have proactively implemented key protective mechanisms in our design:

- **Interface Standardization and Specification (Connectorization):** For power input and data transmission interfaces, we universally adopt standardized male and female connectors(Pin Header/Socket) to forcibly ensure correct orientation and connection, thus eliminating damage caused by incorrect insertion.

- **Core Circuit Solidification Design:** Critical circuit components are directly soldered onto the Printed Circuit Board (PCB), achieving extremely stable, normatively laid-out management, which eliminates the potential weak points associated with external cable connections.

This structural design optimization has significantly reduced the probability of failure in the core components of the NVIDIA Jetson Orin Nano and Raspberry Pi Pico W due to wiring mistakes, fundamentally enhancing the overall system's operational stability, long-term reliability, and effectively extending the product's Mean Time Between Failures (MTBF).

To establish the power input solution for the __Jetson Orin Nano__, we have incorporated a __pluggable terminal block__ onto the main circuit PCB as its dedicated power supply interface.

The rationale for this design choice is as follows:

- **Power Path Requirement:** The Jetson Orin Nano relies on 11.1V lithium battery power supplied directly via the power socket and does not support reverse power delivery from its 5V pins.

- **Connection Stability:** Directly connecting the power cable to a buck converter module carries the inherent risk of contact loosening, which could lead to unstable circuit power delivery and potentially damage the PCB.

In summary, utilizing a pluggable terminal block as the interface for the power supply cable ensures connection stability and enhances overall system safety, while also facilitating subsequent maintenance and troubleshooting operations.

<div align=center>
    <table>
        <tr>
            <th>Pluggable Terminal Block(Power supply Terminal Block)</th>
            <th>Actual Photo of the Circuit(Power supply)</th>
        </tr>
        <tr align=center>
            <td><img src="./img/Pluggable Terminal Block.png" width=400 alt="Terminal block" /></td>
            <td><img src="./img/Circuit 2.png" width=400 alt="Circuit" /></td>
        </tr>
    </table>
</div>

<div align=center>
    <table>
        <tr>
            <th width=500>Top side of the PCB</th>
            <th width=500>Bottom Side of the PCB</th>
        </tr>
        <tr align=center>
            <td><img src="./img/PCB_Body_Fount.png" width=400 alt="Circuit Body Fount" /></td>
            <td><img src="./img/PCB_Body_Bottom.png" width=400 alt="Circuit Body Bottom" /></td>
        </tr>
    </table>
</div>

<div align=center>
<table>
<tr>
<th>2.5mm Connector 2/3 Pin Male/female Adapter Right Angle Pin Header White Socket(2.5毫米接頭 2/3 針公母轉接頭 直角針腳 白色插座)</th>
<th>Actual Photo of the Circuit(電路實際照片)</th>
</tr><tr>
<td width=500 align=center><img src="./img/pin.jpg" width="400" height="400" alt="pin"></td> 
<td width=500 align=center><img src="./img/ciruit.png" width="400" height="400" alt="ciruit"></td> 
</tr>
</table>
</div>

# <div align="center">![HOME](../../other/img/home.png)[Return Home](../../)</div>  
