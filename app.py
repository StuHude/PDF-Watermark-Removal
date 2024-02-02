from flask import Flask, render_template, request, send_file
import os
import cv2
import numpy as np
import fitz
from PyPDF2 import PdfReader, PdfWriter
from io import BytesIO
from fpdf import FPDF
from PIL import Image
import tempfile
from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import A4
CONVERT_DPI = 300

app = Flask(__name__)


# 图像去除水印函数
def remove_watermark(image_path):
    img = cv2.imread(image_path)
    lower_hsv = np.array([160, 160, 160])
    upper_hsv = np.array([255, 255, 255])
    mask = cv2.inRange(img, lower_hsv, upper_hsv)
    mask = cv2.GaussianBlur(mask, (1, 1), 0)
    img[mask == 255] = [255, 255, 255]
    cv2.imwrite(image_path, img)


# 将PDF转换为图片，并保存到指定目录

def pdf_to_images(pdf_path, output_folder):
    images = []
    doc = fitz.open(pdf_path)
    dpi = CONVERT_DPI / 72  # 使用全局DPI设置
    for page_num in range(doc.page_count):
        page = doc[page_num]
        # 设置分辨率为300 DPI
        pix = page.get_pixmap(matrix=fitz.Matrix(300 / 72, 300 / 72))
        image_path = os.path.join(output_folder, f"page_{page_num + 1}.png")
        pix.save(image_path)
        images.append(image_path)
        # 去除每张图片的水印
        remove_watermark(image_path)
    return images


# 将图片合并为PDF

# 定义A4纸张在72dpi下的像素尺寸（宽度和高度）
A4_SIZE_PX_72DPI = (595, 842)


def images_to_pdf(image_paths, output_path):
    pdf_writer = FPDF(unit='pt', format='A4')

    for image_path in image_paths:
        with Image.open(image_path) as img:
            width, height = img.size

            # 计算实际DPI（假设从pdf转图片时已设置为300 DPI）
            dpi = 300
            ratio = min(A4_SIZE_PX_72DPI[0] / width, A4_SIZE_PX_72DPI[1] / height)

            # 缩放图像以适应A4纸张，并保持长宽比
            img_resized = img.resize((int(width * ratio), int(height * ratio)))

            # 创建临时文件并写入图片数据
            with tempfile.NamedTemporaryFile(suffix=".png", delete=False) as temp_file:
                img_resized.save(temp_file.name, format='PNG')

            # 添加一页
            pdf_writer.add_page()

            # 使用临时文件路径添加图像到PDF
            pdf_writer.image(temp_file.name, x=0, y=0, w=A4_SIZE_PX_72DPI[0], h=A4_SIZE_PX_72DPI[1])

    # 清理临时文件
    for image_path in image_paths:
        _, temp_filename = os.path.split(image_path)
        if os.path.exists(temp_filename):
            os.remove(temp_filename)

    pdf_writer.output(output_path)



@app.route('/')
def index():
    return render_template('index.html')


@app.route('/upload', methods=['POST'])
def upload():
    uploaded_file = request.files['file']
    if uploaded_file.filename != '':
        pdf_path = 'uploads/uploaded_file.pdf'
        uploaded_file.save(pdf_path)
        return render_template('index.html', message='文件上传成功')


@app.route('/remove_watermark', methods=['GET'])
def remove_watermark_route():
    pdf_path = 'uploads/uploaded_file.pdf'
    output_folder = 'output_images'
    os.makedirs(output_folder, exist_ok=True)  # 创建输出目录（如果不存在）
    image_paths = pdf_to_images(pdf_path, output_folder)
    output_pdf_path = 'output_file.pdf'
    images_to_pdf(image_paths, output_pdf_path)
    return render_template('index.html', message='水印去除成功')


@app.route('/download')
def download():
    output_pdf_path = 'output_file.pdf'
    return send_file(output_pdf_path, as_attachment=True)


if __name__ == '__main__':
    app.run(debug=True)
