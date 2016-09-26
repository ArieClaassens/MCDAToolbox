# Adds the required fields to a feature class that only contains the spatial data of the DHA (which includes a boolean field identifying clearance status, i.e. Cleared = 1 or Cleared = 0)
import arcpy

#Global variables
TargetFC=arcpy.GetParameterAsText(0)

########################################################
#Code starts here
arcpy.AddMessage("\nStarting the Add MCE Fields Tool\n")

# Check if we can obtain a schema lock - adapted from https://pro.arcgis.com/en/pro-app/arcpy/functions/testschemalock.htm
if arcpy.TestSchemaLock(TargetFC):
	# Adopted from http://pro.arcgis.com/en/pro-app/arcpy/geoprocessing_and_python/writing-messages-in-script-tools.htm
	# If the target feature class is empty, create an error message, and raise an ExecuteError
	if int(arcpy.GetCount_management(TargetFC)[0]) == 0:
		arcpy.AddError("{0} has no features. Please use a feature class that already contains the required DHA polygons and attributes.".format(TargetFC))
		raise arcpy.ExecuteError

	# Add the fields required for the MCA weighting
	# Check if the field exists before creating it?
	arcpy.AddField_management(in_table=TargetFC, field_name="LANDCOVER", field_type="LONG", field_precision="", field_scale="", field_length="", field_alias="", field_is_nullable="NULLABLE", field_is_required="NON_REQUIRED", field_domain="")
	arcpy.AddMessage("LANDCOVER field added")
	arcpy.AddField_management(in_table=TargetFC, field_name="LANDCOVERWEIGHT", field_type="LONG", field_precision="", field_scale="", field_length="", field_alias="", field_is_nullable="NULLABLE", field_is_required="NON_REQUIRED", field_domain="")
	arcpy.AddMessage("LANDCOVERWEIGHT field added")
	arcpy.AddField_management(in_table=TargetFC, field_name="ASPECT", field_type="LONG", field_precision="", field_scale="", field_length="", field_alias="", field_is_nullable="NULLABLE", field_is_required="NON_REQUIRED", field_domain="")
	arcpy.AddMessage("ASPECT field added")
	arcpy.AddField_management(in_table=TargetFC, field_name="ASPECTWEIGHT", field_type="LONG", field_precision="", field_scale="", field_length="", field_alias="", field_is_nullable="NULLABLE", field_is_required="NON_REQUIRED", field_domain="")
	arcpy.AddMessage("ASPECTWEIGHT field added")
	arcpy.AddField_management(in_table=TargetFC, field_name="INFRASTRUCTURE", field_type="LONG", field_precision="", field_scale="", field_length="", field_alias="", field_is_nullable="NULLABLE", field_is_required="NON_REQUIRED", field_domain="")
	arcpy.AddMessage("INFRASTRUCTURE field added")
	arcpy.AddField_management(in_table=TargetFC, field_name="INFRASTRUCTUREWEIGHT", field_type="LONG", field_precision="", field_scale="", field_length="", field_alias="", field_is_nullable="NULLABLE", field_is_required="NON_REQUIRED", field_domain="")
	arcpy.AddMessage("INFRASTRUCTUREWEIGHT field added")
	arcpy.AddField_management(in_table=TargetFC, field_name="KEYFEATURES", field_type="LONG", field_precision="", field_scale="", field_length="", field_alias="", field_is_nullable="NULLABLE", field_is_required="NON_REQUIRED", field_domain="")
	arcpy.AddMessage("KEYFEATURES field added")
	arcpy.AddField_management(in_table=TargetFC, field_name="KEYFEATURESWEIGHT", field_type="LONG", field_precision="", field_scale="", field_length="", field_alias="", field_is_nullable="NULLABLE", field_is_required="NON_REQUIRED", field_domain="")
	arcpy.AddMessage("KEYFEATURESWEIGHT field added")
	arcpy.AddField_management(in_table=TargetFC, field_name="ACCIDENTS", field_type="LONG", field_precision="", field_scale="", field_length="", field_alias="", field_is_nullable="NULLABLE", field_is_required="NON_REQUIRED", field_domain="")
	arcpy.AddMessage("ACCIDENTS field added")
	arcpy.AddField_management(in_table=TargetFC, field_name="ACCIDENTSWEIGHT", field_type="LONG", field_precision="", field_scale="", field_length="", field_alias="", field_is_nullable="NULLABLE", field_is_required="NON_REQUIRED", field_domain="")
	arcpy.AddMessage("ACCIDENTSWEIGHT field added")
	arcpy.AddField_management(in_table=TargetFC, field_name="POI", field_type="LONG", field_precision="", field_scale="", field_length="", field_alias="", field_is_nullable="NULLABLE", field_is_required="NON_REQUIRED", field_domain="")
	arcpy.AddMessage("POI field added")
	arcpy.AddField_management(in_table=TargetFC, field_name="POIWEIGHT", field_type="LONG", field_precision="", field_scale="", field_length="", field_alias="", field_is_nullable="NULLABLE", field_is_required="NON_REQUIRED", field_domain="")
	arcpy.AddMessage("POIWEIGHT field added")
	arcpy.AddField_management(in_table=TargetFC, field_name="RIVERS", field_type="LONG", field_precision="", field_scale="", field_length="", field_alias="", field_is_nullable="NULLABLE", field_is_required="NON_REQUIRED", field_domain="")
	arcpy.AddMessage("RIVERS field added")
	arcpy.AddField_management(in_table=TargetFC, field_name="RIVERSWEIGHT", field_type="LONG", field_precision="", field_scale="", field_length="", field_alias="", field_is_nullable="NULLABLE", field_is_required="NON_REQUIRED", field_domain="")
	arcpy.AddMessage("RIVERSWEIGHT field added")
	arcpy.AddField_management(in_table=TargetFC, field_name="SLOPE", field_type="LONG", field_precision="", field_scale="", field_length="", field_alias="", field_is_nullable="NULLABLE", field_is_required="NON_REQUIRED", field_domain="")
	arcpy.AddMessage("SLOPE field added")
	arcpy.AddField_management(in_table=TargetFC, field_name="SLOPEWEIGHT", field_type="LONG", field_precision="", field_scale="", field_length="", field_alias="", field_is_nullable="NULLABLE", field_is_required="NON_REQUIRED", field_domain="")
	arcpy.AddMessage("SLOPEWEIGHT field added")
	arcpy.AddField_management(in_table=TargetFC, field_name="POPULATION", field_type="LONG", field_precision="", field_scale="", field_length="", field_alias="", field_is_nullable="NULLABLE", field_is_required="NON_REQUIRED", field_domain="")
	arcpy.AddMessage("POPULATION field added")
	arcpy.AddField_management(in_table=TargetFC, field_name="POPULATIONWEIGHT", field_type="LONG", field_precision="", field_scale="", field_length="", field_alias="", field_is_nullable="NULLABLE", field_is_required="NON_REQUIRED", field_domain="")
	arcpy.AddMessage("POPULATIONWEIGHT field added")
	arcpy.AddField_management(in_table=TargetFC, field_name="SCORE", field_type="LONG", field_precision="", field_scale="", field_length="", field_alias="", field_is_nullable="NULLABLE", field_is_required="NON_REQUIRED", field_domain="")
	arcpy.AddMessage("SCORE field added")
	arcpy.AddField_management(in_table=TargetFC, field_name="WEIGHTEDSCORE", field_type="LONG", field_precision="", field_scale="", field_length="", field_alias="", field_is_nullable="NULLABLE", field_is_required="NON_REQUIRED", field_domain="")
	arcpy.AddMessage("WEIGHTEDSCORE field added")
	arcpy.AddField_management(in_table=TargetFC, field_name="RANKING", field_type="TEXT", field_precision="", field_scale="", field_length="50", field_alias="", field_is_nullable="NULLABLE", field_is_required="NON_REQUIRED", field_domain="")
	arcpy.AddMessage("RANKING field added")
	arcpy.AddMessage("\nThe required fields were all added successfully.\n")
else:
	arcpy.AddError("Unable to acquire the necessary schema lock to add the new fields to {0}.".format(TargetFC))
	raise arcpy.ExecuteError
