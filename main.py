import argparse


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="물체인식을 통한 주차장 주차자리 안내 시스템 (PLS - Parking Lot Service)")

    parser.add_argument("-i", dest="image_path", default="images/image01.png", help="테스트 이미지 경로")
    parser.add_argument("--gui", dest="gui", action="store_true", help="GUI 사용여부")
    parser.add_argument("-fw", dest="frame_width", default=1280, help="프레임 가로 길이")
    parser.add_argument("-fh", dest="frame_height", default=467, help="프레임 세로 길이")
    parser.add_argument("--arduino_port", dest="arduino_port", default="COM3", help="아두이노 포트")
    parser.add_argument("--savepath", dest="savepath", default="data.pickle", help="저장된 전처리 데이터 경로")
    parser.add_argument("--yolo_model", dest="yolo_model_name", default="yolov8l", help="YOLO 모델 이름")
    parser.add_argument("--entry_index", dest="entry_index", default=-1, help="주차장 입구 목록 인덱스")
    # parser.add_argument("-o", dest="output", required=True, help="출력 폴더 경로")

    args = vars(parser.parse_args())

    if args["gui"]:
        import gui

        gui.app(args)
    else:
        import logic

        logic.real_time_start(args)
