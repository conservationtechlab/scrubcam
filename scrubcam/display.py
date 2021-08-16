"""Elements for displaying to Scrubcam screen

Contains functions and classes involved with displaying to the PiTFT
screen attached to the Pi 4.

"""

import logging

from PIL import Image, ImageDraw, ImageFont

log = logging.getLogger(__name__)


class Display():
    """Handles drawing labelled boxes to output frame
    
    May need to be renamed as true display mechanics are inherited
    from DenCam and this class only really focuses on the box-drawing.
    Moreover, this is currently not used properly in scrubcam.py but
    only in objdetect_continuosly.py.

    """

    def __init__(self, configs, camera, state):
        self.resolution = configs['CAMERA_RESOLUTION']

        self.camera = camera
        self.state = state

        overlay_img = Image.new('RGBA', self.resolution, (0, 0, 0, 0))

        pad = Image.new('RGBA',
                        (((overlay_img.size[0] + 31) // 32) * 32,
                         ((overlay_img.size[1] + 15) // 16) * 16,))

        pad.paste(overlay_img, (0, 0))

        self.overlay = self.camera.add_overlay(pad.tobytes(),
                                               size=overlay_img.size)
        self.overlay.alpha = 128
        self.overlay.layer = 3

    def update(self, lboxes):
        self.camera.remove_overlay(self.overlay)

        overlay_img = Image.new('RGBA', self.resolution, (0, 0, 0, 0))
        draw = ImageDraw.Draw(overlay_img)

        if self.state.value == 3:

            for lbox in lboxes:
                left, top, width, height = lbox['box']

                draw.rectangle([(left, top), (left + width, top + height)],
                               outline=(168, 50, 82),
                               width=10)
                font = '/usr/share/fonts/truetype/freefont/FreeMonoBold.ttf'
                the_font = ImageFont.truetype(font, 50)
                text = '{}:{:.1f}'.format(lbox['class_name'],
                                          100 * lbox['confidence'])
                draw.text((left + 10, top + 10),
                          text,
                          font=the_font,
                          fill=(255, 0, 0))

        pad = Image.new('RGBA',
                        (((overlay_img.size[0] + 31) // 32) * 32,
                         ((overlay_img.size[1] + 15) // 16) * 16,))

        pad.paste(overlay_img, (0, 0))

        self.overlay = self.camera.add_overlay(pad.tobytes(),
                                               size=overlay_img.size)
        self.overlay.alpha = 128
        self.overlay.layer = 3


class OverlayHandler():
    def __init__(self, camera, resolution):
        self.camera = camera
        self.resolution = resolution
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
        text = '{}:{:.1f}'.format(lbox['class_name'],
                                  100 * lbox['confidence'])
        draw.text((left + 10, top + 10),
                  text,
                  font=the_font,
                  fill=(255, 0, 0))

    def clean_image(self):
        self.image = Image.new('RGBA', self.resolution, (0, 0, 0, 0))

    def remove_previous(self):
        self.camera.remove_overlay(self.overlay)

    def apply_overlay(self):
        pad = Image.new('RGBA',
                        (((self.image.size[0] + 31) // 32) * 32,
                         ((self.image.size[1] + 15) // 16) * 16,))

        pad.paste(self.image, (0, 0))

        self.overlay = self.camera.add_overlay(pad.tobytes(),
                                               size=self.image.size)
        self.overlay.alpha = 128
        self.overlay.layer = 3


# class Viewer(Thread):

#     def __init__(self, image, stop_flag):
#         super().__init__()
#         self.image = image
#         self.stop_flag = stop_flag

#     def run(self):
#         while True:
#             log.debug('Viewer loop')
#             if self.image['lboxes'] is not None:
#                 box = self.image['lboxes'][0]['box']
#                 self.image['img'] = draw.box_on_image(self.image['img'],
#                                                       box)

#             time.sleep(1)
