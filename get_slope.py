#-------------------------------------------------------------------------------
# Name:        get_slope
# Purpose:     Calculates the slope of a feature.
#
# Author:      Arie Claassens
#
# Created:     11-07-2016
# Copyright:   (c) Arie Claassens 2016
# License:     GNU GPL. View the LICENSE file.
#-------------------------------------------------------------------------------

"""
Calculates the Slope value for the Hazards Feature Class using the
Slope raster with the Get Cell Value Spatial Analysis Tool.
"""

# If it is a polygon, we need to find the centroid and use that for the Slope?
########################################################
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
TARGET_FC = arcpy.GetParameterAsText(3)
SLOPE_RASTER = arcpy.GetParameterAsText(4)
UPDATE_ONLY = arcpy.GetParameterAsText(5) # Boolean result received as text


# Tool Parameters
arcpy.env.addOutputsToMap = False
getcontext().prec = 4 # Set decimal precision
REQUIRED_FIELD = "SLOPE" # Which field must we filter on and check for?

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
LOGSTAMP = "AddSlope" # Identifies the source of the log entries
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

    # Check if the raster layer has any features before we start
    if int(arcpy.GetRasterProperties_management(SLOPE_RASTER, "ALLNODATA").
           getOutput(0)) == 1:
        LOGGER.error("{0} has no features. Please use a raster layer that \
                      already contains the required features and attributes." \
                      .format(SLOPE_RASTER))
        raise arcpy.ExecuteError

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
        LIST_FC.append(get_projection(SLOPE_RASTER))
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
    RASTER_OBJ = arcpy.Raster(SLOPE_RASTER)
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

    LOGGER.info("Starting the Slope calculations")
    START_TIME = time.time()

    ########################################################
    #Check if the input is sane
    #Check if the TARGET_FC has an SLOPE attribute and of Type LONG

    #Check if the SLOPE FC is a raster dataset

    # Identify NODATA value for the Raster. See
    #http://gis.stackexchange.com/questions/111449/how-to-access-raster-NODATA-value
    RASTER_OBJECT = arcpy.Raster(SLOPE_RASTER)
    NODATA = RASTER_OBJECT.noDataValue
    #arcpy.AddMessage("NODATA is: "+str(NODATA))

    ########################################################

    arcpy.AddMessage("\nStarting the Slope value calculations\n")
    START_TIME = time.time()

    # Find a better way of calculating the total number of rows to be updated
    #COUNT_RECORDS = collections.Counter(row[0] for row in
    #                                   arcpy.da.SearchCursor(TARGET_FC, "OBJECTID",
    #                                                         QRY_FILTER))
    # See https://docs.python.org/3/library/collections.html#collections.COUNTER -
    # we've got OID: 1 pairs for all the rows.
    #COUNT_RECORDS = sum(COUNT_RECORDS.values())
    COUNT_RECORDS = 0
    arcpy.AddMessage("COUNT_RECORDS START: " + str(COUNT_RECORDS))

    with arcpy.da.SearchCursor(TARGET_FC, ["OBJECTID"], QRY_FILTER) as countcursor:
        for row in countcursor:
            COUNT_RECORDS += 1
            #arcpy.AddMessage("COUNT_RECORDS is now: " + str(COUNT_RECORDS))


    arcpy.AddMessage("COUNT_RECORDS END: " + str(COUNT_RECORDS))

    if COUNT_RECORDS == 0:
        arcpy.AddError("The Hazards FC does not contain any features to process.")
        raise arcpy.ExecuteError

    COUNTER = 0

    with arcpy.da.UpdateCursor(TARGET_FC, FIELD_LIST, QRY_FILTER) as cursor:
        for row in cursor:
            COUNTER += 1
            # https://docs.python.org/3/library/decimal.html
            pctDone = Decimal(COUNTER)/Decimal(COUNT_RECORDS) *100
            arcpy.AddMessage("Processing OID " + str(row[0]) + ", with SLOPE of "+
                             str(row[3]) + ". Feature " + str(COUNTER) + " of " +
                             str(COUNT_RECORDS) + " or " + str(pctDone) + " %")
            # arcpy.AddMessage the coordinate tuple
            #arcpy.AddMessage("X and Y: " + str(row[1]) + " " + str(row[2]))
            # Set a default value to cater for NODATA returned by the GetCellValue tool
            cellvalue = -180 # get a better placeholder value!!!
            # Get the Cell Value from the SLOPE Raster
            try:
                cellresult = arcpy.GetCellValue_management(SLOPE_RASTER,
                                                           str(row[1]) + " " +
                                                           str(row[2]))
                # See http://gis.stackexchange.com/questions/55246/casting-arcpy-result-as-integer-instead-arcpy-getcount-management
                cellvalue = float(cellresult.getOutput(0))
                #arcpy.AddMessage(row[3])
                # If the cell does not have a value, set a value to add to TARGET_FC
                #if (row[3] == str(NODATA)):
                #   row[3] = -2

            except Exception as err:
                arcpy.AddMessage(err.args[0])

            row[3] = cellvalue
            #arcpy.AddMessage("Slope Cell Value is " + str(row[3]))
            cursor.updateRow(row)

    # Calculate the execution time
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