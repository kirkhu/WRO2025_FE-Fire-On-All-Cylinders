<div align=center><img src="../../other/img/logo.png" width=300></div>

# <div align="center">Controller Selection-控制器選擇 </div> 
- Jetson Nano 與 Jetson Orin Nano 皆為 NVIDIA 所研發的嵌入式邊緣 AI 運算產品 。兩者均具備卓越的 AI 運算能力，並內建 GPIO（通用輸入/輸出）腳位 ，使其成為開發智慧家居、自駕車  和 DIY 專案等應用的理想主控器。

- 鑑於去年世界賽的經驗以及今年全國選拔賽的觀察，我們原先選用 Jetson Nano 作為自駕車的主控單元，負責影像辨識處理。然而，隨著比賽規則的修改和我們對功能需求的提升，Jetson Nano 的性能似乎已難以完全滿足。考量到性能更佳的 Jetson Orin Nano 現已降價，我們決定對這兩款主控器進行詳盡比較，以選出最能助益我們參與今年世界賽的高效能主控器。

- Both the Jetson Nano and Jetson Orin Nano are embedded edge AI products developed by NVIDIA. They possess excellent AI computing capabilities and feature built-in GPIO (General-Purpose Input/Output) pins , making them highly suitable main controllers for developing applications such as smart homes, self-driving cars, and DIY projects.

- Based on our experience in the World Championship last year and observations from the National Selection Trials this year, we initially used the Jetson Nano as the main controller for our self-driving car, primarily for image recognition processing. However, with the revision of the competition rules and our enhanced functional requirements, the Jetson Nano's performance appears insufficient to fully meet our needs. Considering that the superior performance Jetson Orin Nano has now decreased in price, we have decided to conduct a detailed comparison between these two main controllers. Our goal is to select the high-performance controller that will be most beneficial for our participation in this year's World Championship.


## Jetson Nano & Jetson Orin Nano Controller
Jetson Nano 與 Jetson Orin Nano 主控制器比較，比較結果如以下表格：
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
<td>Expensive</td>
<td>Very Expensive</td>
</tr>
</table>
</div>
  綜合去年世界賽、今年全國選拔賽的實戰經驗，以及參考世界冠軍隊伍的車輛設計，並配合主控器優缺點的比較分析，我們明確地發現 Jetson Orin Nano 在影像處理效能方面，顯著優於原有的 Jetson Nano 及 Raspberry Pi 4。考量到 Jetson Orin Nano 和 Jetson Nano 在體積大小上相近，便於整合，我們最終決定在 2025 年 WRO 世界機器人奧林匹亞大賽「未來工程師——自駕車挑戰賽」 中，採用 Jetson Orin Nano 作為主要的車輛控制器。

  Based on the practical experience gained from the World Championship last year and the National Selection Trials this year, alongside a review of the World Champion models and a comparative analysis of controller advantages and disadvantages, we clearly identified that the Jetson Orin Nano offers significantly superior image processing performance compared to both the existing Jetson Nano and the Raspberry Pi 4. Considering that the Jetson Orin Nano is similar in size to the Jetson Nano, making integration straightforward, we have ultimately decided to utilize the Jetson Orin Nano as the main vehicle controller for the 2025 WRO (World Robot Olympiad) Future Engineers - Self-Driving Cars Challenge.

 ***
- ### Supplementary Information
#### 這是我們對 Jetson Nano 和 Jetson Orin Nano 的比較。
### 中文:
  ##### 1. Hardware Architecture / 硬體架構
    Jetson Nano：配備四核心 ARM Cortex-A57 處理器和 128 核心的 NVIDIA Maxwell GPU，搭載 4GB LPDDR4 記憶體。

    Jetson Orin Nano：配備六核 Arm Cortex-A78AE CPU 處理器和 1024核心的 NVIDIA Ampere GPU，搭載 8GB LPDDR5 記憶體。

  ##### 2. Deep Learning Acceleration / 深度學習加速
    Jetson Nano：支援 NVIDIA CUDA 和 cuDNN，可加速深度學習工作負載。對於影像分類與物體偵測等任務，Jetson Nano 的 GPU 可顯著提升處理速度。

    Jetson Orin Nano：支援最新一代 NVIDIA CUDA、cuDNN 和 TensorRT，可高效加速深度學習推理與訓練工作負載。對於即時影像分割、多感測器融合與複雜的 Transformer 模型等任務，Jetson Orin Nano 的 Ampere 架構 GPU 與專用 Tensor Core 可提供較前代提升 80 倍的 AI 運算性能。

  ##### 3. OpenCV Performance / OpenCV 效能
    Jetson Nano：由於支援 CUDA，處理基於深度學習的影像辨識任務表現更佳。OpenCV 可利用 NVIDIA GPU 加速影像處理操作。

    Jetson Orin Nano：憑藉新一代 CUDA 核心與專用 Tensor Core，在處理複雜深度學習模型（如 Transformer 和 3D 視覺任務）時表現卓越。OpenCV 可透過 NVIDIA GPU 實現硬體加速，並支援最新的 AI 影像處理演算法。

  ##### 4. Power Consumption / 功耗
    Jetson Nano：功耗較高，在一般使用情況下約為 5W 至 10W，若使用 GPU 加速，功耗會更高。

    Jetson Orin Nano：搭载新一代Ampere架构，能效比显著提升。在典型AI工作负载下功耗约为7W至15W，支持动态功耗管理，在提供强大算力的同时保持优异的能效表现。

  ##### 5. Performance Comparison in Actual Application Scenarios / 實際應用場景下的效能比較
    Jetson Nano：使用 OpenCV 搭配 DNN 模組進行即時物體偵測、影像分類等任務時，其速度明顯優於 Raspberry Pi 4。在 CUDA 加速下，Jetson Nano 可更快處理視訊串流並即時進行推論。

    Jetson Orin Nano：搭载新一代GPU架构和Tensor Core，在运行OpenCV DNN模块进行高精度物体检测、语义分割等任务时，性能大幅领先前代产品。借助CUDA和TensorRT加速，可实时处理4K多路视频流，并支持更复杂的AI模型推理。

  ##### 6. Development Ecology / 開發生態系
    Jetson Nano 的開發生態系專為 AI 與電腦視覺任務設計，NVIDIA 提供 JetPack SDK，其中包含優化後的 OpenCV，方便開發者快速部署深度學習模型。

    Jetson Orin Nano 的開發生態系統全面升級，專為新一代 AI 與自主機器應用設計。NVIDIA 提供 JetPack SDK 5.1+，其中包含深度優化的 OpenCV 與 TensorRT 8.0，支援自動模型量化與硬體級加速，讓開發者能夠高效部署複雜的深度學習模型與多感測器融合應用。
### 英文:
#### Comparison of Performance Between Jetson Nano and Jetson Orin Nano

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
