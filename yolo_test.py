from ultralytics import YOLO
from PIL import Image
import cv2

model = YOLO("yolov8x.pt")
# accepts all formats - image/dir/Path/URL/video/PIL/ndarray. 0 for webcam

# from ndarray
im2 = cv2.imread("images/image01.png")
results = model.predict(source=im2, save=True, save_txt=True)  # save predictions as labels

print(results)
