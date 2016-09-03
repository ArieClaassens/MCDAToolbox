"""
Clip the Land Cover raster to a user-defined buffer distance around the
features. The clipped raster data set will be used in subsequent processing
steps, which reduces the computation effort and time required to complete
the processes.
"""

# Clip the Land Cover Raster to speed up future processing
# http://help.arcgis.com/en/arcgisdesktop/10.0/help/index.html#/Extract_by_Mask/009z0000002n000000/

# Imports
#For timing purposes
#from datetime import datetime, date
import time
import arcpy
#from arcpy import env
#from arcpy.sa import *
#from arcpy.da import *
################################################################################
# Global variables
arcpy.env.overwriteOutput = True
arcpy.env.addOutputsToMap = False
#env.workspace = r'D:\Thesis\Data\Afg\Afg_Dev.gdb'

#buffer distance in meter for Population affected
# Convert to input parameter to use inside ArcMap!!!
BUFFER_DIST = "1000 Meters"

# Feature Classes and Raster datasets that will be used.
# Convert to input parameters to use inside ArcMap!!!
HAZARDS_FC = r'D:\Thesis\Data\Afg\Afg_Dev.gdb\Hazards'
POP_RASTER = r'D:\Thesis\Data\Afg\AFG-POP\AFG_Maps\popmap15adj.tif'

# Convert to input parameters to use inside ArcMap!!!
SCRATCH_FGDB = r'C:\TEMP\Default.gdb'
HAZBUFFER_FC_TEMP = SCRATCH_FGDB+"\HazardsBuffer"
HAZBUFFER_DISSOLVE_FC_TEMP = SCRATCH_FGDB+"\HazardsBufferDissolve"
HAZBUFFER_SINGLE_FC_TEMP = SCRATCH_FGDB+"\HazardsBufferSingle"
POP_FC_TEMP = SCRATCH_FGDB+"\PopMap15AdjPoints"
POP_CLIPPED_FC_TEMP = SCRATCH_FGDB+"\PopMap15AdjPoints_Clip"

# Control processes
CLEANUP_STEP = 0


####################################################################################
try:
    # Create Hazard Buffer FC and store in Temp File GDB on fastest drive (SSD)
    # Buffer distance is given in meters, which changes the method to Geodesic.
    arcpy.AddMessage("Starting with Hazard Buffer creation")
    START_TIME = time.time()
    arcpy.Buffer_analysis(in_features=HAZARDS_FC,
                          out_feature_class=HAZBUFFER_FC_TEMP,
                          buffer_distance_or_field=BUFFER_DIST,
                          line_side="FULL", line_end_type="ROUND",
                          dissolve_option="NONE", dissolve_field="",
                          method="PLANAR")
    STOP_TIME = time.time()
    arcpy.AddMessage("Total execution time in seconds = " +
                     str(int(STOP_TIME-START_TIME)) + " and in minutes = " +
                     str(int(STOP_TIME-START_TIME)/60))

    # Raster to Point conversion, storing in Temp File GDB too
    arcpy.AddMessage("Starting with Raster to Point conversion")
    START_TIME = time.time()
    arcpy.RasterToPoint_conversion(in_raster=POP_RASTER,
                                   out_point_features=POP_FC_TEMP,
                                   raster_field="Value")
    STOP_TIME = time.time()
    arcpy.AddMessage("Total execution time in seconds = " +
                     str(int(STOP_TIME-START_TIME)) +
                     " and in minutes = " + str(int(STOP_TIME-START_TIME)/60))

    # Clip the PopFC to the buffer polygons to reduce the workload and
    # improve performance
    # First merge the hazard buffers and use that as a mask for the population
    # layer clipping. Won't lose any data needed for intersect later
    # See http://gis.stackexchange.com/questions/30294/how-to-find-and-merge-duplicate-points
    ## What about cluster tolerance parameter and ranking? See Intersect
    # (Analysis) help documentation
    ## Population impact should be calculated for DHA too - provides more
    # accurate overall impact information,
    ## as opposed to tallying the total pop affected for all mines in a DHA.
    # Will also help grade uncleared DHA's
    arcpy.AddMessage("Starting with Clipping of Population Point FC")
    START_TIME = time.time()
    arcpy.AddMessage("Merging the overlapping Hazard Buffers into multi-part \
                      features to create a clip mask")
    arcpy.Dissolve_management(in_features=HAZBUFFER_FC_TEMP,
                              out_feature_class=HAZBUFFER_DISSOLVE_FC_TEMP,
                              dissolve_field="", statistics_fields="",
                              multi_part="MULTI_PART",
                              unsplit_lines="DISSOLVE_LINES")
    # Convert the multi-part features to single-part features to further speed
    # up the clipping processes
    arcpy.AddMessage("Convert the multi-part features to single-part features")
    arcpy.MultipartToSinglepart_management(in_features=HAZBUFFER_DISSOLVE_FC_TEMP,
                                           out_feature_class=HAZBUFFER_SINGLE_FC_TEMP)

    arcpy.AddMessage("Clipping the population density point data using the \
                     merged Hazard Buffers single-part feature class")
    arcpy.Clip_analysis(POP_FC_TEMP, HAZBUFFER_SINGLE_FC_TEMP,
                        POP_CLIPPED_FC_TEMP, "")
    arcpy.AddMessage("Done with Clipping")

    STOP_TIME = time.time()
    arcpy.AddMessage("Total execution time in seconds = "
                     + str(int(STOP_TIME-START_TIME))
                     + " and in minutes = " + str(int(STOP_TIME-START_TIME)/60))

    if CLEANUP_STEP == 1:
        arcpy.AddMessage("Cleaning up")
        #Delete the temporary FCs in the Scratch GDB
        #arcpy.Delete_management(tmpHazFC)
        #arcpy.Delete_management(POP_FC_TEMP)
        #arcpy.Delete_management(tmpHazPopFC)

except Exception as err:
    arcpy.AddError(err.args[0])
    raise arcpy.ExecuteError
