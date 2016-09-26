#------------------------------------------------------------------------------
# Name:        getLandCover
# Purpose:     Calculates the Land Cover value for each hazard area
#
# Author:      Arie Claassens
#
# Created:     11-07-2016
# Copyright:   (c) Arie Claassens 2016
# License:     GNU GPL. View the LICENSE file.
#------------------------------------------------------------------------------

"""
Calculates the LandCover value for the Hazard Area Feature Class using the
LandCover raster with the Get Cell Value Spatial Analysis Tool, based on the
inside centroid X and Y coordinates
"""

#Import libraries
import logging
import logging.handlers
import time
from decimal import Decimal, getcontext #For the progress counter
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
LANDCOVER_RASTER = arcpy.GetParameterAsText(4)
UPDATE_ONLY = arcpy.GetParameterAsText(5) # Boolean result received as text

# Tool Parameters
arcpy.env.addOutputsToMap = False
getcontext().prec = 4 # Set decimal precision
REQUIRED_FIELD = "LANDCOVER" # Which field must we filter on and check for?

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
LOGSTAMP = "AddLandCover" # Identifies the source of the log entries
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
    QRY_FILTER = REQUIRED_FIELD + " IS NULL"
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

    # Check if the target feature class has the required attribute field.
    if not fieldexist(HAZAREA_FC, REQUIRED_FIELD):
        LOGGER.error("The field "+ REQUIRED_FIELD +" does not exist. \
                         Please use the correct Hazard feature class.")
        raise arcpy.ExecuteError

    # Check if the raster layer has any NoData before we start
    # Adapted from https://geonet.esri.com/message/487616#comment-520588
    if int(arcpy.GetRasterProperties_management(LANDCOVER_RASTER, "ANYNODATA").
           getOutput(0)) == 1:
        if int(arcpy.GetRasterProperties_management(LANDCOVER_RASTER, "ALLNODATA").
               getOutput(0)) == 1:
            LOGGER.error("All cells are NoData in " + str(LANDCOVER_RASTER))
            LOGGER.error("Please use a raster layer that contains data.")
            raise arcpy.ExecuteError
    else:
        LOGGER.debug("The raster is without NoData")

    # Compare the spatial references of the input data sets, unless the user
    # actively chooses not to do so.
    LOGGER.info("Check for spatial reference mismatches? : " + CHECK_PROJ)
    if CHECK_PROJ == 'true':
        #LOGGER.info(HAZAREA_FC)
        LIST_FC = [] # Emtpy list to store FC
        # Add spatial references of all items
        LIST_FC.append(get_projection(HAZAREA_FC))
        LIST_FC.append(get_projection(LANDCOVER_RASTER))
        LOGGER.debug("The list of spatial references to check is:")
        LOGGER.debug(LIST_FC)
        LOGGER.info("Comparing spatial references of the data sets")
        # Check for mismatching spatial references
        MISMATCHED = compare_list_items(LIST_FC)
        if MISMATCHED:
            # Terminate the script
            raise arcpy.ExecuteError

    # Determine if we are working with a POINT or POLYGON shape type and adjust
    # the fields list to use the inside centroid X and Y fields added in the
    # first step, i.e. INSIDE_X and INSIDE_Y
    FC_DESC = arcpy.Describe(HAZAREA_FC)
    if FC_DESC.shapeType == "Polygon":
        LOGGER.info("POLYGON feature class detected. Proceeding.")
        FIELDLIST = ['OBJECTID', 'INSIDE_X', 'INSIDE_Y', REQUIRED_FIELD]
    else:
        LOGGER.error("Unsupported shape type detected.")
        raise arcpy.ExecuteError

    LOGGER.info("Starting the Land Cover calculations")
    START_TIME = time.time()

    # Get the total number of records to process
    # See http://gis.stackexchange.com/questions/30140/fastest-way-to-count-the-number-of-features-in-a-feature-class
    COUNT_RECORDS = 0
    LOGGER.info("COUNT_RECORDS START: " + str(COUNT_RECORDS))
    arcpy.MakeFeatureLayer_management(HAZAREA_FC, "inputHazard", QRY_FILTER)
    arcpy.MakeTableView_management("inputHazard", "tableViewTargetFC", QRY_FILTER)
    COUNT_RECORDS = int(arcpy.GetCount_management("tableViewTargetFC").getOutput(0))
    # Destroy the temporary table
    arcpy.Delete_management("tableViewHazards")
    LOGGER.info("COUNT_RECORDS END: " + str(COUNT_RECORDS))

    if COUNT_RECORDS == 0:
        LOGGER.error("The feature class does not contain any features.")
        raise arcpy.ExecuteError

    COUNTER = 0

    with arcpy.da.UpdateCursor(HAZAREA_FC, FIELDLIST) as cursor:
        for row in cursor:
            COUNTER += 1
            # https://docs.python.org/3/library/decimal.html - decimal output
            pctDone = Decimal(COUNTER)/Decimal(COUNT_RECORDS) *100
            LOGGER.info("Processing OID " + str(row[0]) +
                        ", with current LANDCOVER value of "+ str(row[3]) +
                        ". Feature " + str(COUNTER) + " of " +
                        str(COUNT_RECORDS) + " or " + str(pctDone) + " %")
            # Print the coordinate tuple
            LOGGER.debug("X and Y: " + str(row[1]) + " " + str(row[2]))
            # Set an initial default value
            LOGGER.debug("Setting intial default value of -2")
            cellvalue = -2
            # Get the Cell Value from the LandCover Raster
            try:
                cellresult = arcpy.GetCellValue_management(LANDCOVER_RASTER,
                                                           str(row[1]) + " " +
                                                           str(row[2]))
                # See http://gis.stackexchange.com/questions/55246/casting-arcpy-result-as-integer-instead-arcpy-getcount-management
                cellvalue = int(cellresult.getOutput(0))
                LOGGER.debug("The raster cell value is " + str(cellvalue))

            except Exception as err:
                LOGGER.error(err.args[0])

            row[3] = cellvalue
            cursor.updateRow(row)
            LOGGER.debug("The land cover value is now: " + str(row[3]))

    # Calculate the execution time
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
