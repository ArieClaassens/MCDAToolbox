# Add source info to the criteria data field help, e.g. OSM Key Features export, in Toolbox

# Run PyLint tests

# Check if FIELDLIST is used in the arcpy.da.UpdateCursor field listing. Otherwise we're wasting good code

# Move the check_proj code into the mismatch check function - DO LAST?

# Add a filter in script on parameters - define the specific feature class types that are allowed as input, e.g. POLYGON

# Add Pop Impact script that allows user to work with raster data (currently using vector feature class) ?

# What is up with Rasters and NoData?

# OpenData API
# http://anothergisblog.blogspot.com/2016/01/opendata-added-to-arcrest.html

# Extra features:
# "toolboxes\system toolboxes\spatial analyst tools.tbx\multivariate"
# "toolboxes\system toolboxes\spatial statistics tools.tbx"
# "toolboxes\system toolboxes\spatial statistics tools.tbx\analyzing patterns"
# "toolboxes\system toolboxes\spatial statistics tools.tbx\mapping clusters"
# "toolboxes\system toolboxes\spatial statistics tools.tbx\modeling spatial relationships"
# Cluster and Outlier Analysis (Anselin Local Morans I) - for DHA after weighting = hot spots, cold spots and outliers
# Hot Spot Analysis (Getis-Ord Gi*) - for DHA after weighting
# Optimized Hot Spot Analysis - for DHA after weighting
# Multi-Distance Spatial Cluster Analysis (Ripleys K Function) ?
# Similarity Search - apply to uncleared DHA after prioritising the cleared DHA. Extra tool for post-MCDA process

#Geographically Weighted Regression
#      Performs Geographically Weighted Regression (GWR), a local form of linear regression used to model spatially varying relationships.

#Exploratory Regression
#       The Exploratory Regression tool evaluates all possible combinations of the input candidate explanatory variables, looking for OLS models that best explain the dependent variable within the context of user-specified criteria.

# http://desktop.arcgis.com/en/arcmap/10.3/guide-books/python-addins/creating-an-add-in-tool.htm
############################################################################################


#Calculate statistics on Fishnet cells:
# Replace a layer/table view name with a path to a dataset (which can be a layer file) or create the layer/table view within the script
# The following inputs are layers or table views: "DHA_Clearance"
arcpy.Statistics_analysis(in_table="DHA_Clearance", out_table="C:/TEMP/Scratch.gdb/DHA_Clearance_Statistics1", statistics_fields="SW MEAN;S MEAN;SE MEAN;W MEAN;CENTER MEAN;E MEAN;NW MEAN;N MEAN;NE MEAN", case_field="")
#OBJECTID *    FREQUENCY    MEAN_SW    MEAN_S    MEAN_SE    MEAN_W    MEAN_CENTER    MEAN_E    MEAN_NW    MEAN_N    MEAN_NE
#1    1    8    0    17    17    22    14    6    14    15

#Add to Map? This shows the mean value of all the cells. Cell with highest mean value is national primary cluster.


############################################################################################

#--------------------------------------------------------------------------------------------

# Are any of the tools version specific? Do we need to check for a certain version of Python or ArcMap?

# Future proof for Python 3? See https://blog.esri-southafrica.com/2016/01/14/migrating-python-scripts-to-arcgis-pro/

# Least cost path analysis for grading clearance projects, based on following:
# Slope, Aspect, land cover type, distance from base camps, relative altitude, etc. ?

# Set scripts to not update ArcMap UI while running, for speeding up tasks

# Update Toolbox tool parameters - names, description, examples.
# Compile a CHM file for the Toolbox?

# Comparisons between MCDA output is important!

# Add calculation to display processing time per hazard feature for logging?
# Check projection of feature classes / raster data used with TARGET_FC ?
# Check http://pro.arcgis.com/en/pro-app/tool-reference/environment-settings/nodata.htm
# Validation code in scripts - in tool's settings?

############################################################################################
# Future developments to add to thesis:
# Add R Graph scripts / R scripts to identify factor impact? - See Packtpub R books, e.g.
# https://www.packtpub.com/big-data-and-business-intelligence/r-graph-essentials
# Let user select criteria fields a la http://gis.stackexchange.com/questions/170875/arcgis-python-script-tool-field-name-drop-down ?
# Check compatibility with Python 3

# Thesis - offline web map app as output? KML/KMZ for Google Maps?:
# Layer to KML tool vs Map to KML (whole map document)



############################################################################################
########################====================================================================
# DONE
########################====================================================================
############################################################################################

#http://help.arcgis.com/en/arcgisdesktop/10.0/help/index.html#/Extract_by_Mask/009z0000002n000000/
#https://blogs.esri.com/esri/arcgis/2013/05/20/are-you-sure-intersect-is-the-right-tool-for-the-job/ - Nope it isn't

# Sanity checks - schema lock on TARGET_FC, feature count on TARGET_FC,
# extensions availability, etc. before processing starts

# What license level is required for the extension tools to be executed in scripts?
# http://desktop.arcgis.com/en/arcmap/10.3/analyze/python/access-to-licensing-and-extensions.htm

# Add debug /  logging option
# See http://gis.stackexchange.com/questions/135920/arcpy-logging-error-messages
# Note: If logging code fails and logging doesn't close properly, ArcMap needs a restart.
# Need more dev work on this (after thesis?). Close log as part of exception steps?
# http://pro.arcgis.com/en/pro-app/arcpy/get-started/error-handling-with-python.htm

# Add a change projection tool to toolbox? No, use existing Project or Batch Project tools.

############################################################################################
# Primary quadrant detection - overlay hazards FC over DHA FC and find the quadrant with the most hazards.
# Repeat for all DHA and determine the most prevalent quadrant.
# Create overlay representing primary quadrant? heat map / hot spot / clusters?
# Find width and height of DHA and divide by 2 to find max width and height of fishnet blocks.
# Read geometry, find top and left and use that as starting point. No need for Advanced License then
# http://pro.arcgis.com/en/pro-app/arcpy/classes/extent.htm
# http://gis.stackexchange.com/questions/16520/obtaining-extent-of-each-polygon-in-shapefile-using-arcpy
# http://pro.arcgis.com/en/pro-app/arcpy/get-started/reading-geometries.htm
# These two require Advanced Desktop license to create envelopes:
# http://desktop.arcgis.com/en/arcmap/latest/tools/data-management-toolbox/minimum-bounding-geometry.htm
# http://desktop.arcgis.com/en/arcmap/latest/tools/data-management-toolbox/feature-envelope-to-polygon.htm
# Run through all DHA, create fishnet of calculated max w & h and sum hazards in each polygon.
# Check which polygon has highest count and that is the primary cluster.
# Repeat for secondary cluster, and store in secondary cluster location field?
# Use "Central Feature" Tool? Need to group hazards by DHA ID
#     The Central Feature tool is useful for finding the center when you want to minimize distance (Euclidean or Manhattan distance) for all features to the center.

# Fishnet is now generated from lower left to lower right, to upper left to upper right => SW, SE, NW, NE.
# 3x3 Fishnet also generated from bottom left to top right => SW, S, SE, W, Center, E, NW, N, NE.

# Include all 9 cells in analysis results capturing, not just top 2
# Generate reports on cluster location on district level, regional level:
#   User supplies admin boundaries FC, e.g. district
#   Replicate admin boundaries FC, add 9 cluster fields
#   Loop over admin boundaries FC
#        Select all DHA falling inside selected admin area
#        Count number of hazards recorded in each cluster
#        Add total hazards per cluster for the admin area
#        => N: 200, NE: 100, E:123, SE: 50, S: 900, SW: 300, W: 321, NW: 9002
#        User can then determine per area which is the predominant cluster position of the 9 available
#        Scale of admin boundary FC supplied by user will determine scale of report, e.g. ward, municipality, region, district, province, country - though country level can be generated by summing existing DHA records....
############################################################################################

# Add License as a separate script

# WHERE script checks for all entries in REQUIRED_FIELDS, the REQUIRED_FIELD must change to FILTER_FIELD!!!!

# Mixed use of SOURCE_FC and TARGET_FC for Hazard Areas FC. Standardise on HAZAREA_FC across all the scripts

# Toolbox tools descriptions: http://resources.arcgis.com/en/help/main/10.1/index.html#/A_quick_tour_of_documenting_tools_and_toolboxes/001500000014000000/
# Look at the Scripting explanation section for each parameter!!!!

# Swap images in Tool Help so thumbnail is loaded at top
