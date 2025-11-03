<div align="center"><img src="../../other/img/logo.png" width="300" alt=" logo"></div>

## <div align="center">WebSockets Introduction</div>

- Based on our past competition experience, data transmission between our main controller and the subordinate controller relies on the UART protocol. However, as UART is an asynchronous serial communication mechanism, it mandates that both the transmitter and receiver pre-set an identical Baud Rate, with the permissible deviation strictly controlled to within 10%. Exceeding this tolerance is highly prone to generating timing errors, resulting in data distortion or loss.

- This inherent limitation not only substantially increases the complexity of practical system calibration but can also directly lead to vehicle decision-making deviations and inaccurate path judgments, consequently impacting overall competition performance. Therefore, this year, we are actively seeking communication alternatives that offer higher stability and reliability, with the aim of ensuring our autonomous vehicle control system maintains precise and real-time operational efficiency throughout the competitive environment.

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
            <th>Communication Type</th>
            <td>Single Request/Response (Half-Duplex)</td>
            <td>Persistent Connection / Bidirectional Real-Time (Full-Duplex)</td>
            <td>Hardware Point-to-Point Serial Communication (Full-Duplex)</td>
        </tr>
        <tr>
            <th>Connection Establishment Method</th>
            <td>Stateless Connection: Reestablished per Request</td>
            <td>Persistent Connection After Single Handshake (Stateful)</td>
            <td>No Software Handshake: Physical Layer Direct Connection</td>
        </tr>
        <tr>
            <th>Real-time Capability</th>
            <td>Lower (High Latency: Requires Repeated Connections and Polling)</td>
            <td>Extremely High (Low Latency: Features Server Push Capability)</td>
            <td>Extremely High (Ultra-Low Latency: Real-Time Hardware Signal Transfer)</td>
        </tr>
        <tr>
            <th>Transmission Medium </th>
            <td>Application Layer: Dependent on TCP/IP Network Infrastructure</td>
            <td>Application Layer: Protocol Upgrade Based on TCP/IP</td>
            <td>Hardware Physical Layer: Directly via TX/RX Transmission Lines</td>
        </tr>
        <tr>
            <th>Application Scenarios</th>
            <td>-Static Web Content Retrieval, RESTful API Services, Single Data Requests</td>
            <td>Real-Time Dashboards, Interactive Applications, Remote Robotics or IoT Monitoring</td>
            <td>Embedded System Inter-Device Communication, Main/Subordinate Controller Data Exchange</td>
        </tr>
        <tr>
            <th>Transmission Latencyy</th>
            <td>High (Requires repeated connection establishment, Millisecond-level)</td>
            <td>Low (Persistent connection, Stable Millisecond/Sub-millisecond level)</td>
            <td>Ultra-Low (Hardware layer direct transmission, Microsecond level or lower)</td>
        </tr>
    </table>
</div>

- Based on the preceding analysis, we have confirmed that the WebSockets protocol represents a persistent-connection, bidirectional, real-time communication technology. Unlike the request-response paradigm of the traditional HTTP protocol, WebSockets enable the client and server to establish an always-open, dedicated data channel. Both parties can actively push messages at any time, significantly eliminating transmission latency caused by repetitive connection establishment. Its inherent characteristics of high speed and low latency make it an ideal choice for systems requiring rapid response, such as real-time IoT device monitoring and robotic control applications.

- From a software implementation perspective, this solution is highly feasible: the client side can utilize the JavaScript WebSocket object for connection, while the server side can flexibly implement the WebSocket service using mainstream technology stacks like Python (e.g., the WebSockets library or FastAPI framework), Node.js, or Go.

- Although WebSockets operates at the network application layer, its bidirectional real-time communication model and high stability perfectly align with the core requirements for stable, two-way data exchange traditionally fulfilled by the UART protocol in embedded systems. Consequently, we have decided to adopt WebSockets as the high-efficiency alternative to resolve the inherent limitations of UART.

- In the Self-Driving Cars architecture for this competition, we successfully deployed the WebSockets protocol to achieve efficient information exchange between the Jetson Orin Nano (acting as the main controller) and the Raspberry Pi Pico W (serving as the subordinate controller). This includes the transmission of precise chassis control parameters and the real-time return of sensor data. Through this stable and low-latency communication framework, we have significantly enhanced the vehicle's response speed and overall control accuracy.




### CODE


 # <div align="center">![HOME](../../other/img/home.png)[Return Home](../../)</div>  