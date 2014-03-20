#!/usr/bin/env python

import flickrquery
import argparse
import os.path, os
import subprocess, math
import time

parser = argparse.ArgumentParser()
parser.add_argument("output", help="file that will contain the images")
parser.add_argument("num_images", type=int, help="number of images to be downloaded")
parser.add_argument("query", help="query string")
parser.add_argument("-start_date", help="start date", default="1/1/2005")
parser.add_argument("-end_date", help="end date", default="today")
parser.set_defaults(split_dirs=False)

args = parser.parse_args()

def generate_urls(data):
  if data['originalsecret'] and data['originalsecret'] != 'null':
    url_original = 'http://farm%s.staticflickr.com/%s/%s_%s_o.%s' % (data['farm'], data['server'], data['id'], data['originalsecret'], data['originalformat'])
  else:
    url_original = 'http://farm%s.staticflickr.com/%s/%s_%s_o.jpg' % (data['farm'], data['server'], data['id'], data['secret'])
  url_large = 'http://farm%s.staticflickr.com/%s/%s_%s_b.jpg' % (data['farm'], data['server'], data['id'], data['secret'])
  url_normal = 'http://farm%s.staticflickr.com/%s/%s_%s.jpg' % (data['farm'], data['server'], data['id'], data['secret'])
  return [url_original,url_large,url_normal]

query = args.query

all_results = {}

endDate = args.end_date;
if endDate == 'today':
  endDate = time.strftime("%d/%m/%Y")

results = flickrquery.run_flickr_query(query, args.num_images, startDate=args.start_date, endDate=endDate)

print 'Found %d images for query: %s' % (len(results), query)
for photo_id, data in results.items():
  all_results[photo_id] = data;

num_images = 0

result_f = open(args.output, 'w')

for photo_id,data in all_results.items():
  urls = generate_urls(data)
  result_f.write('%s %s %s %s\n' % (photo_id, urls[0], urls[1], urls[2]))
  num_images = num_images + 1
  if num_images >= args.num_images:
    break

