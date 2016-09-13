#------------------------------------------------------------------------------
# Name:        getAccidents
# Purpose:     Calculate the Accidents results
#
# Author:      Arie Claassens
#
# Created:     11-07-2016
# Copyright:   (c) Arie Claassens 2016
# License:     GNU GPL. View the LICENSE file.
#------------------------------------------------------------------------------

"""
Get the count of Accidents within a predefined radius and assign a weight
based on the count:
0 features within radius = 0
1 feature within radius = 1
2 features within radius = 2
2+ features within radius = 3
"""

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
# Adapted from http://gis.stackexchange.com/questions/135920/arcpy-logging-error-messages
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
            arcpy.AddError(type(inst))
            arcpy.AddError(arcpy.GetMessages())
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

def get_projection(featureclass):
    """
    Find and return the full spatial reference of a feature class
    """
    description = arcpy.Describe(featureclass)
    # Export the full text string to ensure a 100% match, preventing
    # discrepancies with differing central meridians, for example.
    proj = description.SpatialReference.exporttostring()
    return proj

def compare_list_items(checklist):
    """
    Loop through the list and compare the items to determine if any item
    is a mismatch with the first item in the list. Used to check for spatial
    reference mismatches between feature classes.
    """
    mismatch = False # Local variable to store match results
    check = '' # Local variable to store the spatial projection
    for item in checklist:
        LOGGER.debug("Processing %s" % item)
        if check == '': # Nothing captured yet, use the first item as base
            check = item
            LOGGER.debug("The check is now %s" % item)
        else:
            # Test if they match
            if check == item:
                LOGGER.debug("The items match. Continue testing")
            else:
                mismatch = True
                LOGGER.debug("The check and current item mismatch")
                break # Break out of the for loop. no further testing needed

    LOGGER.info("Is there a spatial reference mismatch? " + str(mismatch))
    if mismatch:
        LOGGER.critical("Spatial reference mismatch detected.")
    else:
        LOGGER.info("Spatial references of all the feature classes match.")

    return mismatch

# Global variables
# User Input parameters
LOGLEVEL = str(arcpy.GetParameterAsText(0)).upper()
LOGDIR = arcpy.GetParameterAsText(1)
CHECK_PROJ = arcpy.GetParameterAsText(2) # Boolean result received as text
TARGET_FC = arcpy.GetParameterAsText(3)
ACC_FC1 = arcpy.GetParameterAsText(4)
ACC_FC2 = arcpy.GetParameterAsText(5)
BUFFER_DIST = arcpy.GetParameterAsText(6) # buffer distance in meters
UPDATE_ONLY = arcpy.GetParameterAsText(7) # Boolean result received as text

# Tool Parameters
arcpy.env.addOutputsToMap = False
getcontext().prec = 4 # Set decimal precision
REQUIRED_FIELD = "ACCIDENTS" # Which field must we filter on and check for?
ACCIDENTS_LIST = [] # Empty list that will store the feature classes to process
ACCIDENTSLIST_FEATLAYER = [] # Empty list that will store feature layers
# Append the Meters required for the buffer distance parameter
BUFFER_DISTM = BUFFER_DIST + " Meters"
COUNTER = 0

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
LOGSTAMP = "AddAccidents" # Identifies the source of the log entries
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

# Define the query filter
# Should we only update or process all records? True if selected by the user
if not UPDATE_ONLY:
    QRY_FILTER = REQUIRED_FIELD + " IS NOT NULL"
else:
    QRY_FILTER = ""
LOGGER.debug("QRY_FILTER is: " + QRY_FILTER)

# Put everything in a try/finally statement, so that we can close the logger
# even if the script bombs out or we raise an execution error along the line
try:
    # Sanity checks:

    # Check if the target feature class has any features before we start
    if int(arcpy.GetCount_management(TARGET_FC)[0]) == 0:
        LOGGER.error("{0} has no features. Please use a feature class that \
                      already contains the required features and attributes." \
                      .format(TARGET_FC))
        raise arcpy.ExecuteError

    # Check if the target feature class has the required attribute field.
    if not fieldexist(TARGET_FC, REQUIRED_FIELD):
        LOGGER.error("The field "+ REQUIRED_FIELD +" does not exist. \
                         Please use the correct Hazard feature class.")
        raise arcpy.ExecuteError

    #Build the list with the feature classes that will be used
    # We need at least one FC to work with; check first if it has any content
    if int(arcpy.GetCount_management(ACC_FC1)[0]) == 0:
        LOGGER.error("{0} has no features. Please use a feature class that \
                       contains data.".format(ACC_FC1))
        raise arcpy.ExecuteError
    else:
        ACCIDENTS_LIST.append(ACC_FC1)

    #First check if FC2 was passed in to the script before we check if it is empty
    if len(ACC_FC2) > 1:
        if int(arcpy.GetCount_management(ACC_FC2)[0]) == 0:
            LOGGER.error("{0} has no features. Please use a feature class that \
                           contains data.".format(ACC_FC2))
            raise arcpy.ExecuteError
        else:
            ACCIDENTS_LIST.append(ACC_FC2)

    # Compare the spatial references of the input data sets, unless the user
    # actively chooses not to do so.
    LOGGER.info("Check for spatial reference mismatches? : " + CHECK_PROJ)
    if CHECK_PROJ == 'true':
        #LOGGER.info(TARGET_FC)
        LIST_FC = [] # Emtpy list to store FC
        # Add spatial references of all items
        LIST_FC.append(get_projection(TARGET_FC))
        LIST_FC.append(get_projection(ACC_FC1))
        if len(ACC_FC2) > 1:
            LIST_FC.append(get_projection(ACC_FC2))
        LOGGER.debug("The list of spatial references to check is:")
        LOGGER.debug(LIST_FC)
        LOGGER.info("Comparing spatial references of the data sets")
        # Check for mismatching spatial references
        MISMATCHED = compare_list_items(LIST_FC)
        if MISMATCHED:
            # Terminate the main thread
            # See https://docs.python.org/2/library/sys.html#sys.exit
            sys.exit(0)

    # Determine if we are working with a POINT or POLYGON shape type and adjust
    # the fields list to use the inside centroid X and Y fields added in the
    # first step, i.e. INSIDE_X and INSIDE_Y
    FC_DESC = arcpy.Describe(TARGET_FC)
    if FC_DESC.shapeType == "Point":
        LOGGER.info("POINT feature class detected. Proceeding.")
        FIELDLIST = ['OBJECTID', 'SHAPE@X', 'SHAPE@Y', REQUIRED_FIELD]
    elif FC_DESC.shapeType == "Polygon":
        LOGGER.info("POLYGON feature class detected. Proceeding.")
        FIELDLIST = ['OBJECTID', 'INSIDE_X', 'INSIDE_Y', REQUIRED_FIELD]
    else:
        LOGGER.error("Unsupported shape type detected. Please use a \
    feature class with a POINT or POLYGON shape type")
        raise arcpy.ExecuteError

    arcpy.AddMessage("Starting with Accidents Proximity Analysis")
    START_TIME = time.time()

    arcpy.MakeFeatureLayer_management(TARGET_FC, "inputHazard", QRY_FILTER)
    RECORD_COUNT = int(arcpy.GetCount_management("inputHazard").getOutput(0))
    #arcpy.AddMessage("Total number of features: " + str(RECORD_COUNT))

    #Create feature layers out of Infrastructure FC
    LIST_COUNT = 0
    for item in ACCIDENTS_LIST:
        LIST_COUNT += 1
        # Dynamically generate a name for the Feature layer
        itemFlayerName = "Flayer_" + str(LIST_COUNT)
        #arcpy.AddMessage("Adding Feature Layer: " + itemFlayerName)
        arcpy.MakeFeatureLayer_management(item, itemFlayerName)
        ACCIDENTSLIST_FEATLAYER.append(itemFlayerName)
        #arcpy.AddMessage(listInfraFeatLayer)

    arcpy.AddMessage("Starting with the Features' processing....")

    with arcpy.da.UpdateCursor(TARGET_FC, ['OBJECTID', 'ACCIDENTS',
                                           'ACCIDENTS_BUFFER_DIST'],
                               FILTER_QUERY) as cursor:
        for row in cursor:
            #Loop through Hazard FC
            COUNTER += 1
            # https://docs.python.org/2.7/library/decimal.html
            pctDone = Decimal(COUNTER)/Decimal(RECORD_COUNT) * 100
            arcpy.AddMessage("Processing OID " + str(row[0]) +
                             ", with ACCIDENTS grading of " + str(row[1]) +
                             ". Feature " + str(COUNTER) + " of " +
                             str(RECORD_COUNT) + " or " + str(pctDone) + " %")

            # Now loop over items in Infrastructure list and tally up the total
            # after parsing all of them
            # Select the current feature from original Hazard FC
            arcpy.SelectLayerByAttribute_management("inputHazard",
                                                    "NEW_SELECTION",
                                                    "OBJECTID = " + str(row[0]))

            # Initialise the COUNTER, with its local scope, to zero
            totAccidents = 0
            # Now loop through INFRASTRUCTURE feature layers and get the intersection
            for fc in ACCIDENTSLIST_FEATLAYER:
                #arcpy.AddMessage("Now processing Feature Layer : " + fc)
                # Takes longer due to the buffering done as part of each query.
                # But faster than clipping source and using that.
                # Less risk of losing or modding data too.
                outputAcc = arcpy.SelectLayerByLocation_management(fc,
                                                                   "WITHIN_A_DISTANCE_GEODESIC",
                                                                   "inputHazard",
                                                                   BUFFER_DISTM,
                                                                   "")
                # Count the rows and add it to the COUNTER
                # The RECORD_COUNT2 method produces way larger results, e.g. 13
                # versus the 1 reported by looping through the rows.
                #RECORD_COUNT2 = int(arcpy.GetCount_management(outputInfrastructure).getOutput(0))
                #arcpy.AddMessage("RECORD_COUNT2 is: " +  str(RECORD_COUNT2))
                for row2 in outputAcc:
                    # arcpy.AddMessage OIDs of selected features
                    #arcpy.AddMessage(row2.getSelectionSet())
                    #arcpy.AddMessage("\tRunning the row2 inside loop")
                    totAccidents += 1
                    # http://desktop.arcgis.com/en/arcmap/10.3/analyze/arcpy-data-access/featureclasstonumpyarray.htm
                    #arr = arcpy.da.FeatureClassToNumPyArray(row2, "OID@",skip_nulls=True) # Should we do the skip_nulls?
                    #arcpy.AddMessage("Total Accidents in radius: " + str(arr["OID@"].sum()))
                    #totPop = arr["grid_code"].sum()

                #arcpy.AddMessage("ROW totAccidents is: " + str(totAccidents))

            # Update the row with the population sum
            #arcpy.AddMessage("totAccidents is: "+ str(totAccidents))
            # Cast to integer to ensure we deal with integer values
            totAccidents = int(totAccidents)

            # Calculate the grading. A case statement would have worked nicely. Thanks Python!
            if totAccidents == 0:
                gradeAccidents = 0
            elif totAccidents == 1:
                gradeAccidents = 1
            elif totAccidents == 2:
                gradeAccidents = 2
            else:
                gradeAccidents = 3

            arcpy.AddMessage("Accidents grading: " + str(gradeAccidents))
            # Assign the new value to the Accidents field
            row[1] = gradeAccidents
            # Assign the buffer distance to the Accidents buffer distance field
            row[2] = BUFFER_DIST
            cursor.updateRow(row)

    STOP_TIME = time.time()
    arcpy.AddMessage("Total execution time in seconds = " +
                     str(int(STOP_TIME-START_TIME)) + " and in minutes = " +
                     str(int(STOP_TIME-START_TIME)/60))

finally:
    # Shut down logging after script has finished running.
    #http://stackoverflow.com/questions/24816456/python-logging-wont-shutdown
    LOGGER.debug("------- STOP LOGGING-----------")
    LOGGER.removeHandler(HANDLER)
    HANDLER.close()
    logging.shutdown()

