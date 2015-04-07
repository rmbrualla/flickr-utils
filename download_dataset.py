#!/usr/bin/env python

import flickrquery
import argparse
import os.path, os
import subprocess, math
import json
from joblib import Parallel, delayed
import pyprind


parser = argparse.ArgumentParser()
parser.add_argument("output_dir", help="output directory where images will be stored")
parser.add_argument("num_images", type=int, help="number of images to be downloaded")
parser.add_argument("query", help="query string")
parser.add_argument("-start_date", help="start date", default="1/1/2005")
parser.add_argument("-end_date", help="end date", default="1/1/2014")
parser.add_argument("-target_max_dim", type=int, help="Target max dimension", default=1024)
parser.add_argument("--split_dirs", help="split downloaded images in directories", dest="split_dirs",action="store_true")
parser.set_defaults(split_dirs=False)
parser.add_argument('--noload_cache', dest='load_cache', action='store_false')

args = parser.parse_args()



def resize_image(filename, width, height):
  n_pixels = float(width * height)
  n_target_pixels = args.target_max_dim * args.target_max_dim * 3 / 4.0
  #print 'image',filename
  #print 'npixels ',n_pixels, n_target_pixels
  if n_pixels > n_target_pixels * 1.2:
    try:
      ratio = math.sqrt(n_target_pixels / (n_pixels * 1.0))
      # print 'w', width, 'h', height, 'r', ratio
      target_width = int(width * ratio)
      target_height = int(height * ratio)
      cmd = 'mogrify -resize %dx%d %s' % (target_width, target_height, filename)
      #print cmd
      return (os.system(cmd) == 0)
      #mogrify_output = subprocess.check_output(['mogrify', '-resize','%dx%d' % (target_width, target_height), filename])
    except:
      return False
  return True

def check_and_resize_image(filename):
  try:
    jhead_output = subprocess.check_output(['jhead', filename])
  except:
    return False
  else:
    for line in jhead_output.splitlines():
      tokens = line.split()
      if len(tokens) == 5 and tokens[0] == 'Resolution' and int(tokens[2]) > 0 and int(tokens[4]) > 0:
        return resize_image(filename, int(tokens[2]), int(tokens[4]))
    return False

def download_image(data, filename):
  print 'downloading ', filename
  if data['originalsecret'] and data['originalsecret'] != 'null':
    url_original = 'http://farm%s.staticflickr.com/%s/%s_%s_o.%s' % (data['farm'], data['server'], data['id'], data['originalsecret'], data['originalformat'])
  else:
    url_original = 'http://farm%s.staticflickr.com/%s/%s_%s_o.jpg' % (data['farm'], data['server'], data['id'], data['secret'])
  url_large = 'http://farm%s.staticflickr.com/%s/%s_%s_b.jpg' % (data['farm'], data['server'], data['id'], data['secret'])

  cmd = 'wget -t 1 -T 5 --quiet --max-redirect 0 %s -O %s' % (url_original, filename)
  res = os.system(cmd)
  if res == 0:
    return check_and_resize_image(filename)

#    try:
#      jhead_output = subprocess.check_output(['jhead', filename])
#    except:
#      pass
#    else:
#      for line in jhead_output.splitlines():
#        tokens = line.split()
#        if len(tokens) == 5 and tokens[0] == 'Resolution' and int(tokens[2]) > 0 and int(tokens[4]) > 0:
 #         return True

#  print 'Trying to look for the large image...'

  cmd = 'wget -t 1 -T 5 --quiet --max-redirect 0 %s -O %s' % (url_large, filename)
  res = os.system(cmd)

  if res == 0:
    return check_and_resize_image(filename)
#    try:
#      jhead_output = subprocess.check_output(['jhead', filename])
#    except:
#      pass
#    else:
#      for line in jhead_output.splitlines():
#        tokens = line.split()
#        if len(tokens) == 5 and tokens[0] == 'Resolution' and int(tokens[2]) > 0 and int(tokens[4]) > 0:
#          return True
#  return False
  

if not os.path.exists(args.output_dir):
  os.mkdir(args.output_dir)
if not os.path.exists(args.output_dir):
  print 'Cannot create output directory, exiting.'
  exit()

all_results = {}

query_results_file = os.path.join(args.output_dir, 'query_results.txt')
if not os.path.exists(query_results_file) or not args.load_cache:

  queries = args.query.split(';')

  for q in queries:
    print q
    results = flickrquery.run_flickr_query(query_args={'text': q}, max_photos = args.num_images, startDate=args.start_date, endDate=args.end_date)

    print 'Found %d images for query: %s' % (len(results), q)
    for photo_id, data in results.items():
      all_results[photo_id] = data;


  #MAX_IMAGES_DIRECTORY = 1000
  #directory_number = 1
  num_images_in_directory = 0

  num_images = 0
  num_download = 0

  print 'Downloading %d images.' % len(all_results.keys())

  print 'Caching results...'

  f = open(query_results_file, 'w')
  json.dump(all_results, f, sort_keys=True, indent=4, separators=(',', ': '))
  f.close()
else:
  print 'Loading cached results...'
  f = open(query_results_file, 'r')
  all_results = json.load(f)
  f.close()
  print 'Found %d images for the queries.' % len(all_results.keys())




progress_bar = pyprind.ProgPercent(len(all_results.keys()), title='Photos downloaded')
processed_photos =  0


def downloadPhoto(photo_id, data):
  global progress_bar, processed_photos
  progress_bar.update(item_id = str(processed_photos))
  processed_photos = processed_photos + 1
  if args.split_dirs:
    current_directory = os.path.join(args.output_dir, photo_id[0:2])

    if not os.path.exists(current_directory):
      try:
        os.mkdir(current_directory)
      except:
        pass
  else:
    current_directory = args.output_dir

  image_filename = os.path.join(current_directory, '%s.jpg' % photo_id)
  metadata_filename = os.path.join(current_directory, '%s.txt' % photo_id)

  valid = True
  if not os.path.exists(image_filename):
    if not download_image(data, image_filename):
      valid = False
  if valid:
    f = open(metadata_filename, 'w')
    json.dump(data, f, sort_keys=True, indent=4, separators=(',', ': '))
    f.close()
  else:
    try:
      os.system('rm %s' % image_filename)
    except:
      pass


Parallel(n_jobs=1)(delayed(downloadPhoto)(id, data) for id, data in all_results.items()) 
progress_bar.stop()