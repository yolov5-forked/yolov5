import argparse
from pathlib import Path
import sys
import os

FILE = Path(__file__).resolve()
ROOT = FILE.parents[1]  # YOLOv5 root directory
if str(ROOT) not in sys.path:
    sys.path.append(str(ROOT))  # add ROOT to PATH
ROOT = Path(os.path.relpath(ROOT, Path.cwd()))  # relative

def parse_opt():
    parser = argparse.ArgumentParser()
    parser.add_argument('--pretrained', nargs='?', const=False, default=False, help='load model from weights file')
    parser.add_argument('--cfg', type=str, default='../models/segment/yolov5s-seg.yaml', help='model.yaml path')
    shapes=True
    if shapes:
        parser.add_argument('--weights', type=str, default=ROOT / '/home/ronen/devel/PycharmProjects/tf_yolov5/runs/train-segt/exp239/weights/best.h5',
                            help='initial weights path')
        parser.add_argument('--data', type=str, default=ROOT / 'data/shapes-seg.yaml', help='dataset.yaml path')
    else:
        parser.add_argument('--weights', type=str, default=ROOT / '/home/ronen/devel/PycharmProjects/tf_yolov5/utilities/keras_weights/yolov5s-seg.tf',
                            help='initial weights path')
        parser.add_argument('--data', type=str, default=ROOT / 'data/coco128-seg-short.yaml', help='dataset.yaml path')

    parser.add_argument('--hyp', type=str, default=ROOT / 'data/hyps/hyp.scratch-low.yaml', help='hyperparameters path')
    parser.add_argument('--epochs', type=int, default=3, help='total training epochs')
    parser.add_argument('--batch-size', type=int, default=2, help='total batch size for all GPUs, -1 for autobatch')
    parser.add_argument('--imgsz', '--img', '--img-size', type=int, default=640, help='train, val image size (pixels)')
    parser.add_argument('--rect', nargs='?', const=True, default=False, help='rectangular training')
    parser.add_argument('--resume', nargs='?', const=False, default=False, help='resume most recent training')
    parser.add_argument('--nosave', nargs='?', const=True, default=False, help='only save final checkpoint')
    parser.add_argument('--noval', nargs='?', const=True, default=False, help='only validate final epoch')
    parser.add_argument('--noautoanchor', nargs='?', const=False, default=True, help='disable AutoAnchor')
    parser.add_argument('--noplots', nargs='?', const=False, default=False, help='save no plot files')
    parser.add_argument('--evolve', type=int, default=0, help='evolve x generations. Set 0 to disable')
    parser.add_argument('--bucket', type=str, default='', help='gsutil bucket')
    parser.add_argument('--cache', type=str, nargs='?', const='ram', help='image --cache ram/disk')
    parser.add_argument('--image-weights', nargs='?', const=True, default=False, help='use weighted image selection for training')
    parser.add_argument('--device', default='', help='cuda device, i.e. 0 or 0,1,2,3 or cpu')
    parser.add_argument('--multi-scale', nargs='?', const=True, default=False, help='vary img-size +/- 50%%')
    parser.add_argument('--single-cls', nargs='?', const=True, default=False, help='train multi-class data as single-class')
    parser.add_argument('--optimizer', type=str, choices=['SGD', 'Adam', 'AdamW'], default='Adam', help='optimizer')
    parser.add_argument('--sync-bn', action='store_true', help='use SyncBatchNorm, only available in DDP mode')
    parser.add_argument('--workers', type=int, default=0, help='max dataloader workers (per RANK in DDP mode)')
    parser.add_argument('--project', default=ROOT / 'runs/train-seg', help='save to project/name')
    parser.add_argument('--name', default='cfg',help='save to project/name. "cfg" sets model.yaml as name')
    parser.add_argument('--exist-ok', nargs='?', const=True, default=False,  help='existing project/name ok, do not increment')
    parser.add_argument('--quad', nargs='?', const=True, default=False, help='quad dataloader')
    parser.add_argument('--cos-lr', nargs='?', const=True, default=False,  help='cosine LR scheduler')
    parser.add_argument('--label-smoothing', type=float, default=0.0, help='Label smoothing epsilon')
    parser.add_argument('--patience', type=int, default=1000, help='EarlyStopping patience (epochs without improvement)')
    parser.add_argument('--freeze', nargs='+', type=int, default=[0], help='Freeze layers: backbone=10, first3=0 1 2')
    parser.add_argument('--save-period', type=int, default=-1, help='Save checkpoint every x epochs (disabled if < 1)')
    parser.add_argument('--seed', type=int, default=0, help='Global training seed')
    parser.add_argument('--local_rank', type=int, default=-1, help='Automatic DDP Multi-GPU argument, do not modify')
    parser.add_argument('--augment', nargs='?', const=True, default=False, help='enable training dataset augmentation')
    parser.add_argument('--mosaic', nargs='?', const=True, default=False,  help='enable training mosaic dataset. mosaic requires augment enabled (tbd-change that?)')
    parser.add_argument('--anchors_data', type=str, default='/home/ronen/devel/PycharmProjects/shapes-dataset/create_anchors/output/anchors.yaml', help='anchors yaml file')
    # Instance Segmentation Args
    parser.add_argument('--mask-ratio', type=int, default=4, help='Downsample the truth masks to saving memory')
    parser.add_argument('--overlap', nargs='?', const=True, default=True,  help='Overlap masks (train faster at slightly less mAP-tbd)')
    parser.add_argument('--debug', nargs='?', const=True, default=True, help='permits some step-by-step on create dataset')

    return parser.parse_args()

