
const fileUrl = '/download-file'; // 文件下载的 API
const statusUrl = '/file-status'; // 获取文件状态的 API

let imgBase64 = ''; // 用于存储 Base64 编码的图像

let lastModified = null;
let isDownloading = true;  // 锁变量
let progressInterval;

window.onload = function() {
    const themeStyle = document.getElementById('theme-style');

    Swal.fire({
        heightAuto: false,  // 禁用自动高度
        title: 'Select Theme Color',
        input: 'select',
        inputOptions: {
            classical: 'Classical',
            cyber: 'Cyber',
            minimalism: 'Minimalism',
            natural: 'Natural',
            simplified: 'Simplified',
            vibrant: 'Vibrant'
        },
        inputPlaceholder: 'Please select a theme',
        showCancelButton: true,
        confirmButtonText: 'Confirm',
        cancelButtonText: 'Cancel',
        customClass: {
            popup: 'green-popup',
            confirmButton: 'green-button',
            cancelButton: 'green-button',
        },
        preConfirm: (value) => {
            if (!value) {
                Swal.showValidationMessage('Please select a theme');
            } else {
                return value;
            }
        },
        didOpen: () => {
            // 直接在弹窗打开后设置样式
            const popup = Swal.getPopup();
            popup.style.backgroundColor = '#FFF7FF';
            popup.style.border = '2px solid #CC99FF';

            const confirmButton = Swal.getConfirmButton();
            confirmButton.style.backgroundColor = '#6666FF';
            confirmButton.style.color = 'white';

            confirmButton.onmouseover = () => {
                confirmButton.style.backgroundColor = '#7F00FF';
            };
            confirmButton.onmouseleave = () => {
                confirmButton.style.backgroundColor = '#6666FF';
            };

            const cancelButton = Swal.getCancelButton();
            cancelButton.style.backgroundColor = '#6666FF';
            cancelButton.style.color = 'white';

            cancelButton.onmouseover = () => {
                cancelButton.style.backgroundColor = '#7F00FF';
            };
            cancelButton.onmouseleave = () => {
                cancelButton.style.backgroundColor = '#6666FF'; 
            };
        }
    }).then((result) => {
        if (result.isConfirmed) {
            const selectedTheme = result.value;
            switch (selectedTheme) {
                case 'classical':
                    themeStyle.setAttribute('href', "static/css/chartPPT-Classical.css");
                    break;
                case 'cyber':
                    themeStyle.setAttribute('href', "static/css/chartPPT-Cyber.css");
                    break;
                case 'minimalism':
                    themeStyle.setAttribute('href', "static/css/chartPPT-Minimalism.css");
                    break;
                case 'natural':
                    themeStyle.setAttribute('href', "static/css/chartPPT-Natural.css");
                    break;
                case 'simplified':
                    themeStyle.setAttribute('href', "static/css/chartPPT-Simplified.css");
                    break;
                case 'vibrant':
                    themeStyle.setAttribute('href', "static/css/chartPPT-Vibrant.css");
                    break;
            }
        }
    });
}

async function checkFileStatus() {
    if (isDownloading) return;  // 如果正在下载，直接退出

    try {
        const url = new URL(statusUrl, window.location.origin);
        url.searchParams.append('user_tag', sessionStorage.getItem('user_tag'));  // 将 user_tag 作为查询参数

        const response = await fetch(url, {
            method: 'GET',
            headers: {
                'Content-Type': 'application/json'
            }
        });

        const data = await response.json();

        if (lastModified !== data.lastModified && data.lastModified) {
            console.log('File has changed. Previous lastModified:', lastModified);
            lastModified = data.lastModified;
            console.log('New lastModified:', lastModified);

            // 启用锁
            isDownloading = true;

            // 触发文件下载
            await downloadFile();

            // 下载完成后释放锁
            isDownloading = false;
        }
    } catch (error) {
        console.error('Error checking file status:', error);
        isDownloading = false;  // 确保出错时也释放锁
    }
}

function enableButton(button) {
  button.classList.remove('disabled');
  button.classList.add('enabled');
  button.disabled = false;
}


function disableButton(button) {
  button.classList.remove('enabled');
  button.classList.add('disabled');
  button.disabled = true;
}

function downloadFile() {
    // 显示弹窗提示用户文件开始下载
    Swal.fire({
        heightAuto: false,  // 禁用自动高度
        title: 'Download Started',
        text: 'Your file is being downloaded.',
        icon: 'info',
        timer: 3000,
        showConfirmButton: false
    });


    // 创建一个临时的 <a> 元素
    const link = document.createElement('a');
    const userTag = encodeURIComponent(sessionStorage.getItem('user_tag')); // 获取并编码 user_tag
    link.href = `${fileUrl}?user_tag=${userTag}`; // 通过查询参数发送 user_tag
    link.download = 'ChartPPT.pptx'; // 设置下载文件名

    // 将 <a> 元素添加到页面中并模拟点击
    document.body.appendChild(link);
    link.click();

    // 移除 <a> 元素
    document.body.removeChild(link);
}


let lastStatus = ''; // 保存上一次的任务状态

function checkProgress(userTag) {
    // 向 Flask 服务器请求进度状态
    fetch(`/progress_status?user_tag=${userTag}`)
        .then(response => response.json())
        .then(data => {
            if (data.status) {
                console.log(data.status);

                // 仅当状态和之前不同的时候更新弹窗
                if (data.status !== lastStatus) {
                    lastStatus = data.status; // 更新 lastStatus

                    // 更新 Swal 弹窗中的 text 属性
                    Swal.fire({
                        heightAuto: false,
                        title: 'Processing...',
                        text: data.status,
                        icon: 'info',
                        allowOutsideClick: false,
                        showConfirmButton: false, // 不显示 OK 按钮
                        didOpen: () => {
                            Swal.showLoading(); // 显示加载动画
                        }
                    });
                }
            } else if (data.error) {
                console.error(data.error);
            }
        })
        .catch(error => console.error('Error:', error));
}


function startProgressPolling(userTag) {
    progressInterval = setInterval(function () {
        checkProgress(userTag);
    }, 200);
}


function stopProgressPolling() {
    // 停止轮询
    clearInterval(progressInterval);
}


document.addEventListener('DOMContentLoaded', function() {

    const ranges = [
        {
            slider: document.getElementById('horizontal-threshold'),
            valueSpan: document.getElementById('horizontal-threshold-value')
        },
        {
            slider: document.getElementById('vertical-threshold'),
            valueSpan: document.getElementById('vertical-threshold-value')
        },
        {
            slider: document.getElementById('enhance-saturation'),
            valueSpan: document.getElementById('enhance-saturation-value')
        },
        {
            slider: document.getElementById('enhance-brightness'),
            valueSpan: document.getElementById('enhance-brightness-value')
        },
        {
            slider: document.getElementById('shape-size'),
            valueSpan: document.getElementById('shape-size-value')
        }
    ];

    fetch('/get_user_tag')
    .then(response => response.json())
    .then(data => {
        console.log(data.user_tag)
        // 存储 user_tag 到 sessionStorage
        sessionStorage.setItem('user_tag', data.user_tag);
        console.log('userTag:', sessionStorage.getItem('user_tag'));
    })
    .catch(error => {
        console.error('Error fetching user_tag:', error);
    });

//    const button = document.getElementById('convert-button');
//    disableButton(button)

    const rangeInputs = document.querySelectorAll('input[type="range"]');
    const drawer = document.getElementById('drawer');
    const tutorialModal = document.getElementById('tutorial-modal');
    const tutorialBtn = document.getElementById('tutorial-button');
    const closeBtns = document.getElementsByClassName('close');
    const mainContent = document.querySelector('main');

    rangeInputs.forEach(input => {
        const valueDisplay = document.getElementById(`${input.id}-value`);
        input.addEventListener('input', function() {
            valueDisplay.textContent = this.value + (this.id === 'shape-size' ? '%' : '');
        });
    });

    document.querySelectorAll('.parameter').forEach(parameter => {
        parameter.addEventListener('mouseenter', function() {
            // 改变字体粗细并添加动画
            this.classList.add('hovered');

            // 创建工具提示框
            const tooltip = document.createElement('div');
            tooltip.className = 'tooltip';
            tooltip.innerText = this.getAttribute('title');
            document.body.appendChild(tooltip);

            // 定位工具提示框
            const rect = this.getBoundingClientRect();
            tooltip.style.left = `${rect.left + window.scrollX}px`;
            tooltip.style.top = `${rect.top + window.scrollY - tooltip.offsetHeight - 10}px`;

            // 为工具提示框添加动画
            requestAnimationFrame(() => {
                tooltip.classList.add('visible');
            });
        });

        parameter.addEventListener('mouseleave', function() {
            // 恢复字体粗细并移除动画
            this.classList.remove('hovered');

            // 移除工具提示框
            document.querySelectorAll('.tooltip').forEach(tooltip => {
                tooltip.classList.remove('visible');
                tooltip.addEventListener('transitionend', () => {
                    tooltip.remove();
                });
            });
        });
    });


    // Disable line-style select if "Add Lines Between Shapes" is unchecked
    document.getElementById('add-lines').addEventListener('change', function() {
        document.getElementById('line-style').disabled = !this.checked;
    });


    tutorialBtn.onclick = function() {
        tutorialModal.style.display = "block";
    }

    Array.from(closeBtns).forEach(btn => {
        btn.onclick = function() {
            tutorialModal.style.display = "none";
        }
    });

    window.onclick = function(event) {
        if (event.target == tutorialModal) {
            tutorialModal.style.display = "none";
        }
    }


    // 每隔 0.5 秒检查一次文件状态
    setInterval(checkFileStatus, 500);

    const upload = document.getElementById('upload');

    const download = document.getElementById('download');
    const convertButton = document.getElementById('convert-button');
    const selectLabel = document.getElementById('select-label');
    const image = document.getElementById('image');
    const canvas = document.getElementById('imageCanvas');
    const ctx = canvas.getContext('2d');

    upload.addEventListener('change', function(event) {
        const file = event.target.files[0];
        if (file && !['image/png', 'image/jpeg', 'image/jpg'].includes(file.type)) {
            return;
        }
        if (file) {
            const reader = new FileReader();
            reader.onload = function(e) {
                imgBase64 = e.target.result; // 获取 Base64 编码的图像并保存
                const img = new Image();
                img.onload = function() {
                    // 在这里可以进行图像预览或其他处理
                    canvas.width = img.width;
                    canvas.height = img.height;
                    ctx.drawImage(img, 0, 0);
                    canvas.style.display = 'block';

                    selectLabel.style.position = 'absolute';

                    // 设置 z-index 确保覆盖在图片上
                    selectLabel.style.zIndex = '1000';

                    // 调整位置，例如将其置于图片上方
                    selectLabel.style.opacity = '0.8';  // 透明度 80%

                    // 获取像素数据，包含颜色通道
                    const imageData = ctx.getImageData(0, 0, img.width, img.height);
                    const channels = imageData.data.length / (img.width * img.height);

                    console.log(`Image shape: (${img.width}, ${img.height}, ${channels})`);
//                    selectLabel.style.display = 'none';
                };
                img.src = imgBase64; // 将图像显示在画布上
            };
            reader.readAsDataURL(file);
            // 显示 drawer
            drawer.style.bottom = '0';
            drawer.style.transition = 'bottom 0.5s ease-out';

            // 移动 mainContent
            mainContent.style.transform = 'translateY(-40vh)';
            mainContent.style.transition = 'transform 0.5s ease-out';

        }
    });

    document.getElementById('upload').addEventListener('change', (event) => {
        const file = event.target.files[0];
        if (!file) {
            Swal.fire({
                heightAuto: false,  // 禁用自动高度
                title: 'No File Selected',
                text: 'Please select a file to upload.',
                icon: 'warning',
                confirmButtonText: 'OK'
            });
            return;
        }

        const formData = new FormData();
        formData.append('file', file);

        const userTag = sessionStorage.getItem('user_tag');
        formData.append('user_tag', userTag);

        fetch('/upload_image', {
            method: 'POST',
            body: formData
        })
        .then(response => response.text())
        .then(text => {
            console.log('Response text:', text);
            if (text === 'Success') {
                Swal.fire({
                    heightAuto: false,  // 禁用自动高度
                    title: 'Success!',
                    text: 'File uploaded successfully.',
                    icon: 'success',
                    confirmButtonText: 'OK'
                });
            } else if (text === 'Error') {
                Swal.fire({
                    heightAuto: false,  // 禁用自动高度
                    title: 'Invalid File Format',
                    text: 'Please upload a PNG, JPG, or JPEG file.',
                    icon: 'error',
                    confirmButtonText: 'OK'
                });
            } else {
                Swal.fire({
                    heightAuto: false,  // 禁用自动高度
                    title: 'Unexpected Response',
                    text: 'Unexpected response: ' + text,
                    icon: 'info',
                    confirmButtonText: 'OK'
                });
            }
        })
        .catch(error => {
            console.error('Error:', error);
            Swal.fire({
                heightAuto: false,  // 禁用自动高度
                title: 'Error!',
                text: 'An error occurred. Check the console for details.',
                icon: 'error',
                confirmButtonText: 'OK'
            });
        });

    });

    convertButton.addEventListener('click', (event) => {
        const horizontalThreshold = document.getElementById('horizontal-threshold').value;
        const verticalThreshold = document.getElementById('vertical-threshold').value;
        const removeOverlap = document.getElementById('remove-overlap').checked;
        const recognizeShape = document.getElementById('recognize-shape').checked;

        const enhanceSaturation = document.getElementById('enhance-saturation').value;
        const enhanceBrightness = document.getElementById('enhance-brightness').value;
        const shapeSize = document.getElementById('shape-size').value;
        const addLines = document.getElementById('add-lines').checked;
        const lineStyle = document.getElementById('line-style').value;


        const requestBody = {
            image: imgBase64,
            user_tag: sessionStorage.getItem('user_tag'),
            ocr_parameters: {
                horizontal_threshold: parseFloat(horizontalThreshold), // 将字符串值转换为数值
                vertical_threshold: parseFloat(verticalThreshold),
                remove_overlap: removeOverlap,
                recognize_shape: recognizeShape
            },
            ppt_parameters: {
                enhance_saturation: parseFloat(enhanceSaturation),
                enhance_brightness: parseFloat(enhanceBrightness),
                shape_size_ratio: parseFloat(shapeSize),
                add_lines_between_shapes: addLines,
                line_style: lineStyle
            }
        };

        // 打印请求体以进行检查
        console.log(requestBody);

        fetch('/run_main_logic', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify(requestBody)
        })
        .then(response => {
            const contentType = response.headers.get('Content-Type');

            if (contentType && contentType.includes('application/json')) {
                return response.json().then(data => {
                    console.log('Response:', data);

                    if (!response.ok) {
                        throw new Error(`Error ${response.status}: ${data.error || 'Something went wrong'}`);
                    }

                    return data;
                });
            } else {
                return response.text().then(text => {
                    console.error('Non-JSON response:', text);
                    throw new Error(`Unexpected content type: ${contentType || 'Unknown'}. Response: ${text}`);
                });
            }
        })
        .then(data => {
            console.log('Success: Image sent to main logic:', data);
            Swal.close();
            Swal.fire({
                heightAuto: false,
                title: 'Success',
                text: 'Image processed successfully!',
                icon: 'success',
                timer: 2000,
                showConfirmButton: false
            });
        })
        .catch((error) => {
            console.error('Error:', error);

            // 检查响应是否为JSON格式
            if (error.response && error.response.headers.get('Content-Type').includes('application/json')) {
                error.response.json().then(data => {
                    Swal.close();
                    Swal.fire({
                        heightAuto: false,
                        title: 'Error',
                        text: `${data.error || error.message}. Please upload a new process flow diagram.`,
                        icon: 'error',
                        timer: 5000,
                        showConfirmButton: false
                    });
                }).catch(() => {
                    // 无法解析为JSON时的处理
                    Swal.close();
                    Swal.fire({
                        heightAuto: false,
                        title: 'Request in Progress',
                        text: 'Current requests are too frequent. Retrying, please wait...',
                        icon: 'warning',
                        timer: 3000,
                        showConfirmButton: false
                    });
                });
            } else {
                // 非JSON格式的错误响应
                Swal.close();
                Swal.fire({
                    heightAuto: false,
                    title: 'Request in Progress',
                    text: 'Current GPT requests are too frequent. Please try again later.',
                    icon: 'warning',
                    timer: 3000,
                    showConfirmButton: false
                });
            }
        })
        .finally(() => {
            stopProgressPolling();
            isDownloading = false;

            const main = document.querySelector('main');
            const drawer = document.getElementById('drawer');

            main.style.transition = 'transform 0.5s ease-out';
            drawer.style.transition = 'transform 0.5s ease-out';

            main.style.transform = 'translateY(0)';
            drawer.style.transform = 'translateY(0)';

            setTimeout(() => {
                mainContent.style.transform = 'translateY(0)';
                drawer.style.bottom = '-100%';
                mainContent.style.transition = 'transform 0.5s ease-out';
                drawer.style.transition = 'bottom 0.5s ease-out';
            }, 500);
        });


        startProgressPolling(sessionStorage.getItem('user_tag'))

        Swal.fire({
            heightAuto: false,
            title: 'Processing...',
            text: 'Starting to convert the image. Please wait...',
            icon: 'info',
            allowOutsideClick: false,
            didOpen: () => {
                Swal.showLoading();
            }
        });

    });

    // 初始化显示百分号
    ranges.forEach(({ slider, valueSpan }) => {
        valueSpan.textContent = `${slider.value}%`;

        // 添加监听器，更新滑块的显示值
        slider.addEventListener('input', function () {
            valueSpan.textContent = `${slider.value}%`;
        });
    });

    document.getElementById('reset-button').addEventListener('click', function() {
        document.getElementById('horizontal-threshold').value = 100;
        document.getElementById('vertical-threshold').value = 100;
        document.getElementById('remove-overlap').checked = true;
        document.getElementById('recognize-shape').checked = false;
        document.getElementById('enhance-brightness').value = 100;
        document.getElementById('enhance-saturation').value = 100;
        document.getElementById('shape-size').value = 100;
        document.getElementById('add-lines').checked = false;
        document.getElementById('line-style').value = 'curve';
        document.getElementById('line-style').disabled = false; // 禁用下拉框

        ranges.forEach(({ slider, valueSpan }) => {
            valueSpan.textContent = `${slider.value}%`;
        });
    });

});

