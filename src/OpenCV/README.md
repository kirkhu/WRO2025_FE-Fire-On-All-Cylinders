 <div align="center"><img src="../../other/img/logo.png" width="300" alt=" logo"></div>

## <div align="center">OpenCV Introduction－OpenCV介紹</div> 

### 中文:
- OpenCV（開源電腦視覺庫）是一個用於電腦視覺和機器學習的開源軟體庫。它包含 2,500 多種最佳化演算法，涵蓋影像處理、物件偵測、影像辨識、人臉辨識、運動追蹤和 3D 重建等各種視覺任務。 OpenCV 由於其多功能性和高效性，被廣泛應用於自動駕駛、機器人、醫學影像處理和安全監控等不同領域。
- OpenCV 支援多種程式語言（例如 C++、Python 和 Java），並且可以在各種作業系統上運行，包括 Windows、Linux、macOS 和 Android。它不僅可以在 CPU 上運行，還支援 GPU 和嵌入式設備的硬體加速，使其適用於 Nvidia Jetson Nano 和 Raspberry Pi 等資源有限的設備，並能有效運作。
- 因此，OpenCV應用程式可以透過識別賽道上的障礙物和路邊牆壁來協助本次比賽，使車輛能夠避開障礙物並順利完成任務。
### 英文:
- OpenCV (Open Source Computer Vision Library) is an open-source software library for computer vision and machine learning. It consists of over 2,500 optimized algorithms, covering various vision tasks such as image processing, object detection, image recognition, face recognition, motion tracking, and 3D reconstruction. Due to its versatility and efficiency, OpenCV is widely used across different fields, including autonomous driving, robotics, medical image processing, and security surveillance.
- OpenCV supports multiple programming languages (such as C++, Python, and Java) and can run on various operating systems, including Windows, Linux, macOS, and Android. It not only operates on CPUs but also supports hardware acceleration for GPUs and embedded devices, making it suitable for resource-limited devices like the Nvidia Jetson Nano and Raspberry Pi, where it performs efficiently.
- Therefore, the OpenCV application can assist in this competition by recognizing obstacles and roadside walls on the track, enabling the vehicle to avoid obstacles and successfully complete the task.
- ### 在 Nvidia Jetson Nano 上安裝 OpenCV 應用程式的步驟：
- ### Steps to install the OpenCV application on the Nvidia Jetson Nano:
   __1.Update and Upgrade Packages:__
   ```
   sudo apt-get update
   sudo apt-get upgrade
   ```
   __2.install nano__
   ```
   sudo apt-get install nano
   ```
   __3.install dphys-swapfile__
   ```
   sudo apt-get install dphys-swapfile
   ```
   __4.Check Memory__
       Check Memory space to ensure at least 6.5GB is available.
   ```
   free -m
   ```
   __5.Download OpenCV__
   ```
   wget https://github.com/Qengineering/Install-OpenCV-Jetson-Nano/raw/main/OpenCV-4-5-0.sh
   sudo chmod 755 ./OpenCV-4-5-0.sh
   ```
   __6.install OpenCV__
   ```
   ./OpenCV-4-5-0.sh
   rm OpenCV-4-5-0.sh
   ```
   __7.remove the dphys-swapfile to save an additional 275 MB__
   ```
   sudo /etc/init.d/dphys-swapfile stop
   sudo apt-get remove --purge dphys-swapfile
   sudo rm -rf ~/opencv
   ```    
- __Reference links:__
- __參考連結：__
  <ol>
  <li><a href="https://qengineering.eu/install-opencv-on-jetson-nano.html" target="_blank">Q-engineering</a></li>
  <li><a href="https://docs.arducam.com/Nvidia-Jetson-Camera/Native-Camera/Quick-Start-Guide/?fbclid=IwZXh0bgNhZW0CMTEAAR3rpGy1GsiVuHBFvi6qkJIelI8P88syOjCk1rvKRaBONlKQOsQ7BPMmfVI_aem_jJuQ5IOzOy0no-wMudOhlQ" target="_blank">ArduCam</a></li>
  <li><a href="https://zh.wikipedia.org/wiki/OpenCV" target="_blank">Wikipedia</a></li>
  <li><a href="https://steam.oxxostudio.tw/category/python/ai/opencv.html#google_vignette" target="_blank">steam educational website</a></li>
  </ol>

# <div align="center">![HOME](../../other/img/home.png)[Return Home](../../)</div> 
