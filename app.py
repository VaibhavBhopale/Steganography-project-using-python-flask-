from flask import Flask, render_template, request, redirect, url_for, send_file
import cv2
import numpy as np
import os

app = Flask(__name__)

# Convert message to binary
def msg_to_bin(msg):
    if type(msg) == str:
        return ''.join([format(ord(i), "08b") for i in msg])
    elif type(msg) in {bytes, np.ndarray}:
        return [format(i, "08b") for i in msg]
    elif type(msg) in {int, np.uint8}:
        return format(msg, "08b")
    else:
        raise TypeError("Input type not supported")

# Hide data into image
def hide_data(img, secret_msg):
    nBytes = img.shape[0] * img.shape[1] * 3 // 8
    if len(secret_msg) > nBytes:
        raise ValueError("Error: Insufficient bytes, need a bigger image or less data!")
    secret_msg += '#####'
    dataIndex = 0
    bin_secret_msg = msg_to_bin(secret_msg)
    dataLen = len(bin_secret_msg)
    
    for values in img:
        for pixels in values:
            r, g, b = msg_to_bin(pixels)
            if dataIndex < dataLen:
                pixels[0] = int(r[:-1] + bin_secret_msg[dataIndex], 2)
                dataIndex += 1
            if dataIndex < dataLen:
                pixels[1] = int(g[:-1] + bin_secret_msg[dataIndex], 2)
                dataIndex += 1
            if dataIndex < dataLen:
                pixels[2] = int(b[:-1] + bin_secret_msg[dataIndex], 2)
                dataIndex += 1
            if dataIndex >= dataLen:
                break
    return img

# Show data from image
def show_data(img):
    bin_data = ""
    for values in img:
        for pixels in values:
            r, g, b = msg_to_bin(pixels)
            bin_data += r[-1]
            bin_data += g[-1]
            bin_data += b[-1]
    allBytes = [bin_data[i: i + 8] for i in range(0, len(bin_data), 8)]
    decodedData = ""
    for byte in allBytes:
        decodedData += chr(int(byte, 2))
        if decodedData[-5:] == "#####":
            break
    return decodedData[:-5]

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/encode', methods=['POST'])
def encode():
    if 'image' not in request.files or 'message' not in request.form:
        return redirect(url_for('index'))
    
    image = request.files['image']
    message = request.form['message']
    image_path = "static/temp_image.png"
    image.save(image_path)

    img = cv2.imread(image_path)
    if img is None:
        return redirect(url_for('index'))

    try:
        encoded_img = hide_data(img, message)
        encoded_image_path = "static/encoded_image.png"
        cv2.imwrite(encoded_image_path, encoded_img)
        return send_file(encoded_image_path, as_attachment=True)
    except Exception as e:
        return str(e)
    finally:
        os.remove(image_path)

@app.route('/decode', methods=['POST'])
def decode():
    if 'image' not in request.files:
        return redirect(url_for('index'))
    
    image = request.files['image']
    image_path = "static/temp_image.png"
    image.save(image_path)

    img = cv2.imread(image_path)
    if img is None:
        return redirect(url_for('index'))

    try:
        hidden_message = show_data(img)
        return render_template('index.html', decoded_message=hidden_message)
    except Exception as e:
        return str(e)
    finally:
        os.remove(image_path)

if __name__ == '__main__':
    app.run(debug=True)
