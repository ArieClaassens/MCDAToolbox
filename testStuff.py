"""
Used for testing bits of code
"""
import sys # required for the sys.exit() call to halt the script
import logging
import logging.handlers
import time
import arcpy

# Adapted from http://gis.stackexchange.com/questions/135920/arcpy-logging-error-messages
LOGLEVEL = str(arcpy.GetParameterAsText(0)).upper()
LOGDIR = arcpy.GetParameterAsText(1)
CHECK_PROJ = arcpy.GetParameterAsText(2) # Boolean result received as text
TARGET_FC = arcpy.GetParameterAsText(3)
TEST_FC = arcpy.GetParameterAsText(4)
REQUIRED_FIELD = "LANDCOVER"

###############################################################################
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

# From http://desktop.arcgis.com/en/arcmap/10.3/analyze/python/access-to-licensing-and-extensions.htm
def check_extension(extension_name):
    """
    Check for the availability of an ArcGIS extension. Returns True of False.
    """
    try:
        if arcpy.CheckExtension(extension_name) == "Available":
            available = True
        else:
            available = False
            raise LicenseError
    except LicenseError:
        LOGGER.warning(extension_name + " license is unavailable")
    except arcpy.ExecuteError:
        LOGGER.error(arcpy.GetMessages(2))
    finally:
        # Return the result of the test
        return available

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

def compare_projections(fclist):
    """
    Loop through the featureclass list amd compare the spatial references
    of the items to determine if they all use the same spatial projection.
    """
    mismatch = False # Local variable to store match results
    proj = '' # Local variable to store the spatial projection
    for item in fclist:
        LOGGER.debug("Processing %s" % item)
        if proj == '': # Nothing captured yet, use the Target_FC as base
           description = arcpy.Describe(item)
           proj = description.SpatialReference.Name(item)
           LOGGER.debug("The proj is now %s" % proj)
        else:
             # Test if they match
             description = arcpy.Describe(item)
             proj = description.SpatialReference.Name(item)
             if proj == arcpy.Describe.SpatialReference.Name(item):
                LOGGER.debug("The projections match. Continuing testing")
             else:
                  # Update local variable to store latest spatial reference
                  proj = arcpy.Describe.SpatialReference.Name(item)
                  mismatch = True
                  LOGGER.warning("The projections mismatch.")
                  break # Break out of the for loop. no further testing needed

    return mismatch



###############################################################################
# Set up the logging parameters and inform the user
DATE_STRING = time.strftime("%Y%m%d")
LOGFILE = unicode(LOGDIR + '\\'+ DATE_STRING +'_mcdatool.log').encode('unicode-escape')
MAXBYTES = 2097152
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

###############################################################################
###############################################################################
# Put everything in a try/finally statement, so that we can close the logger
# even if script bombs out or we call an execution error along the line
try:
# Sanity checks:

    # Check if the feature class has any features before we start
    if int(arcpy.GetCount_management(TARGET_FC)[0]) == 0:
       arcpy.AddError("{0} has no features. Please use a feature class that \
                      already contains the required features and attributes." \
                      .format(TARGET_FC))
       raise arcpy.ExecuteError

	# Check if the raster layer has any features before we start
    if int(arcpy.GetRasterProperties_management(LANDCOVER_RASTER, "ALLNODATA").
           getOutput(0)) == 1:
        LOGGER.error("{0} has no features. Please use a raster layer that \
                      already contains the required features and attributes." \
                      .format(LANDCOVER_RASTER))
        raise arcpy.ExecuteError
		
	# Check if the target feature class has the required attribute field.
    if not fieldexist(TARGET_FC, REQUIRED_FIELD):
        arcpy.AddWarning("The field "+ REQUIRED_FIELD +" does not exist. \
                         Please use the correct Hazard feature class.")
        raise arcpy.ExecuteError
		
    # Check if we have the required extension, otherwise stop the script.
    if not check_extension("Spatial"):
       LOGGER.critical("Extension is not available. Please check in the extension.")
       raise arcpy.ExecuteError

    # Compare the spatial references of the input data sets, unless the user
    # actively chooses not to do so.
    LOGGER.info("Check for spatial reference mismatches? : " + CHECK_PROJ)
    if CHECK_PROJ == 'true':
        #LOGGER.info(TARGET_FC)
        LIST_FC = [] # Emtpy list to store FC
        # Add spatial references of all items
        LIST_FC.append(get_projection(TARGET_FC))
        LIST_FC.append(get_projection(TEST_FC))
        LOGGER.debug("The list of spatial references to check is:")
        LOGGER.debug(LIST_FC)
        LOGGER.info("Comparing spatial references of the data sets")
        # Check for mismatching spatial references
        MISMATCHED = compare_list_items(LIST_FC)
        if MISMATCHED:
           # Terminate the main thread
           # See https://docs.python.org/2/library/sys.html#sys.exit
           sys.exit(0)

    #Code
    COUNTER = 0
    LOGGER.debug("Starting the test Stuff Tool")

    LOGGER.debug("A debug message")
    LOGGER.info("An info message")
    LOGGER.warning("A warning message")
    LOGGER.error("An error message")
    LOGGER.critical("A critical error message")


    while (COUNTER <= 3):
        arcpy.AddMessage("AddMessage function called "+str(COUNTER)+" times")
        LOGGER.debug("--> " + str(COUNTER) +': This message should go to the log file')
        LOGGER.info("--> " + str(COUNTER)+': So should this')
        LOGGER.warning("--> " + str(COUNTER)+': And this, too')
        COUNTER += 1

    #try:
    #    #Something that might fail
    #    divbyzeroBOOM = 1024/0
    #except Exception as e:
    #    LOGGER.exception(e)
    #finally:
             # Close everything down



finally:
	# Shut down logging after script has finished running.
	#http://stackoverflow.com/questions/24816456/python-logging-wont-shutdown
	LOGGER.debug("------- STOP LOGGING-----------")
	LOGGER.removeHandler(HANDLER)
	HANDLER.close()
	logging.shutdown()
