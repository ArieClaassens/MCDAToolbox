#https://community.esri.com/thread/139164
import arcpy

# reference your raster
ras = r"D:\Thesis\Data\Afg\ESA\ESACCI-LC-L4-LCCS-Map-300m-P5Y-2010-v1.6.1.tif"
raster = arcpy.Raster(ras)

# determine number of pixels
cnt_pix = raster.height * raster.width

# determine if raster has no data values
if int(arcpy.GetRasterProperties_management(ras, "ANYNODATA").getOutput(0)) == 1:

    # determine if raster has all data values
    if int(arcpy.GetRasterProperties_management(ras, "ALLNODATA").getOutput(0)) == 1:
        print "All cells of raster are NoData"
        print "Data pixels  : {0} ({1}%)".format(0, 0.0)
        print "Nodata pixels: {0} ({1}%)".format(cnt_pix, 100.0)

    else:
        # handle integer different from float
        if raster.isInteger and raster.hasRAT:
            print "Integer raster with RAT"
            lst_cnt = [r.COUNT for r in arcpy.SearchCursor(raster)]
            cnt_data = sum(lst_cnt)
            cnt_nodata = cnt_pix - cnt_data

        else:
            # raster is float or has no RAT, determine nodata pixels
            print "Floating raster"
            arcpy.CheckOutExtension("Spatial")
            ras_isn = arcpy.sa.IsNull(raster)
            arcpy.CheckInExtension("Spatial")

            where = "VALUE = 1"
            lst_cnt = [r.COUNT for r in arcpy.SearchCursor(ras_isn, where_clause=where)]
            cnt_nodata = sum(lst_cnt)
            cnt_data = cnt_pix - cnt_nodata

        # now determine percentages
        print "Data pixels  : {0} ({1}%)".format(cnt_data, round(float(cnt_data) * 100.0 / float(cnt_pix),2))
        print "Nodata pixels: {0} ({1}%)".format(cnt_nodata, round(float(cnt_nodata) * 100.0 / float(cnt_pix),2))

else:
    print "Raster without NoData"
    print "Data pixels  : {0} ({1}%)".format(cnt_pix, 100.0)
    print "Nodata pixels: {0} ({1}%)".format(0, 0.0)