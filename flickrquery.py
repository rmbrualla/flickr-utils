#Image querying script written by Tamara Berg,
#and extended heavily James Hays

#9/26/2007 added dynamic timeslices to query more efficiently.
#8/18/2008 added new fields and set maximum time slice.
#8/19/2008 this is a much simpler function which gets ALL geotagged photos of
# sufficient accuracy.  No queries, no negative constraints.
# divides up the query results into multiple files
# 1/5/2009
# now uses date_taken instead of date_upload to get more diverse blocks of images
# 1/13/2009 - uses the original im2gps keywords, not as negative constraints though

import sys, string, math, socket
import time as os_time
from flickrapi2 import FlickrAPI
from datetime import datetime, date, time
import calendar
from flickr_api_key import *

import pyprind


def convertDate(date_string):
    tokens = date_string.split('/')
    year = int(tokens[2])
    month = int(tokens[1])
    day = int(tokens[0])
    d = date(year, month, day)
    t = time(0, 0)
    dt = datetime.combine(d, t)
    return calendar.timegm(dt.utctimetuple())


def NumberImagesInInterval(fapi, mintime, maxtime, query_args):
    min_taken_date=str(datetime.fromtimestamp(round(mintime)))
    max_taken_date=str(datetime.fromtimestamp(round(maxtime)))

    rsp1 = fapi.photos_search(api_key=flickrAPIKey,
                             media="photos",
                             per_page="300", 
                             page="1",
                             min_upload_date=min_taken_date,
                             max_upload_date=max_taken_date,
                             **query_args)
    os_time.sleep(1)
    fapi.testFailure(rsp1)
    total1 = int(rsp1.photos[0]['total'])
    #print 'Calling api (%s, %s) => %d' % (min_taken_date, max_taken_date, total1)

    return (total1, rsp1)


def processResult(rsp):
    global progress_bar
    result = {}
    k = getattr(rsp,'photos',None)
    if k:
        m = getattr(rsp.photos[0],'photo',None)
        if m:
            for b in rsp.photos[0].photo:
                if b!=None:
                    photo_id = b['id']

                    photo_data = { }
                    photo_data['id'] = b['id']
                    photo_data['secret'] = b['secret']
                    photo_data['server'] = b['server']
                    photo_data['farm'] = b['farm']
                    photo_data['owner'] = b['owner']
                    photo_data['title'] = b['title']
                    photo_data['originalsecret'] = b['originalsecret']
                    photo_data['originalformat'] = b['originalformat']
                    photo_data['o_height'] = b['o_height']
                    photo_data['o_width'] = b['o_width']
                    photo_data['datetaken'] = b['datetaken'].encode("ascii","replace")
                    photo_data['dateupload'] = b['dateupload'].encode("ascii","replace")
                    photo_data['tags'] = b['tags'].encode("ascii","replace")
                    photo_data['license'] = b['license'].encode("ascii","replace")
                    photo_data['latitude'] = b['latitude'].encode("ascii","replace")
                    photo_data['longitude'] = b['longitude'].encode("ascii","replace")
                    photo_data['accuracy'] = b['accuracy'].encode("ascii","replace")
                    photo_data['views'] = b['views']

                    result[photo_id] = photo_data
                    progress_bar.update(item_id = str(date.fromtimestamp(float(photo_data['dateupload']))))
    return result



def subdivide(num_photos, start_time, end_time, query_args, fapi):
    result = {}

    if num_photos == 0:
        return result   
    photos_per_page = 100
    num_pages = (num_photos + photos_per_page) / photos_per_page
    #print 'subdivide photos: %s pages: %d range: %d %d' % (num_photos, num_pages, start_time, end_time)
    time_delta = (end_time - start_time) / num_pages
    t1 = start_time
    for i in range(num_pages):
        t2 = t1 + time_delta
        tries = 0
        while tries < 10:
            (n, rsp) = NumberImagesInInterval(fapi, t1, t2, query_args)
            if n <= num_photos and n > 0:
                break
            tries = tries + 1
        if tries == 10:
            n = 0;
        if n > 2 * photos_per_page:
            res = subdivide(n, t1, t2, query_args, fapi)
            result.update(res)
        elif (n < photos_per_page * 3) and (n > 0):
            extra_args = {'extras':  "tags, original_format, license, geo, date_taken, date_upload, o_dims, views"}
            extra_args.update(query_args)
            tries = 0
            while tries < 10:

                (n2, rsp2) = NumberImagesInInterval(fapi, t1, t2, extra_args)
                if n2 == n:
                    break
                tries = tries + 1
            if tries < 10:
                res = processResult(rsp2)
                result.update(res)
        t1 = t2
    return result;

def run_flickr_query(max_photos = 1000, startDate = "1/1/2010", endDate = "31/12/2011", query_args = {}):
    global progress_bar

    socket.setdefaulttimeout(30)  #30 second time out on sockets before they throw
    #an exception.  I've been having trouble with urllib.urlopen hanging in the 
    #flickr API.  This will show up as exceptions.IOError.

    #the time out needs to be pretty long, it seems, because the flickr servers can be slow
    #to respond to our big searches.

    ###########################################################################
    # Modify this section to reflect your data and specific search 
    ###########################################################################
    # flickr auth information:
    # change these to your flickr api keys and secret

    # make a new FlickrAPI instance
    fapi = FlickrAPI(flickrAPIKey, flickrSecret)

    #print '\n\nquery_string is ' + query_string
    total_images_queried = 0;


    # number of seconds to skip per query  

    starttime = convertDate(startDate)
    endtime = convertDate(endDate)


    photos_per_page = 100;

    tries = 0
    while tries < 10:
        (num_photos, rsp) = NumberImagesInInterval(fapi, starttime, endtime, query_args)
        if num_photos < 100000 and num_photos > 0:
            break
        tries = tries + 1
    if tries == 10:
        return {}
    print 'Querying for "%s" (%d photos)' % (query_args['text'], num_photos)

    progress_bar = pyprind.ProgPercent(num_photos, title='Photos processed')

    result = subdivide(num_photos, starttime, endtime, query_args, fapi)
    progress_bar.stop()

    return result

#     #this is the desired number of photos in each block
#     desired_photos = min(250, max_photos)
  
#     total_image_num = 0

#     results = {}

#     min_taken_date=str(datetime.fromtimestamp(round(starttime)))
#     max_taken_date=str(datetime.fromtimestamp(round(endtime)))
#     print 'Calling api (%s, %s), ' % (min_taken_date, max_taken_date), query_args

#     rsp = fapi.photos_search(api_key=flickrAPIKey,
#                             media="photos",
#                             page="1",
#                             #has_geo = "1", #bbox="-180, -90, 180, 90",
#                             #text=query_string,
#                             #accuracy="6", #6 is region level.  most things seem 10 or better.
#                             min_upload_date=min_taken_date,
#                             max_upload_date=max_taken_date,
#                             **query_args)
#                             ##min_taken_date=str(datetime.fromtimestamp(mintime)),
#                             ##max_taken_date=str(datetime.fromtimestamp(maxtime)))
#     #we want to catch these failures somehow and keep going.
#     os_time.sleep(1)
#     fapi.testFailure(rsp)
#     total_images = rsp.photos[0]['total'];


#     #end of while binary search    
#     print 'finished binary search'

#     print 'mintime: ' + min_taken_date + ' maxtime: ' + max_taken_date + ' numimgs: ' + total_images
#     print 'total images: %s in %d pages' % (total_images, int(rsp.photos[0]['pages']))

#     i = getattr(rsp,'photos',None)
#     if i:
            
        
#         current_image_num = 1;
        
#         num = int(rsp.photos[0]['pages'])
#         print 'total %d images in %d pages' % (int(total_images), num)
        
#         num_visit_pages = num #min(16,num)
    
#         pagenum = 1;
#         while( pagenum <= num_visit_pages ):
#             if len(results) > max_photos:
#                 break
#         #for pagenum in range(1, num_visit_pages + 1):  #page one is searched twice
#             print '  page number ' + str(pagenum)
#             try:
#                 rsp = fapi.photos_search(api_key=flickrAPIKey,
#                                     media="photos",
#                                     page=str(pagenum),
#                                     #has_geo = "1", #bbox="-180, -90, 180, 90",
#                                     #text=query_string,
#                                     #accuracy="6", #6 is region level.  most things seem 10 or better.
#                                     extras = "tags, original_format, license, geo, date_taken, date_upload, o_dims, views",
#                                     min_upload_date=min_taken_date,
#                                     max_upload_date=max_taken_date,
#                                     **query_args)
#                                     ##min_taken_date=str(datetime.fromtimestamp(mintime)),
#                                     ##max_taken_date=str(datetime.fromtimestamp(maxtime)))
#                 os_time.sleep(1)
#                 fapi.testFailure(rsp)
#             except KeyboardInterrupt:
#                 print('Keyboard exception while querying for images, exiting\n')
#                 raise
# #                except:
# #                    print sys.exc_info()[0]
# #                    #print type(inst)     # the exception instance
# #                    #print inst.args      # arguments stored in .args
# #                    #print inst           # __str__ allows args to printed directly
# #                    print ('Exception encountered while querying for images\n')
#             else:

#                 # and print them
#                 k = getattr(rsp,'photos',None)
#                 if k:
#                     m = getattr(rsp.photos[0],'photo',None)
#                     if m:
#                         for b in rsp.photos[0].photo:
#                             if b!=None:
#                                 photo_id = b['id']

#                                 photo_data = { }
#                                 photo_data['id'] = b['id']
#                                 photo_data['secret'] = b['secret']
#                                 photo_data['server'] = b['server']
#                                 photo_data['farm'] = b['farm']

#                                 photo_data['owner'] = b['owner']
#                                 photo_data['title'] = b['title']
#                                 photo_data['originalsecret'] = b['originalsecret']
#                                 photo_data['originalformat'] = b['originalformat']
#                                 photo_data['o_height'] = b['o_height']
#                                 photo_data['o_width'] = b['o_width']
#                                 photo_data['datetaken'] = b['datetaken'].encode("ascii","replace")
#                                 photo_data['dateupload'] = b['dateupload'].encode("ascii","replace")
#                                 photo_data['tags'] = b['tags'].encode("ascii","replace")
#                                 photo_data['license'] = b['license'].encode("ascii","replace")
#                                 photo_data['latitude'] = b['latitude'].encode("ascii","replace")
#                                 photo_data['longitude'] = b['longitude'].encode("ascii","replace")
#                                 photo_data['accuracy'] = b['accuracy'].encode("ascii","replace")
#                                 photo_data['views'] = b['views']
#                                 photo_data['interestingness'] = (current_image_num, total_images)

#                                 results[photo_id] = photo_data

#                                 current_image_num = current_image_num + 1;
#                                 total_image_num = total_image_num + 1;
#                 pagenum = pagenum + 1;  #this is in the else exception block.  It won't increment for a failure.

#         #this block is indented such that it will only run if there are no exceptions
#         #in the original query.  That means if there are exceptions, mintime won't be incremented
#         #and it will try again
# #            timeskip = maxtime - mintime #used for initializing next binary search
# #            mintime  = maxtime



    return results
