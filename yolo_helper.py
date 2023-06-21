import cv2
from ultralytics import YOLO


def use_yolo_from_file(filepath="images/image01.png", model_name="yolov8n.pt"):
    im2 = cv2.imread(filepath)
    return use_yolo(im2, model_name)


def use_yolo(img_data, model_name="yolov8n.pt"):
    global model

    model = YOLO(model_name)

    results = model.predict(source=img_data)

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
