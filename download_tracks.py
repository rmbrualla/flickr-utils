#!/usr/bin/python

from flickrapi2 import FlickrAPI
import argparse
import os.path, os, sys, glob
from flickr_api_key import *
import get_image_track
import json


parser = argparse.ArgumentParser()
parser.add_argument("images_dir", help="input image dir")
parser.add_argument("-images_file", help="input image file containing photo ids, one per line", default = '')
parser.add_argument("-unseen_images_file", help="output file to store the unseen images", default = '')
parser.add_argument("-stats_file", help="output file to store stats", default = '')
args = parser.parse_args()

photo_ids = []
if len(args.images_file) == 0:
  images = glob.glob(os.path.join(args.images_dir, '*.jpg'))
  photo_ids = map(lambda im: os.path.split(os.path.splitext(im)[0])[1], images)
else:
  lines = open(args.images_file,'r').readlines()
  photo_ids = filter(lambda m:len(m) > 0, map(lambda line: line.strip(), lines))

fapi = FlickrAPI(flickrAPIKey, flickrSecret)

def storeJSON(obj, fname):
  f = open(fname, 'w')
  json.dump(obj, f, separators=(',',':'))
  f.close()

unseen_images = {}
stats = []

print 'Photo ids %d' % len(photo_ids)

backup = 100;
it = 0;

for photo_id in photo_ids:

  track_file = os.path.join(args.images_dir, photo_id + '.track')
  if os.path.exists(track_file):
    # If exists, ignore this photo and continue
    print 'Track exists'
    continue
  track = get_image_track.getImageTrack(fapi, photo_id)
  track_info = {'parent':photo_id,'track':track};

  storeJSON(track_info, track_file)

  children_track_info = {'parent':photo_id}

  stat = { };
  stat['children_track_exist'] = 0
  stat['children_track_new'] = 0
  stat['unseen_image'] = 0
  stat['track_length'] = len(track)
  for im in track:
    if im['photo_id'] == photo_id: continue
    im_file = os.path.join(args.images_dir, im['photo_id'] + '.jpg')
    if not os.path.exists(im_file):
      stat['unseen_image'] = stat['unseen_image'] + 1
      unseen_images[im['photo_id']] = im
      continue
    track_file = os.path.join(args.images_dir, im['photo_id'] + '.track')
    if os.path.exists(track_file):
      stat['children_track_exist'] = stat['children_track_exist'] + 1
      continue
    else:
      stat['children_track_new'] = stat['children_track_new'] + 1;
      storeJSON(children_track_info, track_file)
  stats.append(stat)

  print 'Track %d images: %d unseen, %d children, %d existing' % (len(track), stat['unseen_image'] , stat['children_track_new'], stat['children_track_exist'])
  
  it = it + 1;
  if it % backup == 0:
    
    print 'Backup at %d\nTotal unseen images: %d' % (it,len(unseen_images))
    if len(args.unseen_images_file) > 0:
      storeJSON(unseen_images.values(), args.unseen_images_file)
    if len(args.stats_file) > 0:
      storeJSON(stats, args.stats_file)
    
  


print 'Total unseen images: %d' % len(unseen_images)

if len(args.unseen_images_file) > 0:
  storeJSON(unseen_images.values(), args.unseen_images_file)

if len(args.stats_file) > 0:
  storeJSON(stats, args.stats_file)

