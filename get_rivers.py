#------------------------------------------------------------------------------
# Name:        getRivers
# Purpose:     Calculates how many rivers intersect with the polygon.
#
# Author:      Arie Claassens
#
# Created:     11-07-2016
# Copyright:   (c) Arie Claassens 2016
# License:     GNU GPL. View the LICENSE file.
#------------------------------------------------------------------------------

"""
Get the count of Rivers and Water Basins within a predefined radius and
assign a weight based on the count:
0 features within radius = 0
1 feature within radius = 1
2 features within radius = 2
2+ features within radius = 3
"""


########################################################
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


########################################################
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
        except:
            msg = record.msg

        if record.levelno >= logging.ERROR:
            arcpy.AddError(msg)
        elif record.levelno >= logging.WARNING:
            arcpy.AddWarning(msg)
        elif record.levelno >= logging.INFO:
            arcpy.AddMessage(msg)

        super(ArcPyLogHandler, self).emit(record)

def get_projection(featureclass):
    """
    Find and return the spatial reference name of a feature class.
    """
    description = arcpy.Describe(featureclass)
    # Export the full text string to ensure a 100% match, preventing
    # discrepancies with differing central meridians, for example.
    #proj = description.SpatialReference.Name
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
                LOGGER.warning("The check and current item mismatch.")
                break # Break out of the for loop. no further testing needed

    LOGGER.info("Is there a spatial reference mismatch? " + str(mismatch))
    if mismatch:
        LOGGER.critical("Spatial reference mismatch between the feature classes.")
    else:
        LOGGER.info("Spatial references of all the feature classes match.")

    return mismatch

########################################################
# User Input parameters
LOGLEVEL = str(arcpy.GetParameterAsText(0)).upper()
LOGDIR = arcpy.GetParameterAsText(1)
CHECK_PROJ = arcpy.GetParameterAsText(2) # Boolean result received as text
TARGET_FC = arcpy.GetParameterAsText(0)
RIVERS_FC1 = arcpy.GetParameterAsText(1)
RIVERS_FC2 = arcpy.GetParameterAsText(2)
BUFFER_DIST = arcpy.GetParameterAsText(3)
UPDATE_ONLY = arcpy.GetParameterAsText(4) # Boolean result received as text


# Tool Parameters
arcpy.env.addOutputsToMap = False
getcontext().prec = 4 # Set decimal precision
REQUIRED_FIELD = "RIVERS" # Which field must we filter on and check for?
RIVERSFEATCLASS_LIST = [] # Empty list that will store the feature classes to process
RIVERSFEATLAYER_LIST = [] # Empty list that will store feature layers
COUNTER = 0
# Append the Meters required for the buffer distance parameter
BUFFER_DISTM = BUFFER_DIST + " Meters"

# Define the query filter
# Should we only update or process all records? True if selected by the user
if not UPDATE_ONLY:
    QRY_FILTER = REQUIRED_FIELD + " IS NOT NULL"
else:
    QRY_FILTER = ""
LOGGER.debug("QRY_FILTER is: " + QRY_FILTER)


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
LOGSTAMP = "AddRivers" # Identifies the source of the log entries
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


###############################################################################
# Put everything in a try/finally statement, so that we can close the logger
# even if script bombs out or we call an execution error along the line
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
    if int(arcpy.GetCount_management(RIVERS_FC1)[0]) == 0:
        arcpy.AddError("{0} has no features. Please use a feature class that \
                       contains data.".format(RIVERS_FC1))
        raise arcpy.ExecuteError
    else:
        RIVERSFEATCLASS_LIST.append(RIVERS_FC1)

    #First check if FC2 was passed in to the script before we check if it is empty
    if len(RIVERS_FC2) > 1:
        if int(arcpy.GetCount_management(RIVERS_FC2)[0]) == 0:
            arcpy.AddError("{0} has no features. Please use a feature class that \
                           contains data.".format(RIVERS_FC2))
            raise arcpy.ExecuteError
        else:
            RIVERSFEATCLASS_LIST.append(RIVERS_FC2)

    # Check if we have the required extension, otherwise stop the script.
    # Get Cell value is a standard tool in all ArcMap license levels.

    # Compare the spatial references of the input data sets, unless the user
    # actively chooses not to do so.
    LOGGER.info("Check for spatial reference mismatches? : " + CHECK_PROJ)
    if CHECK_PROJ == 'true':
        #LOGGER.info(TARGET_FC)
        LIST_FC = [] # Emtpy list to store FC
        # Add spatial references of all items
        LIST_FC.append(get_projection(TARGET_FC))
        LIST_FC.append(get_projection(LANDCOVER_RASTER))
        LOGGER.debug("The list of spatial references to check is:")
        LOGGER.debug(LIST_FC)
        LOGGER.info("Comparing spatial references of the data sets")
        # Check for mismatching spatial references
        MISMATCHED = compare_list_items(LIST_FC)
        if MISMATCHED:
            # Terminate the main thread
            # See https://docs.python.org/2/library/sys.html#sys.exit
            sys.exit(0)

    # Identify NoData value for the Raster.
    # WHAT DO WE DO WITH IT? SUBSTITUE A USER-SUPPLIED VALUE?!!!!!!!!!!!!!!!!!!!!!!!!!!!
    # See http://gis.stackexchange.com/questions/111449/how-to-access-raster-nodata-value
    RASTER_OBJ = arcpy.Raster(LANDCOVER_RASTER)
    NODATA = RASTER_OBJ.noDataValue
    LOGGER.debug("NODATA is: "+str(NODATA))

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



    #############################################################################
    arcpy.AddMessage("Starting with River/Water Basins Proximity Analysis")
    START_TIME = time.time()

    arcpy.MakeFeatureLayer_management(TARGET_FC, "inputHazard", FILTER_QUERY)
    RECORD_COUNT = int(arcpy.GetCount_management("inputHazard").getOutput(0))
    #arcpy.AddMessage("Total number of features: " + str(RECORD_COUNT))

    #Create feature layers out of Infrastructure FC
    LIST_COUNT = 0
    for item in RIVERSFEATCLASS_LIST:
        LIST_COUNT += 1
        # Dynamically generate a name for the Feature layer
        itemFlayerName = "Flayer_" + str(LIST_COUNT)
        #arcpy.AddMessage("Adding Feature Layer: " + itemFlayerName)
        arcpy.MakeFeatureLayer_management(item, itemFlayerName)
        RIVERSFEATLAYER_LIST.append(itemFlayerName)
        #arcpy.AddMessage(listInfraFeatLayer)

    arcpy.AddMessage("\nStarting with the features' processing....")

    with arcpy.da.UpdateCursor(TARGET_FC, ['OBJECTID', 'RIVERS',
                                           'RIVERS_BUFFER_DIST'],
                               FILTER_QUERY) as cursor:
        for row in cursor:
            #Loop through HazardBuffer FC
            COUNTER += 1
            # https://docs.python.org/3/library/decimal.html
            pctDone = Decimal(COUNTER)/Decimal(RECORD_COUNT) *100
            arcpy.AddMessage("Processing OID " + str(row[0]) +
                             ", with RIVERS grading of "+ str(row[1]) +
                             ". Feature " + str(COUNTER) + " of " +
                             str(RECORD_COUNT) + " or " + str(pctDone) + " %")

            # Now loop over items in Infrastructure list and tally up the total
            # after parsing all of them
            # Select the current feature from original Hazard FC
            arcpy.SelectLayerByAttribute_management("inputHazard",
                                                    "NEW_SELECTION",
                                                    "OBJECTID = " + str(row[0]))

            ###############################
            # Initialise the COUNTER, with its local scope, to zero
            totRivers = 0
            ##############################
            # Now loop through INFRASTRUCTURE feature layers and get the intersection
            for fc in RIVERSFEATLAYER_LIST:
                #arcpy.AddMessage("Now processing Feature Layer : " + fc)
                # Takes longer due to the buffering done as part of each query.
                # But faster than clipping source and using that.
                # Less risk of losing or modding data too.
                outputRivers = arcpy.SelectLayerByLocation_management(fc,
                                                                      "WITHIN_A_DISTANCE_GEODESIC",
                                                                      "inputHazard",
                                                                      BUFFER_DISTM,
                                                                      "")
                # Count the rows and add it to the COUNTER
                # The ROW_COUNT2 method produces way larger results, e.g. 13
                # versus the 1 reported by looping through the rows.
                #ROW_COUNT2 = int(arcpy.GetCount_management(outputInfrastructure).getOutput(0))
                #arcpy.AddMessage("RECORD_COUNT2 is: " +  str(ROW_COUNT2))
                for row2 in outputRivers:
                    # arcpy.AddMessage OIDs of selected features
                    #arcpy.AddMessage(row2.getSelectionSet())
                    #arcpy.AddMessage("\tRunning the row2 inside loop")
                    totRivers += 1
                    # http://desktop.arcgis.com/en/arcmap/10.3/analyze/arcpy-data-access/featureclasstonumpyarray.htm
                    #arr = arcpy.da.FeatureClassToNumPyArray(row2, "OID@",
                    # skip_nulls=True) # Should we do the skip_nulls?
                    #arcpy.AddMessage("Total Infrastructure in radius: " +
                    # str(arr["OID@"].sum()))
                    #totPop = arr["grid_code"].sum()

                #arcpy.AddMessage("ROW totRivers is: " + str(totRivers))

            # Update the row with the population sum
            #arcpy.AddMessage("totRivers is: "+ str(totRivers))
            # Cast to integer to ensure we deal with integer values
            totRivers = int(totRivers)

            # Calculate the grading. A case statement would have been handy.
            if totRivers == 0:
                gradeRivers = 0
            elif totRivers == 1:
                gradeRivers = 1
            elif totRivers == 2:
                gradeRivers = 2
            else:
                gradeRivers = 3

            arcpy.AddMessage("River/Water Basin grading: " + str(gradeRivers))
            # Assign the new value to the RIVERS field
            row[1] = gradeRivers
            # Assign the buffer distance to the Rivers buffer distance field
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