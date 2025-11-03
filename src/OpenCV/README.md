 <div align="center"><img src="../../other/img/logo.png" width="300" alt=" logo"></div>

## <div align="center">OpenCV Introduction</div> 

- **OpenCV (Open Source Computer Vision Library)** is a **robust open-source software library** **dedicated to** computer vision and machine learning. It incorporates over 2,500 **optimized** algorithms, covering a **wide array of visual tasks**, ranging from **fundamental** image processing, object detection, image recognition, and facial recognition to motion tracking and 3D reconstruction. Due to its exceptional **versatility and high efficiency**, OpenCV is **extensively utilized** in **numerous fields** such as autonomous driving, robotics, medical image processing, and security surveillance.

- OpenCV **boasts excellent cross-platform compatibility**, supporting multiple programming languages like C++, Python, and Java, and runs on various operating systems including Windows, Linux, macOS, and Android. Beyond operation on the Central Processing Unit (CPU), it also supports **hardware acceleration** via the Graphics Processing Unit (GPU) and embedded devices. This capability allows for its efficient deployment on **resource-constrained devices** such as **Nvidia Jetson Orin Nano**.

- **Consequently, by leveraging** OpenCV's visual recognition technology, the **Vehicle** can **accurately** identify the **red pillar** and **green pillar** (i.e., traffic signs) on the **game field**, black boundary walls such as the **interior walls**  or **exterior walls** , the **magenta** **parking lot limitations**, and the **blue lines** and **orange lines** on the ground, thereby **effectively controlling** the vehicle's **Driving direction**.


- ### Steps to install the OpenCV application on the Nvidia Jetson Orin Nano:
   
   __1.Update and Upgrade Packages:__
   ```bash
      sudo apt-get update
      sudo apt-get upgrade
   ```
   __2.Install the CMake general build tool__
   ```bash
      sudo apt install -y cmake
   ```

   __3.Download the OpenCV Main Source Code__
      
   ```bash
      cd ~
      git clone https://github.com/opencv/opencv.git
      cd opencv
      git checkout 4.7.0  
   ``` 

   __4.Download the Opencv_contrib Module__
  ```bash
      cd ~
      git clone https://github.com/opencv/opencv_contrib.git
      cd opencv_contrib
      git checkout 4.7.0 
  ```
  __5.Installing Dependencies__
  
   ```bash
      sudo apt update
      sudo apt install -y libgtk-3-dev pkg-config build-essential cmake git \
         libatlas-base-dev libjpeg-dev libpng-dev libtiff-dev \
         libavcodec-dev libavformat-dev libswscale-dev \
         libv4l-dev v4l-utils libxvidcore-dev libx264-dev \
         libtbb2 libtbb-dev libdc1394-22-dev
  ```
  __6.Create and Clean the Build Folder__
  ```bash
      mkdir -p ~/opencv/build
      cd ~/opencv/build
      rm -rf *
  ```
  __7.Configure the Python Path__
  ```bash
      PYTHON_EXEC=$(pyenv which python3)
      PYTHON_PREFIX=$(pyenv prefix)
      PYTHON_INCLUDE=$PYTHON_PREFIX/include/python3.11
      PYTHON_LIB=$PYTHON_PREFIX/lib/libpython3.11.so
      PYTHON_PACKAGES=$PYTHON_PREFIX/lib/python3.11/site-packages
  ```
  __8.Configure the CMake__
  ```bash
      cmake \
         -D CMAKE_BUILD_TYPE=Release \
         -D CMAKE_INSTALL_PREFIX=/usr/local \
         -D OPENCV_EXTRA_MODULES_PATH=~/opencv_contrib/modules \
         -D WITH_GSTREAMER=ON \
         -D WITH_CUDA=ON \
         -D ENABLE_FAST_MATH=ON \
         -D CUDA_FAST_MATH=ON \
         -D WITH_CUBLAS=ON \
         -D WITH_GTK=ON \
         -D BUILD_opencv_python3=ON \
         -D PYTHON3_EXECUTABLE=$PYTHON_EXEC \
         -D PYTHON3_INCLUDE_DIR=$PYTHON_INCLUDE \
         -D PYTHON3_LIBRARY=$PYTHON_LIB \
         -D PYTHON3_PACKAGES_PATH=$PYTHON_PACKAGES \
         -D BUILD_opencv_world=OFF \
         -D BUILD_EXAMPLES=OFF \
         -D BUILD_TESTS=OFF \
         -D BUILD_DOCS=OFF \
         -D BUILD_PERF_TESTS=OFF \
         ...
  ```
  __9.Build an OpenCV package with CUDA acceleration support__

  ``` bash 
      make -j$(nproc)
  ```
  __10.Installing Opencv__
  ```bash 
      sudo make install
  ```
  __11.Confirm successful installation__
  ```bash
      python3 -c "import cv2; print('OpenCV version:', cv2.__version__)"
      python3 -c "import cv2; print(cv2.getBuildInformation())" | grep -E "GStreamer|GTK|CUDA"

  ```   


- __Reference links:__
  <ol>
  <li><a href="https://qengineering.eu/install-opencv-on-jetson-nano.html" target="_blank">Q-engineering</a></li>
  <li><a href="https://docs.arducam.com/Nvidia-Jetson-Camera/Native-Camera/Quick-Start-Guide/?fbclid=IwZXh0bgNhZW0CMTEAAR3rpGy1GsiVuHBFvi6qkJIelI8P88syOjCk1rvKRaBONlKQOsQ7BPMmfVI_aem_jJuQ5IOzOy0no-wMudOhlQ" target="_blank">ArduCam</a></li>
  <li><a href="https://zh.wikipedia.org/wiki/OpenCV" target="_blank">Wikipedia</a></li>
  <li><a href="https://steam.oxxostudio.tw/category/python/ai/opencv.html#google_vignette" target="_blank">steam educational website</a></li>
  </ol>

# <div align="center">![HOME](../../other/img/home.png)[Return Home](../../)</div> 
