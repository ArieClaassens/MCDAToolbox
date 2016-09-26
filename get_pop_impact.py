#------------------------------------------------------------------------------
# Name:        getPopHazardImpact
# Purpose:     Calculates the total number of the population impacted
#              by the hazards
#
# Author:      Arie Claassens
#
# Created:     11-07-2016
# Copyright:   (c) Arie Claassens 2016
# License:     GNU GPL. View the LICENSE file.
#------------------------------------------------------------------------------

"""
Calculate the total population potentially affected by virtue of being
located within a predefined buffer distance from the hazard point or area.
Uses the Population vector point feature class created from the population
raster layer earlier.
"""

#Import libraries
import logging
import logging.handlers
import time
from decimal import Decimal, getcontext #For progress COUNTER
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
        LOGGER.debug("Processing " + str(item))
        if check == '': # Nothing captured yet, use the first item as base
            check = item
            LOGGER.debug("The check is now " + str(item))
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

# User Input parameters
LOGLEVEL = str(arcpy.GetParameterAsText(0)).upper()
LOGDIR = arcpy.GetParameterAsText(1)
CHECK_PROJ = arcpy.GetParameterAsText(2) # Boolean result received as text
HAZAREA_FC = arcpy.GetParameterAsText(3)
POP_FC = arcpy.GetParameterAsText(4)
BUFFER_DIST = arcpy.GetParameterAsText(5) # buffer distance in meters
UPDATE_ONLY = arcpy.GetParameterAsText(6) # Boolean result received as text

# Tool Parameters
arcpy.env.addOutputsToMap = False
getcontext().prec = 4 # Set decimal precision
REQUIRED_FIELDS = ['POPULATION', 'POPULATION_BUFFER_DIST']
FILTER_FIELD = "POPULATION" # Which field must we filter on and check for?
# Append the Meters required for the buffer distance parameter
BUFFER_DISTM = BUFFER_DIST + " Meters"
COUNTER = 0

# Tool configuration:
# Set up the logging parameters and inform the user
DATE_STRING = time.strftime("%Y%m%d")
LOGFILE = unicode(LOGDIR + '\\'+ DATE_STRING +
                  '_mcdatool.log').encode('unicode-escape')
MAXBYTES = 10485760 # 10MB
BACKUPCOUNT = 10
# Change this variable to a unique identifier for each script it runs in.
# Cannot use LOGGER.findCaller(), as we're calling from an embedded script in
# the Python toolbox.
LOGSTAMP = "AddPOPImpact" # Identifies the source of the log entries
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
# Should we only update only records with a NULL value?
if UPDATE_ONLY:
    QRY_FILTER = FILTER_FIELD + " IS NULL"
else:
    QRY_FILTER = ""
LOGGER.debug("QRY_FILTER is: " + QRY_FILTER)

# Put everything in a try/finally statement, so that we can close the logger
# even if the script bombs out or we raise an execution error along the line
try:
    # Sanity checks:

    # Check if the target feature class has any features before we start
    if int(arcpy.GetCount_management(HAZAREA_FC)[0]) == 0:
        LOGGER.error("{0} has no features. Please use a feature class that \
                      already contains the required features and attributes." \
                      .format(HAZAREA_FC))
        raise arcpy.ExecuteError

    # Check if the target feature class has all of the required attribute fields.
    for checkfield in REQUIRED_FIELDS:
        if not fieldexist(HAZAREA_FC, checkfield):
            LOGGER.debug("Check for field: " + checkfield)
            LOGGER.error("The field "+ checkfield +" does not exist. \
                             Please use the correct feature class.")
            raise arcpy.ExecuteError

    # Check if the population feature class has any features before we start
    if int(arcpy.GetCount_management(POP_FC)[0]) == 0:
        LOGGER.error("{0} has no features. Please use a feature class that \
                      already contains the required features and attributes." \
                      .format(POP_FC))
        raise arcpy.ExecuteError

    # Compare the spatial references of the input data sets, unless the user
    # actively chooses not to do so.
    LOGGER.debug("Check for spatial reference mismatches? : " + CHECK_PROJ)
    if CHECK_PROJ == 'true':
        LIST_FC = [] # Emtpy list to store FC
        # Add spatial references of all items
        LIST_FC.append(get_projection(HAZAREA_FC))
        LIST_FC.append(get_projection(POP_FC))
        LOGGER.debug("The list of spatial references to check is:")
        LOGGER.debug(LIST_FC)
        LOGGER.info("Comparing spatial references of the data sets")
        # Check for mismatching spatial references
        MISMATCHED = compare_list_items(LIST_FC)
        if MISMATCHED:
            # Terminate the script
            raise arcpy.ExecuteError

    # Adjust the fields list to include the Object ID and Shape data
    LOGGER.info("Adding OBJECTID and SHAPE@ fields to FIELDLIST")
    # Insert the fields at the start of the list to obtain the required
    # field ordering
    REQUIRED_FIELDS.insert(0, 'SHAPE@')
    REQUIRED_FIELDS.insert(0, 'OBJECTID')
    FIELDLIST = REQUIRED_FIELDS
    LOGGER.debug("The FIELDLIST is now " + str(FIELDLIST))

    LOGGER.info("Starting the Population Hazard Impact analysis")
    START_TIME = time.time()

    # Get the total number of records to process after creating feature layer
    COUNT_RECORDS = 0
    LOGGER.debug("Creating Hazard Area Feature Layer")
    arcpy.MakeFeatureLayer_management(HAZAREA_FC, "inputHazard", QRY_FILTER)
    COUNT_RECORDS = int(arcpy.GetCount_management("inputHazard").getOutput(0))
    LOGGER.info("Hazard Area feature count: " + str(COUNT_RECORDS))

    if COUNT_RECORDS == 0:
        LOGGER.error("The feature class does not contain any features.")
        raise arcpy.ExecuteError

    # Get the total number of population features after creating feature layer
    LOGGER.info("Creating Population Feature Layer")
    arcpy.MakeFeatureLayer_management(POP_FC, "popFeatures")
    COUNT_POP_RECORDS = int(arcpy.GetCount_management("popFeatures").getOutput(0))
    LOGGER.info("Population feature count: " + str(COUNT_POP_RECORDS))

    COUNTER = 0
    LOGGER.info("Starting to iterate over DHA using UpdateCursor")
    with arcpy.da.UpdateCursor(HAZAREA_FC, FIELDLIST, QRY_FILTER) as cursor:
        for row in cursor:
            TOT_POP = 0
            #Loop through Hazard Areas FC
            COUNTER += 1 # Start counter at 1, for human consumption
            pctDone = Decimal(COUNTER)/Decimal(COUNT_RECORDS) * 100
            arcpy.AddMessage("Processing OID " + str(row[0]) +
                             " with POPULATION IMPACT of "+ str(row[2]) +
                             ". Feature " + str(COUNTER) + " of " +
                             str(COUNT_RECORDS) + " or " + str(pctDone) + " %")

            # Select the current feature from Hazard Area FC
            arcpy.SelectLayerByAttribute_management("inputHazard",
                                                    "NEW_SELECTION",
                                                    "OBJECTID = {0}".format(row[0]))

            # Select all features in the population raster layer that intersects
            # with the current hazard feature
            # Takes longer due to the buffering done as part of each query.
            arcpy.SelectLayerByLocation_management("popFeatures",
                                                   "WITHIN_A_DISTANCE_GEODESIC",
                                                   "inputHazard",
                                                   BUFFER_DISTM, "NEW_SELECTION")

            TOT_POP = int(arcpy.GetCount_management("popFeatures")[0])
            # Round the floating number and cast as integer
            TOT_POP = int(round(TOT_POP))
            LOGGER.info("Potential population affected is : " + str(TOT_POP))

            # Assign the new value to the POPULATION field
            row[2] = TOT_POP
            # Assign the buffer distance to the POPULATION buffer distance field
            row[3] = BUFFER_DIST
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
