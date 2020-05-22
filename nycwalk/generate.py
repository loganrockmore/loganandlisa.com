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
allTracksJSON = getPolylineFormattedObject(encodedPolylinesByType)
walkingTracksJSON = [trackJSON for trackJSON in allTracksJSON if trackJSON['type'] == 'walking']
outputJavascript(javascriptOutputFilePath, walkingTracksJSON)
