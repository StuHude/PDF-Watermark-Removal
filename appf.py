from flask import Flask, request, send_file
from flask import Flask, render_template, request, send_file
import os
import shutil
from io import BytesIO
import img2pdf
from PIL import Image
from PyPDF2 import PdfReader
from collections import OrderedDict

app = Flask(__name__)

@app.route('/')
def index():
    return render_template('indexx.html')
@app.route('/remove_watermark', methods=['POST'])
def remove_watermark():
    def is_gray(a, b, c):
        r = 40
        if a + b + c < 350:
            return True
        if abs(a - b) > r:
            return False
        if abs(a - c) > r:
            return False
        if abs(b - c) > r:
            return False
        return True


    def remove_watermark(image):
        image = image.convert("RGB")
        color_data = image.getdata()

        new_color = []
        for item in color_data:
            if is_gray(item[0], item[1], item[2]):
                new_color.append(item)
            else:
                new_color.append((255, 255, 255))

        image.putdata(new_color)
        return image


    def process_page(pdf, page_index, skipped):
        content = pdf.pages[page_index]['/Resources']['/XObject'].get_object()
        images = {}
        for obj in content:
            if content[obj]['/Subtype'] == '/Image':
                size = (content[obj]['/Width'], content[obj]['/Height'])
                data = content[obj]._data
                if content[obj]['/ColorSpace'] == '/DeviceRGB':
                    mode = "RGB"
                else:
                    mode = "P"

                if content[obj]['/Filter'] == '/FlateDecode':
                    img = Image.frombytes(mode, size, data)
                else:
                    img = Image.open(BytesIO(data))
                images[int(obj[3:])] = img
        images = OrderedDict(sorted(images.items())).values()
        widths, heights = zip(*(i.size for i in images))
        total_height = sum(heights)
        max_width = max(widths)
        concat_image = Image.new('RGB', (max_width, total_height))
        offset = 0
        for i in images:
            concat_image.paste(i, (0, offset))
            offset += i.size[1]
        if not skipped:
            concat_image = remove_watermark(concat_image)
        concat_image.save("./temp/{}.jpg".format(page_index))


    file = request.files['file']
    temp_dir = './temp/'

    if not os.path.exists(temp_dir):
        os.makedirs(temp_dir)

    input_pdf_path = os.path.join(temp_dir, 'input.pdf')
    file.save(input_pdf_path)

    pdf = PdfReader(open(input_pdf_path, "rb"))
    for i in range(len(pdf.pages)):
        process_page(pdf, i, False)

    output_pdf_bytes = BytesIO()
    output_pdf_bytes.write(img2pdf.convert(*[f"./temp/{i}.jpg" for i in range(pdf.getNumPages())]))

    shutil.rmtree(temp_dir, True)

    return send_file(output_pdf_bytes, attachment_filename='output.pdf', as_attachment=True)


if __name__ == '__main__':
    app.run(debug=True)