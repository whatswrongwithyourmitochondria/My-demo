#!/usr/bin/env python
# -*- coding: utf-8 -*-
import os
import copy
import time
import argparse

import cv2 as cv
import numpy as np
import tensorflow as tf


def get_args():
    parser = argparse.ArgumentParser()

    parser.add_argument("--device", type=int, default=0)
    parser.add_argument("--movie", type=str, default=None)
    parser.add_argument("--width", help='cap width', type=int, default=640)
    parser.add_argument("--height", help='cap height', type=int, default=360)

    parser.add_argument(
        "--model",
        type=str,
        default="model/model_float16_quant.tflite",
    )
    parser.add_argument(
        "--input_size",
        type=str,
        default='512,512',
    )

    args = parser.parse_args()

    return args


def run_inference(interpreter, input_size, image):
    # Pre process:Resize, BGR->RGB, PyTorch standardization, float32 cast
    temp_image = copy.deepcopy(image)
    imgUMat = cv.imread(temp_image)
    resize_image = cv.resize(imgUMat, dsize=(input_size[0], input_size[1]))
    x = cv.cvtColor(resize_image, cv.COLOR_BGR2RGB)
    x = np.array(x, dtype=np.float32)
    mean = [0.485, 0.456, 0.406]
    std = [0.229, 0.224, 0.225]
    x = (x / 255 - mean) / std
    x = x.reshape(-1, input_size[0], input_size[1], 3).astype('float32')

    # Inference
    input_details = interpreter.get_input_details()
    interpreter.set_tensor(input_details[0]['index'], x)
    interpreter.invoke()

    output_details = interpreter.get_output_details()
    result_map = interpreter.get_tensor(output_details[0]['index'])

    # Post process
    result_map = np.array(result_map).squeeze()
    result_map = (1 - result_map)
    min_value = np.min(result_map)
    max_value = np.max(result_map)
    result_map = (result_map - min_value) / (max_value - min_value)
    result_map *= 255
    result_map = result_map.astype('uint8')

    return result_map

def ResizeWithAspectRatio(image, width=None, height=None, inter=cv.INTER_AREA):
    dim = None
    (h, w) = image.shape[:2]

    if width is None and height is None:
        return image
    if width is None:
        r = height / float(h)
        dim = (int(w * r), height)
    else:
        r = width / float(w)
        dim = (width, int(h * r))

    return cv.resize(image, dim, interpolation=inter)


def main():
    args = get_args()
    """cap_device = args.device
    cap_width = args.width
    cap_height = args.height

    if args.movie is not None:
        cap_device = args.movie"""

    model_path = args.model
    input_size = [int(i) for i in args.input_size.split(',')]

    # Initialize video capture
    """cap = cv.VideoCapture(cap_device)
    cap.set(cv.CAP_PROP_FRAME_WIDTH, cap_width)
    cap.set(cv.CAP_PROP_FRAME_HEIGHT, cap_height)"""

    # Load model
    interpreter = tf.lite.Interpreter(model_path=model_path)
    interpreter.allocate_tensors()

    elapsed_time = 0.0

    while True:
        start_time = time.time()

        # Capture read
        image = "img/portrait.jpg"
        """if not ret:
            break"""
        imgUMat = cv.imread(image)

        result_map = run_inference(
            interpreter,
            input_size,
            "img/portrait.jpg"
        )
        elapsed_time = time.time() - start_time

        # Inference elapsed time
        elapsed_time_text = "Elapsed time: "
        elapsed_time_text += str(round((elapsed_time * 1000), 1))
        elapsed_time_text += 'ms'
        cv.putText(imgUMat, elapsed_time_text, (10, 30), cv.FONT_HERSHEY_SIMPLEX,
                   0.7, (0, 255, 0), 1, cv.LINE_AA)

        # Map Resize
        debug_image = cv.resize(result_map,
                                dsize=(imgUMat .shape[1], imgUMat.shape[0]))

        image_result = ResizeWithAspectRatio(debug_image, width=600)
        image = ResizeWithAspectRatio(imgUMat, width=600)
        cv.imshow('U-2-Net Original', image)
        cv.imshow('U-2-Net Result', image_result)
        key = cv.waitKey(1)
        if key == 27:  # ESC
            break

    #cap.release()
    cv.destroyAllWindows()


if __name__ == '__main__':
    main()