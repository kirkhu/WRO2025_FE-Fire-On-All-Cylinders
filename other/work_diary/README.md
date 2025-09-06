<div align="center"><img src="../../other/img/logo.png" width="300" alt=" logo"></div>

# <div align="center">Work Diary-工作日記</div>
以下是本次自動駕駛汽車模型設計與任務解決的開發記錄，涵蓋了機械設計與製造、電路設計與實現、電子裝置選型、程式設計與測試以及整體的解題過程。

The following is a development record of the self-driving car model design and task-solving, covering mechanical design and manufacturing, circuit design and implementation, electronic device selection, programming and testing, and the overall problem-solving process.
## 2025/2/28 ~ 2025/3/30  

**成員:** 胡賢邑、林展榮、張奕崴

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
**成員:** 胡賢邑、林展榮、張奕崴

**內容:**

 - 我們在這一周進行了主控制器系統安裝及測試，同時也開始了避障程序的撰寫和反覆測試穩定性、修改程序中的問題以求在避賽中取得亮眼的成績。

<div align="center">
    <table>
        <tr align=center>
            <th width=50% style="text-align: center;">系統安裝</th>
            <th width=50% style="text-align: center;">避障程序撰寫</th>
        </tr>
        <tr>
            <td><img src="./img/3/1.jpg"/></td>
            <td><img src="./img/3/3.jpg"/></td>
        </tr>
    </table>
</div>

## 2025/03/11 ~ 2025/03/17

**成員:** 胡賢邑、林展榮、張奕崴

**內容:**  

 - 為了讓電路板配置更整齊，我們採用 EasyEDA 繪製電路板，並將設計完成的圖稿透過洗印方式製作出第一代電路板。由於這是我們首次接觸電路板設計，當時未能注意到設計軟體中其實已提供標準的元件排版範例。我們改以自行測量排針與排針之間的間距，但因經驗不足，最終在電路板製作完成後才發現設計的間距過小，導致元件無法順利插入。這次失誤讓我們獲得了寶貴的學習經驗，也立即推動我們對設計進行修正與優化。經過快速調整後，我們完成了第二代電路板，成功解決了間距問題，使元件安裝更為順利，整體佈線也更加合理。

 - To achieve a more organized circuit board layout, we used EasyEDA to design the PCB and then fabricated the first-generation board using a printed-etching process. Since this was our first experience with PCB design, we failed to notice that the software already provided standard component layout templates. Instead, we manually measured the spacing between pin headers. Due to our lack of experience, we only discovered after fabrication that the spacing was too narrow, which prevented the components from being properly inserted. This mistake provided us with valuable hands-on experience and immediately motivated us to revise and optimize our design. After a quick round of adjustments, we successfully developed the second-generation PCB, which resolved the spacing issue, improved component installation, and made the overall wiring layout more efficient.
<div align="center" >
<table >
<tr align="center">
<th>第一代正面</th>
<th>第一代背面</th>
<tr align="center">
<td>
<img src="./img/4/1.png" width = "300"  alt="data" align=center /></td>
<td>
<img src="./img/4/2.png" width = "300"  alt="data" align=center /></td>
</tr>
</table>
</div>

## 2025/04/3 ~ 2025/04/14

**成員:** 胡賢邑、林展榮、張奕崴

**內容:**  
 - 在第二代版本開發過程中，我們基於第一代的反饋，透過內建範例圖重新校準排針間距，成功優化了原始設計。然而，因作業疏忽導致 PCB 佈局時誤將背面視圖當作正面設計，致使電路板輸出後極性顛倒。此問題於組裝測試階段立即被發現，並於第三代版本中修正佈局方向，同時複查所有層面對齊規範，確保設計與實體成品的一致性。

<div align="center" >
    <table >
        <tr align="center">
            <th>第二代正面</th>
            <th>第二代背面</th>
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
**成員:** 胡賢邑、林展榮、張奕崴

**內容:** 


- 經修正前兩代的設計問題後，第三代版本已成功通過功能測試。實際運行測試顯示，排針接點與電路佈局無異常，系統可穩定運作。
<div align="center" >
<table >
<tr align="center">
<th>第三代正面</th>
<th>第三代背面</th>
<tr align="center">
<td>
<img src="./img/6/5.png" width = "300"  alt="data" align=center /></td>
<td>
<img src="./img/6/6.png" width = "300"  alt="data" align=center /></td>
</tr>
</table>
</div>

## 2025/07/2 ~ 2025/07/21
**成員:** 胡賢邑、林展榮、張奕崴

**內容:** 

 - 我們在進行避障程序的測試時，注意到了自駕車在進行過彎時會有些許卡頓，經過檢查過後發現問題出現在底盤上，因為轉向節跟底盤直接接觸，之間的磨擦力導致傳向結構出現卡頓，所以我們將原本用來接觸轉向節的孔洞擴大改為放置軸承用於減小摩擦力，經過測試後新版底板的軸承結構讓轉彎更加順暢。

 <div align=center>
    <table>
        <tr>
            <th colspan=2>修改前與修改後</th>
        </tr>
        <tr>
            <td><img src="./img/7/前底盤.png"/></td>
            <td><img src="./img/7/現底盤.png"/></td>
        </tr>
    </table>
 </div>

## 2025/08/25 ~ 2025/08/31
**成員:** 胡賢邑、林展榮、張奕崴

**內容:**
- 有了這次全國賽的經驗之後，發現了Jetson Nano在運算方面的不足，所以我們決定將主控制器改為運算效率更高的Jetson Orin Nano，並且著手研究使用Web Sucks搭建Jetson Orin Nano和Raspberry Pico之間的通訊，因為搭建Web Sucks通訊需要雙方都能連線到網路，因此我們將原先的Raspberry Pi Pico換成Raspberry Pi Pico2 WH，以應對需要WIFI的需求。

<div align=center>
    <table>
       <tr>
           <th width=50%>本次全國賽機型</th>
           <th width=50%>本次國際賽機型</th>
       </tr>
       <tr>
           <td align=center><img src="./img/8/5.png" height=200/></td>
           <td align=center><img src="./img/8/6.png" height=200/></td>
       </tr>
       <tr>
           <th>一代轉向結構</th>
           <th>二代轉向結構</th>
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