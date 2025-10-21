# -*- coding: utf-8 -*-
import arcpy
import webbrowser
import os

class Toolbox:
    def __init__(self):
        """Define the toolbox (the name of the toolbox is the name of the
        .pyt file)."""
        self.label = "Google Maps Tools"
        self.alias = "googlemaps"
        self.description = "Tools for opening locations in Google Maps"
        # List of tool classes associated with this toolbox
        self.tools = [OpenGoogleMaps]

class OpenGoogleMaps:
    def __init__(self):
        """Define the tool (tool name is the name of the class)."""
        self.label = "Open Location in Google Maps"
        self.description = "Click on the map to open that location in Google Maps"
        self.canRunInBackground = False

    def getParameterInfo(self):
        """Define the tool parameters."""
        # Use GPFeatureRecordSetLayer with proper initialization
        param0 = arcpy.Parameter(
            displayName="Click on map to select location",
            name="input_point",
            datatype="GPFeatureRecordSetLayer",
            parameterType="Required",
            direction="Input")
        
        # Create the feature set properly
        # First create a temporary feature class to use as template
        temp_workspace = arcpy.env.scratchGDB
        temp_fc_name = "temp_point_template"
        temp_fc_path = os.path.join(temp_workspace, temp_fc_name)
        
        # Delete if exists
        if arcpy.Exists(temp_fc_path):
            arcpy.management.Delete(temp_fc_path)
        
        # Create temporary point feature class
        temp_fc = arcpy.management.CreateFeatureclass(
            temp_workspace,
            temp_fc_name,
            "POINT",
            spatial_reference=arcpy.SpatialReference(4326)  # WGS84
        )
        
        # Create feature set from the template
        feature_set = arcpy.FeatureSet(temp_fc)
        param0.value = feature_set
        
        # Clean up the temporary feature class
        arcpy.management.Delete(temp_fc)
        
        # Optional zoom level parameter
        param1 = arcpy.Parameter(
            displayName="Google Maps Zoom Level (1-20)",
            name="zoom_level",
            datatype="GPLong",
            parameterType="Optional",
            direction="Input")
        
        param1.value = 15  # Default zoom level
        
        params = [param0, param1]
        return params

    def isLicensed(self):
        """Set whether the tool is licensed to execute."""
        return True

    def updateParameters(self, parameters):
        """Modify the values and properties of parameters before internal
        validation is performed.  This method is called whenever a parameter
        has been changed."""
        return

    def updateMessages(self, parameters):
        """Modify the messages created by internal validation for each tool
        parameter. This method is called after internal validation."""
        
        # Validate zoom level
        if parameters[1].value is not None:
            if parameters[1].value < 1 or parameters[1].value > 20:
                parameters[1].setErrorMessage("Zoom level must be between 1 and 20")
        
        return

    def execute(self, parameters, messages):
        """The source code of the tool."""
        try:
            # Get parameters
            input_features = parameters[0].value
            zoom_level = parameters[1].value if parameters[1].value else 15
            
            # Check if input_features is valid
            if input_features is None:
                arcpy.AddError("No input features provided. Please click on the map to select a location.")
                return
            
            # Get count of input features
            try:
                result = arcpy.management.GetCount(input_features)
                feature_count = int(result[0])
            except:
                arcpy.AddError("Could not read input features. Please try clicking on the map again.")
                return
            
            if feature_count == 0:
                arcpy.AddError("No location selected. Please click on the map to select a location.")
                return
            
            arcpy.AddMessage(f"Processing {feature_count} location(s)...")
            
            # Get the active map's spatial reference for context
            try:
                aprx = arcpy.mp.ArcGISProject("CURRENT")
                active_map = aprx.activeMap
                map_sr = active_map.spatialReference
                arcpy.AddMessage(f"Map coordinate system: {map_sr.name}")
            except:
                arcpy.AddWarning("Could not get active map reference, continuing...")
            
            # Process the input features
            with arcpy.da.SearchCursor(input_features, ["SHAPE@"]) as cursor:
                for row in cursor:
                    point_geom = row[0]
                    
                    if point_geom is None:
                        arcpy.AddWarning("Skipping null geometry")
                        continue
                    
                    # Project to WGS84 if needed (Google Maps uses WGS84)
                    sr_wgs84 = arcpy.SpatialReference(4326)
                    
                    if point_geom.spatialReference.factoryCode != 4326:
                        arcpy.AddMessage(f"Projecting from {point_geom.spatialReference.name} to WGS84...")
                        point_geom = point_geom.projectAs(sr_wgs84)
                    
                    # Extract latitude and longitude
                    lat = point_geom.centroid.Y
                    lon = point_geom.centroid.X
                    
                    # Validate coordinates
                    if abs(lat) > 90 or abs(lon) > 180:
                        arcpy.AddError(f"Invalid coordinates: Lat={lat}, Lon={lon}")
                        continue
                    
                    # Create Google Maps URL
                    google_maps_url = f"https://www.google.com/maps?q={lat},{lon}&z={zoom_level}"
                    
                    # Add message to the tool output
                    arcpy.AddMessage(f"Opening location ({lat:.6f}, {lon:.6f}) in Google Maps...")
                    arcpy.AddMessage(f"URL: {google_maps_url}")
                    
                    # Open in default browser
                    webbrowser.open(google_maps_url)
                    
                    # Only process the first point
                    break
            
            arcpy.AddMessage("Google Maps opened successfully!")
            
        except Exception as e:
            arcpy.AddError(f"Error opening Google Maps: {str(e)}")
            import traceback
            arcpy.AddError(traceback.format_exc())
        
        return

    def postExecute(self, parameters):
        """This method takes place after outputs are processed and
        added to the display."""
        return