import io
import argparse
import yaml

import picamera
from PIL import Image, ImageDraw

import vision

parser = argparse.ArgumentParser()
parser.add_argument('config',
                    help='Filename of configuration file')
args = parser.parse_args()
CONFIG_FILE = args.config

with open(CONFIG_FILE) as f:
    configs = yaml.load(f, Loader=yaml.SafeLoader)

RECORD = configs['RECORD']
    
detector = vision.ObjectDetectionSystem(configs)

stream = io.BytesIO()

resolution = (1280, 720)

camera = picamera.PiCamera()
camera.rotation = configs['CAMERA_ANGLE']
camera.resolution = resolution



if configs['PREVIEW_ON']:
    camera.start_preview()


    overlay = Image.new('RGBA', resolution, (0, 0, 0, 0))

    draw = ImageDraw.Draw(overlay)
    draw.rectangle([(100, 100), (200, 200)], outline=(255,0,0), width=3)


    pad = Image.new('RGBA',
                    (((overlay.size[0] + 31) // 32) *32,
                     ((overlay.size[1] + 15) // 16) * 16,
                    ))

    pad.paste(overlay, (0,0))

    o = camera.add_overlay(pad.tobytes(), size=overlay.size)
    o.alpha = 128
    o.layer = 3



    
for _ in camera.capture_continuous(stream, format='jpeg'):
    stream.truncate()
    stream.seek(0)

    detector.infer(stream)
    detector.print_report()
    top_box =  detector.top_box()

    if top_box is not None:
        left, top, width, height = top_box

        camera.remove_overlay(o)
        overlay = Image.new('RGBA', resolution, (0, 0, 0, 0))

        draw = ImageDraw.Draw(overlay)
        draw.rectangle([(left, top), (left+width, top + height)],
                       outline=(255,0,0),
                       width=3)


        pad = Image.new('RGBA',
                        (((overlay.size[0] + 31) // 32) *32,
                         ((overlay.size[1] + 15) // 16) * 16,
                        ))

        pad.paste(overlay, (0,0))

        o = camera.add_overlay(pad.tobytes(), size=overlay.size)
        o.alpha = 128
        o.layer = 3


