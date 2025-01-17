# YOLOv5 🚀 by Ultralytics, AGPL-3.0 license
"""
Run YOLOv5 segmentation inference on images, videos, directories, streams, etc.

Usage - sources:
    $ python segment/predict.py --weights yolov5s-seg.pt --source 0                               # webcam
                                                                  img.jpg                         # image
                                                                  vid.mp4                         # video
                                                                  screen                          # screenshot
                                                                  path/                           # directory
                                                                  list.txt                        # list of images
                                                                  list.streams                    # list of streams
                                                                  'path/*.jpg'                    # glob
                                                                  'https://youtu.be/Zgi9g1ksQHc'  # YouTube
                                                                  'rtsp://example.com/media.mp4'  # RTSP, RTMP, HTTP stream

Usage - formats:
    $ python segment/predict.py --weights yolov5s-seg.pt                 # PyTorch
                                          yolov5s-seg.torchscript        # TorchScript
                                          yolov5s-seg.onnx               # ONNX Runtime or OpenCV DNN with --dnn
                                          yolov5s-seg_openvino_model     # OpenVINO
                                          yolov5s-seg.engine             # TensorRT
                                          yolov5s-seg.mlmodel            # CoreML (macOS-only)
                                          yolov5s-seg_saved_model        # TensorFlow SavedModel
                                          yolov5s-seg.pb                 # TensorFlow GraphDef
                                          yolov5s-seg.tflite             # TensorFlow Lite
                                          yolov5s-seg_edgetpu.tflite     # TensorFlow Edge TPU
                                          yolov5s-seg_paddle_model       # PaddlePaddle
"""

import argparse
import os
import platform
import sys
from pathlib import Path
import yaml

FILE = Path(__file__).resolve()
ROOT = FILE.parents[1]  # YOLOv5 root directory
if str(ROOT) not in sys.path:
    sys.path.append(str(ROOT))  # add ROOT to PATH
ROOT = Path(os.path.relpath(ROOT, Path.cwd()))  # relative


# from models.common import DetectMultiBackend
from utils.dataloaders import IMG_FORMATS, VID_FORMATS, LoadImages, LoadStreams  # , LoadScreenshots, LoadStreams
IMG_FORMATS = 'bmp', 'dng', 'jpeg', 'jpg', 'mpo', 'png', 'tif', 'tiff', 'webp', 'pfm'  # include image suffixes
VID_FORMATS = 'asf', 'avi', 'gif', 'm4v', 'mkv', 'mov', 'mp4', 'mpeg', 'mpg', 'ts', 'wmv'  # include video suffixes
# from tf_dataloaders import IMG_FORMATS, VID_FORMATS, LoadImages, LoadStreams  # , LoadScreenshots, LoadStreams

# from tf_dataloaders import IMG_FORMATS, VID_FORMATS, LoadImages, LoadStreams  # , LoadScreenshots, LoadStreams
from utils.tf_general import (LOGGER, Profile, check_file, check_img_size, check_imshow, check_requirements, colorstr,
                              cv2,
                              increment_path, print_args, scale_boxes, scale_segments, xywh2xyxy
                              )
from utils.tf_plots import Annotator, colors, save_one_box
from utils.segment.tf_general import masks2segments, process_mask, process_mask_native
new_model=True # todo clean old model
from models.tf_model import TFModel # todo clean old model
from models.build_model import build_model, Decoder

from nms import non_max_suppression


FILE = Path(__file__).resolve()
ROOT = FILE.parents[1]  # YOLOv5 root directory
if str(ROOT) not in sys.path:
    sys.path.append(str(ROOT))  # add ROOT to PATH
ROOT = Path(os.path.relpath(ROOT, Path.cwd()))  # relative

# TBD put it here till all pytorch is removed
import tensorflow as tf
from tensorflow import keras
import numpy as np


def dir_filelist(images_dir, ext_list='.*'):
    filenames = []
    for f in os.listdir(images_dir):
        ext = os.path.splitext(f)[1]
        if ext.lower() not in ext_list:
            continue
        filenames.append(f'{images_dir}/{f}')
    return filenames

    if save_model:
        keras_model.save(model_save_path)


def run(
        model_cfg_file,
        load_weights=False,
        save_weights=False,
        load_model=False,
        save_model=False,
        model_load_path=ROOT / './saved_models/yolov5s-seg_saved_model',
        model_save_path=ROOT / './saved_models/yolov5s-seg_saved_model',  # used if load_model=False
        weights_load_path=ROOT / './saved_weights/yolov5l-seg_weights.tf',  # used if load_model=False
        weights_save_path=ROOT / './saved_weights/yolov5l-seg_weights.tf',  # used if load_model=False
        source=ROOT / 'data/images',  # file/dir/URL/glob/screen/0(webcam)
        class_names_file='',
        data=ROOT / 'data/coco12.yaml',  # dataset.yaml path
        imgsz=(640, 480),  # inference size (height, width)
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
        project=ROOT / 'runs/predict-seg',  # save results to project/name
        name='exp',  # save results to project/name
        exist_ok=False,  # existing project/name ok, do not increment
        line_thickness=3,  # bounding box thickness (pixels)
        hide_labels=False,  # hide labels
        hide_conf=False,  # hide confidences
        half=False,  # use FP16 half-precision inference
        dnn=False,  # use OpenCV DNN for ONNX inference
        vid_stride=1,  # video frame-rate stride
        retina_masks=False,
        no_strech=False  # resize image to max rectangle
):
    source = str(source)
    # class_names = [c.strip() for c in open(class_names_file).readlines()]

    with open(data) as f:
        data_cfg = yaml.load(f, Loader=yaml.FullLoader)  # model dict
    class_names = data_cfg['names']
    anchors = data_cfg['anchors']
    nl = len(anchors)  # number of detection layers
    na = len(anchors[0]) // 2  # number of anchors

    save_img = not nosave and not source.endswith('.txt')  # save inference images
    is_file = Path(source).suffix[1:] in (IMG_FORMATS + VID_FORMATS)
    is_url = source.lower().startswith(('rtsp://', 'rtmp://', 'http://', 'https://'))
    webcam = source.isnumeric() or source.endswith('.streams') or (is_url and not is_file)
    screenshot = source.lower().startswith('screen')
    if is_url and is_file:
        source = check_file(source)  # download

    # Directories
    save_dir = increment_path(Path(project) / name, exist_ok=exist_ok)  # increment run
    (save_dir / 'labels' if save_txt else save_dir).mkdir(parents=True, exist_ok=True)  # make dir

    # Load model
    stride = 32
    imgsz = check_img_size(imgsz, s=stride)  # check image size

    # Dataloader
    bs = 1  # batch_size # ronen
    if webcam:
        view_img = check_imshow(warn=True)
        dataset = LoadStreams(source, img_size=imgsz, stride=stride, auto=no_strech, vid_stride=vid_stride)
        bs = len(dataset)

    elif screenshot:
        pass  # place holder
        # dataset = LoadScreenshots(source, img_size=imgsz, stride=stride, auto=no_strech)
    else:
        dataset = LoadImages(source, img_size=imgsz, stride=stride, auto=no_strech, vid_stride=vid_stride)

    if load_model:
        keras_model = tf.keras.models.load_model(model_load_path, compile=True)

    else:
        dynamic = False
        if not new_model:# todo clean old model
            tf_model = TFModel(cfg=model_cfg_file,
                               ref_model_seq=None, nc=80, imgsz=imgsz, training=False)
            im = keras.Input(shape=(*imgsz, 3), batch_size=None if dynamic else bs)

            keras_model = tf.keras.Model(inputs=im, outputs=tf_model.predict(im))
        else:
            keras_model = build_model(model_cfg_file, nl, na, imgsz=imgsz)

    if load_weights:  # normally True when load_model is false
        keras_model.load_weights(weights_load_path)
    # if save_weights:
    #     keras_model.save_weights(weights_save_path)
    # if save_model:
    #     keras_model.save(model_save_path)

    keras_model.summary()

    seen, windows, dt = 0, [], (Profile(), Profile(), Profile())

    input_data_source = 'images_dir'
    images_dir = source
    if input_data_source == 'image_file':
        paths = [source]
    elif input_data_source == 'images_dir':
        paths = dir_filelist(images_dir, ('.jpeg', '.jpg', '.png', '.bmp'))
    else:
        paths = []

    for image_index, path in enumerate(paths):
        im0 = tf.image.decode_image(open(path, 'rb').read(), channels=3, dtype=tf.float32)
        im = tf.image.resize_with_pad(
            im0,
            target_height=imgsz[0],
            target_width=imgsz[1],
        )

        im = tf.expand_dims(im, axis=0)
        with dt[1]:
            visualize = increment_path(save_dir / Path(path).stem, mkdir=True) if (
                        visualize and not load_model) else False
            if visualize:
                pred, proto, _ = tf_model.predict(im, visualize=visualize)
                pred = pred.numpy()  # make it ndarray, same as keras predict output
            else:
                # For step-by-step debug use keras_model(im)
                if not new_model: # todo clean old model
                    pred, proto, _ = keras_model.predict(im) # model returns pred, proto, train_out:
                else:
                    train_out, proto = keras_model(im)
                    preds = []
                    nc=80 # todo config
                    nm=32 # todo config

                    decoder = Decoder(nc, nm, anchors, imgsz)
                    for layer_idx, train_out_layer in enumerate(train_out):
                        p = decoder.decoder(train_out_layer, layer_idx)
                        preds.append(p)
                    pred = tf.concat(preds, axis=1)

        #     # NMS
        pred=tf.squeeze(pred, axis=0)
        nms_pred=non_max_suppression(pred, conf_thres, iou_thres, max_det)
        b, h, w, ch = tf.cast(im.shape, tf.float32)  # batch, channel, height, width
        nms_pred = nms_pred.numpy()
        nms_pred[..., :4] *= [w, h, w, h]  # xywh normalized to pixels
        #
        # with dt[2]:
        #     print('conf_thres',conf_thres)
        #     nms_pred = non_max_suppression(pred, conf_thres, iou_thres, classes, agnostic_nms, max_det=max_det, nm=32)
        #     b, h, w, ch = tf.cast(im.shape, tf.float32)  # batch, channel, height, width
        #     nms_pred = nms_pred.numpy()
        #     nms_pred[..., :4] *= [w, h, w, h]  # xywh normalized to pixels
        # take entry 0 - assumed image by image
        proto = proto[0]
        im = im[0]
        p = Path(path)
        s = ''
        seen += 1

        save_path = str(save_dir / p.name)  # im.jpg
        txt_path = str(save_dir / 'labels' / p.stem) + ('' if dataset.mode == 'image' else f'_{frame}')  # im.txt
        # s += '%gx%g ' % im.shape[2:]  # print string
        imc = im0.copy() if save_crop else im0  # for save_crop
        annotator = Annotator(im0, line_width=line_thickness, example=str(class_names))

        if len(nms_pred):
            if retina_masks:
                # scale bbox first the crop masks
                nms_pred[:, :4] = scale_boxes(im.shape[2:], nms_pred[:, :4],
                                              im0.shape).round()  # rescale boxes to im0 size
                masks = process_mask_native(proto, nms_pred[:, 6:], nms_pred[:, :4], im0.shape[:2])  # HWC
            else:
                # Do:  a. mask=mask@proto b. crop to dounsampled by 4 predicted bbox bounderies:
                masks = process_mask(proto, nms_pred[:, 6:], nms_pred[:, :4], im.shape[0:2], upsample=True)  # HWC
                nms_pred_box = tf.math.round(scale_boxes(im.shape[0:2], nms_pred[:, :4],
                                              im0.shape))#.round()  # rescale boxes to im0 size
                nms_pred = tf.concat([nms_pred_box, nms_pred[:,4:]], axis=1)

            # Segments
            if save_txt:
                segments = [
                    scale_segments(im0.shape if retina_masks else im.shape, x, im0.shape, normalize=True)
                    for x in reversed(masks2segments(masks))]

            # Print results: sum detections per class
            for c in np.unique(nms_pred[:, 5]):
                n = np.sum(nms_pred[:, 5] == c)  # detections per class
                s += f"{n} {class_names[int(c)]}{'s' * (n > 1)}, "  # add to string

            # Mask plotting
            if len(masks):
                annotator.masks(
                    masks,
                    colors=[colors(x, True) for x in nms_pred[:, 5]],
                    image=im
                )

            # Write results
            for j, (*xyxy, conf, cls) in enumerate(reversed(nms_pred[:, :6])):
                if save_txt:  # Write to file
                    seg = segments[j].reshape(-1)  # (n,2) to (n*2)
                    line = (cls, *seg, conf) if save_conf else (cls, *seg)  # label format
                    with open(f'{txt_path}.txt', 'a') as f:
                        f.write(('%g ' * len(line)).rstrip() % line + '\n')

                if save_img or save_crop or view_img:  # Add bbox to image
                    c = int(cls)  # integer class
                    label = None if hide_labels else (class_names[c] if hide_conf else f'{class_names[c]} {conf:.2f}')
                    annotator.box_label(xyxy, label, color=colors(c, True))
                    # annotator.draw.polygon(segments[j], outline=colors(c, True), width=3)
                if save_crop:
                    save_one_box(xyxy, imc, file=save_dir / 'crops' / class_names[c] / f'{p.stem}.jpg', BGR=True)

        # Stream results
        im0 = annotator.result()
        if view_img:
            if platform.system() == 'Linux' and p not in windows:
                windows.append(p)
                cv2.namedWindow(str(p), cv2.WINDOW_NORMAL | cv2.WINDOW_KEEPRATIO)  # allow window resize (Linux)
                cv2.resizeWindow(str(p), im0.shape[1], im0.shape[0])
            cv2.imshow(str(p), im0)
            if cv2.waitKey(1) == ord('q'):  # 1 millisecond
                exit()

        # Save results (image with detections)
        if save_img:
            tf.keras.utils.save_img(save_path, im0)
        # int time (inference-only)
        LOGGER.info(f"{s}{'' if len(nms_pred) else '(no detections), '}{dt[1].dt * 1E3:.1f}ms")

    # Print results
    t = tuple(x.t / seen * 1E3 for x in dt)  # speeds per image
    LOGGER.info(f'Speed: %.1fms pre-process, %.1fms inference, %.1fms NMS per image at shape {(1, 3, *imgsz)}' % t)
    if save_txt or save_img:
        s = f"\n{len(list(save_dir.glob('labels/*.txt')))} labels saved to {save_dir / 'labels'}" if save_txt else ''
        LOGGER.info(f"Results saved to {colorstr('bold', save_dir)}{s}")


def parse_opt():
    parser = argparse.ArgumentParser()
    # parser.add_argument('--model_version', type=str, default='yolov5n',
    #                     help='model version is the prefix of model and weights files for both load and save actions')

    parser.add_argument('--model_cfg_file', type=str, default='../models/segment/yolov5s-seg.yaml',
                        help="model's yaml config file")

    parser.add_argument('--load_model', action='store_true', help='load model with ckpt. Otherwise, load weights')
    parser.add_argument('--save_model', action='store_true', help='save keras model with weights')
    parser.add_argument('--load_weights', action='store_false',
                        help='load_weights. Normally True if load_model is False')
    parser.add_argument('--save_weights', action='store_true', help='save_weights')
    parser.add_argument('--model_load_path', type=str, default=ROOT / 'models/segment/model_saved', #'/home/ronen/devel/PycharmProjects/tf_yolov5/models/keras_model',#'/home/ronen/devel/PycharmProjects/tf_yolov5/models/segment/model_saved'
                        help='lmodel_load_path')
    parser.add_argument('--model_save_path', type=str, default=ROOT / 'segment/saved_models/yolov5l-seg_saved_model',
                        help='model_save_path')
    # shapes weights:
    shapes=False
    if shapes:
        parser.add_argument('--weights_load_path', type=str, default=ROOT / 'models/keras_weights/rr.tf',
                            help='load weights path')
        parser.add_argument('--source', type=str,
                            default='/home/ronen/devel/PycharmProjects/shapes-dataset/dataset/train/images')  # default=ROOT / 'data/images', help='file/dir/URL/glob/screen/0(webcam)')
        parser.add_argument('--class_names_file', type=str, default=ROOT / '../shapes-dataset/dataset/class.names',
                            help='anchors and class names')
        parser.add_argument('--data', type=str, default=ROOT / 'data/shapes-seg.yaml', help='anchors and class names')

    else:

        parser.add_argument('--weights_load_path', type=str, default=ROOT / 'utilities/keras_weights/rrcoco.h5',#'/home/ronen/devel/PycharmProjects/tf_yolov5/utilities/keras_weights/rrcoco.tf',
                            help='load weights path')
        parser.add_argument('--source', type=str, default=ROOT / 'data/image_bus')# '/home/ronen/devel/PycharmProjects/shapes-dataset/dataset/train/images'
        parser.add_argument('--class_names_file', type=str, default=ROOT / 'data/class-names/coco.names',
                             help='class names')

        parser.add_argument('--data', type=str, default=ROOT / 'data/coco128-seg.yaml', help='anchors and class names')

    # parser.add_argument('--weights_save_path', type=str, default=ROOT / 'utilities/keras_weights/yolov5s-seg.tf',
    #                     help='save weights path')
    # parser.add_argument('--class_names_file', type=str, default=ROOT / 'data/class-names/coco.names',
    #                     help='class names')
    parser.add_argument('--imgsz', '--img', '--img-size', nargs='+', type=int, default=[640, 640],
                        help='inference size h,w')
    parser.add_argument('--conf_thres', type=float, default=0.6, help='confidence threshold')
    parser.add_argument('--iou_thres', type=float, default=0.45, help='NMS IoU threshold')
    parser.add_argument('--max-det', type=int, default=1000, help='maximum detections per image')
    parser.add_argument('--device', default='', help='cuda device, i.e. 0 or 0,1,2,3 or cpu')
    parser.add_argument('--view-img', action='store_true', help='show results')
    parser.add_argument('--save-txt', action='store_false', help='save results to *.txt')
    parser.add_argument('--save-conf', action='store_true', help='save confidences in --save-txt labels')
    parser.add_argument('--save-crop', action='store_true', help='save cropped prediction boxes')
    parser.add_argument('--nosave', action='store_true', help='do not save images/videos')
    parser.add_argument('--classes', nargs='+', type=int, help='filter by class: --classes 0, or --classes 0 2 3')
    parser.add_argument('--agnostic-nms', action='store_true', help='class-agnostic NMS')
    parser.add_argument('--augment', action='store_true', help='augmented inference')
    parser.add_argument('--visualize', action='store_true', help='visualize features - not supported in load_model')
    parser.add_argument('--update', action='store_true', help='update all models')
    parser.add_argument('--project', default=ROOT / 'runs/predict-seg', help='save results to project/name')
    parser.add_argument('--name', default='exp', help='save results to project/name')
    parser.add_argument('--exist-ok', action='store_true', help='existing project/name ok, do not increment')
    parser.add_argument('--line-thickness', default=3, type=int, help='bounding box thickness (pixels)')
    parser.add_argument('--hide-labels', default=False, action='store_true', help='hide labels')
    parser.add_argument('--hide-conf', default=False, action='store_true', help='hide confidences')
    parser.add_argument('--half', action='store_true', help='use FP16 half-precision inference')
    parser.add_argument('--retina-masks', action='store_true', help='whether to plot masks in native resolution')
    opt = parser.parse_args()
    opt.imgsz *= 2 if len(opt.imgsz) == 1 else 1  # expand
    print_args(vars(opt))
    return opt


def main(opt):
    # check_requirements(exclude=('tensorboard', 'thop'))

    run(**vars(opt))


if __name__ == '__main__':
    opt = parse_opt()
    main(opt)
