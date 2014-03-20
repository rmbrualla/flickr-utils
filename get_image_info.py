#!/usr/bin/python

from flickrapi2 import FlickrAPI
import argparse
import os.path, os, sys
import subprocess, math
import time
from flickr_api_key import *
from datetime import datetime, timedelta
import json
from xml.dom import minidom
from xml.etree import ElementTree

def getImageInfo(fapi, pid):
  info = {}
  info_xml_str = ''
  try:
      rsp = fapi.photos_getInfo(api_key=flickrAPIKey, photo_id=pid)
      time.sleep(1)
      fapi.testFailure(rsp)
      info = rsp

      node = minidom.parseString(rsp.xml)
      photo = node.getElementsByTagName('photo');
      node = photo[0];
      info_xml_str = node.toprettyxml(indent='  ',encoding='utf-8')
      info_xml_str = '\n'.join([line for line in info_xml_str.split('\n') if line.strip()])
      info = rsp.photo[0];
  
  except KeyboardInterrupt:
      print('Keyboard exception while querying for images, exiting\n')
      raise
  except Exception as inst:
      print sys.exc_info()[0]
      print inst
      print ('Exception encountered while querying for images\n')
  return (info,info_xml_str)


def main():
  parser = argparse.ArgumentParser()
  parser.add_argument("photo_id", help="input photo id")
  parser.add_argument("output_file", help="output file storing the info")
  args = parser.parse_args()

  fapi = FlickrAPI(flickrAPIKey, flickrSecret)

  (info,info_xml_str) = getImageInfo(fapi, args.photo_id)

  f = open(args.output_file,'w')
  f.write(info_xml_str);
  f.close()


if __name__ == "__main__":
    main()

