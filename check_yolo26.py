import onnxruntime as ort
import numpy as np
import cv2

def test_yolo26():
    session = ort.InferenceSession("models/yolo26n.onnx")
    input_name = session.get_inputs()[0].name
    
    # Try a real small image or just zeroes
    dummy_input = np.zeros((1, 3, 640, 640), dtype=np.float32)
    outputs = session.run(None, {input_name: dummy_input})
    
    out = outputs[0][0] # (300, 6)
    
    # Sort by confidence
    out = out[out[:, 4].argsort()[::-1]]
    
    print("Top 3 detections:")
    for i in range(3):
        print(out[i])

if __name__ == "__main__":
    test_yolo26()
