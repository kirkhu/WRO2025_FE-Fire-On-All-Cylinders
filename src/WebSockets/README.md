<div align="center"><img src="../../other/img/logo.png" width="300" alt=" logo"></div>

## <div align="center">Web Sockets Introduction</div>

- 回顧歷屆競賽經驗，我們的主控系統與下位控制器之間的資料交換是仰賴 UART 協定。然而，由於 UART 屬於非同步串列通訊機制，要求發送端與接收端必須預先達成一致的鮑率設定，且容許誤差須嚴格控制在 10% 以內。一旦超出此範圍，便極易引發時序錯誤，導致資料失真或遺失。此一固有限制不僅大幅提升了系統實務調校的複雜度，更可能直接導致自駕車的決策偏差與路徑判斷失準，從而嚴重影響最終的競賽成績。有鑒於此，我們今年積極尋求具備更高穩定性與可靠度的通訊替代方案，以期確保自駕車控制系統在激烈的競賽環境中，能始終維持精確且即時的運作效能。

- Based on our past competition experience, data transmission between our main controller and the subordinate controller relies on the UART protocol. However, as UART is an asynchronous serial communication mechanism, it mandates that both the transmitter and receiver pre-set an identical Baud Rate, with the permissible deviation strictly controlled to within 10%. Exceeding this tolerance is highly prone to generating timing errors, resulting in data distortion or loss.

- This inherent limitation not only substantially increases the complexity of practical system calibration but can also directly lead to vehicle decision-making deviations and inaccurate path judgments, consequently impacting overall competition performance. Therefore, this year, we are actively seeking communication alternatives that offer higher stability and reliability, with the aim of ensuring our autonomous vehicle control system maintains precise and real-time operational efficiency throughout the competitive environment.

- 為了解決 UART 通訊固有的穩定性與即時性限制，並提升自駕車系統在嚴苛競賽環境下的運作精確度，以下將針對三種常見的串列資料傳輸協定進行深入的特性比較與分析
- To address the inherent limitations in stability and real-time performance of the UART protocol, and to enhance the operational precision of our autonomous vehicle system within demanding competition environments, a detailed comparison and analysis of the characteristics of three common serial data transfer protocols will follow. This comparative analysis aims to evaluate each protocol's performance across critical dimensions such as transmission rate, hardware complexity, fault tolerance, and applicability scenarios, thereby serving as the foundation for selecting our next-generation communication solution.

<div align=center>
    <table width=1200>
        <tr>
            <th colspan=4>Comparison of WebSockets vs HTTP vs UART</th>
        </tr>
        <tr>
            <th rowspan=2 width=20%>Characteristics</th>
            <th width=25%><div align=center><img src="img/HTTP.png" width=150/></div></th>
            <th width=25%><div align=center><img src="img/WebSockets.png" width=150/></div></th>
            <th width=25%><div align=center><img src="img/UART.png" /></div></th>
        </tr>
        <tr>
            <th>HTTP</th>
            <th>WebSockets</th>
            <th>UART</th>
        </tr>
        <tr>
            <th>Communication Type 通訊型態</th>
            <td>Single Request/Response (Half-Duplex)-請求 - 回應(半雙工)</td>
            <td>Persistent Connection / Bidirectional Real-Time (Full-Duplex)-持續連線(全雙工 )</td>
            <td>Hardware Point-to-Point Serial Communication (Full-Duplex)-點對點(全雙工)</td>
        </tr>
        <tr>
            <th>Connection Establishment Method - 建立連線</th>
            <td>Stateless Connection: Reestablished per Request-每次請求都重新建立</td>
            <td>Persistent Connection After Single Handshake (Stateful)-只需一次握手，保持連線</td>
            <td>No Software Handshake: Physical Layer Direct Connection-物理層面直接連線</td>
        </tr>
        <tr>
            <th>Real-time Capability-即時性</th>
            <td>Lower (High Latency: Requires Repeated Connections and Polling)-低(需重複請求)</td>
            <td>Extremely High (Low Latency: Features Server Push Capability)-高(伺服器可主動推送)</td>
            <td>Extremely High (Ultra-Low Latency: Real-Time Hardware Signal Transfer)-高(即時傳輸)</td>
        </tr>
        <tr>
            <th>Transmission Medium 傳輸媒介</th>
            <td>Application Layer: Dependent on TCP/IP Network Infrastructure-網路(TCP/HTTP)</td>
            <td>Application Layer: Protocol Upgrade Based on TCP/IP -網路(TCP/WebSocket協定)</td>
            <td>Hardware Physical Layer: Directly via TX/RX Transmission Lines- 實體線路（UART TX/RX）</td>
        </tr>
        <tr>
            <th>Application Scenarios-適用場景</th>
            <td>-Static Web Content Retrieval, RESTful API Services, Single Data Requests網頁瀏覽、API 請求</td>
            <td>Real-Time Dashboards, Interactive Applications, Remote Robotics or IoT Monitoring-即時聊天、線上遊戲、IoT</td>
            <td>Embedded System Inter-Device Communication, Main/Subordinate Controller Data Exchange-裝置間資料傳輸</td>
        </tr>
        <tr>
            <th>Transmission Latencyy</th>
            <td>High (Requires repeated connection establishment, Millisecond-level)</td>
            <td>Low (Persistent connection, Stable Millisecond/Sub-millisecond level)</td>
            <td>Ultra-Low (Hardware layer direct transmission, Microsecond level or lower)</td>
        </tr>
    </table>
</div>

- 綜合前述分析，我們確認 WebSockets 協定是一種具備持久連線能力的雙向即時通訊技術。相較於傳統 HTTP 協定的請求-回應模式，WebSockets 允許客戶端與伺服器建立一條始終開啟的專屬資料通道，雙方可隨時主動推送訊息，極大程度地消除了反覆連線所造成的傳輸延遲。其高速與低延遲的特性，使其成為 IoT 即時監控、機器人控制等高反應需求系統的理想選擇。

- 在程式實作上，此方案具備高度可行性：前端可利用 JavaScript 的 WebSocket 物件建立連線；而伺服器端則可靈活採用 Python (如 WebSockets 函式庫或 FastAPI 框架)、Node.js 或 Go 等主流技術棧實現服務。

- 儘管 WebSockets 屬於網路應用層協定，但其雙向即時通訊模式與高穩定性，完美契合了 UART 協定在嵌入式系統中對穩定雙向資料交換的核心需求。因此，我們決定採用 WebSockets 作為解決 UART 固有缺陷的高效替代方案。

- 在本次競賽的自駕車架構中，我們成功部署 WebSockets 協定，實現了 Jetson Orin Nano (作為主控端) 與 Raspberry Pi Pico W (作為下位控制器) 之間的高效資訊交換。這包括了精準的底盤控制參數傳輸，以及即時的感測器資料回傳。藉由此穩定且低延遲的通訊架構，我們顯著提升了車輛的反應速度與整體控制精準度。」

-Based on the preceding analysis, we have confirmed that the WebSockets protocol represents a persistent-connection, bidirectional, real-time communication technology. Unlike the request-response paradigm of the traditional HTTP protocol, WebSockets enable the client and server to establish an always-open, dedicated data channel. Both parties can actively push messages at any time, significantly eliminating transmission latency caused by repetitive connection establishment. Its inherent characteristics of high speed and low latency make it an ideal choice for systems requiring rapid response, such as real-time IoT device monitoring and robotic control applications.

- From a software implementation perspective, this solution is highly feasible: the client side can utilize the JavaScript WebSocket object for connection, while the server side can flexibly implement the WebSocket service using mainstream technology stacks like Python (e.g., the WebSockets library or FastAPI framework), Node.js, or Go.

- Although WebSockets operates at the network application layer, its bidirectional real-time communication model and high stability perfectly align with the core requirements for stable, two-way data exchange traditionally fulfilled by the UART protocol in embedded systems. Consequently, we have decided to adopt WebSockets as the high-efficiency alternative to resolve the inherent limitations of UART.

- In the Self-Driving Cars architecture for this competition, we successfully deployed the WebSockets protocol to achieve efficient information exchange between the Jetson Orin Nano (acting as the main controller) and the Raspberry Pi Pico W (serving as the subordinate controller). This includes the transmission of precise chassis control parameters and the real-time return of sensor data. Through this stable and low-latency communication framework, we have significantly enhanced the vehicle's response speed and overall control accuracy."




### CODE


 # <div align="center">![HOME](../../other/img/home.png)[Return Home](../../)</div>  