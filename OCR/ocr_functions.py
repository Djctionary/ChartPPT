import glob
import os
import time
from pptx.util import Inches, Pt
from typing import List, Tuple, Dict
from Code.FLask.COLOUR.colour_function import colour_progress

def get_latest_image(upload_folder, user_tag):
    """

    :param upload_folder:
    :param user_tag:
    :return:
    """
    # 在指定路径下查找符合指定格式的图片文件
    supported_extensions = ['png', 'jpg', 'jpeg', 'gif']

    # 查找所有支持格式的图片文件
    image_files = []
    for ext in supported_extensions:
        image_files.extend(glob.glob(os.path.join(upload_folder, user_tag, f"img_*.{ext}")))

    # 如果没有图片文件，返回 None
    if not image_files:
        return None

    # 找到最新的一张照片并返回其路径
    latest_image = max(image_files, key=os.path.getctime)
    return latest_image


def get_box_coordinates(box):
    """

    :param box:
    :return:
    """
    # box[0] 是左上角，box[2] 是右下角
    top_left = box[0]  # 左上角坐标
    bottom_right = box[2]  # 右下角坐标

    # 返回左上角和右下角的坐标
    return top_left[0], top_left[1], bottom_right[0], bottom_right[1]


def zoom_box_coordinates(origin_boxes, box_roi):
    """

    :param origin_boxes:
    :param box_roi:
    :return:
    """
    # 检查输入是否为有效的坐标列表
    # 获取box的中心点，缩放时需要基于中心缩放
    x_coords = [point[0] for point in origin_boxes]
    y_coords = [point[1] for point in origin_boxes]

    # 计算中心点
    center_x = sum(x_coords) / len(x_coords)
    center_y = sum(y_coords) / len(y_coords)

    # 对每个点进行放缩
    scaled_box = []
    for point in origin_boxes:
        x, y = point
        new_x = center_x + (x - center_x) * box_roi
        new_y = center_y + (y - center_y) * box_roi
        scaled_box.append([new_x, new_y])

    return scaled_box


def get_box_boundaries(Inches_box: List[List[float]]) -> Tuple[float, float, float, float]:
    """

    :param Inches_box:
    :return:
    """
    # 根据四个点获取左、上、右、下边界
    left = min(point[0] for point in Inches_box)
    top = min(point[1] for point in Inches_box)
    right = max(point[0] for point in Inches_box)
    bottom = max(point[1] for point in Inches_box)
    return left, top, right, bottom


# def is_same_phrase(box1: List[List[float]], box2: List[List[float]]) -> bool:
#     """
#
#     :param box1:
#     :param box2:
#     :param threshold:
#     :return:
#     """
#     vertical_threshold_scale = 0.6
#     horizontal_threshold_scale = 0.5
#
#     # 获取两个文本框的上、下、左、右边界
#     left1, top1, right1, bottom1 = get_box_boundaries(box1)
#     left2, top2, right2, bottom2 = get_box_boundaries(box2)
#
#     # 打印box1和box2的边界信息
#     # print(f"Box 1 Boundaries: left={left1}, top={top1}, right={right1}, bottom={bottom1}")
#     # print(f"Box 2 Boundaries: left={left2}, top={top2}, right={right2}, bottom={bottom2}")
#
#     # 判断两个文本框的垂直方向是否重叠
#     # vertical_overlap = min(bottom1, bottom2) - max(top1, top2)
#     # vertical_threshold = min(bottom1 - top1, bottom2 - top2) * threshold
#
#     vertical_overlap = max(top1, top2) - min(bottom1, bottom2)
#     vertical_threshold = min(bottom1 - top1, bottom2 - top2) * vertical_threshold_scale
#
#     # 打印垂直方向的重叠和阈值信息
#     print(f"Vertical Overlap: {vertical_overlap}")
#     print(f"Vertical Threshold: {vertical_threshold}")
#
#     # 如果垂直重叠小于一定阈值且文本框的水平距离较近，认为它们属于同一个词组
#     if vertical_overlap < vertical_threshold:
#         # # 打印四个变量的值
#         # print(f"left1: {left1}, right1: {right1}, left2: {left2}, right2: {right2}")
#         #
#         # # 打印 min 和 max 的结果
#         # print(f"max(left2, left1): {max(left2, left1)}")
#         # print(f"min(right1, right2): {min(right1, right2)}")
#         # 判断水平方向的距离
#         horizontal_distance = max(left2, left1) - min(right1, right2)
#         horizontal_threshold = min(right1 - left1, right2 - left2) * horizontal_threshold_scale
#
#         # 打印水平方向的距离和阈值信息
#         print(f"Horizontal Distance: {horizontal_distance}")
#         print(f"Horizontal Threshold: {horizontal_threshold}")
#
#         return horizontal_distance < horizontal_threshold
#
#     # 如果垂直重叠不满足要求，打印返回False
#     # print("Not the same phrase (vertical overlap is too small).")
#     return False


def is_same_phrase(box1: List[List[float]], box2: List[List[float]], direction: str, horizontal_threshold, vertical_threshold) -> bool:
    """

    :param vertical_threshold:
    :param horizontal_threshold:
    :param box1:
    :param box2:
    :param threshold:
    :return:
    """
    vertical_threshold_scale = 0.8 * vertical_threshold / 100
    horizontal_threshold_scale = 0.5 * horizontal_threshold / 100

    # 获取两个文本框的上、下、左、右边界
    left1, top1, right1, bottom1 = get_box_boundaries(box1)
    left2, top2, right2, bottom2 = get_box_boundaries(box2)

    # 打印box1和box2的边界信息
    # print(f"Box 1 Boundaries: left={left1}, top={top1}, right={right1}, bottom={bottom1}")
    # print(f"Box 2 Boundaries: left={left2}, top={top2}, right={right2}, bottom={bottom2}")

    # 判断两个文本框的垂直方向是否重叠
    # vertical_overlap = min(bottom1, bottom2) - max(top1, top2)
    # vertical_threshold = min(bottom1 - top1, bottom2 - top2) * threshold

    vertical_overlap = max(top1, top2) - min(bottom1, bottom2)
    vertical_threshold = min(bottom1 - top1, bottom2 - top2) * vertical_threshold_scale

    # 打印垂直方向的重叠和阈值信息
    # print(f"Vertical Overlap: {vertical_overlap}")
    # print(f"Vertical Threshold: {vertical_threshold}")

    # # 打印四个变量的值
    # print(f"left1: {left1}, right1: {right1}, left2: {left2}, right2: {right2}")
    #
    # # 打印 min 和 max 的结果
    # print(f"max(left2, left1): {max(left2, left1)}")
    # print(f"min(right1, right2): {min(right1, right2)}")
    # 判断水平方向的距离
    horizontal_distance = max(left2, left1) - min(right1, right2)
    horizontal_threshold = min(right1 - left1, right2 - left2) * horizontal_threshold_scale

    # 打印水平方向的距离和阈值信息
    # print(f"Horizontal Distance: {horizontal_distance}")
    # print(f"Horizontal Threshold: {horizontal_threshold}")

    if direction == 'row':
        if -horizontal_threshold < horizontal_distance < horizontal_threshold and vertical_overlap < 0:
            return True
        else:
            return False
    elif direction == 'column':
        if -vertical_threshold < vertical_overlap < vertical_threshold and horizontal_distance < 0:
            return True
        else:
            return False

    return False


def is_vertical_overlap(box1: List[List[float]], box2: List[List[float]], vertical_threshold_scale: float = 0.6) -> bool:
    """
    判断两个文本框在垂直方向上的重叠情况

    :param box1: 第一个文本框的边界信息
    :param box2: 第二个文本框的边界信息
    :param vertical_threshold_scale: 垂直方向上的重叠阈值比例
    :return: 布尔值，表示垂直方向上是否有足够的重叠
    """
    left1, top1, right1, bottom1 = get_box_boundaries(box1)
    left2, top2, right2, bottom2 = get_box_boundaries(box2)

    vertical_overlap = max(top1, top2) - min(bottom1, bottom2)
    vertical_threshold = min(bottom1 - top1, bottom2 - top2) * vertical_threshold_scale

    # 打印垂直方向的重叠和阈值信息
    # print(f"Vertical Overlap: {vertical_overlap}")
    # print(f"Vertical Threshold: {vertical_threshold}")

    return vertical_overlap < vertical_threshold


def is_horizontal_overlap(box1: List[List[float]], box2: List[List[float]], horizontal_threshold_scale: float = 0.5) -> bool:
    """
    判断两个文本框在水平方向上的距离是否足够近，认为它们属于同一词组

    :param box1: 第一个文本框的边界信息
    :param box2: 第二个文本框的边界信息
    :param horizontal_threshold_scale: 水平方向上的距离阈值比例
    :return: 布尔值，表示水平方向上的距离是否在阈值范围内
    """
    left1, top1, right1, bottom1 = get_box_boundaries(box1)
    left2, top2, right2, bottom2 = get_box_boundaries(box2)

    # 打印box1和box2的边界信息
    # print(f"left1: {left1}, right1: {right1}, left2: {left2}, right2: {right2}")

    horizontal_distance = max(left2, left1) - min(right1, right2)
    horizontal_threshold = min(right1 - left1, right2 - left2) * horizontal_threshold_scale

    # 打印水平方向的距离和阈值信息
    # print(f"Horizontal Distance: {horizontal_distance}")
    # print(f"Horizontal Threshold: {horizontal_threshold}")

    return horizontal_distance < horizontal_threshold


def merge_boxes(box1: List[List[float]], box2: List[List[float]]) -> List[List[float]]:
    """

    :param box1:
    :param box2:
    :return:
    """
    # 合并两个文本框，取最左、最上、最右和最下的边界
    left1, top1, right1, bottom1 = get_box_boundaries(box1)
    left2, top2, right2, bottom2 = get_box_boundaries(box2)

    # 返回合并后的文本框四个顶点的坐标
    return [
        [min(left1, left2), min(top1, top2)],
        [max(right1, right2), min(top1, top2)],
        [max(right1, right2), max(bottom1, bottom2)],
        [min(left1, left2), max(bottom1, bottom2)]
    ]


import time

def merge_same_phrases(results: List[dict], horizontal_threshold, vertical_threshold) -> List[dict]:
    """
    Merge the phrases based on bounding box similarity. Ensure every text box is compared with every other one.

    :param vertical_threshold:
    :param horizontal_threshold:
    :param results: List of text boxes and their respective positions.
    :return: A new list with merged results.
    """
    start_time = time.time()  # 记录开始时间
    merged_results = []
    processed_results = [False] * len(results)
    merge_occurred = True

    # 重复执行合并，直到不再发生合并
    while merge_occurred:
        merge_occurred = False  # 标记是否有合并发生
        merged_results = []  # 每次开始重新初始化合并结果
        processed_results = [False] * len(results)  # 重置已处理标记

        # 遍历每一个 result
        for i, result in enumerate(results):
            if processed_results[i]:
                continue  # 跳过已经处理的文本框

            current_merge = result  # 初始化当前的合并对象

            # 检查水平方向的合并
            for j, other_result in enumerate(results):
                if i == j or processed_results[j]:
                    continue  # 不和自己或已经合并的文本框进行比较

                # print(f"Comparing text box {i} with text box {j} (horizontal)")
                if is_same_phrase(current_merge['Inches_box'], other_result['Inches_box'], 'row', horizontal_threshold, vertical_threshold):
                    # 合并文本框
                    current_merge['Inches_box'] = merge_boxes(current_merge['Inches_box'], other_result['Inches_box'])
                    # 合并文本，水平方向添加空格
                    current_merge['text'] += ' ' + other_result['text']
                    # 标记该文本框已经被处理
                    processed_results[j] = True
                    merge_occurred = True  # 有合并发生

            # 检查垂直方向的合并
            for j, other_result in enumerate(results):
                if i == j or processed_results[j]:
                    continue  # 不和自己或已经合并的文本框进行比较

                # print(f"Comparing text box {i} with text box {j} (vertical)")
                if is_same_phrase(current_merge['Inches_box'], other_result['Inches_box'], 'column', horizontal_threshold, vertical_threshold):
                    # 合并文本框
                    current_merge['Inches_box'] = merge_boxes(current_merge['Inches_box'], other_result['Inches_box'])
                    # 合并文本，垂直方向添加\n
                    current_merge['text'] += "\n" + other_result['text']
                    # 标记该文本框已经被处理
                    processed_results[j] = True
                    merge_occurred = True  # 有合并发生

            # 将最终的合并结果加入结果列表
            merged_results.append(current_merge)
            processed_results[i] = True

        # 更新结果列表为本次合并后的列表
        results = merged_results

    end_time = time.time()  # 记录结束时间
    # print(f"All merged results: {merged_results}")
    # print(f"Time taken for merging: {end_time - start_time:.2f} seconds")
    return merged_results


def ocr_process(result, img, ocr_params, ppt_params):
    from Code.FLask.app import app
    # 解包 OCR 参数
    horizontal_threshold = ocr_params.get('horizontal_threshold')
    vertical_threshold = ocr_params.get('vertical_threshold')
    remove_overlap = ocr_params.get('remove_overlap')

    # 记录 OCR 参数
    app.logger.info("Horizontal Threshold: %s", horizontal_threshold)
    app.logger.info("Vertical Threshold: %s", vertical_threshold)
    app.logger.info("Remove Overlap: %s", remove_overlap)

    # 解包 PPT 参数
    enhance_saturation = ppt_params.get('enhance_saturation')
    enhance_brightness = ppt_params.get('enhance_brightness')

    # 记录 PPT 参数
    app.logger.info("Enhance Saturation: %s", enhance_saturation)
    app.logger.info("Enhance Brightness: %s", enhance_brightness)

    DPI = 192  # Dots Per Inch
    ALL_ROI = 0.9  # ALL Zoom Factor
    BOX_ROI = 1.5  # BOX Zoom Factor
    PPT_width = 13.33
    PPT_height = 7.5

    if result is None:
        app.logger.error("OCR result is None. Check the image path or OCR settings.")
        return None

    txts = []
    boxes = []

    # 处理 OCR 结果
    for index, item in enumerate(result):
        if index == 0:  # 跳过第一个元素
            continue

        bounding_box = item['bounding_box']

        # 提取 bounding_box 中的坐标
        points = [bounding_box[0], bounding_box[1], bounding_box[2], bounding_box[3]]

        # 找到 x 和 y 坐标均最大的元素作为 bottom_right
        bottom_right = max(points, key=lambda p: (p[0], p[1]))
        points.remove(bottom_right)

        # 找到 x 和 y 坐标均最小的元素作为 top_left
        top_left = min(points, key=lambda p: (p[0], p[1]))
        points.remove(top_left)

        if points:
            top_right = points[0]
            bottom_left = points[1]

            txts.append(item['text'])  # 提取文本
            boxes.append([top_left, top_right, bottom_right, bottom_left])  # 添加新的顺序
        else:
            app.logger.warning("不符合条件的元素: text = %s, 原 bounding_box = %s, 跳过此元素", item['text'], bounding_box)

    # 初始化最小和最大值
    min_x, min_y, max_x, max_y = float('inf'), float('inf'), float('-inf'), float('-inf')

    # 遍历所有 boxes，找到最小和最大的 x, y 值
    for box in boxes:
        x1, y1, x2, y2 = get_box_coordinates(box)

        min_x = min(min_x, x1)
        min_y = min(min_y, y1)
        max_x = max(max_x, x2)
        max_y = max(max_y, y2)

    # 计算最大宽度和高度
    max_width = max_x - min_x
    max_height = max_y - min_y

    center_pt_x = (max_x + min_x) / 2
    center_pt_y = (max_y + min_y) / 2

    # 检查 DPI 是否为零
    if DPI == 0:
        app.logger.error("DPI cannot be zero.")
        return None

    # 确保计算值不会导致无穷大
    if max_width / DPI == float('inf') or max_height / DPI == float('inf'):
        app.logger.error("The calculation resulted in infinity. Check max_width and DPI.")
        return None

    # 记录最大宽度和高度
    app.logger.info("最大宽度: %s", max_width)
    app.logger.info("最大高度: %s", max_height)

    # 计算缩放比例
    width_inches = Inches(max_width / DPI)
    height_inches = Inches(max_height / DPI)

    SF_W = width_inches / Inches(PPT_width)
    SF_H = height_inches / Inches(PPT_height)
    SF = max(SF_W, SF_H)

    # 记录缩放系数
    app.logger.info("SF_W: %s", SF_W)
    app.logger.info("SF_H: %s", SF_H)
    app.logger.info("SF: %s", SF)

    # 第二步：计算图片坐标系偏移量（将图片中心点与PPT中心点重合）
    coord_diff_x = PPT_width / 2 - ALL_ROI * (center_pt_x / SF) / DPI
    coord_diff_y = PPT_height / 2 - ALL_ROI * (center_pt_y / SF) / DPI

    # print("coord_diff_x:", coord_diff_x)
    # print("coord_diff_y:", coord_diff_y)

    pre_results = []
    for box, text in zip(boxes, txts):
        pre_result_entry = {
            'text': text,
            'Inches_box': box
        }
        pre_results.append(pre_result_entry)  # 将结果添加到列表中

    merged_results = merge_same_phrases(pre_results, horizontal_threshold, vertical_threshold)

    if remove_overlap:
        filtered_results = remove_overlapping_boxes(merged_results)
    else:
        filtered_results = merged_results

    cv_results = colour_progress(filtered_results, img, enhance_saturation, enhance_brightness)

    for entry in cv_results:
        box = entry['Inches_box']  # Extract the box from result
        text = entry['text']  # Extract the text from result
        colour = entry['colour']
        # print("start-------------------------------------------")
        # print("box:", box)
        # print("text:", text)
        # print("colour:", colour)
        # 第三步：移动图片坐标原点，使图片中心点与 ppt 中心点重合
        box = [
            [ALL_ROI * ((x / SF) / DPI) + coord_diff_x, ALL_ROI * ((y / SF) / DPI) + coord_diff_y]
            for x, y in box
        ]

        # 第四步：单独缩放 box 的大小
        box = zoom_box_coordinates(box, BOX_ROI)
        entry['Inches_box'] = box
        # print("end-------------------------------------------")

    return cv_results


def remove_overlapping_boxes(results: List[dict], overlap_threshold: float = 0.5) -> List[dict]:
    """
    Remove text boxes that have an overlap area greater than the given threshold.

    :param results: List of merged text boxes and their respective positions.
    :param overlap_threshold: The threshold for overlap area to determine if a box should be removed.
    :return: A new list with overlapping boxes removed.
    """
    def compute_iou(left1, top1, right1, bottom1, left2, top2, right2, bottom2):
        # Calculate the (x, y)-coordinates of the intersection rectangle
        x_left = max(left1, left2)
        y_top = max(top1, top2)
        x_right = min(right1, right2)
        y_bottom = min(bottom1, bottom2)

        # Compute the area of intersection rectangle
        if x_right < x_left or y_bottom < y_top:
            return 0.0

        intersection_area = (x_right - x_left) * (y_bottom - y_top)

        # Compute the area of both the prediction and ground-truth rectangles
        box1_area = (right1 - left1) * (bottom1 - top1)
        box2_area = (right2 - left2) * (bottom2 - top2)

        # Compute the intersection over union by taking the intersection
        # area and dividing it by the sum of prediction + ground-truth
        # areas - the intersection area
        iou = intersection_area / float(box1_area + box2_area - intersection_area)
        # print("IOU", iou)
        return iou

    filtered_results = []
    for i, result in enumerate(results):
        should_add = True
        left1, top1, right1, bottom1 = get_box_boundaries(result['Inches_box'])
        for j in range(i):
            left2, top2, right2, bottom2 = get_box_boundaries(results[j]['Inches_box'])
            # print("@@@@@@@@@@@@@@@@@@@@")
            # print(f"BOX1:{result['text']}, BOX2:{results[j]['text']}")
            # print(f'Box 1: left1={left1}, top1={top1}, right1={right1}, bottom1={bottom1}')
            # print(f'Box 2: left2={left2}, top2={top2}, right2={right2}, bottom2={bottom2}')
            # print("!!!!!!!!!!!!!!!!!!!")
            if compute_iou(left1, top1, right1, bottom1, left2, top2, right2, bottom2) > overlap_threshold:
                should_add = False
                # print(f"BOX1:{result['text']}, BOX2:{results[j]['text']} overlapping")
                break
        if should_add:
            filtered_results.append(result)

    return filtered_results


