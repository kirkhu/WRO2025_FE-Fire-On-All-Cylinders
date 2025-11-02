<div align="center"><img src="../../other/img/logo.png" width="300" alt=" logo"></div>

## <div align="center"> Automatic storage and recording of game field object LAB values - 場地物件LAB值的自動化儲存記錄</div>
為精確記錄交通標誌積木（紅、綠）、停車區的洋紅色邊牆，以及轉彎區的藍、橘線，我們開發了一套車輛控制程式，它透過CSI鏡頭讀取到的畫面，將各物件顏色能最終的LAB值儲存在 Jetson Orin Nano 控制器中。這項自動化功能省去了手動記錄的繁瑣步驟，不僅節省了時間，更確保了數據的準確性與一致性。

To accurately record the LAB values for the traffic sign blocks (red and green), the magenta side walls of the parking lot, and the blue lines and orange lines in the turning areas, we developed a Vehicle's control program. This program reads the image captured by the CSI camera and stores the final LAB values for the color of each object in the Jetson Orin Nano controller. This automation eliminates the tedious step of manual recording, significantly saving time and ensuring the accuracy and consistency of the data.
- #### Introduction to LAB Image Processing and Automatic Recording - LAB影像處理與自動記錄
    - 色彩空間轉換：我們調用 cv2.cvtColor() 函數，將 CSI 鏡頭擷取到的原始 RGB 影像轉換成 LAB 色彩空間 (L：明度，A：紅綠軸，B：黃藍軸)。
    - 顏色範圍定義與濾波：接著，透過 cv2.inRange() 函數並設定六個 LAB 閾值 (L_{low}、L_{high}、A_{low}、A_{high}、B_{low}、B_{high})，精確定義目標顏色範圍。cv2.inRange() 會比較 LAB 影像中的每個像素，僅保留落在設定範圍內的像素，從而得到濾波後的影像。
    - 數值儲存與應用：取得濾波後影像後，我們透過圖形介面按鈕，選擇對應顏色物件來儲存其 LAB 數值。這些數值將被保存在 masks.py 檔案中。
    - 主程式呼叫：在車輛控制程式的主程式中，我們透過以下代碼片段，呼叫 masks.py 中的各物件 LAB 數值，並輸入給相對應的視覺辨識函數，實現精確的顏色辨識。

    1. Color Space Conversion: We use the `cv2.cvtColor()` function to convert the original `RGB` image captured by the CSI camera into the `LAB` color space (`L`: Lightness, `A`: Red-Green axis, `B`: Yellow-Blue axis).
    2. Color Range Definition and Filtering: Subsequently, we precisely define the target color range by utilizing the `cv2.inRange()` function and setting six `LAB` thresholds: `L_{low}`, `L_{high}`, `A_{low}`, `A_{high}`, `B_{low}`, and `B_{high}`. The `cv2.inRange()` function compares every pixel in the `LAB` image with the defined range, retaining only the pixels within the range and filtering out the rest, thus yielding the filtered image.
    3. Value Storage and Application: After obtaining the filtered image, we use a graphical interface button to select the corresponding color object and save its `LAB` values. These values are stored in the `masks.py` file.([masks.py](../Programming/common/masks.py))
    4. Main Program Call: In the main Vehicle's control program10, we call the `LAB` values for each object from the masks.py file using the code snippet below, and input them to the corresponding function for `LAB` visual recognition.
        ```python
        from masks import rMagenta, rRed, rGreen, rBlue, rOrange, rBlack
        ```

<div align="center">

**Red traffic sign block-紅色交通標誌方塊**

|Adjusting the LAB Range Values for Red Color(調整紅色的 LAB 範圍值)|Save the LAB range values for Red(儲存紅色的 LAB )|Real-time image of the red traffic sign block(紅色交通標誌方塊的即時影像)|
|:----:|:----:|:----:|
|<img src="./img/Red/Adjusting_the_LAB_Range_Values_for_Red_Color.png" alt="Adjusting_the_LAB_Range_Values_for_Red_Color" align=center />|<img src="./img/Red/Save_the_LAB_range_values_for_red.png"  alt="Save_the_LAB_range_values_for_red" align=center />|<img src="./img/Red/Live_image_ of_the_red_traffic_sign_block.png" alt="Live_image_ of_the_red_traffic_sign_block" align=center />|



**Green traffic sign block-綠色交通標誌方塊**


|Adjusting the LAB Range Values for GreenColor(調整綠色的 LAB 範圍值)|Save the LAB range values for Green(儲存綠色的 LAB )|Real-time image of the green traffic sign block(綠色交通標誌方塊的即時影像)|
|:----:|:----:|:----:|
|<img src="./img/Green/Adjusting_the_LAB_Range_Values_for_green_Color.png" alt="Adjusting_the_LAB_Range_Values_for_green_Color" align=center />|<img src="./img/Green/Save_the_LAB_range_values_for_green.png"  alt="Save_the_LAB_range_values_for_green" align=center />|<img src="./img/Green/Live_image_ of_the_green_traffic_sign_block.png" alt="Live_image_ of_the_green_traffic_sign_block" align=center />|



**Blue line-藍色線條**


|Adjusting the LAB Range Values for Blue Color(調整藍色的 LAB 範圍值)|Save the LAB range values for Blue(儲存藍色的 LAB )|Real-time image of the blue lines藍色線條的即時影像）|
|:----:|:----:|:----:|
|<img src="./img/Blueline/Adjusting_the_LAB_Range_Values_for_blueline_Color.png" alt="Adjusting_the_LAB_Range_Values_for_blueline_Color" align=center />|<img src="./img/Blueline/Save_the_LAB_range_values_for_blueline.png"  alt="Save_the_LAB_range_values_for_blueline" align=center />|<img src="./img/Blueline/Live_image_ of_the_blueline.png" alt="Live_image_ of_the_blueline" align=center />|



**Orange line-橘色線條**


|Adjusting the LAB Range Values for Orange Color(調整橘色的 LAB 範圍值)|Save the LAB range values for Orange(儲存橘色的 LAB)|Real-time image of the orange lines(橘色線條的即時影像) |
|:----:|:----:|:----:|
|<img src="./img/Orangeline/Adjusting_the_LAB_Range_Values_for_Orangeline_Color.png" alt="Adjusting_the_LAB_Range_Values_for_Orange line_Color" align=center />|<img src="./img/Orangeline/Save_the_LAB_range_values_for_Orangeline.png"  alt="Save_the_LAB_range_values_for_Orange linee" align=center />|<img src="./img/Orangeline/Live_image_ of_the_Orangeline_block.png" alt="Live_image_ of_the_Orange_line" align=center />|



**magenta side walls-洋紅牆面**


|Adjusting the LAB Range Values for magenta Color(調整洋紅色的 LAB 範圍值)|Save the LAB range values for magenta(儲存洋紅色的 LAB )|Real-time image of the magenta side walls(洋紅色邊牆的即時影像)|
|:----:|:----:|:----:|
|<img src="./img//magenta/Adjusting_the_LAB_Range_Values_for_magenta_Color.png" alt="Adjusting_the_LAB_Range_Values_for_magenta_Color" align=center />|<img src="./img/magenta/Save_the_LAB_range_values_for_magenta.png"  alt="Save_the_LAB_range_values_for_pink" align=center />|<img src="./img/magenta/Live_image_ of_the_magenta_traffic_sign_block.png" alt="Live_image_ of_the_magenta_traffic_sign_block" align=center />|

</div>


# <div align="center">![HOME](../../other/img/home.png)[Return Home](../../)</div>  
