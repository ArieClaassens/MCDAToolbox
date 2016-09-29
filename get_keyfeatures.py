#------------------------------------------------------------------------------
# Name:        getKeyFeatures
# Purpose:     Calculates the Key Features value for each feature
#
# Author:      Arie Claassens
#
# Created:     11-07-2016
# Copyright:   (c) Arie Claassens 2016
# License:     GNU GPL. View the LICENSE file.
#------------------------------------------------------------------------------

"""
Get the count of KeyFeatures (Buildings) within a predefined radius
and assign a weight based on the count:
0 features within radius = 0
1 feature within radius = 1
2 features within radius = 2
2+ features within radius = 3
"""

#Import libraries
import logging
import logging.handlers
import time
from decimal import Decimal, getcontext #For progress COUNTER
import arcpy
#from arcpy import env

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
    proj = description.SpatialReference.Name
    return proj

def compare_list_items(checklist):
    """
    Loop through the list and compare the items to determine if any item
    is a mismatch with the first item in the list. Used to check for spatial
    reference mismatches between feature classes.
    """
    mismatch = False # Local variable to store match results
    check = '' # Local variable to store the spatial projection
    for checkitem in checklist:
        LOGGER.debug("Processing " + str(checkitem))
        if check == '': # Nothing captured yet, use the first item as base
            check = checkitem
            LOGGER.debug("The check is now " + str(checkitem))
        else:
            # Test if they match
            if check == checkitem:
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
KEYFEATURES_FC1 = arcpy.GetParameterAsText(4)
KEYFEATURES_FC2 = arcpy.GetParameterAsText(5)
BUFFER_DIST = arcpy.GetParameterAsText(6) # buffer distance in meters
UPDATE_ONLY = arcpy.GetParameterAsText(7) # Boolean result received as text

# Tool Parameters
arcpy.env.addOutputsToMap = False
getcontext().prec = 4 # Set decimal precision
REQUIRED_FIELDS = ['KEYFEATURES', 'KEYFEATURES_BUFFER_DIST']
FILTER_FIELD = "KEYFEATURES" # Which field must we filter on and check for?
KEYFEATURECLASS_LIST = [] # Empty list for the feature classes to process
KEYFEATURELAYER_LIST = [] # Empty list to store resulting feature layers
# Append the Meters qualifier required for the buffer distance parameter
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
LOGSTAMP = "AddKeyFeatures" # Identifies the source of the log entries
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

    #Build the list with the feature classes that will be used
    # We need at least one FC to work with, check first if it has content
    if int(arcpy.GetCount_management(KEYFEATURES_FC1)[0]) == 0:
        LOGGER.error("{0} has no features. Please use a feature class that \
                       contains data.".format(KEYFEATURES_FC1))
        raise arcpy.ExecuteError
    else:
        KEYFEATURECLASS_LIST.append(KEYFEATURES_FC1)

    #First check if FC2 was passed in to the script before we check if it is empty
    if len(KEYFEATURES_FC2) > 1:
        if int(arcpy.GetCount_management(KEYFEATURES_FC2)[0]) == 0:
            LOGGER.error("{0} has no features. Please use a feature class that \
                           contains data.".format(KEYFEATURES_FC2))
            raise arcpy.ExecuteError
        else:
            KEYFEATURECLASS_LIST.append(KEYFEATURES_FC2)

    # Compare the spatial references of the input data sets, unless the user
    # actively chooses not to do so.
    LOGGER.info("Check for spatial reference mismatches? : " + CHECK_PROJ)
    if CHECK_PROJ == 'true':
        #LOGGER.info(HAZAREA_FC)
        LIST_FC = [] # Emtpy list to store FC
        # Add spatial references of all items
        LIST_FC.append(get_projection(HAZAREA_FC))
        LIST_FC.append(get_projection(KEYFEATURES_FC1))
        if len(KEYFEATURES_FC2) > 1:
            LIST_FC.append(get_projection(KEYFEATURES_FC2))
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

    arcpy.AddMessage("Starting with Key Features Proximity Analysis")
    START_TIME = time.time()

    # Get the total number of records to process
    arcpy.MakeFeatureLayer_management(HAZAREA_FC, "inputHazard", QRY_FILTER)
    RECORD_COUNT = int(arcpy.GetCount_management("inputHazard").getOutput(0))
    LOGGER.info("Total number of features: " + str(RECORD_COUNT))

    if RECORD_COUNT == 0:
        LOGGER.warning("The Hazard Areas FC does not contain any features.")
        raise arcpy.ExecuteError

    #Create feature layers out of Key Features FCs
    LIST_COUNT = 0
    for item in KEYFEATURECLASS_LIST:
        LIST_COUNT += 1
        # Dynamically generate a name for the Feature layer
        itemFlayerName = "Flayer_" + str(LIST_COUNT)
        LOGGER.debug("Adding Feature Layer: " + itemFlayerName)
        arcpy.MakeFeatureLayer_management(item, itemFlayerName)
        KEYFEATURELAYER_LIST.append(itemFlayerName)

    LOGGER.info("Starting with the hazards area processing")
    with arcpy.da.UpdateCursor(HAZAREA_FC, FIELDLIST, QRY_FILTER) as cursor:
        for row in cursor:
            #Loop through Hazard Areas FC
            COUNTER += 1
            pctDone = Decimal(COUNTER)/Decimal(RECORD_COUNT) *100
            LOGGER.info("Processing OID " + str(row[0]) +
                        ", with KEYFEATURES grading of "+ str(row[2]) +
                        ". Feature " + str(COUNTER) + " of " +
                        str(RECORD_COUNT) + " or " + str(pctDone) + " %")

            # Iterate over items in key features list and tally up the total
            # Select the current feature from original Hazard FC
            arcpy.SelectLayerByAttribute_management("inputHazard",
                                                    "NEW_SELECTION",
                                                    "OBJECTID = " + str(row[0]))

            # Initialize the counter, with local scope, to zero
            TOTAL_KEY_ITEMS = 0
            # Now loop through INFRASTRUCTURE feature layers and intersect
            # with the selected feature to calculate the total
            for fc in KEYFEATURELAYER_LIST:
                LOGGER.debug("Now processing feature Layer : " + fc)
                # Takes longer due to the buffering done as part of each query.
                # But faster than clipping source and using that.
                TEMP = arcpy.SelectLayerByLocation_management(fc,
                                                              "WITHIN_A_DISTANCE_GEODESIC",
                                                              "inputHazard",
                                                              BUFFER_DISTM,
                                                              "")
                # Count the rows and add it to the COUNTER
                TOTAL_KEY_ITEMS += int(arcpy.GetCount_management(TEMP).getOutput(0))

            LOGGER.debug("TOTAL_KEY_ITEMS is: " + str(TOTAL_KEY_ITEMS))
            # Update the row with the key features sum
            # Cast to integer to ensure we deal with integer values
            TOTAL_KEY_ITEMS = int(TOTAL_KEY_ITEMS)
            LOGGER.debug("FINAL TOTAL_KEY_ITEMS is: " + str(TOTAL_KEY_ITEMS))

            # Calculate the grading. A case statement would have been nice to have.
            if TOTAL_KEY_ITEMS == 0:
                gradeKeyFeatures = 0
            elif TOTAL_KEY_ITEMS == 1:
                gradeKeyFeatures = 1
            elif TOTAL_KEY_ITEMS == 2:
                gradeKeyFeatures = 2
            else:
                gradeKeyFeatures = 3

            arcpy.AddMessage("KEYFEATURES grading: " + str(gradeKeyFeatures))
            # Assign the new value to the KeyFeatures field
            row[2] = gradeKeyFeatures
            # Assign the buffer distance to the Key Features buffer distance field
            row[3] = BUFFER_DIST
            cursor.updateRow(row)
    STOP_TIME = time.time()
    LOGGER.info("Total execution time in seconds = " +
                str(int(STOP_TIME - START_TIME)) + " and in minutes = " +
                str(int(STOP_TIME - START_TIME) / 60))

finally:
    # Shut down logging after script has finished running.
    #http://stackoverflow.com/questions/24816456/python-logging-wont-shutdown
    LOGGER.debug("------- STOP LOGGING-----------")
    LOGGER.removeHandler(HANDLER)
    HANDLER.close()
    logging.shutdown()

