#------------------------------------------------------------------------------
# Name:        calc_score
# Purpose:     Calculate the priority ranking and MCDA Weighted Score
#
# Author:      Arie Claassens
#
# Created:     11-07-2016
# Copyright:   (c) Arie Claassens 2016
# License:     GNU GPL. View the LICENSE file.
#------------------------------------------------------------------------------

"""
Calculate the unweighted and weighted score of each feature, based on the
value assigned to each location factor and the relative weight assigned
by the user to each factor.
"""

#
# Move the RANK calculation to a separate script, so that we can display the
# score statistics to the user?
# Or keep settings in a configuration file, which the user can edit? Put all
# classification breaks in there.

# Copy SOURCE_FC to TARGET_FC and run calculations on TARGET_FC, so we can repeat
# the process with new values, keeping the SOURCE_FC intact.


#Import libraries
import sys # required for the sys.exit() call to halt the script
import logging
import logging.handlers
#from datetime import datetime, date
import time # For timing purposes
from decimal import Decimal, getcontext #For progress COUNTER
# https://arcpy.wordpress.com/2012/07/02/retrieving-total-counts/
#import collections
import arcpy


# Functions and classes
# Adapted from:
# http://gis.stackexchange.com/questions/135920/arcpy-logging-error-messages
class ArcPyLogHandler(logging.handlers.RotatingFileHandler):
	"""
	Custom logging class that bounces messages to the arcpy tool window and
	reflects back to the log file.
	"""
	def emit(self, record):
		"""
		Write the log message to the tool output window (stdout) and log file.
		"""
		try:
			msg = record.msg.format(record.args)
		#except:
		except Exception as inst:
			# Log the exception type and all error messages returned
			LOGGER.error(type(inst))
			LOGGER.error(arcpy.GetMessages())
			msg = record.msg

		if record.levelno >= logging.ERROR:
			arcpy.AddError(msg)
		elif record.levelno >= logging.WARNING:
			arcpy.AddWarning(msg)
		elif record.levelno >= logging.INFO:
			arcpy.AddMessage(msg)

		super(ArcPyLogHandler, self).emit(record)

# Adapted from:
# http://bjorn.kuiper.nu/2011/04/21/tips-tricks-fieldexists-for-arcgis-10-python
def fieldexist(featureclass, fieldname):
	"""
	Test for the existence of fieldname in featureclass. Returns True if the
	field exists and False if it does not.
	"""
	fieldlist = arcpy.ListFields(featureclass, fieldname)
	fieldcount = len(fieldlist)
	return bool(fieldcount == 1)

def check_weights_same(weightslist):
	"""
	Check for at least four unique weights assigned to the full list of factors.
	Convert the list of factor weights to a set and back to a list and then
	check the number of list items.
	Ensures that the user does not assign the same value to all factors.
	"""
	privateset = set(weightslist)
	uniquelist = list(privateset)
	if len(uniquelist) > 4:
		LOGGER.debug("Length of the unique values list: {0}".format(len(uniquelist)))
		return True
	else:
		LOGGER.error("Length of the unique values list: {0}".format(len(uniquelist)))
		return False

# SDSS priority calculation formulas
def landcover_calc(landcovervalue):
	"""
	Calculate the classification of the land cover parameter based on the
	land cover key recorded for this feature.
	"""
	if landcovervalue == 200:
		landcover = 1
	else:
		landcover = 3
	return landcover

def aspect_calc(aspectvalue):
	"""
	Calculate the classification of the aspect parameter based on the value
	of the aspect recorded for this feature.
	"""
	if aspectvalue < 0:
		asp = 0
	elif aspectvalue == 0 and aspectvalue < 22.6:
		asp = 3
	elif aspectvalue > 22.5 and aspectvalue < 67.6:
		asp = 2
	elif aspectvalue > 67.5 and aspectvalue < 112.6:
		asp = 1
	elif aspectvalue > 112.5 and aspectvalue < 157.6:
		asp = 0
	elif aspectvalue > 157.5 and aspectvalue < 202.6:
		asp = 0
	elif aspectvalue > 202.5 and aspectvalue < 247.6:
		asp = 0
	elif aspectvalue > 247.5 and aspectvalue < 292.6:
		asp = 0
	elif aspectvalue > 292.5 and aspectvalue < 337.6:
		asp = 2
	else:
		asp = 3
	return asp

def infrastructure_calc(infracount):
	"""
	Calculate the classification of the infrastructure parameter based on the
	number of infrastructure features located near this feature.
	"""
	if infracount == 0:
		infra = 0
	elif infracount == 1:
		infra = 1
	elif infracount == 2:
		infra = 2
	else:
		infra = 3
	return infra

def keyfeatures_calc(keyfeatcount):
	"""
	Calculate the classification of the key features parameter based on the
	number of key features located near this feature.
	"""
	if keyfeatcount == 0:
		keyfeature = 0
	elif keyfeatcount == 1:
		keyfeature = 1
	elif keyfeatcount == 2:
		keyfeature = 2
	else:
		keyfeature = 3
	return keyfeature

def accidents_calc(accidentcount):
	"""
	Calculate the classification of the accidents parameter based on the number
	of accidents recorded for this feature.
	"""
	if accidentcount == 0:
		acc = 0
	elif accidentcount == 1:
		acc = 1
	elif accidentcount == 2:
		acc = 2
	else:
		acc = 3
	return acc

def poi_calc(poicount):
	"""
	Calculate the classification of the POI parameter based on the number of
	points of interest located near this feature.
	"""
	if poicount == 0:
		poi = 0
	elif poicount == 1:
		poi = 1
	elif poicount == 2:
		poi = 2
	else:
		poi = 3
	return poi

def rivers_calc(rivercount):
	"""
	Calculate the classification of the rivers/water basins parameter based on
	the number of river/water basin features located near this feature.
	"""
	if rivercount == 0:
		rivers = 0
	elif rivercount == 1:
		rivers = 1
	elif rivercount == 2:
		rivers = 2
	else:
		rivers = 3
	return rivers

def slope_calc(slopevalue):
	"""
	Calculate the classification of the slope parameter based on the value of
	the slope recorded for this feature.
	"""
	if slopevalue == 0:
		slp = 0
	elif slopevalue > 15:
		slp = 1
	elif slopevalue > 10 and slopevalue < 15:
		slp = 2
	else:
		slp = 3
	return slp

def population_calc(populationcount):
	"""
	Calculate the classification of the population parameter based on the
	total population located near this feature.
	"""
	if populationcount == 0:
		pop = 0
	elif populationcount > 0 and populationcount < 51:
		pop = 1
	elif populationcount > 50 and populationcount < 101:
		pop = 2
	else:
		pop = 3
	return pop

# Accept user input to define the break points
def sdss_priority_calc(score):
	"""
	Calculate the overall priority of the feature based on the total score of
	the unweighted factor values calculated for this feature.
	"""
	if score < LOWSCORE_BREAKPOINT:
		sdss_priority = "Low"
	elif score >= LOWSCORE_BREAKPOINT and score < MEDIUMSCORE_BREAKPOINT:
		sdss_priority = "Medium"
	else:
		sdss_priority = "High"
	return sdss_priority


# Global variables
# User Input parameters
LOGLEVEL = str(arcpy.GetParameterAsText(0)).upper()
LOGDIR = arcpy.GetParameterAsText(1)
SOURCE_FC = arcpy.GetParameterAsText(2) # Source of DHA polygons with their factor results
TARGET_FC = arcpy.GetParameterAsText(3) # New FC to create with the user's input
# need to create a table with the settings used to create the TARGET_FC?
LOWSCORE_BREAKPOINT = int(arcpy.GetParameterAsText(4))  # Defines the low score breakpoint
MEDIUMSCORE_BREAKPOINT = int(arcpy.GetParameterAsText(5)) # Defines the Medium score breakpoint
BAREAREA_CODE = int(arcpy.GetParameterAsText(6)) # Defines the bare area land cover code
LANDCOVER_WEIGHT = int(arcpy.GetParameterAsText(7))
ASPECT_WEIGHT = int(arcpy.GetParameterAsText(8))
INFRASTRUCTURE_WEIGHT = int(arcpy.GetParameterAsText(9))
KEYFEATURES_WEIGHT = int(arcpy.GetParameterAsText(10))
ACCIDENTS_WEIGHT = int(arcpy.GetParameterAsText(11))
POI_WEIGHT = int(arcpy.GetParameterAsText(12))
RIVERS_WEIGHT = int(arcpy.GetParameterAsText(13))
SLOPE_WEIGHT = int(arcpy.GetParameterAsText(14))
POPULATION_WEIGHT = int(arcpy.GetParameterAsText(15))

arcpy.env.addOutputsToMap = False # Set this with user input?
getcontext().prec = 4 # Set decimal precision
REQUIRED_FIELDS = ['LANDCOVER', 'ASPECT', 'INFRASTRUCTURE', 'KEYFEATURES',
				   'ACCIDENTS', 'POI', 'RIVERS', 'SLOPE', 'POPULATION',
				   'SCORE', 'RANKING', 'LANDCOVERWEIGHT', 'ASPECTWEIGHT',
				   'INFRASTRUCTUREWEIGHT', 'KEYFEATURESWEIGHT',
				   'ACCIDENTSWEIGHT', 'POIWEIGHT', 'RIVERSWEIGHT',
				   'SLOPEWEIGHT', 'POPULATIONWEIGHT', 'WEIGHTEDSCORE']

# Tool configuration:
# Set up the logging parameters and inform the user
DATE_STRING = time.strftime("%Y%m%d")
LOGFILE = unicode(LOGDIR + '\\'+ DATE_STRING +
				  '_mcdatool.log').encode('unicode-escape')
MAXBYTES = 2097152 # 2MB
BACKUPCOUNT = 10
# Change this variable to a unique identifier for each script it runs in.
# Cannot use LOGGER.findCaller(), as we're calling from an embedded script in
# the Python toolbox.
LOGSTAMP = "CalcScore" # Identifies the source of the log entries
LOGGER = logging.getLogger(LOGSTAMP)
HANDLER = ArcPyLogHandler(LOGFILE, MAXBYTES, BACKUPCOUNT)
FORMATTER = logging.Formatter("%(asctime)s %(name)-15s %(levelname)-8s %(message)s")
HANDLER.setFormatter(FORMATTER)
LOGGER.addHandler(HANDLER)
LOGGER.setLevel(LOGLEVEL)
LOGGER.debug("------- START LOGGING-----------")
# Use the default arcpy.AddMessage method to only show this in the tool output
# window, otherwise we will log it to the log file too.
arcpy.AddMessage("Your Log file is: " + LOGFILE)

# Put everything in a try/finally statement, so that we can close the logger
# even if the script bombs out or we raise an execution error along the line
try:
	# Sanity checks:

	# Check if the weights are not all the same value
	weightlist = [LANDCOVER_WEIGHT, ASPECT_WEIGHT, INFRASTRUCTURE_WEIGHT,
				  KEYFEATURES_WEIGHT, ACCIDENTS_WEIGHT, POI_WEIGHT,
				  RIVERS_WEIGHT, SLOPE_WEIGHT, POPULATION_WEIGHT]

	if check_weights_same(weightlist):
		LOGGER.debug("The weights do not all match")
	else:
		LOGGER.error("Please assign at least four different factor weights.")
		raise arcpy.ExecuteError

	# Check if the source feature class has the required attribute fields.
	for checkfield in REQUIRED_FIELDS:
		if not fieldexist(SOURCE_FC, checkfield):
			LOGGER.debug("Check for field: " + checkfield)
			LOGGER.error("The field "+ checkfield +" does not exist.")
			raise arcpy.ExecuteError

	# Adjust the fields list to include the Object ID and Shape data
	LOGGER.info("Adding OBJECTID to REQUIRED_FIELDS")
	# Insert the fields at the start of the list to obtain the required
	# field ordering
	REQUIRED_FIELDS.insert(0,'OBJECTID')
	FIELDLIST = REQUIRED_FIELDS

	# We need data to work with, so let's check first if it has any content
	if int(arcpy.GetCount_management(SOURCE_FC)[0]) == 0:
		LOGGER.error("{0} has no features. Please use a feature class \
					   that contains data.".format(SOURCE_FC))
		raise arcpy.ExecuteError

	# Get the total number of records
	RECORD_COUNT = int(arcpy.GetCount_management(SOURCE_FC).getOutput(0))
	COUNTER = 0
	LOGGER.info("Total number of hazard features: " + str(RECORD_COUNT))

	LOGGER.info("Starting with the SDSS Rating Analysis")
	START_TIME = time.time()

	LOGGER.debug("Copying the Source FC to its new location")
	arcpy.Copy_management(SOURCE_FC, TARGET_FC)

	LOGGER.debug("Starting the processing of the Target FC")

	with arcpy.da.UpdateCursor(TARGET_FC, FIELDLIST) as cursor:
		 #Loop through Hazard FC
		for row in cursor:
			# Display progress information
			COUNTER += 1
			# See https://docs.python.org/2.7/library/decimal.html
			pctDone = Decimal(COUNTER)/Decimal(RECORD_COUNT) * 100
			LOGGER.info("Processing OID " + str(row[0]) + ", with SCORE of "+
						str(row[10]) + ". " + str(COUNTER) + " of " +
						str(RECORD_COUNT) + " or " + str(pctDone) + " %")
			#Land Cover Grade
			gradeLandcover = landcover_calc(row[1])
			LOGGER.debug("Land Cover grading: " + str(gradeLandcover))
			#Aspect Grade
			gradeAspect = aspect_calc(row[2])
			LOGGER.debug("Aspect grading: " + str(gradeAspect))
			#Infrastructure Grade
			gradeInfrastructure = infrastructure_calc(row[3])
			LOGGER.debug("Infrastructure grading: " + str(gradeInfrastructure))
			#Key Features
			gradeKeyFeatures = keyfeatures_calc(row[4])
			LOGGER.debug("Key Features grading: " + str(gradeKeyFeatures))
			#Accidents
			gradeAccidents = accidents_calc(row[5])
			LOGGER.debug("Accidents grading: " + str(gradeAccidents))
			#POI
			gradePOI = poi_calc(row[6])
			LOGGER.debug("POI grading: " + str(gradePOI))
			#Rivers
			gradeRivers = rivers_calc(row[7])
			LOGGER.debug("Rivers grading: " + str(gradeRivers))
			#Slope
			gradeSlope = slope_calc(row[8])
			LOGGER.debug("Slope grading: " + str(gradeSlope))
			#Population affected
			gradePopulation = population_calc(row[9])
			LOGGER.debug("Population grading: " + str(gradePopulation))
			#Final Score and Ranking Calculation
			finalScore = (gradeLandcover + gradeAspect + gradeInfrastructure +
						  gradeKeyFeatures + gradeAccidents + gradePOI +
						  gradeRivers + gradeSlope + gradePopulation)
			finalRanking = sdss_priority_calc(finalScore)
			LOGGER.info("The final score is: " + str(finalScore) +
						", and the final ranking is: " + str(finalRanking))
			# Assign the new values to the SCORE and RANKING fields
			LOGGER.debug("Updating the row with the SCORE and RANKING values")
			row[10] = finalScore
			row[11] = finalRanking
			# Assign the weights values supplied for all the factors
			LOGGER.debug("Adding the WEIGHTS and WEIGHTED SCORE values")
			row[12] = LANDCOVER_WEIGHT
			row[13] = ASPECT_WEIGHT
			row[14] = INFRASTRUCTURE_WEIGHT
			row[15] = KEYFEATURES_WEIGHT
			row[16] = ACCIDENTS_WEIGHT
			row[17] = POI_WEIGHT
			row[18] = RIVERS_WEIGHT
			row[19] = SLOPE_WEIGHT
			row[20] = POPULATION_WEIGHT
			#Weighted Land cover
			wLandCover = gradeLandcover * LANDCOVER_WEIGHT
			#Weighted Aspect
			wAspect = gradeAspect * ASPECT_WEIGHT
			#Weighted Infrastructure
			wInfrastructure = gradeInfrastructure * INFRASTRUCTURE_WEIGHT
			#Weighted Key Features
			wKeyFeatures = gradeKeyFeatures * KEYFEATURES_WEIGHT
			#Weighted Accidents
			wAccidents = gradeAccidents * ACCIDENTS_WEIGHT
			#Weighted POI
			wPOI = gradePOI * POI_WEIGHT
			#Weighted Rivers / Water Basins
			wRivers = gradeRivers * RIVERS_WEIGHT
			#Weighted Slope
			wSlope = gradeSlope * SLOPE_WEIGHT
			#Weighted Population Potentially Affected
			wPop = gradePopulation * POPULATION_WEIGHT
			#Calculate Weighted Score by adding weighted aspect values
			weigthedScore = (wLandCover + wAspect + wInfrastructure +
							 wKeyFeatures + wAccidents + wPOI + wRivers +
							 wSlope + wPop)
			LOGGER.info("The weighted score is: "+ str(weigthedScore))
			# Assign the Weighted Score
			row[21] = weigthedScore
			# Update the row
			cursor.updateRow(row)
	STOP_TIME = time.time()
	LOGGER.info("Total execution time in seconds = " +
				str(int(STOP_TIME-START_TIME)) + " and in minutes = " +
				str(int(STOP_TIME-START_TIME)/60))

finally:
	# Shut down logging after script has finished running.
	#http://stackoverflow.com/questions/24816456/python-logging-wont-shutdown
	LOGGER.debug("------- STOP LOGGING-----------")
	LOGGER.removeHandler(HANDLER)
	HANDLER.close()
	logging.shutdown()
