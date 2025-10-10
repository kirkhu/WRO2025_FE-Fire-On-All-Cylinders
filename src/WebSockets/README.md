<div align="center"><img src="../../other/img/logo.png" width="300" alt=" logo"></div>

## <div align="center">Web Sockets Introduction</div>

- Web Sockets 是一種在單一 TCP 連線上實現全雙工(Full-duplex)通訊的網路協定，讓伺服器與用戶端能夠在建立連線後持續交換資料，而不需要像傳統HTTP那樣每次都重新建立連線。這項技術特別適合即時性應用，例如線上聊天、即時遊戲、即時股價更新、物聯網資料傳輸等。

- 當用戶端透過HTTP發出WebSockets請求並與伺服器完成握手之後，雙方之間就能自由地互傳訊息。與輪詢(Polling)或常連線(Long Pollling)相比，WebSockets的資料傳輸延遲更低、效能更高，也能顯著減少伺服器的負擔。

- 在程式設計上，開發者可以透過Javascript的WebSocket物件用於瀏覽器端建立連線，伺服器端則常用Python(如WebSockets、FastAPI)、Node.js、Go等框架支援。

- 而在此次比賽中我們就使用的Web Sockets這種通訊協定，使Jetson Orin Nano和Raspberry Pi Pico W可以進行資訊交換，像是傳送底盤控制參數，感測器數值交換等。以下是三種傳輸協定的特性比較。

<div align=center>
    <table width=500>
        <tr>
            <th colspan=4>WebSockets vs HTTP vs UART 比較</th>
        </tr>
        <tr>
            <td>特性</td>
            <td>HTTP</td>
            <td>WebSockets</td>
            <td>UART</td>
        </tr>
        <tr>
            <td>通訊型態</td>
            <td>請求 - 回應(半雙工)</td>
            <td>持續連線(全雙工)</td>
            <td>點對點(全雙工)</td>
        </tr>
        <tr>
            <td>建立連線</td>
            <td>每次請求都重新建立</td>
            <td>只需一次握手，保持連線</td>
            <td>物理層面直接連線</td>
        </tr>
        <tr>
            <td>即時性</td>
            <td>低(需重複請求)</td>
            <td>高(伺服器可主動推送)</td>
            <td>高(即時傳輸)</td>
        </tr>
        <tr>
            <td>傳輸媒介</td>
            <td>網路(TCP/HTTP)</td>
            <td>網路(TCP/WebSocket協定)</td>
            <td>實體線路（UART TX/RX）</td>
        </tr>
        <tr>
            <td>適用場景</td>
            <td>網頁瀏覽、API 請求</td>
            <td>即時聊天、線上遊戲、IoT</td>
            <td>裝置間資料傳輸</td>
        </tr>
        <tr>
            <td>延遲</td>
            <td>高</td>
            <td>低</td>
            <td>低</td>
        </tr>
    </table>
</div>

