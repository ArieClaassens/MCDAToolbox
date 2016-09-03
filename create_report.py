#-------------------------------------------------------------------------------
# Name:        createReport
# Purpose:     create a PDF report of the MCDA results and their parameters. Build a map book?
#              http://desktop.arcgis.com/en/arcmap/10.3/map/page-layouts/building-map-books-with-arcgis.htm
#              Map book with title and map index (overview) page - with ancillary pages will do the trick, I think.
#              See http://desktop.arcgis.com/en/arcmap/10.3/analyze/arcpy-mapping/introduction-to-arcpy-mapping.htm
#              and https://geochalkboard.wordpress.com/2010/11/01/print-and-export-maps-from-arcmap-with-arcpy-mapping/
#              and http://desktop.arcgis.com/en/arcmap/10.3/analyze/arcpy-mapping/getting-started-with-arcpy-mapping-tutorial.htm
# Author:      Arie Claassens
#
# Created:     07-07-2016
# Copyright:   (c) Arie Claassens 2016
# License:     <your licence>
#-------------------------------------------------------------------------------

"""
Create a comparison report on multiple MCDA output feature classes. The user
supplies a number of feature classes to compare, which are then combined in
a single map book. The output contains the various feature classes as well
as an extract of the user-supplied radii and relative weights used to
calculate the unweighted and weighted hazard classification.
"""

#Imports
import arcpy

# Global variables

#Map book components
# Title page
# Data-driven pages for each output?
# Ancillary page where we list the various weight combinations used
# Summary map where we select only the DHA with the highest ranking and overlay
# them all on one map to build a sum of the different scenarios?
# Select the max weighted score value for a FC and then select all the features
# with that weight and add to a temp FC, repeat for all selected MCDA output FC
# and build a map where we display each FC in a different colour. Focus here
# is on location of highest ranking DHA. Do the various weights end up with the
# same clustering properties / location?

MAP_AUTHOR = "Arie Claassens' Land Clearance MCDA Toolset"


SOURCE_MXD = arcpy.GetParameterAsText(0)
TARGET_PDF = arcpy.GetParameterAsText(1)


# Code
arcpy.AddMessage("Generating Report")

MXD = arcpy.mapping.MapDocument(SOURCE_MXD)

############################################
## TRAIL RUN START
############################################
# Apply the required settings
MXD.author = MAP_AUTHOR # Can we set this here before we print? Only when we update an MXD, AFAIK.

# Generate the PDF document
arcpy.mapping.ExportToPDF(MXD, TARGET_PDF)
############################################
## TRAIL RUN END
############################################
