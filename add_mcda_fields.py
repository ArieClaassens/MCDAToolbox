#------------------------------------------------------------------------------
# Name:        AddMCEFields
# Purpose:     Add the attributes fields required by the Multi-Criteria
#              Decision Analysis processes.
#
# Author:      Arie Claassens
#
# Created:     11-07-2016
# Copyright:   (c) Arie Claassens 2016
# License:     GNU GPL. View the LICENSE file.
#------------------------------------------------------------------------------

"""
Add the attributes required for the Multi-Criteria Decision Analysis and
primary cluster location processes.
"""

# Library Imports
import logging
import logging.handlers
import time
import arcpy

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
            LOGGER.info(msg)

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

# Global variables
# User Input:
LOGLEVEL = str(arcpy.GetParameterAsText(0)).upper()
LOGDIR = arcpy.GetParameterAsText(1)
# Define a variable to store the location of the feature class that will be
# updated with the new attribute fields.
TARGET_FC = arcpy.GetParameterAsText(0)

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
LOGSTAMP = "AddMCDAFields" # Identifies the source of the log entries
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
    # Start the process by first running the sanity checks
    # Sanity checks:

    # Check if we can obtain a schema lock - adapted from
    # https://pro.arcgis.com/en/pro-app/arcpy/functions/testschemalock.htm
    if not arcpy.TestSchemaLock(TARGET_FC):
    # Warn the user that the required schema lock could not be obtained.
        LOGGER.error("Unable to acquire the necessary schema lock on \
                       ".format(TARGET_FC))
        raise arcpy.ExecuteError

    # Check if the feature class has any features before we start
    if int(arcpy.GetCount_management(TARGET_FC)[0]) == 0:
        LOGGER.error("{0} has no features. Please use a feature class that \
                      already contains the required features and attributes." \
                      .format(TARGET_FC))
        raise arcpy.ExecuteError

    # Check if we have the required extension, otherwise stop the script.
    #check_extension("Spatial") # base functionality

    # Define an empty multi-dimensional array to hold the 21 fields and their
    # 9 parameters
    ARRAY_FIELDS = []

    # Append the required fields with their parameters to the array
    # The fields are [field_name, field_type, field_precision, field_scale,
    # field_length, field_alias, field_is_nullable, field_is_required,
    # field_domain]
    # Keep field names under 64 alphanumeric and underscore characters for safety.
    # Refer to http://desktop.arcgis.com/en/arcmap/latest/manage-data/administer-file-gdbs/file-geodatabase-size-and-name-limits.htm
    # and http://support.esri.com/technical-article/000005588
    ARRAY_FIELDS.append(["LANDCOVER", "LONG", "", "", "", "", "NULLABLE",
                         "NON_REQUIRED", ""])
    ARRAY_FIELDS.append(["LANDCOVERWEIGHT", "LONG", "", "", "", "", "NULLABLE",
                         "NON_REQUIRED", ""])
    ARRAY_FIELDS.append(["ASPECT", "LONG", "", "", "", "", "NULLABLE",
                         "NON_REQUIRED", ""])
    ARRAY_FIELDS.append(["ASPECTWEIGHT", "LONG", "", "", "", "", "NULLABLE",
                         "NON_REQUIRED", ""])
    ARRAY_FIELDS.append(["INFRASTRUCTURE", "LONG", "", "", "", "", "NULLABLE",
                         "NON_REQUIRED", ""])
    ARRAY_FIELDS.append(["INFRA_BUFFER_DIST", "LONG", "", "", "", "",
                         "NULLABLE", "NON_REQUIRED", ""])
    ARRAY_FIELDS.append(["INFRASTRUCTUREWEIGHT", "LONG", "", "", "", "",
                         "NULLABLE", "NON_REQUIRED", ""])
    ARRAY_FIELDS.append(["KEYFEATURES", "LONG", "", "", "", "", "NULLABLE",
                         "NON_REQUIRED", ""])
    ARRAY_FIELDS.append(["KEYFEATURES_BUFFER_DIST", "LONG", "", "", "", "",
                         "NULLABLE", "NON_REQUIRED", ""])
    ARRAY_FIELDS.append(["KEYFEATURESWEIGHT", "LONG", "", "", "", "",
                         "NULLABLE", "NON_REQUIRED", ""])
    ARRAY_FIELDS.append(["ACCIDENTS", "LONG", "", "", "", "", "NULLABLE",
                         "NON_REQUIRED", ""])
    ARRAY_FIELDS.append(["ACCIDENTS_BUFFER_DIST", "LONG", "", "", "", "",
                         "NULLABLE", "NON_REQUIRED", ""])
    ARRAY_FIELDS.append(["ACCIDENTSWEIGHT", "LONG", "", "", "", "", "NULLABLE",
                         "NON_REQUIRED", ""])
    ARRAY_FIELDS.append(["POI", "LONG", "", "", "", "", "NULLABLE",
                         "NON_REQUIRED", ""])
    ARRAY_FIELDS.append(["POI_BUFFER_DIST", "LONG", "", "", "", "", "NULLABLE",
                         "NON_REQUIRED", ""])
    ARRAY_FIELDS.append(["POIWEIGHT", "LONG", "", "", "", "", "NULLABLE",
                         "NON_REQUIRED", ""])
    ARRAY_FIELDS.append(["RIVERS", "LONG", "", "", "", "", "NULLABLE",
                         "NON_REQUIRED", ""])
    ARRAY_FIELDS.append(["RIVERS_BUFFER_DIST", "LONG", "", "", "", "",
                         "NULLABLE", "NON_REQUIRED", ""])
    ARRAY_FIELDS.append(["RIVERSWEIGHT", "LONG", "", "", "", "", "NULLABLE",
                         "NON_REQUIRED", ""])
    ARRAY_FIELDS.append(["SLOPE", "LONG", "", "", "", "", "NULLABLE",
                         "NON_REQUIRED", ""])
    ARRAY_FIELDS.append(["SLOPEWEIGHT", "LONG", "", "", "", "", "NULLABLE",
                         "NON_REQUIRED", ""])
    ARRAY_FIELDS.append(["POPULATION", "LONG", "", "", "", "", "NULLABLE",
                         "NON_REQUIRED", ""])
    ARRAY_FIELDS.append(["POPULATION_BUFFER_DIST", "LONG", "", "", "", "",
                         "NULLABLE", "NON_REQUIRED", ""])
    ARRAY_FIELDS.append(["POPULATIONWEIGHT", "LONG", "", "", "", "", "NULLABLE",
                         "NON_REQUIRED", ""])
    ARRAY_FIELDS.append(["HAZARD_COUNT", "LONG", "", "", "", "", "NULLABLE",
                         "NON_REQUIRED", ""])
    ARRAY_FIELDS.append(["SW", "LONG", "", "", "", "", "NULLABLE",
                         "NON_REQUIRED", ""])
    ARRAY_FIELDS.append(["S", "LONG", "", "", "", "", "NULLABLE",
                         "NON_REQUIRED", ""])
    ARRAY_FIELDS.append(["SE", "LONG", "", "", "", "", "NULLABLE",
                         "NON_REQUIRED", ""])
    ARRAY_FIELDS.append(["W", "LONG", "", "", "", "", "NULLABLE",
                         "NON_REQUIRED", ""])
    ARRAY_FIELDS.append(["CENTER", "LONG", "", "", "", "", "NULLABLE",
                         "NON_REQUIRED", ""])
    ARRAY_FIELDS.append(["E", "LONG", "", "", "", "", "NULLABLE",
                         "NON_REQUIRED", ""])
    ARRAY_FIELDS.append(["NW", "LONG", "", "", "", "", "NULLABLE",
                         "NON_REQUIRED", ""])
    ARRAY_FIELDS.append(["N", "LONG", "", "", "", "", "NULLABLE",
                         "NON_REQUIRED", ""])
    ARRAY_FIELDS.append(["NE", "LONG", "", "", "", "", "NULLABLE",
                         "NON_REQUIRED", ""])
    ARRAY_FIELDS.append(["SCORE", "LONG", "", "", "", "", "NULLABLE",
                         "NON_REQUIRED", ""])
    ARRAY_FIELDS.append(["WEIGHTEDSCORE", "LONG", "", "", "", "", "NULLABLE",
                         "NON_REQUIRED", ""])
    ARRAY_FIELDS.append(["RANKING", "TEXT", "", "", "50", "", "NULLABLE",
                         "NON_REQUIRED", ""])


    LOGGER.debug("ARRAY_FIELDS content: " + ARRAY_FIELDS)
    LOGGER.info("Starting the Add MCDA Fields process")

    # Check if feature class is of point or polygon type, in which case we
    # calculate the centroid inside X,Y coordinates and add them
    # as INSIDE_X and INSIDE_Y fields to the feature class. Other
    # shape types are not supported, so raise an error to stop the process.
    # WHY DO WE USE CENTROID_INSIDE AS OPPOSED TO PLAIN CENTROID? COS WE KEEP
    # IT INSIDE THE POLYGON FEATURE THEN.
    # SEE http://pro.arcgis.com/en/pro-app/tool-reference/data-management/add-geometry-attributes.htm
    FC_DESC = arcpy.Describe(TARGET_FC)
    if FC_DESC.shapeType == "Point":
        LOGGER.info("POINT feature class detected. Proceeding.")
    elif FC_DESC.shapeType == "Polygon":
        LOGGER.info("POLYGON feature class detected. Adding \
    the inside centroid X and Y coordinates.")
        arcpy.AddGeometryAttributes_management(
            Input_Features=TARGET_FC,
            Geometry_Properties="CENTROID_INSIDE", Length_Unit="", Area_Unit="",
            Coordinate_System="")
    else:
        arcpy.AddError("Unsupported shape type detected. Please use a \
        feature class with a POINT or POLYGON shape type")
        raise arcpy.ExecuteError

    # Test to see if the required fields already exist in the feature class
    # Loop through the array of fields and test against the field name.
    # Throw an error if a match is found.
    for row in ARRAY_FIELDS:
        if fieldexist(TARGET_FC, row[0]):
            arcpy.AddWarning("The field "+str(row[0])+" already exists.")
            raise arcpy.ExecuteError

    # Loop through the array and create the fields using the values stored
    # in the array. Available in all ArcMap license versions as a standard
    # function. Does not require any additional extensions.
    for row in ARRAY_FIELDS:
        arcpy.AddField_management(
            in_table=TARGET_FC, field_name=row[0],
            field_type=row[1], field_precision=row[2], field_scale=row[3],
            field_length=row[4], field_alias=row[5], field_is_nullable=row[6],
            field_is_required=row[7], field_domain=row[8])
        LOGGER.info(str(row[0]) + " field added")
    # Notify the user that the fields were added
    LOGGER.info("The required fields were added.")

finally:
    # Shut down logging after script has finished running.
    #http://stackoverflow.com/questions/24816456/python-logging-wont-shutdown
    LOGGER.debug("------- STOP LOGGING-----------")
    LOGGER.removeHandler(HANDLER)
    HANDLER.close()
    logging.shutdown()
