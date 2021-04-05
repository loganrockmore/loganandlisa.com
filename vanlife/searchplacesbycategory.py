#!/usr/bin/python

import datetime
import gpxpy
import json
import os
import pprint
import re
import requests
import sys

# TODO: share this with generate.py
dateRangesToInclude = [
	['2018-07-29T15:23', '2018-08-20T00:00'],
	# burning man
	['2018-09-08T00:00', '2018-09-10T16:45'],
	# seattle visit
	['2018-09-14T00:00', '2018-10-10T22:02'],
	# seattle visit
	['2018-10-12T11:49', '2018-10-14T15:43'],
	# seattle wedding
	['2018-10-31T12:30', '2018-11-09T18:40'],
	# orlando trip
	['2018-11-18T14:49', '2018-11-18T20:59'],
	# la crosse wedding
	['2018-11-26T12:20', '2018-11-26T17:03'],
	# minneapolis/st. paul airbnb
	['2018-11-28T00:00', '2018-12-19T17:52'],
	# christmas on kings mountain, la crosse trip, sketchfest in san francisco
	['2019-02-02T12:00', '2019-02-02T19:45'],
	# santa rosa, pliny the younger
	['2019-02-04T01:00', '2019-03-06T12:00'],
	# south dakota paperwork wedding
	['2019-03-09T17:00', '2019-04-09T23:00'],
	# sf condo, georgia/flordia baseball trip
	['2019-04-21T05:00', '2019-05-02T23:00'],
	# monterrey mexico, new york city ipo
	['2019-05-13T12:00', '2019-05-17T15:15'], # seattle sailing trip
	# seattle errands
	['2019-05-19T05:00', '2019-07-03T00:00'],
	# leavenworth fourth of july trip
	['2019-07-08T12:00', '2019-07-11T22:00'],
	# wine party weekend
	['2019-07-15T01:00', '2019-07-19T16:00'],
	# seattle BRASA build time
	['2019-08-05T01:00', '2019-08-06T23:00'],
	# mikey and martha's wedding, burning man
	['2019-09-04T10:00', '2019-09-09T12:00'],
	# philly, new york, aarhus, amsterdam, munich, iowa, las vegas
	['2019-10-03T12:00', '2019-11-14T00:00'],
	# telluride
	['2019-11-18T00:00', '2019-11-22T00:00'],
	# san francisco, hawaii
	['2019-12-05T00:00', '2019-12-19T16:00'],
	# la crosse, minneapolis
	['2020-01-20T00:00', '2020-01-30T00:00'],
	# whistler
	['2020-02-06T03:00', '2020-02-14T08:00'],
	# minneapolis, separate trips
	['2020-02-24T08:00', '2020-02-25T22:00'],
	# pittsburgh
	['2020-02-29T07:00', '2020-03-01T22:00'],
]

foursquareClientID = 'OYLFUIIRXAXJHXIRFPVNTZ1J0U1SNYKRO22EUH0UOQUOH3TW'
foursquareClientSecret = 'POC5KS4RHS1OV1QXHPJQRVGYVCAIM1LW4LJAAT03GMFOILMR'

gpxFolder = '/Users/logan/Library/Mobile Documents/com~apple~CloudDocs/Arc Export for Vanlife Map'

gpxFiles = os.listdir(gpxFolder)
gpxFiles.sort()

searchCategory = ' '.join(sys.argv[1:])

print 'searching for "%s"' % (searchCategory)

# create the date time ranges
dateTimeRanges = []
for dateRange in dateRangesToInclude:
	startDate = datetime.datetime.strptime(dateRange[0], "%Y-%m-%dT%H:%M")
	
	if len(dateRange) ==  2:
		endDate = datetime.datetime.strptime(dateRange[1], "%Y-%m-%dT%H:%M")
	else:
		endDate = datetime.datetime.now()
		
	dateTimeRanges.append([startDate, endDate])
	
def dateTimeIsInRange(dateTime, dateTimeRanges):
	for range in dateTimeRanges:
		if dateTime >= range[0] and dateTime <= range[1]:
			return True
	return False
	
# loop through all of the GPX files
for gpxFile in gpxFiles:

	# skip .DS_Store
	if gpxFile == '.DS_Store' or gpxFile.endswith('.icloud'):
		continue
		
	print "searching " + gpxFile
	
	# parse the file
	gpxFileContents = open(gpxFolder + '/' + gpxFile, 'r')
	gpx = gpxpy.parse(gpxFileContents)
	
	# add to the global list
	for waypoint in gpx.waypoints:
	
		# skip if out of range
		if not dateTimeIsInRange(waypoint.time, dateTimeRanges):
			continue
			
		# get the foursquare data for this link
		if waypoint.link:
			
			# get the venue id
			search = re.match(r'http://foursquare.com/venue/(.*)', waypoint.link)
			if not search:
				print 'unable to find foursquare venue id from link (%s)' % (waypoint.link)
			else:
				venueID = search.groups()[0]
				
				# hit the foursquare API
				foursquareAPIURL = 'https://api.foursquare.com/v2/venues/%s' % (venueID)
				params = {
							'client_id': foursquareClientID,
							'client_secret': foursquareClientSecret,
							'v': '20200219',
				}
				r = requests.get(foursquareAPIURL, params=params)
				
				if 429 == r.status_code:
					print r.status_code
					print r.text
					print
					print 'stopping script, nothing else is going to work'
					sys.exit(1)
					
				elif not 200 == r.status_code:
					print 'non-200 status code from foursquare api for url %s' % (foursquareAPIURL)
					print r.status_code
					print r.text
				else:
					responseJSON = json.loads(r.text)
					
					# look at each category
					categories = responseJSON['response']['venue']['categories']
					
					foundCategory = False
					for category in categories:
						categoryName = category['name']
						
						if categoryName == searchCategory:
							foundCategory = True
							break
					
					# it's a match! print this data
					if foundCategory:
						print "%s: %s (%s)" % (waypoint.time, waypoint.name, waypoint.link)