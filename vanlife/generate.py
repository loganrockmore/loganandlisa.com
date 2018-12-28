#!/usr/bin/python

import datetime
import gpxpy
import itertools
import json
import polyline
import os

dateRangesToInclude = [
	['2018-09-14', '2018-10-14'],
	['2018-10-31', '2018-11-09'],
	['2018-11-26', '2018-12-20'],
]

gpxFolder = '/Users/logan/Library/Mobile Documents/iCloud~com~bigpaua~LearnerCoacher/Documents/Export/GPX'
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
		datesToInclude.append(datetime.date.strftime(dateToInclude, "%Y-%m-%d"))
		
# decimal places to round to
roundAmount = 2
	
# create global lists
waypoints = []
tracksByType = {}

# loop through all of the GPX files
for gpxFile in gpxFiles:
	
	# skip this file, if specified
	gpxFileDatePrefix = gpxFile[:10]
	if gpxFileDatePrefix not in datesToInclude:
		continue
		
	# parse the file
	gpxFileContents = open(gpxFolder + '/' + gpxFile, 'r')
	gpx = gpxpy.parse(gpxFileContents)
	
	# add to the global list
	waypoints.extend(gpx.waypoints)
	
	for track in gpx.tracks:
		
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
trackPointsByType = {}
for trackType, tracks in tracksByType.items():
	trackPointsByType[trackType] = []
	
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
			
			trackPointsByType[trackType].extend(pointsArray)
		
tracksJSON = []
for trackType, trackPoints in trackPointsByType.items():

	lineColor = {
		'airplane': '#0000FF',
		'car': '#FF0000',
		'walking': '#00FF00',
	}.get(trackType, '#000000')

	tracksJSON.append({
		'polyline': polyline.encode(trackPoints),
		'lineColor':  lineColor,
		'type': trackType,
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
