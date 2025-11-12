<div align="center"><img src="../../other/img/logo.png" width="300" alt=" logo"></div>

## <div align="center"> Automatic storage and recording of game field object LAB values</div>

To accurately record the LAB values for the traffic sign blocks (red and green), the magenta side walls of the parking lot, and the blue lines and orange lines in the turning areas, we developed a Vehicle's control program. This program reads the image captured by the CSI camera and stores the final LAB values for the color of each object in the Jetson Orin Nano controller. This automation eliminates the tedious step of manual recording, significantly saving time and ensuring the accuracy and consistency of the data.
- #### Introduction to LAB Image Processing and Automatic Recording

    1. Color Space Conversion: We use the `cv2.cvtColor()` function to convert the original `RGB` image captured by the CSI camera into the `LAB` color space (`L`: Lightness, `A`: Red-Green axis, `B`: Yellow-Blue axis).
    2. Color Range Definition and Filtering: Subsequently, we precisely define the target color range by utilizing the `cv2.inRange()` function and setting six `LAB` thresholds: `L_{low}`, `L_{high}`, `A_{low}`, `A_{high}`, `B_{low}`, and `B_{high}`. The `cv2.inRange()` function compares every pixel in the `LAB` image with the defined range, retaining only the pixels within the range and filtering out the rest, thus yielding the filtered image.
    3. Value Storage and Application: After obtaining the filtered image, we use a graphical interface button to select the corresponding color object and save its `LAB` values. These values are stored in the `masks.py` file.([masks.py](../Programming/common/masks.py))
    4. Main Program Call: In the main Vehicle's control program10, we call the `LAB` values for each object from the masks.py file using the code snippet below, and input them to the corresponding function for `LAB` visual recognition.
        ```python
        from masks import rMagenta, rRed, rGreen, rBlue, rOrange, rBlack
        # Import all functions from 'function.py' (e.g., find_contours, max_contour).
        ```

<div align="center">

### Red traffic sign block ###

|Adjusting the LAB Range Values for Red Color|Save the LAB range values for Red|Real-time image of the red traffic sign block|
|:----:|:----:|:----:|
|<img src="./img/Red/Adjusting_the_LAB_Range_Values_for_Red_Color.png" alt="Adjusting_the_LAB_Range_Values_for_Red_Color" align=center />|<img src="./img/Red/Save_the_LAB_range_values_for_red.png"  alt="Save_the_LAB_range_values_for_red" align=center />|<img src="./img/Red/Live_image_of_the_red_traffic_sign_block.png" alt="Live_image_ of_the_red_traffic_sign_block" align=center />|

### Green traffic sign block ###

|Adjusting the LAB Range Values for GreenColor|Save the LAB range values for Green|Real-time image of the green traffic sign block|
|:----:|:----:|:----:|
|<img src="./img/Green/Adjusting_the_LAB_Range_Values_for_green_Color.png" alt="Adjusting_the_LAB_Range_Values_for_green_Color" align=center />|<img src="./img/Green/Save_the_LAB_range_values_for_green.png"  alt="Save_the_LAB_range_values_for_green" align=center />|<img src="./img/Green/Live_image_of_the_green_traffic_sign_block.png" alt="Live_image_ of_the_green_traffic_sign_block" align=center />|


### Blue line ###


|Adjusting the LAB Range Values for Blue Color|Save the LAB range values for Blue|Real-time image of the blue lines）|
|:----:|:----:|:----:|
|<img src="./img/Blueline/Adjusting_the_LAB_Range_Values_for_blueline_Color.png" alt="Adjusting_the_LAB_Range_Values_for_blueline_Color" align=center />|<img src="./img/Blueline/Save_the_LAB_range_values_for_blueline.png"  alt="Save_the_LAB_range_values_for_blueline" align=center />|<img src="./img/Blueline/Live_image_of_the_blueline.png" alt="Live_image_ of_the_blueline" align=center />|

### Orange line ###

|Adjusting the LAB Range Values for Orange Colo|Save the LAB range values for Orange|Real-time image of the orange lines|
|:----:|:----:|:----:|
|<img src="./img/Orangeline/Adjusting_the_LAB_Range_Values_for_Orangeline_Color.png" alt="Adjusting_the_LAB_Range_Values_for_Orange line_Color" align=center />|<img src="./img/Orangeline/Save_the_LAB_range_values_for_Orangeline.png"  alt="Save_the_LAB_range_values_for_Orange linee" align=center />|<img src="./img/Orangeline/Live_image_of_the_Orangeline_block.png" alt="Live_image_ of_the_Orange_line" align=center />|

### magenta side walls ###

|Adjusting the LAB Range Values for magenta Color|Save the LAB range values for magenta|Real-time image of the magenta side walls|
|:----:|:----:|:----:|
|<img src="./img//magenta/Adjusting_the_LAB_Range_Values_for_magenta_Color.png" alt="Adjusting_the_LAB_Range_Values_for_magenta_Color" align=center />|<img src="./img/magenta/Save_the_LAB_range_values_for_magenta.png"  alt="Save_the_LAB_range_values_for_pink" align=center />|<img src="./img/magenta/Live_image_of_the_magenta_traffic_sign_block.png" alt="Live_image_ of_the_magenta_traffic_sign_block" align=center />|

</div>

# <div align="center">![HOME](../../other/img/home.png)[Return Home](../../)</div>  
