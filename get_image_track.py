#!/usr/bin/python

from flickrapi2 import FlickrAPI
import argparse
import os.path, os, sys
import subprocess, math
import time
from flickr_api_key import *
from datetime import datetime, timedelta
import json


def getImageInfo(fapi, pid):
  info = {}
  try:
      rsp = fapi.photos_getInfo(api_key=flickrAPIKey, photo_id=pid)
      time.sleep(1)
      fapi.testFailure(rsp)
      info['owner'] = rsp.photo[0].owner[0]['nsid']
      info['date_taken'] = rsp.photo[0].dates[0]['taken']
  except KeyboardInterrupt:
      print('Keyboard exception while querying for images, exiting\n')
      raise
  except:
      print sys.exc_info()[0]
      print ('Exception encountered while querying for images\n')
  return info


def getCloseImages(fapi, owner, mintime, maxtime):
  page = 1;
  npages = 1;

  images = []
  while page <= npages:
    try:
        rsp = fapi.photos_search(api_key=flickrAPIKey, user_id=owner, min_taken_date=mintime, max_taken_date=maxtime, page=str(page))
        time.sleep(1)
        fapi.testFailure(rsp)
        npages = int(rsp.photos[0]['pages'])
        if page == 1: print 'Downloading %s images for track.' % (rsp.photos[0]['total'])
        for photo in rsp.photos[0].photo:
          image = { }
          image['photo_id'] = photo['id']
          image['server'] = photo['server']
          image['farm'] = photo['farm']
          image['owner'] = photo['owner']
          image['secret'] = photo['secret']
          image['title'] = photo['title']
          images.append(image)

    except KeyboardInterrupt:
        print('Keyboard exception while querying for images, exiting\n')
        raise
    except:
        print sys.exc_info()[0]
        print ('Exception encountered while querying for images\n')
    page = page + 1
  return images

def getImageTrack(fapi, photo_id, hours = 5):
  info = getImageInfo(fapi, photo_id)
  if (not 'owner' in info) or (not 'date_taken' in info): return []

  try:
    dt = datetime.strptime(info['date_taken'],'%Y-%m-%d %H:%M:%S')
    delta = timedelta(hours=hours);

    return getCloseImages(fapi, info['owner'], str(dt-delta), str(dt+delta));
  except ValueError:
    return []

def main():
  parser = argparse.ArgumentParser()
  parser.add_argument("photo_id", help="input photo id")
  parser.add_argument("output_file", help="output file storing the track")
  parser.add_argument("-delta_hours", help="hours around time photo was taken", type=int, default=2)
  args = parser.parse_args()

  fapi = FlickrAPI(flickrAPIKey, flickrSecret)

  images = getImageTrack(fapi, args.photo_id, args.delta_hours)

  fp = open(args.output_file,'w')
  json.dump(images, fp, separators=(',',':'))
  fp.close()

if __name__ == "__main__":
    main()

