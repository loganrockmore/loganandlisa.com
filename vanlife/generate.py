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
]

gpxFolder = '/Users/logan/Downloads/Arc Monthly Export'
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
		
		# add to the data structure
		if not track.type in tracksByType:
			tracksByType[track.type] = []
			
		tracksByType[track.type].append(track)
	
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
for trackType, tracks in tracksByType.items():
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
		'airplane': '#9128DD',
		'boat': '#4973E8',
		'car': '#FF5E4A',
		'cycling': '#4C23E8',
		'walking': '#5CBA8C',
	}.get(trackType, '#FF5E4A') # TODO: figure out what's going on here; until then, assume it's a car
	
	if lineColor == '#000000':
		print "here's a transport type we don't support: ", trackType
			
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
