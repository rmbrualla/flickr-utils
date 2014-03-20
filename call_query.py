#!/usr/bin/python

import flickrquery

results = flickrquery.run_flickr_query('madrid', 10, startDate='1/2/2010', endDate='10/2/2010')

print len(results)
