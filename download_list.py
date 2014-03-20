#!/usr/bin/env python

import flickrquery
import argparse
import os.path, os
import subprocess, math


parser = argparse.ArgumentParser()
parser.add_argument("output_dir", help="output directory where images will be stored")
parser.add_argument("input_lists", nargs='+', help="input files containing images to be downloaded")
args = parser.parse_args()

def check_image(filename):
  try:
    jhead_output = subprocess.check_output(['jhead', filename])
  except:
    return False
  else:
    for line in jhead_output.splitlines():
      tokens = line.split()
      if len(tokens) == 5 and tokens[0] == 'Resolution' and int(tokens[2]) > 0 and int(tokens[4]) > 0:
        return True
    return False

def download_image(urls, filename):
  for url in urls:
    cmd = 'wget -t 3 -T 5 --quiet --max-redirect 0 %s -O %s' % (url, filename)
    res = os.system(cmd)
    if res == 0:
      if check_image(filename):
        return True
  # All tries failed, clean up
  if os.path.exists(fname):
    os.remove(fname)
  return False

images = { }

dups = 0
for f in args.input_lists:
  lines = open(f, 'r').readlines()
  for l in lines:
    tokens = l.strip().split(' ')
    if tokens[0] in images:
      dups = dups + 1
    else:
      images[tokens[0]] = tokens[1:]

print 'Total images to download: %d, dups %d' % (len(images), dups)

if not os.path.exists(args.output_dir):
  os.mkdir(args.output_dir)

downloaded_images = 0
skipped_images = 0
i = 0
for im, urls in images.items():
  fname = os.path.join(args.output_dir, '%s.jpg' % im)
  if os.path.exists(fname):
    skipped_images = skipped_images + 1
    continue
  if download_image([urls[1], urls[2]], fname):
    downloaded_images = downloaded_images + 1
  i = i + 1
  if i % 100 == 0: print 'Processed %d / %d images.' % (i, len(images))
print 'Downloaded %d images, skipped %d existing images.' % (downloaded_images, skipped_images)




