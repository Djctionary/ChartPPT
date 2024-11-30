import base64
import io
import json
import numpy as np
import requests
from PIL import Image
from flask import Flask, render_template, request, jsonify, g, jsonify, session, send_from_directory
import os
import configparser

from google.cloud import vision
from google.oauth2 import service_account
from werkzeug.utils import secure_filename
from datetime import datetime
import uuid
import threading
import paddleocr
import logging
from OCR.ocr_functions import ocr_process
from PPT.ppt_function import ppt_process
from SHAPE.shape_functions import shape_process
import openai
from openai import AzureOpenAI
import time
import re

credentials = service_account.Credentials.from_service_account_file('./fluted-set-435101-j0-3786e34cbd37.json')
ocr_client = vision.ImageAnnotatorClient(credentials=credentials)

os.environ["KMP_DUPLICATE_LIB_OK"] = "TRUE" # add this so that I can run this

config = configparser.ConfigParser()
config.read('Config_Path.ini')

# 从配置文件中获取 API Key
openai.api_key = config['openai']['api_key']

# 创建 AzureOpenAI 客户端
api_base = config['azure_openai']['api_base']
api_key = config['azure_openai']['api_key']
deployment_name = config['azure_openai']['deployment_name']
api_version = config['azure_openai']['api_version']

client = AzureOpenAI(
    api_key=api_key,
    api_version=api_version,
    base_url=f"{api_base}openai/deployments/{deployment_name}"
)
app = Flask(__name__)

# Define the log format and formatter
logFormatStr = '[%(asctime)s] p%(process)s {%(pathname)s:%(lineno)d} %(levelname)s - %(message)s'
formatter = logging.Formatter(logFormatStr, '%m-%d %H:%M:%S')

# Set up logging configuration
logging.basicConfig(format=logFormatStr, filename="global.log", level=logging.DEBUG)

# File handler for summary.log
fileHandler = logging.FileHandler("summary.log")
fileHandler.setLevel(logging.DEBUG)  # Set to DEBUG to capture all logs
fileHandler.setFormatter(formatter)

# Stream handler to output logs to the console
streamHandler = logging.StreamHandler()
streamHandler.setLevel(logging.DEBUG)  # Set to DEBUG to capture all logs
streamHandler.setFormatter(formatter)

# Get Flask's logger and set its level to DEBUG
app.logger.setLevel(logging.DEBUG)  # Ensure Flask logs are at least DEBUG level
app.logger.addHandler(fileHandler)
app.logger.addHandler(streamHandler)

app.secret_key = config['flask']['secret_key']
app.config['UPLOAD_FOLDER'] = config['flask']['upload_folder']
app.config['MAX_CONTENT_LENGTH'] = int(eval(config['flask']['max_content_length']))
# logging.getLogger().setLevel(logging.INFO)

# 确保上传文件夹存在
if not os.path.exists(app.config['UPLOAD_FOLDER']):
    os.makedirs(app.config['UPLOAD_FOLDER'])

# 允许用户上传的文件扩展名
ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg'}
# 输出PPT名字与路径
file_name = 'ChartPPT.pptx'

progress_status = {}
# 创建一个全局锁对象
progress_lock = threading.Lock()


# 全局错误处理器：捕获所有未处理的异常
@app.errorhandler(Exception)
def handle_exception(e):
    app.logger.error(f"Error Unhandled Exception: {e}")
    return jsonify({"error": "An unexpected error occurred."}), 500

# 专门处理 404 错误
@app.errorhandler(404)
def page_not_found(e):
    app.logger.error(f"404 Not Found: {e}")
    return jsonify({"error": "The requested URL was not found on the server."}), 404


@app.route('/')
def index():
    return render_template('chartPPT.html')


@app.route('/get_user_tag', methods=['GET'])
def get_user_tag():
    user_tag = 'tag_' + str(uuid.uuid4())
    app.logger.info(f"Generated user_tag: {user_tag}")  # 打印生成的 user_tag
    return jsonify({"user_tag": user_tag})


@app.route('/upload_image', methods=['POST'])
def upload_image():
    if 'file' not in request.files:
        return jsonify({'error': 'No file provided'}), 400

    file = request.files['file']
    user_tag = request.form.get('user_tag')  # 从请求表单中获取 user_tag

    if not user_tag:
        return jsonify({'error': 'User tag is missing'}), 400

    if file.filename == '':
        return jsonify({'error': 'No selected file'}), 400

    if file and allowed_file(file.filename):
        # 生成用户专属文件夹路径
        user_folder = os.path.join(app.config['UPLOAD_FOLDER'], user_tag, 'input')
        ppt_folder = os.path.join(app.config['UPLOAD_FOLDER'], user_tag, 'output')

        # 确保文件夹存在
        os.makedirs(user_folder, exist_ok=True)
        os.makedirs(ppt_folder, exist_ok=True)

        # 获取文件扩展名
        file_extension = file.filename.rsplit('.', 1)[1].lower()

        # 生成自定义文件名
        unique_filename = f"img_{datetime.now().strftime('%Y%m%d_%H%M%S')}_{uuid.uuid4().hex}.{file_extension}"

        # 保存文件
        file.save(os.path.join(user_folder, secure_filename(unique_filename)))
        return 'Success', 200

    return 'Error', 400



def allowed_file(filename):
    return '.' in filename and \
        filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS


@app.route('/file-status', methods=['GET'])
def file_status():
    user_tag = request.args.get('user_tag')  # 从查询参数中获取 user_tag
    if not user_tag:
        return jsonify({'error': 'User tag is required'}), 400
    # 生成完整文件路径
    file_path = os.path.join(app.config['UPLOAD_FOLDER'], user_tag, 'output', file_name)

    # 检查文件是否存在
    if os.path.exists(file_path):
        # 获取文件最后修改时间
        last_modified = os.path.getmtime(file_path)
        last_modified_iso = datetime.fromtimestamp(last_modified).isoformat()
        app.logger.info(f'File status checked: {file_path} lastModified={last_modified_iso}')
        return jsonify({'lastModified': last_modified_iso})
    else:
        app.logger.info(f'File not found: {file_path}')
        return jsonify({'error': 'File not found'}), 404


@app.route('/download-file', methods=['GET'])
def download_file():
    user_tag = request.args.get('user_tag')  # 从查询参数中获取 user_tag
    if not user_tag:
        return jsonify({'error': 'User tag is required'}), 400
    # 生成完整文件路径
    file_path = os.path.join(app.config['UPLOAD_FOLDER'], user_tag, 'output', file_name)
    file_dir = os.path.join(app.config['UPLOAD_FOLDER'], user_tag, 'output')
    # 检查文件是否存在
    if os.path.exists(file_path):
        app.logger.info(f'File download requested: {file_path}')
        return send_from_directory(directory=file_dir, path=file_name, as_attachment=True)
    else:
        app.logger.error(f'File not found: {file_path}')
        return jsonify({'error': 'File not found'}), 404


@app.route("/WebAPI/CloudVision", methods=["POST"])
def cloud_ocr():
    data = request.json
    img_base64 = data.get("image")
    parameters = data.get('parameters', {})

    # 从参数中提取 OCR 和 PPT 参数
    ocr_params = parameters.get('ocr_parameters', {})
    ppt_params = parameters.get('ppt_parameters', {})

    if not img_base64:
        return jsonify({"error": "No image data provided."}), 400

    # try:
    # 第1步：将 base64 字符串解码为字节流
    img_byte = base64.b64decode(img_base64)

    # 第2步：将字节流转换为 PIL 图像
    image = io.BytesIO(img_byte)
    img = Image.open(image)

    app.logger.info(f"Image mode:{img.mode}")

    if img.mode == 'P':
        # 将 P 模式的图像转换为 RGB 模式
        img = img.convert('RGB')

    img_array = np.array(img)
    app.logger.info(f'Image shape: {img_array.shape}')

    # 第3步：将 PIL 图像转换为 PNG 并发送到 Google Cloud Vision
    img_byte_array = io.BytesIO()
    img.save(img_byte_array, format='PNG')
    content = img_byte_array.getvalue()

    app.logger.info("Start Vision API")
    # 创建 Vision API 请求的图像对象
    image = vision.Image(content=content)
    response = ocr_client.document_text_detection(image=image)

    # 检查 API 响应中的错误
    if response.error.message:
        return jsonify({"error": response.error.message}), 500

    # 处理 Vision API 响应，获取文本和边界框
    text_annotations = response.text_annotations
    results = []
    for text in text_annotations:
        text_content = text.description
        vertices = [(vertex.x, vertex.y) for vertex in text.bounding_poly.vertices]
        results.append({
            "text": text_content,
            "bounding_box": vertices
        })

    app.logger.info(f"Results: {results}")

    ocr_results = ocr_process(results, img_array, ocr_params, ppt_params)

    return jsonify(ocr_results)

    # except Exception as e:
    #     print("e:", e)
    #     return jsonify({"error": str(e)}), 500

#
# @app.route("/WebAPI/PaddleOCR", methods=["POST"])
# def paddle_ocr():
#     data = request.json
#     img_base64 = data.get("image")
#
#     if not img_base64:
#         app.logger.error("No image data provided.")
#         return jsonify({"error": "No image data provided."}), 400
#
#     # 解码图像
#     try:
#         img_byte = base64.b64decode(img_base64)
#         image = io.BytesIO(img_byte)
#         img = Image.open(image)
#
#         if img.mode == 'P':
#             # 将 P 模式的图像转换为 RGB 模式
#             img = img.convert('RGB')
#             channels = 3
#         elif img.mode == 'RGB':
#             channels = 3
#         elif img.mode == 'RGBA':
#             channels = 4
#         elif img.mode == 'L':  # 灰度图像
#             channels = 1
#         else:
#             channels = 'Unknown'
#
#         print(f'Image mode: {img.mode}')  # 打印图像颜色模式 (e.g., 'RGB', 'RGBA', 'L', 'P')
#
#         img = np.array(img)  # 确保 img 是一个 NumPy 数组
#         print(f'Image shape: {img.shape}')
#
#         app.logger.info("Image successfully decoded and converted to NumPy array.")
#     except Exception as e:
#         app.logger.error("Error decoding image: %s", str(e), exc_info=True)
#         return jsonify({"error": "Invalid image data."}), 400  # 返回错误信息
#
#     try:
#         result = ppocr.ocr(img)
#         app.logger.info("OCR processing completed successfully.")
#     except Exception as e:
#         app.logger.error("Error during OCR processing: %s", str(e), exc_info=True)
#         return jsonify({"error": "OCR processing failed."}), 500  # 返回错误信息
#
#     # 如果有需要处理的 OCR 结果
#     ocr_results = ocr_process(result, img)
#
#     return jsonify(ocr_results)  # 返回 OCR 结果

@app.route('/gpt4-process', methods=['POST'])
def process_image():
    # 获取传入的图像数据（base64 编码）
    data = request.get_json()
    img_base64 = data.get('image')

    if not img_base64:
        return jsonify({"error": "No image data provided"}), 400

    app.logger.info("Start GPT-4 API")
    gpt4_start_time = time.time()
    try:
        response = client.chat.completions.create(
            model=deployment_name,
            messages=[
                {
                    "role": "user",
                    "content": [
                        {
                            "type": "text",
                            "text": (
                                # "This is a flowchart with various shapes and colours. Extract the shape and colour of each box that contains text "
                                # "in the format 'Text: Shape - RGB(x, x, x)'. If only text is present or the shape is unknown, "
                                # "use 'Unknown' for shape and 'RGB(255, 255, 255)' for colour. Provide only the RGB values and "
                                # "use English terms for shapes. Stick to this format without extra labels."
                                # "Example: 'Log: Rectangle - RGB(153, 204, 255)'. Also, extract the flowchart's connection logic "
                                # "Extract the logical flow between boxes based on both their content and the connections (lines or arrows) in the flowchart. "
                                # "Format as '{Text1 -> Text2}', showing only direct, meaningful transitions. Example: '{Log -> Square}'."

                                "This is a flowchart with various texts and shapes. Extract the shape of each box that contains text"
                                "in the format '[Text // Shape]'."
                                "If only text is present or the shape is unknown, use 'Unknown' for shape."
                                "The shape type includes only: Rounded Rectangle, Ellipse, Rectangle, Diamond, Flowchart Document, Ellipse, Parallelogram, Flowchart Magnetic Disk and Trapezoid"
                                "Stick to this format without extra labels."
                                "Example: '[Start // Rounded Rectangle]', '[true // Ellipse]'. Also, extract the flowchart's connection logic "
                                "Extract the logical flow between boxes based on both their content and the connections (lines or arrows) in the flowchart. "
                                "Format as '{Text1 -> Text2}', showing only direct, meaningful transitions. Example: '{Start -> true}'."
                            )
                        },
                        {
                            "type": "image_url",
                            "image_url": {
                                "url": f"data:image/jpeg;base64,{img_base64}",
                            },
                        },
                    ],
                }
            ],
            max_tokens=400,
            temperature=0.2,
            top_p=0.7
        )

        # 使用正则表达式提取文本、形状和颜色
        response_content = response.choices[0].message.content
        app.logger.info("Response content: %s", str(response_content))

        # 定义正则表达式模式
        pattern = r"\[([\w\s()-?!.,]+)\s*//\s*([\w\s()-?!.,]+)\]"
        matches = re.findall(pattern, response_content)
        gpt_results = [{"text": match[0].strip(), "shape": match[1].strip()} for match in matches]

        # 使用正则表达式查找所有匹配项
        # matches = re.findall(pattern, response_content)

        # 构建结果列表，将 RGB 颜色值合并为字符串形式
        # gpt_results = [{"text": match[0].strip(), "shape": match[1], "colour": f"RGB({match[2]}, {match[3]}, {match[4]})"}
        #                for match in matches]

        if not gpt_results:
            app.logger.error("No valid shapes and colours found.")
            return jsonify({"error": "No valid shapes and colours found."}), 500

        # 定义连接逻辑的正则表达式模式
        connection_pattern = r"\{([^\{]+?)\s*->\s*([^\{]+?)\}"

        # 使用正则表达式查找所有连接逻辑匹配项
        connection_matches = re.findall(connection_pattern, response_content)

        # 构建连接逻辑结果列表
        connection_results = [{"from": match[0].strip(), "to": match[1].strip()} for match in connection_matches]

        if not connection_results:
            app.logger.error("No logical line found.")
            return jsonify({"error": "No logical line found."}), 500

        gpt_results.extend(connection_results)
        app.logger.info(f"GPT: {gpt_results}")

    except Exception as e:
        app.logger.error(f"Error occurred: {e}", exc_info=True)
        return jsonify({"error": "An error occurred while processing the request."}), 500

    gpt4_end_time = time.time()

    # 计算并打印调用时间
    gpt4_execution_time = gpt4_end_time - gpt4_start_time
    app.logger.info("GPT-4 API 调用时间: %.2f 秒", float(gpt4_execution_time))

    return jsonify(gpt_results)  # 返回结果为 JSON 格式


@app.route('/run_main_logic', methods=['POST'])
def process():
    # 接收图像数据
    data = request.get_json()

    # 检查 JSON 数据的有效性
    if not data:
        return jsonify({"error": "Invalid or missing JSON data."}), 400

    img_base64 = data.get('image')
    user_tag = data.get('user_tag')

    if not img_base64 or not user_tag:
        return jsonify({"error": "Missing 'image' or 'user_tag' in request."}), 400

    with progress_lock:
        progress_status[user_tag] = "Start Processing"

    # 获取 OCR 参数
    ocr_parameters = data.get('ocr_parameters', {})
    horizontal_threshold = ocr_parameters.get('horizontal_threshold')
    vertical_threshold = ocr_parameters.get('vertical_threshold')
    remove_overlap = ocr_parameters.get('remove_overlap')
    recognize_shape = ocr_parameters.get('recognize_shape')

    # 获取 PPT 参数
    ppt_parameters = data.get('ppt_parameters', {})
    enhance_saturation = ppt_parameters.get('enhance_saturation')
    enhance_brightness = ppt_parameters.get('enhance_brightness')
    shape_size_ratio = ppt_parameters.get('shape_size_ratio')
    add_lines_between_shapes = ppt_parameters.get('add_lines_between_shapes')
    line_style = ppt_parameters.get('line_style')

    parameters = {
        "ocr_parameters": {
            "horizontal_threshold": horizontal_threshold,
            "vertical_threshold": vertical_threshold,
            "remove_overlap": remove_overlap,
            "recognize_shape": recognize_shape
        },
        "ppt_parameters": {
            "enhance_saturation": enhance_saturation,
            "enhance_brightness": enhance_brightness,
            "shape_size_ratio": shape_size_ratio,
            "add_lines_between_shapes": add_lines_between_shapes,
            "line_style": line_style
        },
        "user_tag": user_tag
    }

    # 检查 Base64 字符串的有效性和类型
    if img_base64.startswith('data:image/png;base64,'):
        img_base64 = img_base64.split(',')[1]
        mime_type = 'image/png'
    elif img_base64.startswith('data:image/jpeg;base64,'):
        img_base64 = img_base64.split(',')[1]
        mime_type = 'image/jpeg'
    elif img_base64.startswith('data:image/gif;base64,'):
        img_base64 = img_base64.split(',')[1]
        mime_type = 'image/gif'
    else:
        return jsonify({"error": "Invalid base64 image format."}), 400

    # 解码 base64 图像
    try:
        img_byte = base64.b64decode(img_base64)
    except Exception:
        return jsonify({"error": "Invalid base64 image."}), 400

    with progress_lock:
        progress_status[user_tag] = "Performing Text Recognition Using OCR"

    app.logger.info(f"Current progress_status: {progress_status[user_tag]}")

    try:
        ocr_response = requests.post(
            f"http://{config['flask']['server_ip']}:5000/WebAPI/CloudVision",
            json={
                "image": img_base64,
                "parameters": parameters
            }
        )
        if ocr_response.status_code == 200 and 'application/json' in ocr_response.headers.get('Content-Type', ''):
            ocr_results = ocr_response.json()
        else:
            return jsonify({"error": f"Failed to communicate with CloudVision API, status code: {ocr_response.status_code}"}), 500
    except Exception as e:
        return jsonify({"error": f"Error during CloudVision request: {str(e)}"}), 500

    with progress_lock:
        progress_status[user_tag] = "Performing Line and Shape Recognition Using GPT"

    physical_results = None
    logical_results = None

    if not recognize_shape and not add_lines_between_shapes:
        app.logger.info(f"SKIP GPT")
    else:
        try:
            gpt_response = requests.post(
                f"http://{config['flask']['server_ip']}:5000/gpt4-process",
                json={"image": img_base64}
            )
            if gpt_response.status_code == 200 and 'application/json' in gpt_response.headers.get('Content-Type', ''):
                gpt_results = gpt_response.json()
            else:
                return jsonify({"error": f"Failed to communicate with GPT API, status code: {gpt_response.status_code}"}), 500
        except Exception as e:
            return jsonify({"error": f"Error during GPT request: {str(e)}"}), 500

        physical_results, logical_results = shape_process(gpt_results)

        app.logger.info(f"ocr_results: {ocr_results}")
        app.logger.info(f"physical_results: {physical_results}")
        app.logger.info(f"logical_results: {logical_results}")

    with progress_lock:
        progress_status[user_tag] = "Generating PPT"

    # 添加 try-except 块以捕获 ppt_process 中的异常
    try:
        ppt_process(ocr_results, physical_results, logical_results, parameters)
        app.logger.info("PPT processing completed successfully.")
    except Exception as e:
        app.logger.error(f"Error during PPT processing: {str(e)}")
        return jsonify({"error": f"Error during PPT processing: {str(e)}"}), 500

    return jsonify({"success": "Great!"}), 200



@app.route('/progress_status', methods=['GET'])
def get_progress():
    user_tag = request.args.get('user_tag')

    # 使用锁来保护对 progress_status 的读取操作
    with progress_lock:
        if user_tag in progress_status:
            return jsonify({'status': progress_status[user_tag]}), 200
        else:
            return jsonify({'error': 'No such user'}), 404


if __name__ == '__main__':
    # Run the Flask application
    app.run(host=config['flask']['server_ip'], debug=True, threaded=True)

    # app.run(host=config['flask']['server_ip'], port=5000, debug=False, threaded=True)