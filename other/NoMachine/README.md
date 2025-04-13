<div align="center"><img src="../../other/img/logo.png" width="300" alt=" logo"></div>

## <div align="center">NoMachine Introduction</div> 

- NoMachine is a high-performance remote desktop access software that offers cross-platform support, allowing users to remotely connect to another computer anytime, anywhere. Its main features include a fast and smooth remote operation experience, compatible with various operating systems such as Windows, macOS, Linux, iOS, and Android.
- NoMachine uses advanced image compression technology to ensure high-quality graphics and audio transmission, even in low-bandwidth network environments. Additionally, NoMachine supports remote printing, file sharing, USB transfer, and other functions, making it ideal for remote work, technical support, and multi-device management. 
- Especially for development platforms like the NVIDIA® Jetson Nano, NoMachine provides a convenient solution for wireless remote control, greatly enhancing device operational flexibility and application possibilities.

- ### Installing NoMachine
    - #### On the NVIDIA® Jetson Nano
      To install NoMachine on an NVIDIA® Jetson Nano, follow these steps:

      __Download NoMachine for Linux ARM:__
        - In the Jetson Nano’s controller interface, open a browser and navigate to the <a href="https://downloads.nomachine.com/download/?id=1" target="_blank">NoMachine download page</a>. Locate and select the NoMachine for Linux ARM (64-bit) software package, which is compatible with the Jetson Nano.      
        - After downloading, open the terminal and enter cd Downloads to navigate to the folder.
        ```
        cd Downloads
        ```
        - Then, enter unzip Nomachine_7.10.1_1_arm64.zip to unzip the file.
        ```
        unzip Nomachine_7.10.1_1_arm64.zip
        ```
        - Once extracted, enter sudo dpkg -i nomachine_7.10.1_1_arm64.deb to install.
        ```
        sudo dpkg -i nomachine_7.10.1_1_arm64.deb
        ```
        If you see this icon, the installation is complete.
        
        <td><img src="./img/nomachine_ok.png" width="500" alt="nomachine download"></td>

    - #### On the Windows System  of Computer        
      To install NoMachine on Windows, follow these steps:
      
      __Download NoMachine for Windows (64-bit)__
        - In a Windows computer, open a browser and go to the <a href="https://downloads.nomachine.com/windows/?id=3" target="_blank">NoMachine download page</a>. Find and select the NoMachine for Windows (64-bit) software package to download the version compatible with Windows.
        - After downloading, run the installation file. You will need to __restart__ the computer afterward.
        <td><img src="./img/nomachine_download.jpg" width="500" alt="nomachine download"></td>


    - #### Connecting to Jetson Nano
         Open NoMachine on Windows.

         <img src="./img/nomachine_open.jpg" width="500" alt="nomachine open">

        Enter the Jetson Nano IP address.

        Find the IP address.
        ```
        ifconfig  
        ```
        Find the username.
        ```
        hostname 
        ```
        <td><img src="./img/nomachine_ip.jpg" width="500" alt="nomachine ip"></td>

        After connecting, enter the username and password. 
        <td><img src="./img/nomachine_connet.jpg" width="500" alt="nomachine connet"></td>

        Once done, you’ll be able to connect.
        <td><img src="./img/nomachine_jetson_ok.jpg" width="500" alt="nomachine jetson ok"></td>

    - #### Reference link:
    - <a href="https://www.waveshare.net/wiki/JetRacer_ROS_AI_Kit_%E6%95%99%E7%A8%8B%E4%BA%8C%E3%80%81%E5%AE%89%E8%A3%85Jetson_nano_%E9%95%9C%E5%83%8F?fbclid=IwZXh0bgNhZW0CMTEAAR0V-M05bMx0xIQx-QcMI9sqtP8dBWXZpjhOegNngVdwizYW9Frqc738AiA_aem_wfqPbQnY9yv5tcLjEwcHYw#Jetson_Nano.E4.B8.8A.E5.AE.89.E8.A3.85" target="_blank">Waveshare Wiki</a>
    - <a href="https://www.nomachine.com/" target="_blank">NoMachine Website</a>
    - <a href="https://en.wikipedia.org/wiki/NX_technology" target="_blank">Wikipedia</a>

# <div align="center">![HOME](../img/home.png)[Return Home](../../)</div> 
