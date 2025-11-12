<div align=center><img src="../../other/img/logo.png" width=300></div>

# <div align="center">Controller Selection</div> 
- Both the Jetson Nano and Jetson Orin Nano are embedded edge AI products developed by NVIDIA. They possess excellent AI computing capabilities and feature built-in GPIO (General-Purpose Input/Output) pins , making them highly suitable main controllers for developing applications such as smart homes, self-driving cars, and DIY projects.

- Based on our experience in the World Championship last year and observations from the National Selection Trials this year, we initially used the Jetson Nano as the main controller for our self-driving car, primarily for image recognition processing. However, with the revision of the competition rules and our enhanced functional requirements, the Jetson Nano's performance appears insufficient to fully meet our needs. Considering that the superior performance Jetson Orin Nano has now decreased in price, we have decided to conduct a detailed comparison between these two main controllers. Our goal is to select the high-performance controller that will be most beneficial for our participation in this year's World Championship.


## Jetson Nano & Jetson Orin Nano Controller
Comparison of the Jetson Nano and Jetson Orin Nano main controllers, the comparison results are shown in the table below:

<div align=center>
<table> 
<tr> 
<th rowspan="2" width=300>Photo</th> 
<th><div align=center>Nvidia Jetson Nano</th> 
<th><div align=center>Nvidia Jetson Orin Nano</th> 
</tr>
<tr> 
<td><div align=center><img src="./img/jeston_nano.png" width=200></div></td> 
<td><div align=center><img src="./img/jetson_orin_nano.png" width=400></div></td> 
</tr>
<tr> 
<th>Number of Pins</th>
<td>40P</td> 
<td>40P</td>
</tr>
<tr>
<th>CPU</th>
<td>Quad-core ARM® Cortex®-A57 MPCore</td>
<td>6-core Arm® Cortex®-A78AE V8.2 64-bit CPU</td>
</tr>
<tr>
<th>GPU</th>
<td>NVIDIA Maxwell™ architecture with 128 NVIDIA CUDA® cores</td>
<td>NVIDIA Ampere architecture with 1024 NVIDIA CUDA® cores</td>
</tr>
<tr>
<th>Storage Space</th>
<td>4 GB 64-bit LPDDR4</td>
<td>8 GB 128-bit LPDDR5</td>
</tr>
<tr>
<th>Built-in Bluetooth and Wireless WiFi Connectivity</th>
<td>Requires external Bluetooth and wireless WiFi connectivity</td>
<td>Requires external Bluetooth and wireless WiFi connectivity</td>
</tr>
<tr>
<th>Gflops</th>
<td>472</td> <td>40,000 (FP16)</td>
</tr>
<tr>
<th>Price</th>
<td colspan = 2 >Similarly priced</td>

</tr>
</table>
</div>
  Based on the practical experience gained from the World Championship last year and the National Selection Trials this year, alongside a review of the World Champion models and a comparative analysis of controller advantages and disadvantages, we clearly identified that the NVIDIA Jetson Orin Nano offers significantly superior image processing performance compared to both the existing  NVIDIA Jetson Nano and the Raspberry Pi 4. Considering that the NVIDIA Jetson Orin Nano is similar in size to the  NVIDIA Jetson Nano, making integration straightforward, we have ultimately decided to utilize the  NVIDIA Jetson Orin Nano as the main vehicle controller for the 2025 WRO (World Robot Olympiad) Future Engineers - Self-Driving Cars Challenge.

 ***
- ### Supplementary Information

#### Comparison of Performance Between  NVIDIA Jetson Nano and  NVIDIA Jetson Orin Nano
##### 1. Hardware Architecture
* **Jetson Nano**: Equipped with a quad-core ARM Cortex-A57 processor and a 128-core NVIDIA Maxwell GPU, featuring 4GB LPDDR4 memory.
* **Jetson Orin Nano**: Equipped with a six-core Arm Cortex-A78AE CPU processor and a 1024-core NVIDIA Ampere GPU, featuring 8GB LPDDR5 memory.

##### 2. Deep Learning Acceleration
* **Jetson Nano**: Supports NVIDIA CUDA and cuDNN, which accelerate deep learning workloads. The Jetson Nano's GPU significantly boosts processing speed for tasks such as image classification and object detection.
* **Jetson Orin Nano**: Supports the latest generation NVIDIA CUDA, cuDNN, and TensorRT, which efficiently accelerate deep learning inference and training workloads. For tasks like real-time image segmentation, multi-sensor fusion, and complex Transformer models, the Jetson Orin Nano's Ampere architecture GPU and dedicated Tensor Cores can provide up to **80 times the AI performance improvement** over the previous generation.

##### 3. OpenCV Performance
* **Jetson Nano**: Performs better in deep learning-based image recognition tasks due to CUDA support. OpenCV can utilize the NVIDIA GPU to accelerate image processing operations.
* **Jetson Orin Nano**: Excels at processing complex deep learning models (such as Transformer and 3D vision tasks) leveraging the next-generation CUDA cores and dedicated Tensor Cores. OpenCV enables hardware acceleration via the NVIDIA GPU and supports the latest AI image processing algorithms.

##### 4. Power Consumption
* **Jetson Nano**: Has higher power consumption, typically ranging from **5W to 10W** under general usage; power consumption will be higher when using GPU acceleration.
* **Jetson Orin Nano**: Features the new Ampere architecture, which significantly improves power efficiency. Power consumption is typically around **7W to 15W** under typical AI workloads, supporting dynamic power management to maintain excellent energy efficiency while delivering powerful computing capabilities.

##### 5. Performance Comparison in Actual Application Scenarios 
* **Jetson Nano**: When using OpenCV with the DNN module for tasks like real-time object detection and image classification, its speed is clearly superior to the Raspberry Pi 4. With CUDA acceleration, the Jetson Nano can process video streams and perform inference faster in real-time.
* **Jetson Orin Nano**: Equipped with the next-generation GPU architecture and Tensor Cores, its performance significantly outperforms its predecessor when running the OpenCV DNN module for high-precision object detection, semantic segmentation, and other tasks. Utilizing CUDA and TensorRT acceleration, it can process **4K multi-stream video** in real-time and support more complex AI model inference.

##### 6. Development Ecology
* **Jetson Nano**: The development ecosystem is designed for AI and computer vision tasks. NVIDIA provides the JetPack SDK, which includes optimized OpenCV, facilitating the quick deployment of deep learning models for developers.
* **Jetson Orin Nano**: The development ecosystem has been comprehensively upgraded, designed for next-generation AI and autonomous machine applications. NVIDIA provides **JetPack SDK 5.1+**, which includes deeply optimized OpenCV and **TensorRT 8.0**, supporting automatic model quantization and hardware-level acceleration, enabling developers to efficiently deploy complex deep learning models and multi-sensor fusion applications.


# <div align="center">![HOME](../../other/img/home.png)[Return Home](../../)</div> 
