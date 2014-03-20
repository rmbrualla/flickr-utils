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

def convertDate(date_string):
    tokens = date_string.split('/')
    year = int(tokens[2])
    month = int(tokens[1])
    day = int(tokens[0])
    d = date(year, month, day)
    t = time(0, 0)
    dt = datetime.combine(d, t)
    return calendar.timegm(dt.utctimetuple())
    

def run_flickr_query(query_string, max_photos = 1000, startDate = "1/1/2010", endDate = "31/12/2011"):

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

    print '\n\nquery_string is ' + query_string
    total_images_queried = 0;


    # number of seconds to skip per query  
    timeskip = 8 * 604800  #one week

    starttime = convertDate(startDate)
    #mintime = convertDate(startDate) 
    endtime = convertDate(endDate)

    
#    maxtime = startime+20*timeskip
    maxtime = endtime
    mintime = endtime-20*timeskip
    timeskip = min(timeskip, endtime-mintime)

    print 'Start time: ' + str(datetime.fromtimestamp(starttime))
    print 'End time: ' + str(datetime.fromtimestamp(endtime))

    #this is the desired number of photos in each block
    desired_photos = min(250, max_photos)
  
    total_image_num = 0

    results = {}

#    while (maxtime < endtime):
    while (starttime < mintime):

        #new approach - adjust maxtime until we get the desired number of images 
        #within a block. We'll need to keep upper bounds and lower
        #lower bound is well defined (mintime), but upper bound is not. We can't 
        #search all the way from endtime.

#        lower_bound = mintime + 900 #lower bound OF the upper time limit. must be at least 15 minutes or zero results
#        upper_bound = mintime + timeskip * 20 #upper bound of the upper time limit
#        upper_bound = min(upper_bound, endtime)
#        maxtime     = .95 * lower_bound + .05 * upper_bound

        lower_bound = mintime - 20 * timeskip #lower bound OF the upper time limit. must be at least 15 minutes or zero results
        upper_bound = maxtime #upper bound of the upper time limit
        lower_bound = max(lower_bound, starttime)
        mintime     = 0.05 * lower_bound + 0.95 * upper_bound

#        print '\nBinary search on time range upper bound' 
#        print 'Lower bound is ' + str(datetime.fromtimestamp(lower_bound))
#        print 'Upper bound is ' + str(datetime.fromtimestamp(upper_bound))

        if total_image_num > max_photos:
            print 'Number of photos %d > %d limit.' % (total_image_num, max_photos)
            break

        keep_going = 6 #search stops after a fixed number of iterations
        while( keep_going > 0 and starttime < mintime):
        #while( keep_going > 0 and maxtime < endtime):
        
            try:
#                print 'Calling api'
                rsp = fapi.photos_search(api_key=flickrAPIKey,
                                        ispublic="1",
                                        media="photos",
                                        per_page="250", 
                                        page="1",
                                        #has_geo = "1", #bbox="-180, -90, 180, 90",
                                        text=query_string,
                                        #accuracy="6", #6 is region level.  most things seem 10 or better.
                                        min_upload_date=str(mintime),
                                        max_upload_date=str(maxtime))
                                        ##min_taken_date=str(datetime.fromtimestamp(mintime)),
                                        ##max_taken_date=str(datetime.fromtimestamp(maxtime)))
                #we want to catch these failures somehow and keep going.
                os_time.sleep(1)
                fapi.testFailure(rsp)
                total_images = rsp.photos[0]['total'];
                if total_images == '':
                    total_images = '0'
#                print total_images
#                print rsp.photos[0]
                null_test = int(total_images); #want to make sure this won't crash later on for some reason
                null_test = float(total_images);
        
#                print 'numimgs: ' + total_images
#                print 'mintime: ' + str(mintime) + ' maxtime: ' + str(maxtime) + ' timeskip:  ' + str(maxtime - mintime)
            
                if( int(total_images) > desired_photos ):
#                    print 'too many photos in block, increasing mintime'
                    lower_bound = mintime
                    mintime = (upper_bound + mintime) / 2 #midpoint between current value and lower bound.
#                    print 'too many photos in block, reducing maxtime'
#                    upper_bound = maxtime
#                    maxtime = (lower_bound + mintime) / 2 #midpoint between current value and lower bound.
                
                if( int(total_images) < desired_photos):
#                    print 'too few photos in block, reducing mintime'
                    upper_bound = mintime
                    mintime = (lower_bound + mintime) / 2
#                    print 'too few photos in block, increasing maxtime'
#                    lower_bound = maxtime
#                    maxtime = (upper_bound + maxtime) / 2
                
#                print 'Lower bound is ' + str(datetime.fromtimestamp(lower_bound))
 #               print 'Upper bound is ' + str(datetime.fromtimestamp(upper_bound))
            
                if( int(total_images) > 0): #only if we're not in a degenerate case
                    keep_going = keep_going - 1
                else:
                    upper_bound = upper_bound + timeskip;    
            
            except KeyboardInterrupt:
                print('Keyboard exception while querying for images, exiting\n')
                raise
#            except:
#                print sys.exc_info()[0]
                #print type(inst)     # the exception instance
                #print inst.args      # arguments stored in .args
                #print inst           # __str__ allows args to printed directly
#                print ('Exception encountered while querying for images\n')

        #end of while binary search    
#        print 'finished binary search'

        print 'mintime: ' + str(datetime.fromtimestamp(mintime)) + ' maxtime: ' + str(datetime.fromtimestamp(maxtime)) + ' numimgs: ' + total_images

        i = getattr(rsp,'photos',None)
        if i:
                
            s = 'numimgs: ' + total_images
            print s
            
            current_image_num = 1;
            
            num = int(rsp.photos[0]['pages'])
            s =  'total pages: ' + str(num)
            print s
            
            #only visit 16 pages max, to try and avoid the dreaded duplicate bug
            #16 pages = 4000 images, should be duplicate safe.  Most interesting pictures will be taken.
            
            num_visit_pages = min(16,num)
            
            s = 'visiting only ' + str(num_visit_pages) + ' pages ( up to ' + str(num_visit_pages * 250) + ' images)'
            print s
            
            total_images_queried = total_images_queried + min((num_visit_pages * 250), int(total_images))

            #print 'stopping before page ' + str(int(math.ceil(num/3) + 1)) + '\n'
        
            pagenum = 1;
            while( pagenum <= num_visit_pages ):
            #for pagenum in range(1, num_visit_pages + 1):  #page one is searched twice
                print '  page number ' + str(pagenum)
                try:
                    rsp = fapi.photos_search(api_key=flickrAPIKey,
                                        ispublic="1",
                                        media="photos",
                                        per_page="250", 
                                        page=str(pagenum),
                                        sort="interestingness-desc",
                                        #has_geo = "1", #bbox="-180, -90, 180, 90",
                                        text=query_string,
                                        #accuracy="6", #6 is region level.  most things seem 10 or better.
                                        extras = "tags, original_format, license, geo, date_taken, date_upload, o_dims, views",
                                        min_upload_date=str(mintime),
                                        max_upload_date=str(maxtime))
                                        ##min_taken_date=str(datetime.fromtimestamp(mintime)),
                                        ##max_taken_date=str(datetime.fromtimestamp(maxtime)))
                    os_time.sleep(1)
                    fapi.testFailure(rsp)
                except KeyboardInterrupt:
                    print('Keyboard exception while querying for images, exiting\n')
                    raise
#                except:
#                    print sys.exc_info()[0]
#                    #print type(inst)     # the exception instance
#                    #print inst.args      # arguments stored in .args
#                    #print inst           # __str__ allows args to printed directly
#                    print ('Exception encountered while querying for images\n')
                else:

                    # and print them
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
                                    photo_data['interestingness'] = (current_image_num, total_images)

                                    results[photo_id] = photo_data

                                    current_image_num = current_image_num + 1;
                                    total_image_num = total_image_num + 1;
                    pagenum = pagenum + 1;  #this is in the else exception block.  It won't increment for a failure.

            #this block is indented such that it will only run if there are no exceptions
            #in the original query.  That means if there are exceptions, mintime won't be incremented
            #and it will try again
#            timeskip = maxtime - mintime #used for initializing next binary search
#            mintime  = maxtime

        timeskip = maxtime - mintime #used for initializing next binary search
        maxtime  = mintime


    return results
