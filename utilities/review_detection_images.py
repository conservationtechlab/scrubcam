#!/usr/bin/env python
"""View box output on images from a run; optionally export video

Takes a path to a folder of images and csvs and displays all the
images from the associated run with boxes drawn upon them. Optionally
assembles these images into a video (particularly useful if the
original images began as an image sequence exported from a video.
"""
import os
import csv
import argparse
import glob

import cv2
import numpy as np

from viztools import draw

parser = argparse.ArgumentParser()
parser.add_argument('path')
parser.add_argument('msecs_per_image')
parser.add_argument('fps')
parser.add_argument('conf')
parser.add_argument('-x',
                    '--export',
                    action='store_true',
                    help='Export a video.')
parser.add_argument('-l',
                    '--show_labels',
                    action='store_true',
                    help='draw labels on boxes')
args = parser.parse_args()
path = args.path
msecs_per_image = int(args.msecs_per_image)
export_video = args.export
fps = int(args.fps)
conf_threshold = float(args.conf)

FILTER_LABELS = ['person']

img_paths = glob.glob(os.path.join(path, '*.jpeg'))
img_paths = sorted(img_paths)

images = []
for img_path in img_paths:
    
    img = cv2.imread(img_path)
    img_shape = img.shape[:2][::-1]

    csv_path = os.path.splitext(img_path)[0].split('_')[0] + '.csv'
    with open(csv_path) as f:
        csv_reader = csv.reader(f, delimiter=',')

        for row in csv_reader:
            label = row[0]
            score = float(row[1])
            color = (100, 200, 100)
            bbox = [int(item) for item in row[2:]]

            caption = '{} {:.2f}'.format(label, score)
            
            if (score > conf_threshold
                and label in FILTER_LABELS):

                if args.show_labels:
                    draw.labeled_box_on_image(img, bbox, caption)
                draw.box_on_image(img, bbox, color=color)
        
    images.append(img)
    cv2.imshow('View', img)
    key = cv2.waitKey(msecs_per_image)

    if key == ord('q'):
        break

print('Number of frames processed: {}'.format(len(images)))

cv2.destroyAllWindows()

if export_video:
    print('[INFO] exporting video.')
    video = cv2.VideoWriter('output.avi', 0, fps, img_shape)

    for image in images:
        video.write(image)
