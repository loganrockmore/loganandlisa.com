#!/usr/bin/python

import datetime
import gpxpy
import itertools
import json
import polyline
import os

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
	['2020-02-24T08:00', '2020-02-25T18:00'],
	# pittsburgh
	['2020-02-29T06:00', '2020-03-01T22:00'],
	
	# moved to brooklyn
	
	['2020-09-14T03:00', '2020-09-23T23:59'], # melissa and don's wedding trip
	['2020-10-06T13:00', '2020-10-10T20:00'], # new england leaf peeping
	
	['2021-11-17T12:00', '2021-11-21T15:00'], # birthday weekend in eastern PA
	
	['2022-02-01T04:00', '2022-02-12T16:00'], # visit Nina and new houseboats in Minnesota/Wisconsin
]

gpxFolder = '/Users/logan/Library/Mobile Documents/com~apple~CloudDocs/Arc Export for Vanlife Map'
javascriptOutputFilePath = 'arcdata.js'

gpxFiles = os.listdir(gpxFolder)
gpxFiles.sort()

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
	
# decimal places to round to
roundAmount = 4
	
# create global lists
waypoints = []
tracksByType = {}

# loop through all of the GPX files
for gpxFile in gpxFiles:

	# skip .DS_Store
	if gpxFile == '.DS_Store' or gpxFile.endswith('.icloud'):
		continue
		
	print "processing " + gpxFile
	
	# parse the file
	gpxFileContents = open(gpxFolder + '/' + gpxFile, 'r')
	gpx = gpxpy.parse(gpxFileContents)
	
	# add to the global list
	for waypoint in gpx.waypoints:
	
		# skip if out of range
		if not dateTimeIsInRange(waypoint.time, dateTimeRanges):
			continue
			
		# add to the data structure
		waypoints.append(waypoint)
	
	for track in gpx.tracks:
		
		firstSegmentPoints = track.segments[0].points
		if 0 < len(firstSegmentPoints):
		
			firstPoint = firstSegmentPoints[0]
			firstPointDateTime = firstPoint.time
		
			# skip if out of range
			if not dateTimeIsInRange(firstPointDateTime, dateTimeRanges):
				continue
		else:
			# there are no segments, so it's not worth including
			continue
			
		# determine the track type
		trackType = track.type
		
		# override the track type for our map
		# ================================================================
		firstPoint = firstSegmentPoints[0]
		firstPointDateTime = firstPoint.time
		
		seattleBoatTrip = ['2019-05-13T16:00', '2019-05-17T14:20']
		delawareFerry = ['2019-06-15T11:30', '2019-06-15T13:04']
		
		seattleBoatTripTimes = [datetime.datetime.strptime(seattleBoatTrip[0], "%Y-%m-%dT%H:%M"), datetime.datetime.strptime(seattleBoatTrip[1], "%Y-%m-%dT%H:%M")]
		delawareFerryTimes = [datetime.datetime.strptime(delawareFerry[0], "%Y-%m-%dT%H:%M"), datetime.datetime.strptime(delawareFerry[1], "%Y-%m-%dT%H:%M")]
		
		isInSeattleBoatTrip = (firstPointDateTime >= seattleBoatTripTimes[0] and
								firstPointDateTime <= seattleBoatTripTimes[1])
		isInDelawareFerry = (firstPointDateTime >= delawareFerryTimes[0] and
								firstPointDateTime <= delawareFerryTimes[1])
		
		if isInSeattleBoatTrip or isInDelawareFerry:
			trackType = 'boat'
		else:
			trackType = 'car'
			
		# end override
		# ================================================================
		
		# add to the data structure
		if not trackType in tracksByType:
			tracksByType[trackType] = []
			
		tracksByType[trackType].append(track)
	
# make a list of all mapbox layers for waypoints
waypointsJSON = [{
	'coord': [
		round(x.longitude, roundAmount),
		round(x.latitude, roundAmount)
	],
	'name': x.name,
	'link': x.link,
} for i,x in enumerate(waypoints)]

# make a list of all mapbox layers for tracks
tracksJSON = []
keysSorted = sorted(tracksByType.keys())
for trackType in keysSorted:
	tracks = tracksByType[trackType]
	trackTypeArray = []
	
	for index, track in enumerate(tracks):
		for segment in track.segments:
		
			# skip if there aren't any points
			if not segment.points:
				continue
				
			pointsArray = [[
				round(point.longitude, roundAmount),
				round(point.latitude, roundAmount)
			] for point in segment.points]
			
			# remove duplicate adjoining points
			pointsArray = [k for k, g in itertools.groupby(pointsArray)]
			encodedPolyline = polyline.encode(pointsArray)
			
			trackTypeArray.append(encodedPolyline)

	# figure out the line color
	lineColor = {
		'boat': '#0098ff', # blue
		'car': '#504f50'   # gray
	}.get(trackType, '#000000')
	
	if lineColor == '#000000':
		print "encountered a transit type we don't support: ", trackType
		sys.exit(1)
			
	# append to the larger structure
	tracksJSON.append({
		'type': trackType,
		'lineColor':  lineColor,
		'segments': trackTypeArray,
	})
		
# print to the file
javascriptOutputFile = open(javascriptOutputFilePath, 'w+')

prettyPrint = False

javascriptOutputFile.write('const waypoints = ')
if prettyPrint:
	javascriptOutputFile.write(json.dumps(waypointsJSON, indent=4, separators=(',', ': ')))
else:
	javascriptOutputFile.write(json.dumps(waypointsJSON))
javascriptOutputFile.write(';')
javascriptOutputFile.write('\n')
javascriptOutputFile.write('\n')

javascriptOutputFile.write('const tracks = ')
if prettyPrint:
	javascriptOutputFile.write(json.dumps(tracksJSON, indent=4, separators=(',', ': ')))
else:
	javascriptOutputFile.write(json.dumps(tracksJSON))
javascriptOutputFile.write(';')
javascriptOutputFile.write('\n')

javascriptOutputFile.close()
