#------------------------------------------------------------------------------
# Name:        getPrimaryClusterLocation
# Purpose:     Calculate the predominant location of hazard clusters inside
#              the hazard areas.
#
# Author:      Arie Claassens
#
# Created:     August 2016
# Copyright:   (c) Arie Claassens 2016
# License:     GNU GPL. View the LICENSE file.
#------------------------------------------------------------------------------

"""
Calculate the concentration of hazards in nine equal sized cells placed over
each hazard area polygon by iterating over the hazards area, placing a fishnet
of three rows and three columns over the hazard polygon. The tally the number
of hazards intersecting with the hazard area, and locating hazard clusters
within the extent of the hazard area. Record the number of hazards found in each
of the nine polygons, which then represent the SW, S, SE, W, CENTER, E, NW, N
and NE positions on the polygon.
"""


########################################################
#Import libraries
import sys # required for the sys.exit() call to halt the script
import logging
import logging.handlers
import time # For timing purposes
from decimal import Decimal, getcontext #For progress COUNTER
# https://arcpy.wordpress.com/2012/07/02/retrieving-total-counts/
#import collections
import arcpy
from arcpy import env
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

# Adapted from http://bjorn.kuiper.nu/2011/04/21/tips-tricks-fieldexists-for-arcgis-10-python/
def fieldexist(featureclass, fieldname):
    """
    Test for the existence of fieldname in featureclass.
    Input: featureclass to check and fieldname to look for.
    Returns: True if the field exists, False if it does not.
    """
    fieldlist = arcpy.ListFields(featureclass, fieldname)
    fieldcount = len(fieldlist)
    return bool(fieldcount == 1)

def get_projection(featureclass):
    """
    Find and return the spatial reference name of a feature class.
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
                LOGGER.warning("The check and current item mismatch.")
                break # Break out of the for loop. no further testing needed

    LOGGER.info("Is there a spatial reference mismatch? " + str(mismatch))
    if mismatch:
        LOGGER.critical("Spatial reference mismatch between the feature classes.")
    else:
        LOGGER.info("Spatial references of all the feature classes match.")

    return mismatch

########################################################
# Global variables
# User Input parameters
LOGLEVEL = str(arcpy.GetParameterAsText(0)).upper()
LOGDIR = arcpy.GetParameterAsText(1)
CHECK_PROJ = arcpy.GetParameterAsText(2) # Boolean result received as text
SOURCE_FC = arcpy.GetParameterAsText(3)
HAZARD_FC1 = arcpy.GetParameterAsText(4)
HAZARD_FC2 = arcpy.GetParameterAsText(5)
UPDATE_ONLY = arcpy.GetParameterAsText(6) # Boolean result received as text

# Tool Parameters
arcpy.env.addOutputsToMap = False
getcontext().prec = 4 # Set decimal precision
REQUIRED_FIELDS = ['SW', 'S', 'SE', 'W', 'CENTER', 'E', 'NW', 'N', 'NE']
REQUIRED_FIELD = 'SW' # Which field must we filter on and check for?
# Use the SW field as a proxy for all nine cells
HAZARDS_LIST = [] # Empty list that will store the feature classes to process
HAZARDSLIST_FEATLAYER = [] # Empty list that will store the feature layers
COUNTER = 0

# Define the query filter
# Should we only update or process all records?
if not UPDATE_ONLY:
    QRY_FILTER = REQUIRED_FIELD + " IS NOT NULL"
else:
    QRY_FILTER = ""
LOGGER.debug("QRY_FILTER is: " + QRY_FILTER)

########################################################
# Tool configuration:

#########################################################
# Fishnet parameters
# Apply the source data projection to the fishnet feature class to ensure
# consistent projection across the data sets
PROJ = get_projection(FC_DESC)
# Set coordinate system of the fishnet
env.outputCoordinateSystem = PROJ
# In_memory storage of the fishnet, discarded after processing
FISHNET_FC = "in_memory/fishnet3by3"
# Enter 0 for width and height, these values will be calculated by the tool
# Number of rows and columns together with origin and opposite corner
# determine the size of each cell
cellSizeWidth = '0'
cellSizeHeight = '0'
numRows =  '3'
numColumns = '3'
# Set the origin of the fishnet to a default value; update dynamically per row
originCoordinate = '0 0'
# Set the orientation by specifying a point on the Y axis. Update in each row
yAxisCoordinate = '0 0'
# Set the opposite corner of the fishnet to a default value; update in each row
oppositeCorner = '0 0'
# Extent set by origin and opposite corner, no need for a template feature class
templateExtent = '#'
# Each output cell will be a polygon. Slower than polyline, but we're processing
# one DHA at a time and using in_memory storage to improve performance
geometryType = 'POLYGON'
# Don't generate an additional feature class containing fishnet labels
labels = 'NO_LABELS'


# Set up the logging parameters and inform the user
DATE_STRING = time.strftime("%Y%m%d")
LOGFILE = unicode(LOGDIR + '\\'+ DATE_STRING +
                  '_mcdatool.log').encode('unicode-escape')
MAXBYTES = 2097152 # 2MB
BACKUPCOUNT = 10
# Change this variable to a unique identifier for each script it runs in.
# Cannot use LOGGER.findCaller(), as we're calling from an embedded script in
# the Python toolbox.
LOGSTAMP = "AddCellHazardCount" # Identifies the source of the log entries
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
# even if script bombs out or we call an execution error along the line
try:
    # Sanity checks:

    # Remove the in_memory fishnet in case the script was terminated unexpectedly
    arcpy.Delete_management(FISHNET_FC)

    # Check if the target feature class has any features before we start
    if int(arcpy.GetCount_management(SOURCE_FC)[0]) == 0:
        LOGGER.error("{0} has no features. Please use a feature class that \
                      already contains the required features and attributes." \
                      .format(SOURCE_FC))
        raise arcpy.ExecuteError

   # Check if the target feature class has all of the required attribute fields.
    for checkfield in REQUIRED_FIELDS:
        if not fieldexist(SOURCE_FC, checkfield):
            LOGGER.debug("Check for field: " + checkfield)
            LOGGER.error("The field "+ checkfield +" does not exist. \
                             Please use the correct feature class.")
            raise arcpy.ExecuteError

    #Build the list with the feature classes that will be used
    # We need at least one FC to work with; check first if it has any content
    if int(arcpy.GetCount_management(HAZARD_FC1)[0]) == 0:
        LOGGER.error("{0} has no features. Please use a feature class that \
                       contains data.".format(HAZARD_FC1))
        raise arcpy.ExecuteError
    else:
        HAZARDS_LIST.append(HAZARD_FC1)

    #First check if FC2 was supplied before we check if it is empty
    if len(HAZARD_FC2) > 1:
        if int(arcpy.GetCount_management(HAZARD_FC2)[0]) == 0:
            LOGGER.error("{0} has no features. Please use a feature class that \
                           contains data.".format(HAZARD_FC2))
            raise arcpy.ExecuteError
        else:
            HAZARDS_LIST.append(HAZARD_FC2)

    # Check if we have the required extension, otherwise stop the script.
    # XXXX XXXXX is a standard tool in all ArcMap license levels.

    # Compare the spatial references of the input data sets, unless the user
    # actively chooses not to do so.
    LOGGER.info("Check for spatial reference mismatches? : " + CHECK_PROJ)
    if CHECK_PROJ == 'true':
        #LOGGER.info(SOURCE_FC)
        LIST_FC = [] # Empty list to store FC
        # Add spatial references of all items
        LIST_FC.append(get_projection(SOURCE_FC))
        LIST_FC.append(get_projection(HAZARD_FC1))
        if len(HAZARD_FC2) > 1:
            LIST_FC.append(get_projection(HAZARD_FC2))
        LOGGER.debug("The list of spatial references to check is:")
        LOGGER.debug(LIST_FC)
        LOGGER.info("Comparing spatial references of the data sets")
        # Check for mismatching spatial references
        MISMATCHED = compare_list_items(LIST_FC)
        if MISMATCHED:
            # Terminate the main thread
            # See https://docs.python.org/2/library/sys.html#sys.exit
            sys.exit(0)

    # Adjust the fields list to include the Object ID and Shape data
    LOGGER.info("Adding OBJECTID and SHAPE@ fields to FIELDLIST")
    FIELDLIST = ['OBJECTID', 'SHAPE@', REQUIRED_FIELDS]

#############################################################################
    arcpy.AddMessage("Starting with the Hazards Count Analysis")
    START_TIME = time.time()

    # Hoekom doen ons hierdie een? Is dit nodig?
    arcpy.MakeFeatureLayer_management(SOURCE_FC, "inputHazard", FILTER_QUERY)
    RECORD_COUNT = int(arcpy.GetCount_management("inputHazard").getOutput(0))
    #arcpy.AddMessage("Total number of features: " + str(RECORD_COUNT))

    #Create feature layers out of Hazards FC
    LIST_COUNT = 0
    for item in HAZARDS_LIST:
        LIST_COUNT += 1
        # Dynamically generate a name for the Feature layer
        itemFlayerName = "Flayer_" + str(LIST_COUNT)
        #arcpy.AddMessage("Adding Feature Layer: " + itemFlayerName)
        arcpy.MakeFeatureLayer_management(item, itemFlayerName)
        HAZARDSLIST_FEATLAYER.append(itemFlayerName)
        #arcpy.AddMessage(listInfraFeatLayer)

    arcpy.AddMessage("Starting with the hazard areas processing....")

    with arcpy.da.UpdateCursor(SOURCE_FC, FIELDLIST, FILTER_QUERY) as cursor:
        for row in cursor:
            #Loop through Hazard Areas FC
            COUNTER += 1
            # https://docs.python.org/2.7/library/decimal.html
            pctDone = Decimal(COUNTER)/Decimal(RECORD_COUNT) * 100
            LOGGER.info("Processing OID " + str(row[0]) + ". Feature " +
                        str(COUNTER) + " of " + str(RECORD_COUNT) +
                        " or " + str(pctDone) + " %")

            # Get the feature's extent from the @SHAPE data
            extent = row[1].extent
            # display the current values
            LOGGER.debug("SW: {0}. S: {1}. SE: {2}. W: {3}. CENTER: {4}. \
                         E: {5}. NW: {6}. N: {7}. NE: {8}"
                         .format(row[4], row[5], row[6], row[7], row[8],
                                 row[9], row[10], row[11], row[12]))
            LOGGER.debug("XMin: {0}, YMin: {1}, XMax: {0}, YMax: {1}"
                  .format(extent.XMin, extent.YMin, extent.XMax, extent.YMax))

            lowerleft = str(extent.XMin) + " " + str(extent.YMin)
            upperright = str(extent.XMax) + " " + str(extent.YMax)
            # Add 0.1 degree on the Y axis to generate the Y axis coordinate
            yAxisCoordinate = str(extent.XMin)  + " " + str(extent.YMin + 0.1)
            # Corners:
            originCoordinate = lowerleft
            oppositeCorner = upperright

            LOGGER.info("Creating the feature's fishnet")
            # Create 3 x 3 fishnet over the current hazard area
            arcpy.CreateFishnet_management(outFeatureClass, originCoordinate,
                                           yAxisCoordinate, None, None, numRows,
                                           numColumns, oppositeCorner, labels,
                                           None, geometryType)


            # Build dictionary of fishnet cells and hazard count per cell.
            # The 3x3 Fishnet is generated from bottom left to top right, i.e
            # SW, S, SE, W, CENTER, E, NW, N and lastly NE. See the grid
            # below, generated at http://www.tablesgenerator.com/text_tables
            # +----+--------+----+
            # | NW |    N   | NE |
            # +----+--------+----+
            # |  W | CENTER |  E |
            # +----+--------+----+
            # | SW |    S   | SE |
            # +----+--------+----+
            # Create a dictionary to hold the predefined keys and values
            clusterDictionary = {'SW':0, 'S':0, 'SE':0, 'W':0, 'CENTER':0,
                                 'E':0, 'NW':0, 'N':0, 'NE':0}

            # create a counter to use for the dictionary manipulation
            fishnetCounter = 0

            LOGGER.info("Processing the fishnet")
             # Loop through the 9 fishnet cells and intersect with hazards FC to count hazards in each cell
            for row2 in arcpy.da.SearchCursor(outFeatureClass, "SHAPE@"):
                LOGGER.debug("Processing fishnet feature class row {0}".format(fishnetCounter))

                # Loop through the Hazards Feature layer list to find the total
                # using the locally scope variable below
                TOTAL_HAZARDS = 0

                for fc in HAZARDSLIST_FEATLAYER:
                    # Filter the HAZARDS_FC1 and HAZARDS_FC2 on the current hazard area so that we only count the hazards falling inside this hazard area
                    arcpy.SelectLayerByLocation_management(fc, "WITHIN", row[0],
                                                           "", "NEW_SELECTION", "")
                    hazardbyCell = arcpy.SelectLayerByLocation_management(fc, "WITHIN", fishnetCounter[0])
                    CELL_RESULT = arcpy.GetCount_management(hazardbyCell)
                    TOTAL_HAZARDS += int(CELL_RESULT.getOutput(0))

                    # Remove the filter on the HAZARDS FC by clearing the selection
                    arcpy.SelectLayerByAttribute_management(fc,"CLEAR_SELECTION","")

                # Now we have the total hazards in this cell
                LOGGER.debug("TOTAL_HAZARDS is now: {0}".format(TOTAL_HAZARDS))

                # Assign the hazard count to the fishnet polygon that is currently being processed.
                if fishnetCounter == 0:
                   clusterDictionary['SW'] = countHazards
                elif fishnetCounter == 1:
                   clusterDictionary['S'] = countHazards
                elif fishnetCounter == 2:
                   clusterDictionary['SE'] = countHazards
                elif fishnetCounter == 3:
                   clusterDictionary['W'] = countHazards
                elif fishnetCounter == 4:
                   clusterDictionary['CENTER'] = countHazards
                elif fishnetCounter == 5:
                   clusterDictionary['E'] = countHazards
                elif fishnetCounter == 6:
                   clusterDictionary['NW'] = countHazards
                elif fishnetCounter == 7:
                   clusterDictionary['N'] = countHazards
                else:
                   clusterDictionary['NE'] = countHazards

                # Increment counter
                fishnetCounter += 1

            # Print the cluster dictionary now that we have looped over all the cells
            LOGGER.debug("clusterDictionary is: {0}".format(clusterDictionary))

            # Update the row with the new values
            row[4] = clusterDictionary['SW']
            row[5] = clusterDictionary['S']
            row[6] = clusterDictionary['SE']
            row[7] = clusterDictionary['W']
            row[8] = clusterDictionary['CENTER']
            row[9] = clusterDictionary['E']
            row[10] = clusterDictionary['NW']
            row[11] = clusterDictionary['N']
            row[12] = clusterDictionary['NE']

            LOGGER.info("Updating the feature")
            cursor.updateRow(row)

            # Delete the dictionary
            del clusterDictionary
            # Remove the fishnet in preparation for the next row
            arcpy.Delete_management(outFeatureClass)

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

