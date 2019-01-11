#!/usr/bin/python

import datetime
import gpxpy
import itertools
import json
import polyline
import os

dateRangesToInclude = [
	['2018-07-29', '2018-08-19'],
	# burning man
	['2018-09-03', '2018-10-14'],
	# seattle wedding
	['2018-10-31', '2018-11-09'],
	# orlando trip
	['2018-11-18', '2018-11-18'],
	# la crosse wedding
	['2018-11-26', '2018-12-20'],
	# christmas and la crosse trip
]

gpxFolder = '/Users/logan/Downloads/Arc Monthly Export'
javascriptOutputFilePath = 'arcdata.js'

gpxFiles = os.listdir(gpxFolder)
gpxFiles.sort()

# create the list of specific dates to exclude
datesToInclude = []
for dateRange in dateRangesToInclude:
	startDate = datetime.datetime.strptime(dateRange[0], "%Y-%m-%d").date()
	endDate = datetime.datetime.strptime(dateRange[1], "%Y-%m-%d").date()
	
	delta = endDate - startDate
	for i in range(delta.days + 1):
		dateToInclude = startDate + datetime.timedelta(i)
		datesToInclude.append(dateToInclude)
		
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
	
		# skip waypoints not in the dates to include
		if waypoint.time.date() not in datesToInclude:
			continue
			
		# add to the data structure
		waypoints.append(waypoint)
	
	for track in gpx.tracks:
		
		# skip certain tracks in certain days
		firstSegmentPoints = track.segments[0].points
		if 0 < len(firstSegmentPoints):
		
			firstPoint = firstSegmentPoints[0]
			firstPointDate = firstPoint.time.date()
		
			# skip tracks not in the dates to include
			if firstPointDate not in datesToInclude:
				continue
				
			# this is the very first day of #vanlife. skip everything until we start driving
			if firstPointDate == datetime.datetime.strptime('2018-07-29', '%Y-%m-%d').date():
				afterDate = '2018-07-29T15:01:31'
				if firstPoint.time < datetime.datetime.strptime(afterDate, '%Y-%m-%dT%H:%M:%S'):
					continue
		
			# this is the last day of the Orlando trip. skip everything until we start driving
			if firstPointDate == datetime.datetime.strptime('2018-11-18', '%Y-%m-%d').date():
				afterDate = '2018-11-18T17:01:55'
				if firstPoint.time < datetime.datetime.strptime(afterDate, '%Y-%m-%dT%H:%M:%S'):
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
		'airplane': '#0000FF',
		'car': '#FF0000',
		'walking': '#00FF00',
	}.get(trackType, '#FF0000') # TEMP: make unknown segments red
			
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
