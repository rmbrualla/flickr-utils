#!/usr/bin/env python

import flickrquery
import argparse
import os.path, os
import subprocess

def download_image(data, filename):
  if data['originalsecret'] and data['originalsecret'] != 'null':
    url_original = 'http://farm%s.staticflickr.com/%s/%s_%s_o.%s' % (data['farm'], data['server'], data['id'], data['originalsecret'], data['originalformat'])
  else:
    url_original = 'http://farm%s.staticflickr.com/%s/%s_%s_o.jpg' % (data['farm'], data['server'], data['id'], data['secret'])
  url_large = 'http://farm%s.staticflickr.com/%s/%s_%s_b.jpg' % (data['farm'], data['server'], data['id'], data['secret'])

  cmd = 'wget -t 3 -T 5 --quiet --max-redirect 0 %s -O %s' % (url_original, filename)
  res = os.system(cmd)
  if res == 0:
    try:
      jhead_output = subprocess.check_output(['jhead', filename])
    except:
      pass
    else:
      for line in jhead_output.splitlines():
        tokens = line.split()
        if len(tokens) == 5 and tokens[0] == 'Resolution' and int(tokens[2]) > 0 and int(tokens[4]) > 0:
          return True

#  print 'Trying to look for the large image...'

  cmd = 'wget -t 3 -T 5 --quiet --max-redirect 0 %s -O %s' % (url_large, filename)
  res = os.system(cmd)

  if res == 0:
    try:
      jhead_output = subprocess.check_output(['jhead', filename])
    except:
      pass
    else:
      for line in jhead_output.splitlines():
        tokens = line.split()
        if len(tokens) == 5 and tokens[0] == 'Resolution' and int(tokens[2]) > 0 and int(tokens[4]) > 0:
          return True
  return False
  

parser = argparse.ArgumentParser()
parser.add_argument("input file", help="input file with a query and an output directory separated by ';' in each line")
parser.add_argument("num_images", type=int, help="number of images to be downloaded")
parser.add_argument("storage_dir", help="directory where all images will be stored, the output dirs will have simlinks to this directory.")
parser.add_argument("-start_date", help="start date", default="1/1/2005")
parser.add_argument("-end_date", help="end date", default="1/1/2014")
parser.add_argument("--split_dirs", help="split downloaded images in directories", dest="split_dirs",action="store_true")
parser.set_defaults(split_dirs=False)

args = parser.parse_args()

inputf = open(args.input_file, 'r')



if not os.path.exists(args.output_dir):
  os.mkdir(args.output_dir)
if not os.path.exists(args.output_dir):
  print 'Cannot create output directory, exiting.'
  exit()

queries = args.query.split(';')



all_results = {}

for q in queries:

  results = flickrquery.run_flickr_query(q, args.num_images, startDate=args.start_date, endDate=args.end_date)

  print 'Found %d images for query: %s' % (len(results), q)
  for photo_id, data in results.items():
    all_results[photo_id] = data;


MAX_IMAGES_DIRECTORY = 1000
directory_number = 1
num_images_in_directory = 0

num_images = 0

print 'Downloading %d images.' % len(all_results.keys())

for photo_id,data in all_results.items():

  if args.split_dirs:
    current_directory = os.path.join(args.output_dir, '%04d' % directory_number)
    if not os.path.exists(current_directory):
      os.mkdir(current_directory)
  else:
    current_directory = args.output_dir

  if download_image(data, os.path.join(current_directory, '%s.jpg' % photo_id)):
    num_images_in_directory = num_images_in_directory+1
    num_images = num_images + 1
#    print 'Successfully downloaded image: %s' % photo_id

    # Change directory if max number of images per directory is reached.
    if args.split_dirs and num_images_in_directory >= MAX_IMAGES_DIRECTORY:
      directory_number = directory_number+1
      current_directory = os.path.join(args.output_dir, '%04d' % directory_number)
      if not os.path.exists(current_directory):
        os.mkdir(current_directory)
      num_images_in_directory = 0

  if num_images % 100 == 0:
    print 'Processed %d / %d images.' % (num_images, len(results))      

  if num_images >= args.num_images:
    break
