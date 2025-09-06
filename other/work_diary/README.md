<div align="center"><img src="../../other/img/logo.png" width="300" alt=" logo"></div>

# <div align="center">Work Diary-工作日記</div>
以下是本次自動駕駛汽車模型設計與任務解決的開發記錄，涵蓋了機械設計與製造、電路設計與實現、電子裝置選型、程式設計與測試以及整體的解題過程。

The following is a development record of the self-driving car model design and task-solving, covering mechanical design and manufacturing, circuit design and implementation, electronic device selection, programming and testing, and the overall problem-solving process.
## 2025/2/28 ~ 2025/3/30  

**成員:** HU XIAN-YI, LIN ZHAN-RONG, ZHANG YI-WEI

**內容:**  

 - 我們的隊友胡賢邑在過去幾年多次參加「未來工程競賽」，在機構設計和程式控制優化方面累積了豐富的實戰經驗。不過，由於每年比賽的主題與挑戰規則都會有所調整，我們深入討論後，決定針對今年的參賽模型進行輕量化設計。我們縮小了整體結構，這不僅有助於機器進出停車區時更順利，也讓它在場地中移動更靈活，能更有效避開障礙方塊，整體表現也因此更穩定。

 - Our teammate, Hu Xianyi, has participated in the “Future Engineering Competition” multiple times over the past few years, gaining valuable hands-on experience in mechanical design and programming optimization. Since the competition’s themes and challenge rules change every year, we had an in-depth discussion and decided to redesign this year’s model with a focus on weight reduction. By downsizing the overall structure, the robot can now navigate in and out of the parking zone more smoothly, move more flexibly around the field, and avoid obstacle blocks more effectively — all of which contribute to more consistent and improved performance during the competition.

<div align="center">
<table>
<tr align="center">
<th>Last year's senior's model</th>
<th>This year's senior's model</th>
</tr>
<tr align="center">
<td><img src="../../models/Vehicle_2D_3D/img/right.png"  width="300" alt="Vehicle_cad"></td> 
    <td><img src="../../v-photos/img/right.png" width="300" alt="vehicle Underfloor"></td> 
</tr>
</table>
</div>
<div align="center">
<table>
<tr align="center">
<th >Refer to the seniors GitHub reports(參考學長姐們的Github報告)</th>
</tr>
<tr align="center">
<td> <img src="./img/find_data.jpg" width = "500"  alt="data" align=center /></td>
</tr>
</table>
</div>

## 2025/03/01 ~ 2025/03/07
**成員:** HU XIAN-YI, LIN ZHAN-RONG, ZHANG YI-WEI

**內容:**

 - 我們在這一周進行了主控制器系統安裝及測試，同時也開始了避障程序的撰寫和反覆測試穩定性、修改程序中的問題以求在避賽中取得亮眼的成績。

<div align="center">
    <table>
        <tr align=center>
            <th width=50% style="text-align: center;">System Installation</th>
            <th width=50% style="text-align: center;">Obstacle-Avoidance Program Development</th>
        </tr>
        <tr>
            <td><img src="./img/3/1.jpg"/></td>
            <td><img src="./img/3/3.jpg"/></td>
        </tr>
    </table>
</div>

## 2025/03/11 ~ 2025/03/17

**成員:** HU XIAN-YI, LIN ZHAN-RONG, ZHANG YI-WEI

**內容:**  

 - 為了讓電路板配置更整齊，我們採用 EasyEDA 繪製電路板，並將設計完成的圖稿透過洗印方式製作出第一代電路板。由於這是我們首次接觸電路板設計，當時未能注意到設計軟體中其實已提供標準的元件排版範例。我們改以自行測量排針與排針之間的間距，但因經驗不足，最終在電路板製作完成後才發現設計的間距過小，導致元件無法順利插入。這次失誤讓我們獲得了寶貴的學習經驗，也立即推動我們對設計進行修正與優化。經過快速調整後，我們完成了第二代電路板，成功解決了間距問題，使元件安裝更為順利，整體佈線也更加合理。

 - To achieve a more organized circuit board layout, we used EasyEDA to design the PCB and then fabricated the first-generation board using a printed-etching process. Since this was our first experience with PCB design, we failed to notice that the software already provided standard component layout templates. Instead, we manually measured the spacing between pin headers. Due to our lack of experience, we only discovered after fabrication that the spacing was too narrow, which prevented the components from being properly inserted. This mistake provided us with valuable hands-on experience and immediately motivated us to revise and optimize our design. After a quick round of adjustments, we successfully developed the second-generation PCB, which resolved the spacing issue, improved component installation, and made the overall wiring layout more efficient.
<div align="center" >
<table >
<tr align="center">
<th>First-Generation Front View</th>
<th>First-Generation Back View</th>
<tr align="center">
<td>
<img src="./img/4/1.png" width = "300"  alt="data" align=center /></td>
<td>
<img src="./img/4/2.png" width = "300"  alt="data" align=center /></td>
</tr>
</table>
</div>

## 2025/04/03 ~ 2025/04/14

**成員:** HU XIAN-YI, LIN ZHAN-RONG, ZHANG YI-WEI

**內容:**  
 - 在第二代版本的開發過程中，我們根據第一代的回饋，利用設計軟體內建的範例圖重新校準了排針間距，成功改善了原始設計。然而，由於作業上的疏忽，我們在進行 PCB 佈局時誤將背面視圖當作正面設計，導致電路板輸出後發生極性顛倒的問題。所幸在組裝與測試階段便立即發現此錯誤，並在第三代版本中修正了佈局方向。同時，我們也全面複查了各層的對齊規範，以確保設計檔與實體成品能夠完全一致。

 - During the development of the second-generation version, we incorporated feedback from the first generation and recalibrated the pin header spacing using the built-in reference templates in the design software, successfully improving the original layout. However, due to an operational oversight, we mistakenly treated the back view as the front view during the PCB layout process, which resulted in polarity reversal after fabrication. Fortunately, this issue was identified immediately during the assembly and testing stage. In the third-generation version, we corrected the layout orientation and also conducted a thorough review of alignment rules across all layers to ensure full consistency between the design files and the physical product.

<div align="center" >
    <table >
        <tr align="center">
            <th>Second-Generation Front View</th>
            <th>Second-Generation Back View</th>
        </tr>
        <tr align="center">
            <td>
                <img src="./img/4/3.png" width = "300"  alt="data" align=center />
            </td>
            <td>
                <img src="./img/4/4.png" width = "300"  alt="data" align=center />
            </td>
        </tr>
    </table>
</div>


## 2025/06/03 ~ 2025/06/08  
**成員:** HU XIAN-YI, LIN ZHAN-RONG, ZHANG YI-WEI

**內容:** 


- 經修正前兩代的設計問題後，第三代版本已成功通過功能測試。實際運行測試顯示，排針接點與電路佈局無異常，系統可穩定運作。
<div align="center" >
<table >
<tr align="center">
<th>Third-Generation Front View</th>
<th>Third-Generation Back View</th>
<tr align="center">
<td>
<img src="./img/6/5.png" width = "300"  alt="data" align=center /></td>
<td>
<img src="./img/6/6.png" width = "300"  alt="data" align=center /></td>
</tr>
</table>
</div>

## 2025/07/02 ~ 2025/07/21
**成員:** HU XIAN-YI, LIN ZHAN-RONG, ZHANG YI-WEI

**內容:** 

 - 在進行避障程式測試時，我們注意到自駕車在過彎時會出現些許卡頓。經檢查後發現問題源自底盤結構，因為轉向節與底盤直接接觸，過大的摩擦力導致傳動結構卡滯。為了解決此問題，我們將原本用來固定轉向節的孔洞擴大，並改為放置軸承以降低摩擦。經過測試後，採用軸承的新底盤結構有效改善了轉向的流暢度，使自駕車在過彎時更加平順。

 - During obstacle-avoidance testing, we noticed that the autonomous car experienced slight stuttering when making turns. Upon inspection, we identified the issue in the chassis design: the steering knuckle was in direct contact with the chassis, and the resulting friction caused binding in the transmission structure. To address this, we enlarged the original holes used for mounting the steering knuckle and replaced them with bearings to reduce friction. Testing confirmed that the updated chassis with the bearing structure significantly improved turning smoothness, allowing the car to navigate corners more fluidly.

 <div align=center>
    <table>
        <tr>
            <th colspan=2>Before and After Modification</th>
        </tr>
        <tr>
            <td><img src="./img/7/前底盤.png"/></td>
            <td><img src="./img/7/現底盤.png"/></td>
        </tr>
    </table>
 </div>

## 2025/08/18 ~ 2025/08/24
**成員:** HU XIAN-YI, LIN ZHAN-RONG, ZHANG YI-WEI

**內容:** 
 - 比賽日是8月23日。在上午的資格賽中，我們的車輛在第一場順利完成所有圈數並獲得滿分；但在第二場，由於雷達讀數異常，我們不得不申請維修。修復完成後，距離比賽結束僅剩一分鐘，這使得我們只能完成兩圈。不過，我們仍然順利晉級到下午的障礙賽。

 - 在第一場障礙賽中，車輛因閃避幅度過大撞牆，導致比賽中止。經過調整後，第二場障礙賽順利完成避障，然而，由於未能進入結束區而停止，未能取得理想分數。幸運的是，由於對手出現失誤，我們仍然成功晉級。


 <div align=center>
    <table>
        <tr>
            <th>Waiting for test</th>
            <th>Competition photo</th>
            <th>Competition photo</th>
        </tr>
        <tr>
            <td><img src="./img/8/wait.jpg" width=400/></td>
            <td><img src="./img/8/practise.jpg" width=400/></td>
            <td><img src="./img/8"/></td>
        </tr>
    </table>
 </div>


## 2025/08/25 ~ 2025/08/31
**成員:** HU XIAN-YI, LIN ZHAN-RONG, ZHANG YI-WEI

**內容:**
- 在參加全國賽的過程中，我們發現 Jetson Nano 在運算效能上存在不足，因此決定將主控制器升級為運算效率更高的 Jetson Orin Nano。同時，我們開始研究如何利用 WebSockets 建立 Jetson Orin Nano 與 Raspberry Pi Pico 之間的通訊。由於 WebSockets 通訊需要雙方皆能連線至網路，我們將原本的 Raspberry Pi Pico 更換為具備 WiFi 功能的 Raspberry Pi Pico2 WH，以滿足無線連線的需求。

- From our experience in the national competition, we realized that the Jetson Nano had limitations in terms of computing performance. To address this, we decided to upgrade the main controller to the more powerful Jetson Orin Nano. At the same time, we began exploring the use of WebSockets to establish communication between the Jetson Orin Nano and the Raspberry Pi Pico. Since WebSocket communication requires both devices to have network connectivity, we replaced the original Raspberry Pi Pico with the Raspberry Pi Pico2 WH, which comes with built-in WiFi capability to meet this requirement.

<div align=center>
    <table>
       <tr>
           <th width=50%>Model Used in the National Competition</th>
           <th width=50%>Model Used in the International Competition</th>
       </tr>
       <tr>
           <td align=center><img src="./img/8/5.png" height=200/></td>
           <td align=center><img src="./img/8/6.png" height=200/></td>
       </tr>
       <tr>
           <th>First-Generation Steering Structure</th>
           <th>Second-Generation Steering Structure</th>
       </tr>
       <tr>
           <td align=center><img src="./img/8/2.jpg"/></td>
           <td align=center><img src="./img/8/1.jpg"/></td>
       </tr>
       <tr>
           <th>Raspberry Pi Pico</th>
           <th>Raspberry Pi Pico2 WH</th>
       </tr>
       <tr>
           <td align=center><img src="./img/8/3.png" height=200/></td>
           <td align=center><img src="./img/8/4.png" height=200/></td>
       </tr>
    </table>
</div>

# <div align="center">![HOME](../../other/img/home.png)[Return Home](../../)</div>