import io
import argparse
import yaml

from datetime import datetime
import picamera
from PIL import Image, ImageDraw, ImageFont

import vision
from networking import ImageSocketHandler

parser = argparse.ArgumentParser()
parser.add_argument('config_filename')
args = parser.parse_args()
CONFIG_FILE = args.config_filename

with open(CONFIG_FILE) as f:
    configs = yaml.load(f, Loader=yaml.SafeLoader)

RECORD = configs['RECORD']
RECORD_CONF_THRESHOLD = configs['RECORD_CONF_THRESHOLD']
CAMERA_RESOLUTION = configs['CAMERA_RESOLUTION']
CAMERA_ANGLE = configs['CAMERA_ANGLE']

detector = vision.ObjectDetectionSystem(configs)
image_socket = ImageSocketHandler(configs)
stream = io.BytesIO()

camera = picamera.PiCamera()
camera.rotation = CAMERA_ANGLE
camera.resolution = CAMERA_RESOLUTION
# RESOLUTION = camera.resolution


class OverlayHandler():
    def __init__(self, camera):
        self.camera = camera
        self.clean_image()
        self.apply_overlay()

    def draw_box(self, lbox):
        draw = ImageDraw.Draw(self.image)
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

    def clean_image(self):
        self.image = Image.new('RGBA', CAMERA_RESOLUTION, (0, 0, 0, 0))

    def remove_previous(self):
        self.camera.remove_overlay(self.overlay)

    def apply_overlay(self):
        pad = Image.new('RGBA',
                        (((self.image.size[0] + 31) // 32) * 32,
                         ((self.image.size[1] + 15) // 16) * 16,
                        ))

        pad.paste(self.image, (0, 0))

        self.overlay = self.camera.add_overlay(pad.tobytes(),
                                               size=self.image.size)
        self.overlay.alpha = 128
        self.overlay.layer = 3


def main():

    if configs['PREVIEW_ON']:
        camera.start_preview()
        overlay_handler = OverlayHandler(camera)

    try:
        for _ in camera.capture_continuous(stream, format='jpeg'):

            command = image_socket.recv_command()
            print('Command: {}'.format(command))

            overlay_handler.remove_previous()
            overlay_handler.clean_image()

            detector.infer(stream)
            detector.print_report()

            lboxes = detector.labeled_boxes
            if command == 1:
                image_socket.send_image(stream)

            elif len(lboxes) > 0:
                for lbox in lboxes:
                    overlay_handler.draw_box(lbox)

                if RECORD and lboxes[0]['confidence'] > RECORD_CONF_THRESHOLD:
                    # send image over socket
                    image_socket.send_image(stream)

                    top_class = detector.class_of_box(lboxes[0])
                    detector.save_current_frame(top_class)
                    with open('what_was_seen.log', 'a+') as f:
                        tstamp = str(datetime.now().strftime('%Y-%m-%d %H:%M:%S'))
                        f.write('{} | {}\n'.format(tstamp,
                                                   top_class))
                else:
                    image_socket.send_no_image()

            else:
                image_socket.send_no_image()

            overlay_handler.apply_overlay()

            stream.seek(0)
            stream.truncate()
    except KeyboardInterrupt:
        print('KeyboardInterrupt')
        image_socket.close()


if __name__ == "__main__":
    main()
