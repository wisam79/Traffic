import cv2
import sys
import os
import onnxruntime as ort
import numpy as np

# Add project to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from engine.detector import ObjectDetector
from engine.preprocessor import FramePreprocessor

def test_inference():
    video_path = r"C:\Users\Laptop Shop\Downloads\Road traffic.mp4"
    if not os.path.exists(video_path):
        video_path = r"C:\Users\Laptop Shop\Downloads\traffic.mp4"
        
    cap = cv2.VideoCapture(video_path)
    
    # skip some frames to get a frame with cars
    for _ in range(50):
        cap.read()
        
    ret, frame = cap.read()
    cap.release()

    pre = FramePreprocessor()
    det = ObjectDetector(confidence_threshold=0.1)
    
    tensor, scale = pre.preprocess(frame)
    
    # Do raw ONNX inference to see what we really get
    outputs = det.session.run(None, {det.input_name: tensor})
    raw_output = outputs[0][0]
    
    print(f"Raw output shape: {raw_output.shape}")
    
    # Sort by conf
    sorted_idx = np.argsort(raw_output[:, 4])[::-1]
    raw_output = raw_output[sorted_idx]
    
    print("Top 10 raw predictions (x1, y1, x2, y2, conf, class):")
    for i in range(10):
        print(raw_output[i])

if __name__ == "__main__":
    test_inference()
