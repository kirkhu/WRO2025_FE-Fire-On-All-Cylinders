 <div align="center"><img src="../../other/img/logo.png" width="300" alt=" logo"></div>

## <div align="center">OpenCV Introduction</div> 
- OpenCV (Open Source Computer Vision Library) is an open-source software library for computer vision and machine learning. It consists of over 2,500 optimized algorithms, covering various vision tasks such as image processing, object detection, image recognition, face recognition, motion tracking, and 3D reconstruction. Due to its versatility and efficiency, OpenCV is widely used across different fields, including autonomous driving, robotics, medical image processing, and security surveillance.
- OpenCV supports multiple programming languages (such as C++, Python, and Java) and can run on various operating systems, including Windows, Linux, macOS, and Android. It not only operates on CPUs but also supports hardware acceleration for GPUs and embedded devices, making it suitable for resource-limited devices like the Nvidia Jetson Nano and Raspberry Pi, where it performs efficiently.
- Therefore, the OpenCV application can assist in this competition by recognizing obstacles and roadside walls on the track, enabling the vehicle to avoid obstacles and successfully complete the task.

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

  <ol>
  <li><a href="https://qengineering.eu/install-opencv-on-jetson-nano.html" target="_blank">Q-engineering</a></li>
  <li><a href="https://docs.arducam.com/Nvidia-Jetson-Camera/Native-Camera/Quick-Start-Guide/?fbclid=IwZXh0bgNhZW0CMTEAAR3rpGy1GsiVuHBFvi6qkJIelI8P88syOjCk1rvKRaBONlKQOsQ7BPMmfVI_aem_jJuQ5IOzOy0no-wMudOhlQ" target="_blank">ArduCam</a></li>
  <li><a href="https://zh.wikipedia.org/wiki/OpenCV" target="_blank">Wikipedia</a></li>
  <li><a href="https://steam.oxxostudio.tw/category/python/ai/opencv.html#google_vignette" target="_blank">steam educational website</a></li>
  </ol>

# <div align="center">![HOME](../../other/img/home.png)[Return Home](../../)</div> 
