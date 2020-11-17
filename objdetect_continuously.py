import io
import argparse
import yaml

from datetime import datetime
import picamera
from PIL import Image, ImageDraw, ImageFont

import vision

parser = argparse.ArgumentParser()
parser.add_argument('config',
                    help='Filename of configuration file')
args = parser.parse_args()
CONFIG_FILE = args.config

with open(CONFIG_FILE) as f:
    configs = yaml.load(f, Loader=yaml.SafeLoader)

RECORD = configs['RECORD']
RECORD_CONF_THRESHOLD = configs['RECORD_CONF_THRESHOLD']

detector = vision.ObjectDetectionSystem(configs)

stream = io.BytesIO()

resolution = (1280, 720)

camera = picamera.PiCamera()
camera.rotation = configs['CAMERA_ANGLE']
camera.resolution = resolution
# resolution = camera.resolution


if configs['PREVIEW_ON']:
    camera.start_preview()

    overlay_img = Image.new('RGBA', resolution, (0, 0, 0, 0))

    draw = ImageDraw.Draw(overlay_img)
    draw.rectangle([(100, 100), (200, 200)],
                   outline=(255, 0, 0),
                   width=3)

    pad = Image.new('RGBA',
                    (((overlay_img.size[0] + 31) // 32) * 32,
                     ((overlay_img.size[1] + 15) // 16) * 16,
                    ))

    pad.paste(overlay_img, (0, 0))

    overlay = camera.add_overlay(pad.tobytes(), size=overlay_img.size)
    overlay.alpha = 128
    overlay.layer = 3

for _ in camera.capture_continuous(stream, format='jpeg'):
    stream.truncate()
    stream.seek(0)

    detector.infer(stream)
    detector.print_report()

    lboxes = detector.labeled_boxes
    if len(lboxes) > 0:

        if RECORD and lboxes[0]['confidence'] > RECORD_CONF_THRESHOLD:
            top_class = detector.class_of_box(lboxes[0])
            detector.save_current_frame(top_class)
            with open('what_was_seen.log', 'a+') as f:
                tstamp = str(datetime.now().strftime('%Y-%m-%d %H:%M:%S'))
                f.write('{} | {}\n'.format(tstamp,
                                           top_class))

        camera.remove_overlay(overlay)
        overlay_img = Image.new('RGBA', resolution, (0, 0, 0, 0))
        draw = ImageDraw.Draw(overlay_img)

        for lbox in lboxes:
            left, top, width, height = lbox['box']

            draw.rectangle([(left, top), (left + width, top + height)],
                           outline=(168, 50, 82),
                           width=10)
            font_path = '/usr/share/fonts/truetype/freefont/FreeMonoBold.ttf'
            the_font = ImageFont.truetype(font_path, 50)
            text = '{}:{:.1f}'.format(detector.class_of_box(lbox),
                                      100 * lbox['confidence'])
            draw.text((left + 10, top + 10),
                      text,
                      font=the_font,
                      fill=(255, 0, 0))

        pad = Image.new('RGBA',
                        (((overlay_img.size[0] + 31) // 32) * 32,
                         ((overlay_img.size[1] + 15) // 16) * 16,
                        ))

        pad.paste(overlay_img, (0, 0))

        overlay = camera.add_overlay(pad.tobytes(), size=overlay_img.size)
        overlay.alpha = 128
        overlay.layer = 3
