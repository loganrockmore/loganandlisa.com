#!/usr/bin/python

import datetime
import gpxpy
import itertools
import json
import polyline
import os
import urllib

dateRangesToInclude = [
	['2020-03-01T17:00'] # arrived in NYC on March 1, 2020
]

gpxFolder = '/Users/logan/Library/Mobile Documents/com~apple~CloudDocs/Arc Export for Vanlife Map'
javascriptOutputFilePath = 'arcdata.js'

mapboxAccessToken = 'pk.eyJ1IjoibG9nYW5yb2NrbW9yZSIsImEiOiJjamR0N2Nmc2EwODlsMnhsMzhhZjdqc2hxIn0.2b8odx5yDsbWAgYpGjJysw'

roundAmount = 6

gpxFiles = os.listdir(gpxFolder)
gpxFiles.sort()

def dateTimeIsInRange(dateTime, dateTimeRanges):
	for range in dateTimeRanges:
		if dateTime >= range[0] and dateTime <= range[1]:
			return True
	return False

def getDateTimeRangesArray():
	dateTimeRanges = []
	for dateRange in dateRangesToInclude:
		startDate = datetime.datetime.strptime(dateRange[0], "%Y-%m-%dT%H:%M")
		
		if len(dateRange) ==  2:
			endDate = datetime.datetime.strptime(dateRange[1], "%Y-%m-%dT%H:%M")
		else:
			endDate = datetime.datetime.now()
			
		dateTimeRanges.append([startDate, endDate])
	return dateTimeRanges
	
def getTracksByType():
	tracks = {}
	
	# loop through all of the GPX files
	for gpxFile in gpxFiles:
	
		# skip .DS_Store
		if gpxFile == '.DS_Store' or gpxFile.endswith('.icloud'):
			continue
			
		print "processing " + gpxFile
		
		# parse the file
		gpxFileContents = open(gpxFolder + '/' + gpxFile, 'r')
		gpx = gpxpy.parse(gpxFileContents)
		
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
			if not track.type in tracks:
				tracks[track.type] = []
				
			tracks[track.type].append(track)
			
	return tracks

def getEncodedPolylinesByType(tracksByType):
	returnObject = {}
	for trackType, tracks in tracksByType.items():
		
		polylinesArray = []
		
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
				
				polylinesArray.append(encodedPolyline)
		
		returnObject[trackType] = polylinesArray
				
	return returnObject
	
def getMapMatchedEncodedPolylinesByType(encodedPolylinesByType):
	returnObject = {}
	for trackType, encodedPolylines in encodedPolylinesByType.items():
		mapMatchEncodedPolylines = []
		for encodedPolyline in encodedPolylines:
			allPoints = polyline.decode(encodedPolyline)
			
			# the API limits each call to only 100 coordinates, so let's break it up
			limit = 100
			pointsChunked = [allPoints[i * limit:(i + 1) * limit] for i in range((len(allPoints) + limit - 1) // limit )]
			
			mapMatchedEncodedPolylines = []
			
			for points in pointsChunked:
				if len(points) == 1:
					# don't call the API to map match when it's just one point
					encodedPolyline = polyline.encode(points)
					mapMatchedEncodedPolylines.append(encodedPolyline)
					continue
				
				pointsJoinedIntoString = ';'.join(['%f,%f' % (point[0], point[1]) for point in points])
				url = 'https://api.mapbox.com/matching/v5/mapbox/%s/%s?geometries=geojson&access_token=%s' % (trackType, pointsJoinedIntoString, mapboxAccessToken)
				
				# call the API
				f = urllib.urlopen(url)
				contents = f.read()
				jsonContents = json.loads(contents)
				
				# save the polyline
				mapMatchedEncodedPolyline = None
				if jsonContents.has_key("matchings"):
					matchings = jsonContents["matchings"]
					if 0 < len(matchings):
						matching = matchings[-1]
						if matching.has_key("geometry"):
							geometry = matching["geometry"]
							coordinates = geometry["coordinates"]
							mapMatchedEncodedPolyline = polyline.encode(coordinates)
						else:
							print "+ no key geometry"
							print "   %s" % url
							print "   %s" % jsonContents
					else:
						print "+ no matchings"
						print "   %s" % url
						print "   %s" % jsonContents
				else:
					print "+ no key matchings"
					print "   %s" % url
					print "   %s" % jsonContents
					
				# use a non-map matched polyline if we can't get one
				if None == mapMatchedEncodedPolyline:
					mapMatchedEncodedPolyline = polyline.encode(points)
					
				mapMatchedEncodedPolylines.append(mapMatchedEncodedPolyline)
				
			mapMatchEncodedPolylines.append(mapMatchedEncodedPolylines)
		
		# flatten the encoded polylines
		mapMatchEncodedPolylines = [item for sublist in mapMatchEncodedPolylines for item in sublist]
		
		# save this object
		returnObject[trackType] = mapMatchEncodedPolylines
		
	return returnObject
	
def getPolylineFormattedObject(encodedPolylinesByType):
	returnObject = []
	for trackType, encodedPolylines in encodedPolylinesByType.items():
		
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
		returnObject.append({
			'type': trackType,
			'lineColor':  lineColor,
			'segments': encodedPolylines,
		})
	
	return returnObject

def outputJavascript(outputFilePath, jsonObject):
	# print to the file
	javascriptOutputFile = open(outputFilePath, 'w+')
	
	prettyPrint = False
	
	javascriptOutputFile.write('const tracks = ')
	if prettyPrint:
		javascriptOutputFile.write(json.dumps(jsonObject, indent=4, separators=(',', ': ')))
	else:
		javascriptOutputFile.write(json.dumps(jsonObject))
	javascriptOutputFile.write(';')
	javascriptOutputFile.write('\n')
	
	javascriptOutputFile.close()

# run everything
dateTimeRanges = getDateTimeRangesArray()
tracksByType = getTracksByType()
encodedPolylinesByType = getEncodedPolylinesByType(tracksByType)
walkingPolylinesByType = {'walking': encodedPolylinesByType['walking']}
# mapMatchedEncodedPolylinesByType = getMapMatchedEncodedPolylinesByType(walkingPolylinesByType)
formattedObject = getPolylineFormattedObject(walkingPolylinesByType)
outputJavascript(javascriptOutputFilePath, formattedObject)
