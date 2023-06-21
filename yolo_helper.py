import cv2
from ultralytics import YOLO


def use_yolo(filepath="images/image01.png", model_name="yolov8n.pt"):
    global model

    model = YOLO(model_name)

    im2 = cv2.imread(filepath)
    results = model.predict(source=im2)

    data_list = []

    for result in results:
        data = []

        for i in range(result.boxes.xywh.shape[0]):
            xywh = result.boxes.xywh[i]  # box with xywh format, (N, 4)
            xywh[0] -= 40
            xywh[1] -= 40
            cls = result.names[result.boxes.cls[i].item()]  # cls, (N, 1)
            data.append((cls, tuple(xywh.tolist())))
        data_list.append(data)

    return data_list
