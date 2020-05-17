#!/usr/bin/python

import datetime
import gpxpy
import itertools
import json
import polyline
import os

dateRangesToInclude = [
	['2020-03-01T17:00', '2020-03-12T15:00'],
	# phoenix trip
	['2020-03-16T13:00', '2020-03-24T11:00'],
	# costco run
	['2020-03-24T15:00', '2020-05-16T11:00'],
	# long island trip
	['2020-05-16T17:00'],
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
roundAmount = 6
	
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
	
	# only do walking
	if trackType != 'walking':
		continue
	
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
