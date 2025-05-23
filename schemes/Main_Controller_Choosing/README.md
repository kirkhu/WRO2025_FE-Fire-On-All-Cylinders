<div align=center><img src="../../other/img/logo.png" width=300></div>

# <div align="center">Controller Selection-控制器選擇 </div> 

Jetson Nano 和 Raspberry Pi 是台灣常見且低成本的控制器，具備 AI 影像識別能力，適用於多種應用，包括教育中的程式教學、智慧家庭裝置、自駕車以及 DIY 專案。

Jetson Nano and Raspberry Pi are commonly available low-cost controllers in Taiwan with AI image recognition capabilities, suitable for various applications, including programming instruction in education, smart home devices, autonomous vehicles, and DIY projects.

## Jetson Nano & Raspberry Pi Controller 
Comparison-Jetson Nano 與 Raspberry Pi 控制器比較
比較結果如以下表格所示。

The comparison is shown in the table below.

<div align=center>
<table>
<tr>
<th rowspan="2" width=300>Photo(照片)</th>
<th>Nvidia Jetson Nano</th>
<th>Raspberry Pi 4B</th>
</tr><tr>
<td><div align=center><img src="./img/jeston_nano.png" width=200></td>
<td><div align=center><img src="./img/raspberry_pi_4.png" width=200></td>
</tr><tr>
<th>Number of Pins(腳位數量)</th>
<td>40P</td>
<td>40P</td>
</tr><tr>
<th>CPU</th>
<td>Quad-core ARM® Cortex®-A57 MPCore</td>
<td>1.5GHz 64-bit Quad-core ARM Cortex-A72 CPU</td>
</tr><tr>
<th>GPU</th>
<td>NVIDIA Maxwell™ architecture with 128 NVIDIA CUDA®  cores</td>
<td>Broadcom VideoCore VI<br> H.265 (4kp60 decode)<br> H264 (1080p60 decode, 1080p30 encode) OpenGL ES 3.1<br> Vulkan 1.0</td>
</tr><tr>
<th>Storage Spac(儲存空間)</th>
<td>4 GB 64-bit LPDDR4</td>
<td>8GB LPDDR4-3200 SDRAM</td>
</tr><tr>
<th>Built-in Bluetooth and Wireless WiFi Connectivity(內建藍牙與無線 WiFi 連接功能)</th>
<td>Requires external Bluetooth and wireless WiFi connectivity</td>
<td>Built-in</td>
</tr><tr>
<th>Gflops(每秒千兆次浮點運算)</th>
<td>472</td>
<td>13.5</td>
</tr><tr>
<th>Price(價格)</th>
<td>Expensive</td>
<td>Cheap</td>  
</tr>
</table>
</div>
  根據去年的失敗經驗以及世界冠軍得主的機型，並結合以下控制器優缺點的比較，我們發現 Jetson Nano 在影像識別方面明顯優於 Raspberry Pi 4。因此，我們決定在 2025 年 WRO 世界錦標賽中使用 Jetson Nano 作為主要控制器。

  Based on last year’s unsuccessful experience and the world championship-winning model, along with the comparison of advantages and disadvantages of the controllers below, we found that the Jetson Nano significantly outperforms the Raspberry Pi 4 in image recognition. Therefore, we decided to use the Jetson Nano as the main controller in the 2025 WRO World Championship.

 ***
- ### Supplementary Information-補充資訊
#### 這是我們對 Jetson Nano 和 Raspberry Pi 的比較。
### 中文:
  ##### 1. Hardware Architecture / 硬體架構
Jetson Nano：配備四核心 ARM Cortex-A57 處理器和 128 核心的 NVIDIA Maxwell GPU，搭載 4GB LPDDR4 記憶體。

Raspberry Pi 4：配備四核心 ARM Cortex-A72 處理器，最大記憶體選項為 8GB，但缺乏專用 GPU。

  ##### 2. Deep Learning Acceleration / 深度學習加速
Jetson Nano：支援 NVIDIA CUDA 和 cuDNN，可加速深度學習工作負載。對於影像分類與物體偵測等任務，Jetson Nano 的 GPU 可顯著提升處理速度。

Raspberry Pi 4：缺乏專用 GPU 與深度學習加速功能；影像識別任務完全依賴 CPU 處理，效率遠不如 Jetson Nano 的 GPU 加速。

  ##### 3. OpenCV Performance / OpenCV 效能
Jetson Nano：由於支援 CUDA，處理基於深度學習的影像辨識任務表現更佳。OpenCV 可利用 NVIDIA GPU 加速影像處理操作。

Raspberry Pi 4：處理能力依賴 CPU，面對相同任務時速度較慢。對於簡單的影像處理任務，Pi 4 的 CPU 仍可應付，但在處理較複雜的神經網路推論時效率會顯著落後。

  ##### 4. Power Consumption / 功耗
Jetson Nano：功耗較高，在一般使用情況下約為 5W 至 10W，若使用 GPU 加速，功耗會更高。

Raspberry Pi 4：功耗較低，通常約為 3.5W 至 7W，適合對功耗敏感的應用場景。

  ##### 5. Performance Comparison in Actual Application Scenarios / 實際應用場景下的效能比較
Jetson Nano：使用 OpenCV 搭配 DNN 模組進行即時物體偵測、影像分類等任務時，其速度明顯優於 Raspberry Pi 4。在 CUDA 加速下，Jetson Nano 可更快處理視訊串流並即時進行推論。

Raspberry Pi 4：適合處理對效能需求不高的任務，例如簡單影像處理或非即時的影像辨識任務。

  ##### 6. Development Ecology / 開發生態系
Jetson Nano 的開發生態系專為 AI 與電腦視覺任務設計，NVIDIA 提供 JetPack SDK，其中包含優化後的 OpenCV，方便開發者快速部署深度學習模型。

Raspberry Pi 4 雖也支援 OpenCV，但缺乏專屬硬體加速，對於複雜深度學習任務的支援度不如 Jetson Nano。
### 英文:
#### Here's our comparison of the jetson nano and the Raspberry Pi
  #### 1. Hardware architecture
   - Jetson Nano: Equipped with a quad-core ARM Cortex-A57 CPU and a 128-core NVIDIA Maxwell GPU, with 4GB LPDDR4 memory.
   - Raspberry Pi 4: Equipped with a quad-core ARM Cortex-A72 CPU, with a maximum memory option of 8GB, but lacks a dedicated GPU.
  #### 2. Deep learning acceleration
   - Jetson Nano: Supports NVIDIA CUDA and cuDNN, which can accelerate deep learning workloads. For tasks like image classification and object detection, the GPU in Jetson Nano significantly enhances processing speed.
   - Raspberry Pi 4: Lacks a dedicated GPU and deep learning acceleration capabilities; image recognition tasks rely entirely on CPU processing, which is far less efficient than the GPU acceleration of Jetson Nano.
  #### 3. OpenCV performance
   - Jetson Nano：Due to its CUDA support, it performs better when processing image recognition tasks based on deep learning. OpenCV can take advantage of NVIDIA GPUs to accelerate image processing operations.
   - Raspberry Pi 4：Processing power relies on the CPU, so it is slower when faced with the same tasks. For simple image processing tasks, the Pi 4's CPU is also capable, but its efficiency will significantly lag behind when handling more complex neural network inference.
  #### 4. Power consumption
   - Jetson Nano：The power consumption is large, about 5W - 10W in typical usage scenarios, especially when using GPU for acceleration, the power consumption will be higher.
   - Raspberry Pi 4：The power consumption is low, usually about 3.5W - 7W, which is suitable for application scenarios that are sensitive to power consumption requirements.
  #### 5. Performance comparison in actual application scenarios
   - Jetson Nano：When using OpenCV and DNN modules for real-time object detection, image classification and other tasks, the speed is significantly better than Raspberry Pi 4. With CUDA acceleration, Jetson Nano can process video streams faster and perform on-the-fly inference.
   - Raspberry Pi 4：It is suitable for processing tasks that do not require high performance, such as simple image processing operations or non-real-time image recognition tasks.
  #### 6. Development ecology
   - Jetson Nano's development ecosystem is specially designed for AI and computer vision tasks. There is JetPack SDK provided by NVIDIA, which includes optimized OpenCV to facilitate developers to quickly deploy deep learning models.
   - Although Raspberry Pi 4 also supports OpenCV, it lacks dedicated hardware acceleration and its support for complex deep learning tasks is not as good as Jetson Nano.

# <div align="center">![HOME](../../other/img/home.png)[Return Home](../../)</div> 
