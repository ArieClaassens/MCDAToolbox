#Import libraries
import arcpy
from arcpy import env
# For timing purposes
from datetime import datetime, date
import time
###########################################
startTime = time.time()
print datetime.now()
dtgnow = datetime.now()


featureclass = r"D:\Thesis\Data\Afg\Afg_Dev.gdb\DHA_Clearance"
hazardsFC = r"D:\Thesis\Data\Afg\Afg_Dev.gdb\AP_Mines_Original"

# Adapted from http://stackoverflow.com/questions/268272/getting-key-with-maximum-value-in-dictionary
def keywithmaxval(d):
     """
     a) create a list of the dict's keys and values;
     b) return the key with the max value
     """
     v=list(d.values())
     k=list(d.keys())
     return k[v.index(max(v))]


# Create 2 x 2 fishnet and count hazards in each and ID polygon with most hazards
# Record polygon location as primary and secondary cluster locations, e.g. N and W

# http://pro.arcgis.com/en/pro-app/tool-reference/data-management/create-fishnet.htm


description = arcpy.Describe(featureclass)
# Export the full text string to ensure a 100% match, preventing
# discrepancies with differing central meridians, for example.
#proj = description.SpatialReference.Name
proj = description.SpatialReference.exporttostring()

# Set coordinate system of the output fishnet - get this from INPUT_FC
#env.outputCoordinateSystem = arcpy.SpatialReference("NAD 1983 UTM Zone 11N")
env.outputCoordinateSystem = proj

# In_memory storage of the fishnet, discarded after processing
outFeatureClass = "in_memory/fishnet3by3"
#outFeatureClass = r"D:\Thesis\Data\Afg\Afg_Dev.gdb\fishnet3by3"

try:
    # Remove the fishnet in preparation for the next row in the DHA FC
    arcpy.Delete_management(outFeatureClass)
except:
    print(arcpy.GetMessages())



# Fishnet Parameters
# Enter 0 for width and height - these values will be calcualted by the tool
cellSizeWidth = '0'
cellSizeHeight = '0'

# Number of rows and columns together with origin and opposite corner
# determine the size of each cell
numRows =  '3'
numColumns = '3'

# Set the origin of the fishnet to a default value; update in each row
originCoordinate = '0 0'

# Set the orientation by specifying a point on the Y axis. Set programmatically in each row
yAxisCoordinate = '0 0'

# Set the opposite corner of the fishnet to a default value; update in each row
oppositeCorner = '0 0'

# Extent is set by origin and opposite corner - no need to use a template fc
templateExtent = '#'

# Each output cell will be a polygon. Slower than polyline, but we're processing
# one DHA at a time and using in_memory storage to improve performance
geometryType = 'POLYGON'

# Generate an additional feature class containing the fishnet labels?
labels = 'NO_LABELS'
###############################################

# Create a feature layer out of Hazards FC to use as input in SelectLayer_management script, which does not accept FC that reside on disk.
try:
    arcpy.MakeFeatureLayer_management(hazardsFC, "HAZARDS_FC")
except:
   print(arcpy.GetMessages())
# Loop through feature class and spit out XMin, XMax, YMin, YMax values of each feature

# Fetch each feature from the cursor and examine the extent properties
# XMin and YMin define the lower-left coordinates of the feature and
# XMax and YMax define the upper-right coordinates.
with arcpy.da.UpdateCursor(featureclass, ["SHAPE@", "OBJECTID", "PRIMARYCLUSTERLOC", "PRIMARYCLUSTERCOUNT", "SECONDARYCLUSTERLOC", "SECONDARYCLUSTERCOUNT"]) as cursor:
     for row in cursor:
        print("########################################################################################################################################################")
        print(" ")
        extent = row[0].extent
        print("DHA {0}:".format(row[1]))
        print("Primary Cluster Loc: {0}. Primary Loc Count: {1}. Secondary Cluster Loc: {2}. Secondary Loc Count: {3}".format(row[2], row[3], row[4], row[5]))
        print("XMin: {0}, YMin: {1}".format(extent.XMin, extent.YMin))
        lowerleft = str(extent.XMin) + " " + str(extent.YMin)
        print("XMax: {0}, YMax: {1}".format(extent.XMax, extent.YMax))
        upperright = str(extent.XMax) + " " + str(extent.YMax)
        yAxisCoordinate = str(extent.XMin)  + " " + str(extent.YMin + 0.1) # Add 0.1 degree?
        # Corners:
        originCoordinate = lowerleft
        oppositeCorner = upperright

        # Create 3 x 3 fishnet over DHA
        arcpy.CreateFishnet_management(outFeatureClass, originCoordinate, yAxisCoordinate, None, None, numRows, numColumns, oppositeCorner, labels, None, geometryType)

        # Build dictionary of fishnet cells and hazard counts to store cell values and find two highest concentrations of hazards
        # Then reverse sort the dictionary and get the first two entries to get the primary and secondary cluster locations
        # http://bytesizebio.net/2013/04/03/stupid-python-tricks-3296-sorting-a-dictionary-by-its-values/
        # 3x3 Fishnet is generated from bottom left to top right => SW, S, SE, W, CENTER, E, NW, N, NE.
        # Create a dictionary to hold the predefined keys and values
        clusterDictionary = {'SW':0, 'S':0, 'SE':0, 'W':0, 'CENTER':0, 'E':0, 'NW':0, 'N':0, 'NE':0}
        # create a counter to use as a tracker for the dictionary manipulation
        fishnetCounter = 0
        rowcounter = 1 # Temp counter for testing.
        # Loop through the 9 fishnet cells and intersect with hazards FC to count hazards in each cell
        for row2 in arcpy.da.SearchCursor(outFeatureClass, "SHAPE@"):

            print("Processing row {0}".format(rowcounter))
            rowcounter += 1
            # Need to actually filter HAZARDS_FC so that we only work with the hazards in this specific DHA, otherwise we end up including hazards from neighhbouring DHA if they are close enough.
            # Create a temp FC from HAZARDS_FC that only contains the hazards falling in the DHA being processed. Need to get DHA ID from row[1]

            # Filter the HAZARDS_FC on the DHA from current row
            arcpy.SelectLayerByLocation_management("HAZARDS_FC", "WITHIN", row[0], "", "NEW_SELECTION", "")

            hazardsCount = arcpy.SelectLayerByLocation_management("HAZARDS_FC", "WITHIN", row2[0])

            # Loop through hazardsCount result to count number of records
            # Update other scripts to use this method, instead of looping through rows, a la get_keyfeatures.py!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!
            countHazards = 0 # Reset locally scoped counter
            result = arcpy.GetCount_management(hazardsCount)
            countHazards = int(result.getOutput(0))
            print("countHazards is now: {0}".format(countHazards))

            # Assign the hazard count to the fishnet polygon that is currently being processed.
            # Can we not use the row2 iterator?
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

        print("clusterDictionary is:")
        print(clusterDictionary)

        # Find the fishnet polygon with the highest value => primary cluster
        primeloc = keywithmaxval(clusterDictionary)
        primelocvalue = int(clusterDictionary[primeloc])
        print("1st maxvalkey is: {0} with value of {1}".format(primeloc, primelocvalue))

        # Delete this key from the dictionary
        del clusterDictionary[primeloc]

        # Find the next fishnet polygon with the highest value => secondary cluster
        secondloc = keywithmaxval(clusterDictionary)
        secondlocvalue = int(clusterDictionary[secondloc])
        print("2nd maxvalkey is: {0} with value of {1}".format(secondloc, secondlocvalue))

        print("clusterDictionary is now")
        print(clusterDictionary)

        # Delete the dictionary
        del clusterDictionary

        # Update the row with the new values
        row[2] = primeloc
        row[3] = primelocvalue
        row[4] = secondloc
        row[5] = secondlocvalue
        cursor.updateRow(row)

        print("==================================================================")
        print(" ")
        # Remove the fishnet in preparation for the next row in the DHA FC
        arcpy.Delete_management(outFeatureClass)

        # Remove the filter on the HAZARDS_FC by clearing the selection
        arcpy.SelectLayerByAttribute_management("HAZARDS_FC","CLEAR_SELECTION","")

# Remove the feature layer
arcpy.Delete_management("HAZARDS_FC")
