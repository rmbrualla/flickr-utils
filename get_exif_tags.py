#!/usr/bin/python

import sys, string, math, socket
from flickrapi2 import FlickrAPI

socket.setdefaulttimeout(30)

flickrAPIKey = "38efd30366668a955506a96d2369ee3b"  # API key
flickrSecret = "990ae0178e6eed82"

fapi = FlickrAPI(flickrAPIKey, flickrSecret)

try:
    rsp = fapi.photos_getExif(api_key=flickrAPIKey,photo_id=sys.argv[1])

    fapi.testFailure(rsp)
    for exif in rsp.photo[0].exif:
        print '%s=%s' % (exif['label'],exif.raw[0].elementText)
        
except ValueError:
    pass
