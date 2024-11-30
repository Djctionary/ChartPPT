import base64
from io import BytesIO

import cv2
import numpy as np
import time

from PIL import Image


def colour_progress(result, image , enhance_saturation, enhance_brightness, black_threshold=50):
    """
    :param black_threshold:
    :param enhance_brightness:
    :param enhance_saturation:
    :param result: A list of dictionaries with 'text' and 'Inches_box'
    :param image: The image from which the background color is extracted
    :return: A list of dictionaries with 'text', 'Inches_box' and 'colour'
    """
    saturation_scale = 1.2 * enhance_saturation / 100
    value_scale = 1.2 * enhance_brightness / 100

    if result is None:
        # print("OCR result is None. Check the image path or OCR settings.")
        return

    colour_start_time = time.time()
    extracted_data = []

    # Define a threshold for what is considered "close to black"

    for index, entry in enumerate(result):
        box = entry['Inches_box']  # Extract the box from result
        text = entry['text']  # Extract the text from result

        # Convert the box coordinates to integers and extract the bounding box region
        x_min, y_min = int(box[0][0]), int(box[0][1])
        x_max, y_max = int(box[2][0]), int(box[2][1])

        # Extract the region of interest (ROI) in the image
        roi = image[y_min:y_max, x_min:x_max]

        if roi is None or roi.size == 0:
            continue

        # Create a mask to exclude pixels that are close to black
        mask = (roi[:, :, 0] > black_threshold) & (roi[:, :, 1] > black_threshold) & (roi[:, :, 2] > black_threshold)

        # Convert mask to uint8 type
        mask = mask.astype(np.uint8) * 255  # Make mask values 255 for non-black areas

        # Convert ROI to HSV
        hsv_roi = cv2.cvtColor(roi, cv2.COLOR_BGR2HSV)

        # 提高饱和度
        hsv_roi[:, :, 1] = np.clip(hsv_roi[:, :, 1] * saturation_scale, 0, 255)

        # 提高亮度
        hsv_roi[:, :, 2] = np.clip(hsv_roi[:, :, 2] * value_scale, 0, 255)

        # Convert back to BGR for mean color calculation
        enhanced_roi = cv2.cvtColor(hsv_roi, cv2.COLOR_HSV2BGR)

        # Calculate the mean color of the region while ignoring the masked pixels
        mean_color = cv2.mean(enhanced_roi, mask=mask)[:3]  # Apply mask directly

        mean_color_rgb = (int(mean_color[0]), int(mean_color[1]), int(mean_color[2]))  # Convert from BGR to RGB

        # Add the color to the current result entry
        entry['colour'] = f'RGB({mean_color_rgb[0]}, {mean_color_rgb[1]}, {mean_color_rgb[2]})'

        # Append the updated entry to the extracted_data list
        extracted_data.append(entry)

    colour_end_time = time.time()
    colour_elapsed_time = colour_end_time - colour_start_time
    # print("colour_elapsed_time: ", colour_elapsed_time)

    return extracted_data
