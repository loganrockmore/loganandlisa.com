#!/usr/bin/python

import datetime
import gpxpy
import json
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
	
# create global lists
waypoints = []
tracks = []

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
	tracks.extend(gpx.tracks)
	
# make a list of all mapbox layers for waypoints
waypointsJSON = [{
	'coord': [x.longitude, x.latitude],
} for i,x in enumerate(waypoints)]

# make a list of all mapbox layers for tracks
tracksJSON = []
for index, track in enumerate(tracks):

	# determine the line colopr
	lineColor = {
		'airplane': '#0000FF',
		'car': '#FF0000',
		'walking': '#00FF00',
	}.get(track.type, '#000000')
	
	# print the object
	for segment in track.segments:
	
		# skip if there aren't any points
		if not segment.points:
			continue
			
		pointsJSON = [[
			point.longitude,
			point.latitude
		] for point in segment.points]
			
		tracksJSON.append({
			'id': 'route-' + str(index),
			'type': 'line',
			'source': {
				'type': 'geojson',
				'data': {
					'type': 'Feature',
					'geometry': {
						'coordinates': pointsJSON,
						'type': 'LineString'
					}
				},
			},
			'layout': {
			    'line-join': 'round',
			    'line-cap': 'round'
			},
			'paint': {
			    'line-color': lineColor,
			    'line-width': 2
			}
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
