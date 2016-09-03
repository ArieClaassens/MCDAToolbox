#-------------------------------------------------------------------------------
# Name:        main
# Purpose:     Loop through minefields and find all mines inside minefield polygon. Run clustering tool to determine if mines are clustered inside the minefield.
#
#               Be sure to project your data if your study area extends beyond 30 degrees. Chordal distances are not good estimators of geodesic distances beyond about 30 degrees.
#
# Background:   The problem is that minefields may be surveyd in terms of probable circumference, but there is no way of knowing where the mines are and where not.
#               How do we solve this problem?
#               Lets take old minefields and find the clusters inside them.
#                   Loop through each of the old minefields with Python and find the cluster within that specific minefield.
#                   Aggregate function using say 50m cut-off distance generates new FC with "clusters" and a lookup table referencing OIDs of mines!
#                       Request input from user for cut-off distance to aid in identifying the potential clusters, which could then be used to generate hot spots by counting the number of clusters in a minefield polygon or district..
#                   Now convert polygon to point with a weight field denoting number of mines that made up the polygon
#
#
#               (A) Lets also find the clusters of old minefields as a weight per district
#               Now lets classify the terrain and see how the classification matches up with the hot spots / cluster areas.
#               Is there a correlation between the clusters and the overall terrain classification?
#               Is there a correlation between the clusters and any specific terrain factor (which includes points of interest)?
#
#
# Data requirements:
#                   Mines FC
#                   Minefields FC
#                   Districts FC
#                   DEM
#                   POI FC
#
#
# Author:      aclaassens
#
# Created:     16-04-2016
# Copyright:   (c) aclaassens 2016
# Licence:     <your licence>
#-------------------------------------------------------------------------------

# import libraries required. Check case on Tkinter library
# Python GUI libraries
import Tkinter as tk
import ttk
import ScrolledText
import tkMessageBox as mBox
from Tkinter import Menu

# ArcGIS libraries
import arcpy
import MoransI

# Additional libraries e.g. R



# Global parameters
arcpy.env.overwriteOutput = "Yes"

# DEM & Analysis GeoDB
dbDEM='D:\Thesis\Data\Afg\DEM.gdb'
dbAN='D:\Thesis\Data\Afg\Afg_Dev.gdb'




# ==============================================================================
# Feature classes:
# AP_Mines_Updated - AP_Mines_Original with Weight field added (Short Integer) with default value of 1
# Completion_Polygon_Updated - Completion_Polygon_Original with Minecount field added (Long Integer) with default value of 0
# Completion_Polygon_Minecount - Completion_Polygon_Original with Minecount field added (Long Integer) with default value of 0. Use Spatial Join (https://geonet.esri.com/thread/33417) to get
#

# Use arcpy.SaveSettings to save settings to an XML file

# Replace a layer/table view name with a path to a dataset (which can be a layer file) or create the layer/table view within the script

# The following inputs are layers or table views: "Completion_Polygon_Updated", "AP_Mines_Updated"
#arcpy.SpatialJoin_analysis(target_features="Completion_Polygon_Updated", join_features="AP_Mines_Updated", out_feature_class="D:/Thesis/Data/Afg/Afg_Dev.gdb/Completion_Polygon_SpatialJoin", join_operation="JOIN_ONE_TO_ONE", join_type="KEEP_ALL", field_mapping="""OBJECTID_1 "OBJECTID_1" true true false 4 Long 0 0 ,First,#,Completion_Polygon_Updated,OBJECTID_1,-1,-1;OBJECTID_2 "OBJECTID_2" true true false 4 Long 0 0 ,First,#,Completion_Polygon_Updated,OBJECTID_2,-1,-1;OBJECTID "OBJECTID" true true false 4 Long 0 0 ,First,#,Completion_Polygon_Updated,OBJECTID,-1,-1;Id "Id" true true false 4 Long 0 0 ,First,#,Completion_Polygon_Updated,Id,-1,-1;ObjectUID "ObjectUID" true true false 40 Text 0 0 ,First,#,Completion_Polygon_Updated,ObjectUID,-1,-1;FeatureID "FeatureID" true true false 40 Text 0 0 ,First,#,Completion_Polygon_Updated,FeatureID,-1,-1;IsChild "IsChild" true true false 2 Short 0 0 ,First,#,Completion_Polygon_Updated,IsChild,-1,-1;ParentFeat "ParentFeat" true true false 40 Text 0 0 ,First,#,Completion_Polygon_Updated,ParentFeat,-1,-1;Annotation "Annotation" true true false 254 Text 0 0 ,First,#,Completion_Polygon_Updated,Annotation,-1,-1;Subtype "Subtype" true true false 50 Text 0 0 ,First,#,Completion_Polygon_Updated,Subtype,-1,-1;Type "Type" true true false 50 Text 0 0 ,First,#,Completion_Polygon_Updated,Type,-1,-1;Status "Status" true true false 50 Text 0 0 ,First,#,Completion_Polygon_Updated,Status,-1,-1;UserDefine "UserDefine" true true false 50 Text 0 0 ,First,#,Completion_Polygon_Updated,UserDefine,-1,-1;UserDefi_1 "UserDefi_1" true true false 50 Text 0 0 ,First,#,Completion_Polygon_Updated,UserDefi_1,-1,-1;UserDefi_2 "UserDefi_2" true true false 50 Text 0 0 ,First,#,Completion_Polygon_Updated,UserDefi_2,-1,-1;UserDefi_3 "UserDefi_3" true true false 50 Text 0 0 ,First,#,Completion_Polygon_Updated,UserDefi_3,-1,-1;UserDefi_4 "UserDefi_4" true true false 50 Text 0 0 ,First,#,Completion_Polygon_Updated,UserDefi_4,-1,-1;GazetteerR "GazetteerR" true true false 254 Text 0 0 ,First,#,Completion_Polygon_Updated,GazetteerR,-1,-1;LocationID "LocationID" true true false 40 Text 0 0 ,First,#,Completion_Polygon_Updated,LocationID,-1,-1;FilterToke "FilterToke" true true false 4 Long 0 0 ,First,#,Completion_Polygon_Updated,FilterToke,-1,-1;Shape_Leng "Shape_Leng" true true false 8 Double 0 0 ,First,#,Completion_Polygon_Updated,Shape_Leng,-1,-1;hazreduc_g "hazreduc_g" true true false 254 Text 0 0 ,First,#,Completion_Polygon_Updated,hazreduc_g,-1,-1;Region "Region" true true false 254 Text 0 0 ,First,#,Completion_Polygon_Updated,Region,-1,-1;Province "Province" true true false 254 Text 0 0 ,First,#,Completion_Polygon_Updated,Province,-1,-1;District "District" true true false 254 Text 0 0 ,First,#,Completion_Polygon_Updated,District,-1,-1;Village "Village" true true false 254 Text 0 0 ,First,#,Completion_Polygon_Updated,Village,-1,-1;Name "Name" true true false 254 Text 0 0 ,First,#,Completion_Polygon_Updated,Name,-1,-1;ID_1 "ID_1" true true false 254 Text 0 0 ,First,#,Completion_Polygon_Updated,ID_1,-1,-1;areasize "areasize" true true false 8 Double 0 0 ,First,#,Completion_Polygon_Updated,areasize,-1,-1;Stauts "Stauts" true true false 254 Text 0 0 ,First,#,Completion_Polygon_Updated,Stauts,-1,-1;Agency "Agency" true true false 254 Text 0 0 ,First,#,Completion_Polygon_Updated,Agency,-1,-1;Status_1 "Status_1" true true false 254 Text 0 0 ,First,#,Completion_Polygon_Updated,Status_1,-1,-1;Start_Date "Start_Date" true true false 8 Date 0 0 ,First,#,Completion_Polygon_Updated,Start_Date,-1,-1;End_Date "End_Date" true true false 8 Date 0 0 ,First,#,Completion_Polygon_Updated,End_Date,-1,-1;IMSMA_ID "IMSMA_ID" true true false 11 Text 0 0 ,First,#,Completion_Polygon_Updated,IMSMA_ID,-1,-1;REFERENCE "REFERENCE" true true false 25 Text 0 0 ,First,#,Completion_Polygon_Updated,REFERENCE,-1,-1;REPORTSTAR "REPORTSTAR" true true false 23 Text 0 0 ,First,#,Completion_Polygon_Updated,REPORTSTAR,-1,-1;REPORTENDD "REPORTENDD" true true false 23 Text 0 0 ,First,#,Completion_Polygon_Updated,REPORTENDD,-1,-1;AREACLEARE "AREACLEARE" true true false 8 Double 0 0 ,First,#,Completion_Polygon_Updated,AREACLEARE,-1,-1;CLEARANCED "CLEARANCED" true true false 8 Double 0 0 ,First,#,Completion_Polygon_Updated,CLEARANCED,-1,-1;QABY "QABY" true true false 254 Text 0 0 ,First,#,Completion_Polygon_Updated,QABY,-1,-1;TOWNNAME "TOWNNAME" true true false 50 Text 0 0 ,First,#,Completion_Polygon_Updated,TOWNNAME,-1,-1;LOCATOR "LOCATOR" true true false 43 Text 0 0 ,First,#,Completion_Polygon_Updated,LOCATOR,-1,-1;ORGANISATI "ORGANISATI" true true false 254 Text 0 0 ,First,#,Completion_Polygon_Updated,ORGANISATI,-1,-1;ENTRYDATE "ENTRYDATE" true true false 23 Text 0 0 ,First,#,Completion_Polygon_Updated,ENTRYDATE,-1,-1;TASKID "TASKID" true true false 21 Text 0 0 ,First,#,Completion_Polygon_Updated,TASKID,-1,-1;NUMTASKS "NUMTASKS" true true false 8 Double 0 0 ,First,#,Completion_Polygon_Updated,NUMTASKS,-1,-1;OWNERMAC "OWNERMAC" true true false 2 Text 0 0 ,First,#,Completion_Polygon_Updated,OWNERMAC,-1,-1;AREASQM "AREASQM" true true false 8 Double 0 0 ,First,#,Completion_Polygon_Updated,AREASQM,-1,-1;Shape_Le_1 "Shape_Le_1" true true false 8 Double 0 0 ,First,#,Completion_Polygon_Updated,Shape_Le_1,-1,-1;Shape_Le_2 "Shape_Le_2" true true false 8 Double 0 0 ,First,#,Completion_Polygon_Updated,Shape_Le_2,-1,-1;Shape_Length "Shape_Length" false true true 8 Double 0 0 ,First,#,Completion_Polygon_Updated,Shape_Length,-1,-1;Shape_Area "Shape_Area" false true true 8 Double 0 0 ,First,#,Completion_Polygon_Updated,Shape_Area,-1,-1;Minecount "Minecount" true true false 4 Long 0 0 ,First,#,Completion_Polygon_Updated,Minecount,-1,-1;IMSMA_ID_1 "IMSMA_ID" true true false 50 Text 0 0 ,First,#,AP_Mines_Updated,IMSMA_ID,-1,-1;MF_Name "MF_Name" true true false 50 Text 0 0 ,First,#,AP_Mines_Updated,MF_Name,-1,-1;Device "Device" true true false 50 Text 0 0 ,First,#,AP_Mines_Updated,Device,-1,-1;Area "Area" true true false 8 Double 0 0 ,First,#,AP_Mines_Updated,Area,-1,-1;POINT_X "POINT_X" true true false 8 Double 0 0 ,First,#,AP_Mines_Updated,POINT_X,-1,-1;POINT_Y "POINT_Y" true true false 8 Double 0 0 ,First,#,AP_Mines_Updated,POINT_Y,-1,-1;OBJECTID_12 "OBJECTID" true true false 4 Long 0 0 ,First,#,AP_Mines_Updated,OBJECTID,-1,-1;GIS_ID "GIS_ID" true true false 4 Long 0 0 ,First,#,AP_Mines_Updated,GIS_ID,-1,-1;Eastings "Eastings" true true false 8 Double 0 0 ,First,#,AP_Mines_Updated,Eastings,-1,-1;Northings "Northings" true true false 8 Double 0 0 ,First,#,AP_Mines_Updated,Northings,-1,-1;Weight "Weight" true true false 2 Short 0 0 ,Sum,#,AP_Mines_Updated,Weight,-1,-1""", match_option="COMPLETELY_CONTAINS", search_radius="", distance_field_name="")



# ==============================================================================
# Analysis options:

#   Optimized Hot Spot Analysis (Spatial Statistics) - Given incident points or weighted features (points or polygons), creates a map of statistically significant hot and cold spots using the Getis-Ord Gi* statistic. It evaluates the characteristics of the input feature class to produce optimal results. Incident data are points representing events (crime, traffic accidents) or objects (trees, stores) where your focus is on presence or absence rather than some measured attribute associated with each point. !!!! COUNT_INCIDENTS_WITHIN_AGGREGATION_POLYGONS - Use Completion_Polygon_Original - this leads to hot spots with very few mines.... Need to verify hot spot class by counting number of mines in hot spot (minefield) and maybe rank minefields in descending order of mines per hot spot?

# Aggregate Points (Cartography) - Creates polygon features around clusters of proximate point features. Polygons are created around clusters of three or more points within the aggregation distance. A one-to-many relationship table?named the same as the output feature class appended with _Tbl?will be created that links the aggregated polygons to their source point features. CANNOT MODIFY THE INPUT OR OUTPUT OTHERWISE LINKS MAY BE INVALIDATED.

#

#   Spatial Autocorrelation (Morans I) - Measures spatial autocorrelation based on feature locations and attribute values using the Global Moran's I statistic. You can access the results of this tool (including the optional report file) from the Results window. If you disable background processing, results will also be written to the Progress dialog box.

#   Average Nearest Neighbor - Calculates a nearest neighbor index based on the average distance from each feature to its nearest neighboring feature. Generates an HTML report as output..... Bit tricky to visualise but may be of use as an ad hoc report that is stored in filesystem

#   Hot Spot Analysis (Getis-Ord Gi*) - Given a set of weighted features, identifies statistically significant hot spots and cold spots using the Getis-Ord Gi* statistic. This tool identifies statistically significant spatial clusters of high values (hot spots) and low values (cold spots). It creates a new Output Feature Class with a z-score, p-value, and confidence level bin (Gi_Bin) for each feature in the Input Feature Class. GREAT to finding clusters of minefields across districts. Use Fixed Distance Band or Inverse Distance option? Latter? Need to aggregate mines first to obtain weights with varying values.

#   Cluster and Outlier Analysis (Anselin Local Moran's I) (Spatial Statistics) - Given a set of weighted features, identifies statistically significant hot spots, cold spots, and spatial outliers using the Anselin Local Moran's I statistic. This tool creates a new Output Feature Class with the following attributes for each feature in the Input Feature Class: Local Moran's I index, z-score, p-value, and cluster/outlier type (COType). ----- Could use this one to calculate minefield hotspots per district, using either the number of mines (more accurate on local scale but uniform weight for all mines, unless you combine different types of mines) or minefields (less accurate on local scale, but better weight values for each minefield) per district

#   Similarity Search - Identifies which candidate features are most similar or most dissimilar to one or more input features based on feature attributes. GREAT for the final analysis step

#   Minimum Bounding Geometry - Creates a feature class containing polygons which represent a specified minimum bounding geometry enclosing each input feature or each group of input features. GREAT to create an envelope (as opposed to convex hull) around a minefield and identify in which quadrant the majority of mines fall, e.g. North,East,South or West. Will need to create the envelope and then divide into 4 quads and count number of mines in each quad. May be easier with a fishnet?

#   Incremental Spatial Autocorrelation - Measures spatial autocorrelation for a series of distances and optionally creates a line graph of those distances and their corresponding z-scores. Z-scores reflect the intensity of spatial clustering, and statistically significant peak z-scores indicate distances where spatial processes promoting clustering are most pronounced. These peak distances are often appropriate values to use for tools with a Distance Band or Distance Radius parameter. Creates an output table and PDF report, optionally -- This tool can help you select an appropriate Distance Threshold or Radius for tools that have these parameters, such as Hot Spot Analysis or Point Density. The Input Field should contain a variety of values. The math for this statistic requires some variation in the variable being analyzed; it cannot solve if all input values are 1, for example. If you want to use this tool to analyze the spatial pattern of incident data, consider aggregating your incident data.

#   Point Density (Spatial Analyst) - Calculates a magnitude-per-unit area from point features that fall within a neighborhood around each cell. RASTER output

# FYI:
#   Grouping Analysis - uses Spatial Weights. Can we generate this from minefields FC or use minefield polygons?

######################
## Loop through DHA line by line in FC
## Use nearest neighbour / IDW to search for clusters
##
#######################

# PCL option -> http://docs.pointclouds.org/trunk/group__search.html


#-------------------------------------------------------------------------------

#Factors:
    #Landcover
    #Aspect
    #Infrastructure
    #Key Features
    #Accidents
    #POI
    #Rivers
    #Slope
    #Population

# Notes on factors
# need to find out max global value for factor to present to user/use in calc to find natural breaks? Or use global parameters stored in app config?

#-------------------------------------------------------------------------------
# SDSS priority calculation formulas
def LandCoverCalc():
    if Landcover==200:
       lc=1
    else:
        lc=3


def AspectCalc():
    if Aspect < 0:
        asp=0
    elif Aspect ==0 and Aspect < 22.6:
        asp=3
    elif Aspect > 22.5 and Aspect < 67.6:
        asp=2
    elif Aspect > 67.5 and Aspect < 112.6:
        asp=1
    elif Aspect > 112.5 and Aspect < 157.6:
        asp=0
    elif Aspect > 157.5 and Aspect < 202.6:
        asp=0
    elif Aspect > 202.5 and Aspect < 247.6:
        asp=0
    elif Aspect > 247.5 and Aspect < 292.6:
        asp=0
    elif Aspect > 292.5 and Aspect < 337.6:
        asp=2
    else:
        asp=3

def InfrastructureCalc():
    if Infrastructure == 0:
        infra=0
    elif Infrastructure == 1:
        infra=1
    elif Infrastructure == 2:
        infra=2
    else:
        infra=3

def KeyFeaturesCalc():
    if Key_Features ==0:
        kf=0
    elif Key_Features ==1:
        kf=1
    elif Key_Features==2:
        kf=2
    else:
        kf=3

def AccidentsCalc():
    if Accidents==0:
        acc=0
    elif Accidents ==1:
        acc=1
    elif Accidents==2:
        acc=2
    else:
        acc=3

def POICalc():
    if POI==0:
        poi=0
    elif POI ==1:
        poi=1
    elif POI==2:
        poi=2
    else:
        poi=3

def RiversCalc():
    if Rivers==0:
        rivers2=0
    elif Rivers==1:
        rivers2=1
    elif Rivers==2:
        rivers2=2
    else:
        rivers2=3

def SlopeCalc():
    if Slope==0:
        slp=0
    elif Slope > 15:
        slp=1
    elif Slope > 10 and Slope < 15:
        slp=2
    else:
        slp=3

def PopulationCalc():
    if Population==0:
        pop=0
    elif Population > 0 and Population < 51:
        pop=1
    elif Population > 50 and Population < 101:
        pop=2
    else:
        pop=3

def SDSSScoreCalc():
    SDSSscore = in_memory_pop + in_memory_lc + in_memory_slp + in_memory_rivers2 + in_memory_infra + in_memort_poi + in_memory_kf + in_memory_acc + in_memory_asp

def SDSSPriorityCalc():
    if Score < 6:
        SDSS_Priority = "Low"
    elif Score > 5 and Score < 9:
        SDSS_Priority = "Medium"
    else:
         SDSS_Priority = "High"

#Notes:
#Include option for cluster detection on detected mines per minefield?


# Local variables:
#point_shp = "C:\\temp\\point.shp"

# Process: Add Field
#arcpy.AddField_management(point_shp, "NEWFIELD", "TEXT", "", "", "25", "", "NON_NULLABLE", "NON_REQUIRED", "")



def main():
    win = tk.Tk()
    #Define GUI parameters
    win.title("Python GUI-based DeMiner PoC")
    win.geometry("600x600")
    win.resizable(1,1)
    # Change the main windows icon
    win.iconbitmap(r'C:\Python27\ArcGISx6410.4\DLLs\pyc.ico')

    # Modify adding a Label # 1
    aLabel = ttk.Label(win, text="Enter a name:") # 2
    aLabel.grid(column=0, row=0)

    # Button Click Event Callback Function
    def clickMe():
        action.configure(text='Hello ' + name.get()+ ' ' + numberChosen.get())
        action.configure(state='disabled')

    # Adding a Button
    action = ttk.Button(win, text="Click Me!", command=clickMe) # 7
    action.grid(column=2, row=1)

    # Adding a Textbox Entry widget # 5
    name = tk.StringVar() # 6
    nameEntered = ttk.Entry(win, width=12, textvariable=name) # 7
    nameEntered.grid(column=0, row=1) # 8
    nameEntered.focus() # Place cursor into name Entry

    ttk.Label(win, text="Choose a number:").grid(column=1, row=0) # 1
    number = tk.StringVar() # 2
    numberChosen = ttk.Combobox(win, width=12, textvariable=number, state='readonly') #Readonly limits input to existing values
    numberChosen['values'] = (1, 2, 4, 42, 100) # 4
    numberChosen.grid(column=1, row=1) # 5
    numberChosen.current(0)

    # Using a scrolled Text control # 3
    scrolW = 30 # 4
    scrolH = 3
    scr = ScrolledText.ScrolledText(win, width=scrolW, height=scrolH,wrap=tk.WORD) # 6
    scr.grid(column=0, columnspan=3)


    def _quit(): # 7
        win.quit()
        win.destroy()
        exit()

    menuBar = Menu(win)
    win.config(menu=menuBar)

    fileMenu = Menu(menuBar, tearoff=0)
    fileMenu.add_command(label="New")
    fileMenu.add_separator()
    fileMenu.add_command(label="Exit", command=_quit)
    menuBar.add_cascade(label="File", menu=fileMenu)

    # Display a Message Box
    # Callback function
    def _msgBox():
        mBox.showinfo('Info Box', 'A Python GUI created using Tkinter:\nThe year is 2016.')
        mBox.showwarning('Info Box', 'A Python GUI created using Tkinter:\nThe year is 2016.')
        mBox.showerror('Info Box', 'A Python GUI created using Tkinter:\nThe year is 2016.')
        answer = mBox.askyesno("Python Message Dual Choice Box", "Are you sure you really wish to do this?")
        print(answer)
        if answer == True:
            _quit()

    # Add another Menu to the Menu Bar and an item
    helpMenu = Menu(menuBar, tearoff=0)
    helpMenu.add_command(label="About", command=_msgBox)
    menuBar.add_cascade(label="Help", menu=helpMenu)



    # Fire up the GUI
    win.mainloop()

if __name__ == '__main__':
    main()
