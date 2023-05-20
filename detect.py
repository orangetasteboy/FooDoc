# YOLOv5 🚀 by Ultralytics, GPL-3.0 license
"""
Run YOLOv5 detection inference on images, videos, directories, globs, YouTube, webcam, streams, etc.

Usage - sources:
    $ python detect.py --weights yolov5s.pt --source 0                               # webcam
                                                     img.jpg                         # image
                                                     vid.mp4                         # video
                                                     path/                           # directory
                                                     'path/*.jpg'                    # glob
                                                     'https://youtu.be/Zgi9g1ksQHc'  # YouTube
                                                     'rtsp://example.com/media.mp4'  # RTSP, RTMP, HTTP stream

Usage - formats:
    $ python detect.py --weights yolov5s.pt                 # PyTorch
                                 yolov5s.torchscript        # TorchScript
                                 yolov5s.onnx               # ONNX Runtime or OpenCV DNN with --dnn
                                 yolov5s.xml                # OpenVINO
                                 yolov5s.engine             # TensorRT
                                 yolov5s.mlmodel            # CoreML (macOS-only)
                                 yolov5s_saved_model        # TensorFlow SavedModel
                                 yolov5s.pb                 # TensorFlow GraphDef
                                 yolov5s.tflite             # TensorFlow Lite
                                 yolov5s_edgetpu.tflite     # TensorFlow Edge TPU
                                 yolov5s_paddle_model       # PaddlePaddle
"""

import argparse
import os
import platform
import sys
from pathlib import Path

import torch

FILE = Path(__file__).resolve()
ROOT = FILE.parents[0]  # YOLOv5 root directory
if str(ROOT) not in sys.path:
    sys.path.append(str(ROOT))  # add ROOT to PATH
ROOT = Path(os.path.relpath(ROOT, Path.cwd()))  # relative

from models.common import DetectMultiBackend
from utils.dataloaders import IMG_FORMATS, VID_FORMATS, LoadImages, LoadStreams
from utils.general import (LOGGER, Profile, check_file, check_img_size, check_imshow, check_requirements, colorstr, cv2,
                           increment_path, non_max_suppression, print_args, scale_coords, strip_optimizer, xyxy2xywh)
from utils.plots import Annotator, colors, save_one_box
from utils.torch_utils import select_device, smart_inference_mode

import argparse
import io


# import torch
# from flask import Flask, request
# from PIL import Image
#
# app = Flask(__name__)
# models = {}
#
# DETECTION_URL = '/v1/object-detection/<model>'
#
#
# @app.route(DETECTION_URL, methods=['POST'])
@smart_inference_mode()
def run(
        weights='FOOD5_best7.pt',  # model.pt path(s)
        source=ROOT / 'data/images',  # file/dir/URL/glob, 0 for webcam
        #source = request.files['image'],
        data=ROOT / 'data/coco128.yaml',  # dataset.yaml path
        imgsz=(640, 640),  # inference size (height, width)
        conf_thres=0.25,  # confidence threshold
        iou_thres=0.45,  # NMS IOU threshold
        max_det=1000,  # maximum detections per image
        device='',  # cuda device, i.e. 0 or 0,1,2,3 or cpu
        view_img=False,  # show results
        save_txt=False,  # save results to *.txt
        save_conf=False,  # save confidences in --save-txt labels
        save_crop=False,  # save cropped prediction boxes
        nosave=False,  # do not save images/videos
        classes=None,  # filter by class: --class 0, or --class 0 2 3
        agnostic_nms=False,  # class-agnostic NMS
        augment=False,  # augmented inference
        visualize=False,  # visualize features
        update=False,  # update all models
        project=ROOT / 'runs/detect',  # save results to project/name
        name='exp',  # save results to project/name
        exist_ok=False,  # existing project/name ok, do not increment
        line_thickness=3,  # bounding box thickness (pixels)
        hide_labels=False,  # hide labels
        hide_conf=False,  # hide confidences
        half=False,  # use FP16 half-precision inference
        dnn=False,  # use OpenCV DNN for ONNX inference
        vid_stride=1,  # video frame-rate stride
        ):
    source = str(source)
    save_img = not nosave and not source.endswith('.txt')  # save inference images
    is_file = Path(source).suffix[1:] in (IMG_FORMATS + VID_FORMATS)
    is_url = source.lower().startswith(('rtsp://', 'rtmp://', 'http://', 'https://'))
    webcam = source.isnumeric() or source.endswith('.txt') or (is_url and not is_file)
    if is_url and is_file:
        source = check_file(source)  # download

    # Directories
    save_dir = increment_path(Path(project) / name, exist_ok=exist_ok)  # increment run
    (save_dir / 'labels' if save_txt else save_dir).mkdir(parents=True, exist_ok=True)  # make dir

    # Load model
    device = select_device(device)
    model = DetectMultiBackend(weights, device=device, dnn=dnn, data=data, fp16=half)
    stride, names, pt = model.stride, model.names, model.pt
    imgsz = check_img_size(imgsz, s=stride)  # check image size

    # Dataloader
    if webcam:
        view_img = check_imshow()
        dataset = LoadStreams(source, img_size=imgsz, stride=stride, auto=pt, vid_stride=vid_stride)
        bs = len(dataset)  # batch_size
    else:
        dataset = LoadImages(source, img_size=imgsz, stride=stride, auto=pt, vid_stride=vid_stride)
        bs = 1  # batch_size
    vid_path, vid_writer = [None] * bs, [None] * bs

    # Run inference
    model.warmup(imgsz=(1 if pt else bs, 3, *imgsz))  # warmup
    seen, windows, dt = 0, [], (Profile(), Profile(), Profile())
    for path, im, im0s, vid_cap, s in dataset:
        with dt[0]:
            im = torch.from_numpy(im).to(device)
            im = im.half() if model.fp16 else im.float()  # uint8 to fp16/32
            im /= 255  # 0 - 255 to 0.0 - 1.0
            if len(im.shape) == 3:
                im = im[None]  # expand for batch dim

        # Inference
        with dt[1]:
            visualize = increment_path(save_dir / Path(path).stem, mkdir=True) if visualize else False
            pred = model(im, augment=augment, visualize=visualize)

        # NMS
        with dt[2]:
            pred = non_max_suppression(pred, conf_thres, iou_thres, classes, agnostic_nms, max_det=max_det)

        # Second-stage classifier (optional)
        # pred = utils.general.apply_classifier(pred, classifier_model, im, im0s)

        # Process predictions
#----------------------
        for i, det in enumerate(pred):  # per image

            seen += 1
            if webcam:  # batch_size >= 1
                p, im0, frame = path[i], im0s[i].copy(), dataset.count
                s += f'{i}: '
            else:
                p, im0, frame = path, im0s.copy(), getattr(dataset, 'frame', 0)

            p = Path(p)  # to Path
            save_path = str(save_dir / p.name)  # im.jpg
            txt_path = str(save_dir / 'labels' / p.stem) + ('' if dataset.mode == 'image' else f'_{frame}')  # im.txt
            s += '%gx%g ' % im.shape[2:]  # print string
            gn = torch.tensor(im0.shape)[[1, 0, 1, 0]]  # normalization gain whwh
            imc = im0.copy() if save_crop else im0  # for save_crop
            annotator = Annotator(im0, line_width=line_thickness, example=str(names))
            if len(det):
                # Rescale boxes from img_size to im0 size
                det[:, :4] = scale_coords(im.shape[2:], det[:, :4], im0.shape).round()

                # Print results
                for c in det[:, -1].unique():
                    n = (det[:, -1] == c).sum()  # detections per class
                    s += f"{n} {names[int(c)]}{'s' * (n > 1)}, "  # add to string

                # Write results
                j = 1
                # f = open("음식.txt",'w')
                # f.write("음식이름,에너지,수분,단백질,지질,탄수화물,총당류\n")
                # f.close()

                import datetime
                import time
                today = datetime.date.today()
                second = time.strptime(str(today), "%Y-%m-%d")

                # if first != second:
                #     f = open('날짜.txt',mode='w',encoding='cp949')
                #     f.write(str(today))
                #     f = open(f"{today}음식.txt",'w')
                #     f.write("날짜,음식이름,에너지,수분,단백질,지질,탄수화물,총당류\n")
                #     f.close()

                for *xyxy, conf, cls in reversed(det):
                    if save_txt:  # Write to file
                        xywh = (xyxy2xywh(torch.tensor(xyxy).view(1, 4)) / gn).view(-1).tolist()  # normalized xywh
                        line = (cls, *xywh, conf) if save_conf else (cls, *xywh)  # label format
                        with open(f'{txt_path}.txt', 'a') as f:
                            f.write(('%g ' * len(line)).rstrip() % line + '\n')

                    if save_img or save_crop or view_img:  # Add bbox to image
                        c = int(cls)  # integer class
                        label = None if hide_labels else (names[c] if hide_conf else f'{names[c]} {conf:.2f}')
                        annotator.box_label(xyxy, label, color=colors(c, True))
                    if save_crop:
                        save_one_box(xyxy, imc, file=save_dir / 'crops' / names[c] / f'{p.stem}.jpg', BGR=True)
                    # 음식 영양소 정보 저장하는 파일 생성
                    print(label)

                    if ('tteokbokki' in label):
                        f = open("date.txt", "a", encoding='UTF8')
                        f.write(f"{today},떡볶이,151.00,62.90,3.80,1.70,30.20,0\n")
                        f.close()
                    elif ('pizza' in label):
                        f = open("date.txt", "a", encoding='UTF8')  # kcal,g,g,g,g,g
                        f.write(f"{today},피자,233.00,47.70,11.30,7.30,30.40,0\n")
                        f.close()
                    elif ('gimbap' in label):
                        f = open("date.txt", "a", encoding='UTF8')
                        f.write(f"{today},김밥,158.00,63.00,3.60,3.20,28.80,0\n")
                        f.close()
                    elif ('chicken' in label):
                        f = open("date.txt", "a", encoding='UTF8')
                        f.write(f"{today},닭가슴살,127.00,70.40,28.09,0.93,0,0\n")
                        f.close()
                    elif ('salad' in label):
                        f = open("date.txt", "a", encoding='UTF8')
                        f.write(f"{today},샐러드,153.00,73.42,0.95,9.91,14.89,12.19\n")
                        f.close()
            import pandas as pd
            import json
            # df = pd.read_csv(f"{today}음식.txt",sep=",",encoding='cp949')
            # print(df)
            # df.to_excel(f"{today}음식dataset.xlsx",index=True)
            # em_df = pd.ExcelFile(f"{today}음식dataset.xlsx").parse(sheet_name=0, dtype=object, engine='xlrd', verbose=True)
            # em_df.to_csv(path_or_buf=f"{today}음식dataset.csv", sep=',', header=True, index=False, mode='w', encoding='CP949')
            # import json
            # em_df.to_json(path_or_buf=f"{today}음식dataset.json",force_ascii=False, orient = 'records', indent=4)

            df = pd.read_csv("date.txt", sep=",", encoding='UTF8')
            print(df)
            df.to_excel(f"date_dataset.xlsx", index=True)
            em_df = pd.ExcelFile(f"date_dataset.xlsx").parse(sheet_name=0, dtype=object, engine='xlrd', verbose=True)
            em_df.to_csv(path_or_buf=f"date_dataset.csv", sep=',', header=True, index=False, mode='w', encoding='UTF8')
            em_df.to_json(path_or_buf=f"date_dataset.json", force_ascii=False, orient='records', indent=4)

            import numpy as np
            import matplotlib.pyplot as plt
            import pandas as pd
            data = pd.read_csv(r'date_dataset.csv', encoding='UTF8')
            data.head()

            x = np.array(data[['energy', 'water', 'protein', 'fat', 'tansuhwamul', 'sugar']])
            # 총에너지 = 0
            # 총수분 = 0
            # 총단백질 = 0
            # 총지질 = 0
            # 총탄수화물 = 0
            # 총당류 = 0
            # for i in range(len(x)):
            #     총에너지 += x[i][0]
            #     총수분 += x[i][1]
            #     총단백질 += x[i][2]
            #     총지질 += x[i][3]
            #     총탄수화물 += x[i][4]
            #     총당류 += x[i][5]
            # # 하루 권장 섭취량
            # # 에너지, 단백질, 지방, 탄수화물,
            # # 전체평균 1995.96, 71.84, 46.94, 295.25
            # 권장에너지 = 1995.96
            # 권장단백질 = 71.84
            # 권장지방 = 46.94
            # 권장탄수화물 = 295.25
            # if 총에너지 < 권장에너지:
            #     print(f"하루 에너지 권장 섭취량은 {권장에너지 - 총에너지} kcal만큼 남았습니다.")
            # elif 총에너지 >= 권장에너지:
            #     print(f"하루 에너지 권장 섭취량을 충족하였고, {총에너지 - 권장에너지} kcal만큼 넘었습니다.")
            # if 총단백질 < 권장단백질:
            #     print(f"하루 단백질 권장 섭취량은 {권장단백질 - 총단백질} g만큼 남았습니다.")
            # elif 총단백질 >= 권장단백질:
            #     print(f"하루 단백질 권장 섭취량을 충족하였고, {총단백질 - 권장단백질} g만큼 넘었습니다.")
            # if 총지질 < 권장지방:
            #     print(f"하루 지방 권장 섭취량은 {권장지방 - 총지질} g만큼 남았습니다.")
            # elif 총지질 >= 권장지방:
            #     print(f"하루 지방 권장 섭취량을 충족하였고, {총지질 - 권장지방} g만큼 넘었습니다.")
            # if 총탄수화물 < 권장탄수화물:
            #     print(f"하루 탄수화물 권장 섭취량은 {권장탄수화물 - 총탄수화물} g만큼 남았습니다.")
            # elif 총탄수화물 >= 권장탄수화물:
            #     print(f"하루 탄수화물 권장 섭취량을 충족하였고, {총탄수화물 - 권장탄수화물} g만큼 넘었습니다.")

            # Stream results
            im0 = annotator.result()
            if view_img:
                if platform.system() == 'Linux' and p not in windows:
                    windows.append(p)
                    cv2.namedWindow(str(p), cv2.WINDOW_NORMAL | cv2.WINDOW_KEEPRATIO)  # allow window resize (Linux)
                    cv2.resizeWindow(str(p), im0.shape[1], im0.shape[0])
                cv2.imshow(str(p), im0)
                cv2.waitKey(1)  # 1 millisecond

            # Save results (image with detections)
            if save_img:
                if dataset.mode == 'image':
                    cv2.imwrite(save_path, im0)
                else:  # 'video' or 'stream'
                    if vid_path[i] != save_path:  # new video
                        vid_path[i] = save_path
                        if isinstance(vid_writer[i], cv2.VideoWriter):
                            vid_writer[i].release()  # release previous video writer
                        if vid_cap:  # video
                            fps = vid_cap.get(cv2.CAP_PROP_FPS)
                            w = int(vid_cap.get(cv2.CAP_PROP_FRAME_WIDTH))
                            h = int(vid_cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
                        else:  # stream
                            fps, w, h = 30, im0.shape[1], im0.shape[0]
                        save_path = str(Path(save_path).with_suffix('.mp4'))  # force *.mp4 suffix on results videos
                        vid_writer[i] = cv2.VideoWriter(save_path, cv2.VideoWriter_fourcc(*'mp4v'), fps, (w, h))
                    vid_writer[i].write(im0)

        # Print time (inference-only)
        LOGGER.info(f"{s}{'' if len(det) else '(no detections), '}{dt[1].dt * 1E3:.1f}ms")
    # Print results
    t = tuple(x.t / seen * 1E3 for x in dt)  # speeds per image
    LOGGER.info(f'Speed: %.1fms pre-process, %.1fms inference, %.1fms NMS per image at shape {(1, 3, *imgsz)}' % t)
    if save_txt or save_img:
        s = f"\n{len(list(save_dir.glob('labels/*.txt')))} labels saved to {save_dir / 'labels'}" if save_txt else ''
        LOGGER.info(f"Results saved to {colorstr('bold', save_dir)}{s}")
    if update:
        strip_optimizer(weights[0])  # update model (to fix SourceChangeWarning)


def parse_opt():
    parser = argparse.ArgumentParser()
    parser.add_argument('--weights', nargs='+', type=str, default=ROOT / 'FOOD5_best7.pt', help='model path(s)')
    parser.add_argument('--source', type=str, default=ROOT / 'pic1001.jpg', help='file/dir/URL/glob, 0 for webcam')
    parser.add_argument('--data', type=str, default=ROOT / 'data/coco128.yaml', help='(optional) dataset.yaml path')
    parser.add_argument('--imgsz', '--img', '--img-size', nargs='+', type=int, default=[640], help='inference size h,w')
    parser.add_argument('--conf-thres', type=float, default=0.25, help='confidence threshold')
    parser.add_argument('--iou-thres', type=float, default=0.45, help='NMS IoU threshold')
    parser.add_argument('--max-det', type=int, default=1000, help='maximum detections per image')
    parser.add_argument('--device', default='', help='cuda device, i.e. 0 or 0,1,2,3 or cpu')
    parser.add_argument('--view-img', action='store_true', help='show results')
    parser.add_argument('--save-txt', action='store_true', help='save results to *.txt')
    parser.add_argument('--save-conf', action='store_true', help='save confidences in --save-txt labels')
    parser.add_argument('--save-crop', action='store_true', help='save cropped prediction boxes')
    parser.add_argument('--nosave', action='store_true', help='do not save images/videos')
    parser.add_argument('--classes', nargs='+', type=int, help='filter by class: --classes 0, or --classes 0 2 3')
    parser.add_argument('--agnostic-nms', action='store_true', help='class-agnostic NMS')
    parser.add_argument('--augment', action='store_true', help='augmented inference')
    parser.add_argument('--visualize', action='store_true', help='visualize features')
    parser.add_argument('--update', action='store_true', help='update all models')
    parser.add_argument('--project', default=ROOT / 'runs/detect', help='save results to project/name')
    parser.add_argument('--name', default='exp', help='save results to project/name')
    parser.add_argument('--exist-ok', action='store_true', help='existing project/name ok, do not increment')
    parser.add_argument('--line-thickness', default=3, type=int, help='bounding box thickness (pixels)')
    parser.add_argument('--hide-labels', default=False, action='store_true', help='hide labels')
    parser.add_argument('--hide-conf', default=False, action='store_true', help='hide confidences')
    parser.add_argument('--half', action='store_true', help='use FP16 half-precision inference')
    parser.add_argument('--dnn', action='store_true', help='use OpenCV DNN for ONNX inference')
    parser.add_argument('--vid-stride', type=int, default=1, help='video frame-rate stride')
    opt = parser.parse_args()
    opt.imgsz *= 2 if len(opt.imgsz) == 1 else 1  # expand
    print_args(vars(opt))
    return opt


def main(opt):
    check_requirements(exclude=('tensorboard', 'thop'))
    run(**vars(opt))


def detect_fun(request):
    opt = parse_opt()
    main(opt,request)

if __name__ == "__main__":
    opt = parse_opt()
    main(opt)
