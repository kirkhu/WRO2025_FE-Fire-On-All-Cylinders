<div align="center"><img src="../../other/img/logo.png" width="300" alt=" logo"></div>

# <div align="center">Work Diary-工作日記</div>
以下是本次自動駕駛汽車模型設計與任務解決的開發記錄，涵蓋了機械設計與製造、電路設計與實現、電子裝置選型、程式設計與測試以及整體的解題過程。

The following is a development record of the self-driving car model design and task-solving, covering mechanical design and manufacturing, circuit design and implementation, electronic device selection, programming and testing, and the overall problem-solving process.
## 2025/2/28 ~ 2025/3/30  

**成員:** 胡賢邑、林展榮、張奕崴 

**內容:**  


我的搭檔隊友是胡賢邑過去幾年曾多次參與「未來工程師大賽」，在機械結構設計與程式控制優化方面累積了扎實的實戰經驗。然而，由於該競賽每年皆會更新主題與挑戰規則，我們經過深入討論後，決定對今年的參賽模型進行輕量化改良——將整體機構縮小，如此不僅能提升場地穿梭的靈活性，避免與障礙方塊發生碰撞，還能更好停車避免撞到牆，進一步強化競賽表現。



<div align="center">
<table>
<tr align="center">
<th colspan="2">Last year's senior's model</th>
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

## 2025/03/11 ~ 2025/03/17

**成員:** 胡賢邑、林展榮、張奕崴

**內容:**  

- 我們為了要讓電路板變得更整齊我使用洗電路板方式這樣的方式，開發第一代電路板，由於是初次接觸電路板設計，我們未能注意到設計軟體中提供的標準範例圖。當時我們自行測量了排針與排針之間的間距，結果在電路板製作完成後才發現間距設計過小，導致元件無法順利插接。這個寶貴的經驗促使我們立即著手改進，並很快做了第二代優化版本。
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





## 2025/4/3 ~ 2025/4/14

**成員:** 胡賢邑、林展榮、張奕崴

**內容:**  

在第二代版本開發過程中，我們基於第一代的反饋，透過內建範例圖重新校準排針間距，成功優化了原始設計。然而，因作業疏忽導致 PCB 佈局時誤將背面視圖當作正面設計，致使電路板輸出後極性顛倒。此問題於組裝測試階段立即被發現，並於第三代版本中修正佈局方向，同時複查所有層面對齊規範，確保設計與實體成品的一致性。

<div align="center" >
<table >
<tr align="center">
<th>第二代正面</th>
<th>第二代背面</th>
<tr align="center">
<td>
<img src="./img/4/3.png" width = "300"  alt="data" align=center /></td>
<td>
<img src="./img/4/4.png" width = "300"  alt="data" align=center /></td>
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
  
## 2025/08/25 ~ 2025/08/31
**成員:** 胡賢邑、林展榮、張奕崴
**內容:**
- 有了全國賽的經驗之後，我們在阿克曼轉向結構上做出改動，我們為了增加自駕車的轉向角度，因此我們將原先拉桿上的螺絲和十字軸連接改為球狀結構連接。同時我們開始研究如何使用Web Suck搭建Jetson Orin Nano和Raspberry Pi Pico之間的通訊橋梁，為了配合研究我們將Raspberry Pi Pico換成了擁有Wifi模塊的Raspberry Pi Pico2 WH作為此次比賽的I/O控制器。

<div align="center">
    <table>
        <tr align="center">
            <th width="50%" style="text-align: center;">修改前轉向結構</th>
            <th width="50%" style="text-align: center;">修改後轉向結構</th>
        </tr>
        <tr>
            <td><img src="./img/8/2.jpg"></td>
            <td><img src="./img/8/1.jpg"></td>
        </tr>
    </table>
</div>

<div align="center">
    <table>
        <tr align="center">
            <th width="50%" style="text-align: center;">Raspberry Pi Pico</th>
            <th width="50%" style="text-align: center;">Raspberry Pi Pico2 WH</th>
        </tr>
        <tr>
            <td align="center"><img src="./img/8/3.png" height=300></td>
            <td align="center"><img src="./img/8/4.png" height=230></td>
        </tr>
    </table>
</div>

# <div align="center">![HOME](../../other/img/home.png)[Return Home](../../)</div>