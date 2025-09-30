<div align=center> <img src="../../other/img/logo.png" width=300 alt=" logo"> </div>

## <div align="center">Software Platform Construction </div> 

- 安裝前的準備
<ol>
    <li>需要一台原生Ubuntu系統主機***不能使用虛擬機***</li>
    <li>確保Jetson Orin Nano上面已經安裝SSD─用於硬體加速</li>
</ol>

### Nvidia SDK Manager 安裝

- 到官網下載SDK Manager的安裝包=>[超連結](https://developer.nvidia.com/sdk-manager)

  <img src="./img/NVIDIA SDK Manager Download Page.png" width=800>

- 開啟下載資料夾雙擊安裝包，若是安裝完成並且登入成功後開啟可以看到以下畫面

  <img src="./img/Start SDK Manager Page.png" width=800>

### 進行JetPack的升降及安裝操作界紹

- SDK Manager是NVIDIA的官方工具，可以進行Jetson主機的JetPack版本升降級，以下是SDK Manager的操作過程。

  <div align=center>
   <table>
    <tr>
     <th>將Jetson接上主機</th>
     <th>確認是否連接成功</th>
     <th>選擇開發者套件</th>
    </tr>
    <tr>
     <td><img src="./img/11.jpg" width=400 /></td>
     <td><img src="./img/12.png" width=400 /></td>
     <td><img src="./img/13.png" width=400 /></td>
    </tr>
    <tr>
     <th>在選單中選中所需的JetPack版本</th>
     <th>勾選左側選項，點擊下一步</th>
     <th>輸入管理者密碼</th>
    </tr>
    <tr>
     <td><img src="./img/14.png" width=400 /></td>
     <td><img src="./img/15.png" width=400 /></td>
     <td><img src="./img/16.png" width=400></td>
    </tr>
    <tr>
     <th>填入主機板的相關資訊</th>
     <th>安裝完畢後點擊"Finish"結束</th>
     <th>安裝完畢後的Jetson Orin Nano系統介面</th>
    </tr>
    <tr>
     <td><img src="./img/17.png" width=400 /></td>
     <td><img src="./img/18.png" width=400 /></td>
     <td><img src="./img/19.png" width=400 /></td>
    </tr>
   </table>
  </div>

### 系統配置

- 下載

# <div align="center">![HOME](../../other/img/home.png)[Return Home](../../)</div> 