# cell 5 streamcat report
import csv
import requests
from io import StringIO
from collections import defaultdict

def fetch_and_display_csv_data(url):
    response = requests.get(url)
    response.raise_for_status()  # Raise an error for bad responses

    # Split into lines, then skip the first 9 metadata lines
    lines = response.text.splitlines()[9:]
    
    # Create a CSV DictReader
    reader = csv.DictReader(lines)
    
    # Group rows by "Landscape Layer"
    grouped_data = defaultdict(list)
    for row in reader:
        grouped_data[row["Landscape Layer"]].append(row)
    
    # Output each group
    for layer, rows in grouped_data.items():
        print(layer)
        print("-------------------------------------------------")
        print("Metric Description                            |  Metric Value  |  AOI Percent Covered")
        print("----------------------------------------------|---------------|----------------------")
        
        for row in rows:
            # Combine Metric Value with Unit
            value_with_unit = f'{row["Metric Value"]}{row["Metric Unit of Measure"]}'
            print(f'{row["Metric Description"]:<45} | {value_with_unit:<14} | {row["AOI Percent Covered"]}')
        print("\n")  # Blank line between groups

# Usage
api_url = "https://api.epa.gov/waters/v2_5/streamcat_csv?pcomid=23997390&f=json&api_key=grRcWoOIWpPgTCG40v4MFRxR1MtxPfNOrkltHvY8"
fetch_and_display_csv_data(api_url)

# cell 1 Import necessary libraries
from ipyleaflet import Map, basemaps, Marker
from IPython.display import display
import requests
import json

# 1. Create Interactive Map
center_usa = (47.897, -123.111)  # Approximate center of USA
zoom_level = 8

usa_map = Map(center=center_usa, zoom=zoom_level, basemap=basemaps.Esri.WorldStreetMap)
display(usa_map)

# 2. Implement Map Click Handler (Initial - Print Coordinates)
from IPython.display import Markdown, display

def format_watershed_report(waters_data):
    """Formats the raw WATERS API JSON response into a readable Markdown report."""
    output_md = ""

    if "output" in waters_data and waters_data["output"]:
        output = waters_data["output"]

        # Header Section
        if "header" in output and output["header"]:
            header = output["header"]
            output_md += f"### {header.get('display_name', 'Watershed Data')}\n"
            if "attributes" in header and header["attributes"]:
                output_md += "| Attribute | Value | Unit |\n"
                output_md += "|---|---|---|\n"
                for attr in header["attributes"]:
                    display_name = attr.get("display_name", "N/A")
                    value = attr.get("value", "N/A")
                    unit = attr.get("unit_of_measure", "N/A")
                    output_md += f"| {display_name} | {value} | {unit} |\n"
                output_md += "\n"

        # Categories and Subcategories
        if "categories" in output and output["categories"]:
            categories = output["categories"]
            for category_data in categories:
                category_name = category_data.get("category", "N/A")
                category_display_name = category_data.get("display_name", category_name)
                output_md += f"#### Category: {category_display_name}\n"

                if "subcategories" in category_data and category_data["subcategories"]:
                    subcategories = category_data["subcategories"]
                    for subcategory_data in subcategories:
                        subcategory_name = subcategory_data.get("subcategory", "N/A")
                        subcategory_display_name = subcategory_data.get("display_name", subcategory_name)
                        output_md += f"##### Subcategory: {subcategory_display_name}\n"
                        if "attributes" in subcategory_data and subcategory_data["attributes"]:
                            output_md += "| Attribute | Value | Unit |\n"
                            output_md += "|---|---|---|\n"
                            for attr in subcategory_data["attributes"]:
                                display_name = attr.get("display_name", "N/A")
                                value = attr.get("value", "N/A")
                                unit = attr.get("unit_of_measure", "N/A")
                                output_md += f"| {display_name} | {value} | {unit} |\n"
                            output_md += "\n"
                else: # Categories without subcategories (if any)
                     if "attributes" in category_data and category_data["attributes"]:
                        output_md += "| Attribute | Value | Unit |\n"
                        output_md += "|---|---|---|\n"
                        for attr in category_data["attributes"]:
                            display_name = attr.get("display_name", "N/A")
                            value = attr.get("value", "N/A")
                            unit = attr.get("unit_of_measure", "N/A")
                            output_md += f"| {display_name} | {value} | {unit} |\n"
                        output_md += "\n"


        # Status Section (basic display for now)
        if "status" in output and output["status"]:
            status = output["status"]
            output_md += "\n**Status:**\n"
            output_md += f"* Status Code: {status.get('status_code', 'N/A')}\n"
            output_md += f"* Status Message: {status.get('status_message', 'N/A')}\n"
            output_md += f"* Execution Time: {status.get('execution_time', 'N/A')} seconds\n"


    else:
        output_md = "Error: Could not format Watershed Report data."

    return Markdown(output_md) # Return Markdown object for display

# Kwargs click below

def handle_map_click(event, **kwargs):
    """Handles map click, retrieves COMID from NLDI, fetches Watershed Report, and displays formatted report."""
    if kwargs.get('type') == 'click':
        latlng = kwargs.get('coordinates')
        latitude = latlng[0]
        longitude = latlng[1]

        # NLDI API URL for COMID
        nldi_url = f"https://api.water.usgs.gov/nldi/linked-data/comid/position?coords=POINT({longitude} {latitude})"
        api_key = 'grRcWoOIWpPgTCG40v4MFRxR1MtxPfNOrkltHvY8'  # Your API key

        try:
            # --- NLDI Request ---
            response_nldi = requests.get(url=nldi_url, headers={'accept': 'application/json'})
            response_nldi.raise_for_status()
            nldi_data = response_nldi.json()
            comid = None
            features = nldi_data.get('features', [])
            if features:
                properties = features[0].get('properties', {})
                comid = properties.get('comid')

            if comid:
                print(f"Clicked at Latitude: {latitude}, Longitude: {longitude}")
                print(f"NLDI COMID: {comid}")

                # --- EPA WATERS API Request (Watershed Report v2.5) ---
                waters_api_url = f"https://api.epa.gov/waters/v2_5/nhdplus_json?pcomid={comid}&f=json"
                headers = {'X-Api-Key': api_key}
                try:
                    response_waters = requests.get(waters_api_url, headers=headers)
                    response_waters.raise_for_status()
                    waters_data = response_waters.json()

                    # Format and Display the Watershed Report
                    formatted_report = format_watershed_report(waters_data) # Call the formatting function
                    display(formatted_report) # Display the formatted output

                except requests.exceptions.RequestException as e_waters:
                    print(f"Error: Failed to connect to EPA WATERS API (v2.5). {e_waters}")
                except json.JSONDecodeError:
                    print(f"Error: Could not decode JSON response from EPA WATERS API (v2.5).")


            else:
                print(f"Error: COMID not found in NLDI response. Cannot proceed to WATERS API.")

        except requests.exceptions.RequestException as e_nldi:
            print(f"Error: Failed to connect to NLDI API. {e_nldi}")
        except json.JSONDecodeError:
            print(f"Error: Could not decode JSON response from NLDI API.")
        except Exception as e:
            print(f"An unexpected error occurred: {e}")


usa_map.on_interaction(handle_map_click)

print("Click on the map to get NLDI COMID and Watershed data (v2.5) - Formatted Report!")

# cell 2 - Minimal addition for a Streamgage hover popup

from ipyleaflet import Map, basemaps, GeoJSON, Popup
from IPython.display import display, Markdown
import requests
import json

# PyNHD import
from pynhd import NLDI

# 1. Create Interactive Map
center_usa = (47.897, -123.111)  # Approximate center of USA
zoom_level = 9

usa_map = Map(center=center_usa, zoom=zoom_level, basemap=basemaps.Esri.WorldStreetMap)
display(usa_map)

# --- Formatting Function (No Changes) ---
from IPython.display import Markdown, display

def format_watershed_report(waters_data):
    """Formats the raw WATERS API JSON response into a readable Markdown report."""
    output_md = ""
    # ... (unchanged existing report code) ...
    return Markdown(output_md)

def display_map_layers(comid, map_widget):
    """Fetches and displays watershed map layers (Stream Segment, Watershed, HUC8, Streamgages) on the map."""
    # --- 1. Using PyNHD for stream segment geometry ---
    try:
        nldi_query = NLDI()
        flowlines_gdf = nldi_query.navigate_byid(
            fsource="comid",
            fid=str(comid),
            navigation="upstreamMain",
            source="flowlines",
            distance=9999
        )
        flowlines_geojson = json.loads(flowlines_gdf.to_crs(epsg=4326).to_json())
        segment_layer = GeoJSON(
            data=flowlines_geojson,
            style={'color': 'red', 'weight': 5, 'fillOpacity': 0}
        )
        map_widget.add_layer(segment_layer)
    except Exception as e:
        print(f"PyNHD stream segment retrieval failed: {e}")

    # --- 2. Fetch Full Watershed Boundary ---
    watershed_boundary_url = f"https://api.water.usgs.gov/nldi/linked-data/comid/{comid}/basin?f=geojson"
    try:
        response_watershed_boundary = requests.get(watershed_boundary_url)
        response_watershed_boundary.raise_for_status()
        watershed_boundary_data = response_watershed_boundary.json()
        watershed_boundary_layer = GeoJSON(
            data=watershed_boundary_data,
            style={'color': 'purple', 'weight': 3, 'fillOpacity': 0.1, 'dashArray': '5, 5'}
        )
        map_widget.add_layer(watershed_boundary_layer)
    except Exception as e:
        print(f"Error fetching watershed boundary: {e}")

    # --- 3. Fetch Full Watershed Stream Network ---
    watershed_flowlines_url = (
        f"https://api.water.usgs.gov/nldi/linked-data/comid/{comid}/navigation/UT/flowlines?distance=9999&f=geojson"
    )
    try:
        response_watershed_flines = requests.get(watershed_flowlines_url)
        response_watershed_flines.raise_for_status()
        watershed_flines_data = response_watershed_flines.json()
        watershed_flines_layer = GeoJSON(
            data=watershed_flines_data,
            style={'color': 'blue', 'weight': 2, 'fillOpacity': 0}
        )
        map_widget.add_layer(watershed_flines_layer)
    except Exception as e:
        print(f"Error fetching watershed flowlines: {e}")

    # --- 4. HUC8 Boundary - COMMENTED OUT FOR NOW ---
    # huc8_url = ...  # Placeholder

    # --- 5. FETCHING STREAMGAGES WITH PyNHD (unchanged from previous fix) ---
    """
    # Old approach (commented out):
    # streamgages_url = f"https://api.waterdata.usgs.gov/nldi/linked-data/comid/{comid}/nwissite?f=geojson"
    # ...
    """

    try:
        nldi_query = NLDI()
        gages_gdf = nldi_query.navigate_byid(
            fsource="comid",
            fid=str(comid),
            navigation="downstreamMain",
            source="nwissite",
            distance=9999
        )
        # Convert CR to EPSG:4326 for Leaflet
        gages_geojson = json.loads(gages_gdf.to_crs(epsg=4326).to_json())
        gages_layer = GeoJSON(
            data=gages_geojson,
            point_style={'radius': 6, 'color': 'black', 'fillColor': 'yellow', 'fillOpacity': 0.6}
        )
        map_widget.add_layer(gages_layer)

        # ---- NEW: Hover Popup for Streamgages ----
        def on_gages_hover(**kwargs):
            """Displays a popup with station info on mouseover."""
            if kwargs.get('type') == 'mousemove':
                feature = kwargs.get('feature')
                if feature:
                    props = feature.get('properties', {})
                    # Example station property keys, adjust as needed:
                    station_id = props.get('identifier', 'Unknown')
                    station_name = props.get('name', 'N/A')
                    station_type = "Gaging Station"  # or parse from props if available
                    latlng = kwargs.get('coordinates', [0, 0])

                    # Create a text block for the popup
                    popup_text = f"""
                    <b>Station ID:</b> {station_id}<br>
                    <b>Station Name:</b> {station_name}<br>
                    <b>Station Type:</b> {station_type}<br>
                    Latitude: {latlng[0]:.5f} | Longitude: {latlng[1]:.5f}<br>
                    """

                    # Create/Update popup
                    popup = Popup(
                        location=(latlng[0], latlng[1]),
                        child=HTML(popup_text),
                        close_button=False,
                        auto_close=True,
                        close_on_escape_key=True
                    )
                    map_widget.add_layer(popup)

        # Attach the callback to the gages layer
        gages_layer.on_interaction(on_gages_hover)

    except Exception as e:
        print(f"PyNHD streamgages retrieval failed: {e}")


def handle_map_click(event, **kwargs):
    """Handles map click, retrieves COMID from NLDI, fetches Watershed Report, and displays formatted report and map layers."""
    if kwargs.get('type') == 'click':
        latlng = kwargs.get('coordinates')
        latitude = latlng[0]
        longitude = latlng[1]

        # NLDI API URL for COMID
        nldi_url = f"https://api.water.usgs.gov/nldi/linked-data/comid/position?coords=POINT({longitude} {latitude})"
        api_key = 'grRcWoOIWpPgTCG40v4MFRxR1MtxPfNOrkltHvY8'  # Your API key

        try:
            response_nldi = requests.get(url=nldi_url, headers={'accept': 'application/json'})
            response_nldi.raise_for_status()
            nldi_data = response_nldi.json()
            comid = None
            features = nldi_data.get('features', [])
            if features:
                properties = features[0].get('properties', {})
                comid = properties.get('comid')

            if comid:
                print(f"Clicked at Latitude: {latitude}, Longitude: {longitude}")
                print(f"NLDI COMID: {comid}")

                # --- EPA WATERS API Request (Watershed Report v2.5) ---
                waters_api_url = f"https://api.epa.gov/waters/v2_5/nhdplus_json?pcomid={comid}&f=json"
                headers = {'X-Api-Key': api_key}
                try:
                    response_waters = requests.get(waters_api_url, headers=headers)
                    response_waters.raise_for_status()
                    waters_data = response_waters.json()

                    # Format and Display the Watershed Report
                    formatted_report = format_watershed_report(waters_data)
                    display(formatted_report)

                    # --- Fetch and display map layers ---
                    display_map_layers(comid, usa_map)

                except requests.exceptions.RequestException as e_waters:
                    print(f"Error: Failed to connect to EPA WATERS API (v2.5). {e_waters}")
                except json.JSONDecodeError:
                    print(f"Error: Could not decode JSON response from EPA WATERS API (v2.5).")

            else:
                print("Error: COMID not found in NLDI response. Cannot proceed to WATERS API.")

        except requests.exceptions.RequestException as e_nldi:
            print(f"Error: Failed to connect to NLDI API. {e_nldi}")
        except json.JSONDecodeError:
            print("Error: Could not decode JSON response from NLDI API.")
        except Exception as e:
            print(f"An unexpected error occurred: {e}")


usa_map.on_interaction(handle_map_click)
print("Click on the map to get NLDI COMID, Watershed data (v2.5), and Streamgage popup info!")

# cell 4 - StreamCat metrics CSV output

# Import necessary libraries
import pandas as pd
from pynhd.nhdplus_derived import streamcat

# Define the COMIDs to use
comids = [23997390, 23997391, 23997392]
# cell 11 - Save StreamCat metrics to CSV

# Import necessary libraries
import pandas as pd
from pynhd.nhdplus_derived import streamcat

# Define the COMIDs to use
comids = [23997390, 23997391, 23997392]

# Call the streamcat function with the COMIDs
try:
    streamcat_metrics = streamcat(comids=comids)
    
    # Convert the DataFrame to CSV format
    csv_output = streamcat_metrics.to_csv(index=False)
    
    # Print the CSV output
    print(csv_output)
    
    # Specify the file path to save the CSV
    file_path = "streamcat_metrics.csv"
    
    # Save the DataFrame to a CSV file
    streamcat_metrics.to_csv(file_path, index=False)
    print(f"CSV file saved successfully at {file_path}")
except Exception as e:
    print(f"An error occurred: {e}")
# Call the streamcat function with the COMIDs
try:
    streamcat_metrics = streamcat(comids=comids)
    
    # Convert the DataFrame to CSV format
    csv_output = streamcat_metrics.to_csv(index=False)
    
    # Print the CSV output
    print(csv_output)
except Exception as e:
    print(f"An error occurred: {e}")

    # cell 5 streamcat report
import csv
import requests
from io import StringIO
from collections import defaultdict

def fetch_and_display_csv_data(url):
    response = requests.get(url)
    response.raise_for_status()  # Raise an error for bad responses

    # Split into lines, then skip the first 9 metadata lines
    lines = response.text.splitlines()[9:]
    
    # Create a CSV DictReader
    reader = csv.DictReader(lines)
    
    # Group rows by "Landscape Layer"
    grouped_data = defaultdict(list)
    for row in reader:
        grouped_data[row["Landscape Layer"]].append(row)
    
    # Output each group
    for layer, rows in grouped_data.items():
        print(layer)
        print("-------------------------------------------------")
        print("Metric Description                            |  Metric Value  |  AOI Percent Covered")
        print("----------------------------------------------|---------------|----------------------")
        
        for row in rows:
            # Combine Metric Value with Unit
            value_with_unit = f'{row["Metric Value"]}{row["Metric Unit of Measure"]}'
            print(f'{row["Metric Description"]:<45} | {value_with_unit:<14} | {row["AOI Percent Covered"]}')
        print("\n")  # Blank line between groups

# Usage
api_url = "https://api.epa.gov/waters/v2_5/streamcat_csv?pcomid=23997390&f=json&api_key=grRcWoOIWpPgTCG40v4MFRxR1MtxPfNOrkltHvY8"
fetch_and_display_csv_data(api_url)

# cell 1

from ipyleaflet import Map, basemaps, Marker, GeoJSON
from IPython.display import display, Markdown
import requests
import json

# PyNHD import for flowlines and streamgages
from pynhd import NLDI

# Import streamgage popup module
from gage_popup_utils import create_enhanced_popup_content

# 1. Create Interactive Map
center_usa = (47.897, -123.111)  # Approximate center of USA
zoom_level = 9

usa_map = Map(center=center_usa, zoom=zoom_level, basemap=basemaps.Esri.WorldStreetMap)
display(usa_map)

# --- Formatting Function (No Changes) ---
from IPython.display import Markdown, display

def format_watershed_report(waters_data):
    """Formats the raw WATERS API JSON response into a readable Markdown report."""
    output_md = ""

    if "output" in waters_data and waters_data["output"]:
        output = waters_data["output"]

        # Header Section
        if "header" in output and output["header"]:
            header = output["header"]
            output_md += f"### {header.get('display_name', 'Watershed Data')}\n"
            if "attributes" in header and header["attributes"]:
                output_md += "| Attribute | Value | Unit |\n"
                output_md += "|---|---|---|\n"
                for attr in header["attributes"]:
                    display_name = attr.get("display_name", "N/A")
                    value = attr.get("value", "N/A")
                    unit = attr.get("unit_of_measure", "N/A")
                    output_md += f"| {display_name} | {value} | {unit} |\n"
                output_md += "\n"

        # Categories and Subcategories
        if "categories" in output and output["categories"]:
            categories = output["categories"]
            for category_data in categories:
                category_name = category_data.get("category", "N/A")
                category_display_name = category_data.get("display_name", category_name)
                output_md += f"#### Category: {category_display_name}\n"

                if "subcategories" in category_data and category_data["subcategories"]:
                    subcategories = category_data["subcategories"]
                    for subcategory_data in subcategories:
                        subcategory_name = subcategory_data.get("subcategory", "N/A")
                        subcategory_display_name = subcategory_data.get("display_name", subcategory_name)
                        output_md += f"##### Subcategory: {subcategory_display_name}\n"
                        if "attributes" in subcategory_data and subcategory_data["attributes"]:
                            output_md += "| Attribute | Value | Unit |\n"
                            output_md += "|---|---|---|\n"
                            for attr in subcategory_data["attributes"]:
                                display_name = attr.get("display_name", "N/A")
                                value = attr.get("value", "N/A")
                                unit = attr.get("unit_of_measure", "N/A")
                                output_md += f"| {display_name} | {value} | {unit} |\n"
                            output_md += "\n"
                else:  # Categories without subcategories (if any)
                     if "attributes" in category_data and category_data["attributes"]:
                        output_md += "| Attribute | Value | Unit |\n"
                        output_md += "|---|---|---|\n"
                        for attr in category_data["attributes"]:
                            display_name = attr.get("display_name", "N/A")
                            value = attr.get("value", "N/A")
                            unit = attr.get("unit_of_measure", "N/A")
                            output_md += f"| {display_name} | {value} | {unit} |\n"
                        output_md += "\n"

        # Status Section (basic display for now)
        if "status" in output and output["status"]:
            status = output["status"]
            output_md += "\n**Status:**\n"
            output_md += f"* Status Code: {status.get('status_code', 'N/A')}\n"
            output_md += f"* Status Message: {status.get('status_message', 'N/A')}\n"
            output_md += f"* Execution Time: {status.get('execution_time', 'N/A')} seconds\n"

    else:
        output_md = "Error: Could not format Watershed Report data."
    return Markdown(output_md)

def display_map_layers(comid, map_widget):
    """Fetches and displays watershed map layers (Stream Segment, Watershed, HUC8, Streamgages) on the map."""
    # --- 1. Using PyNHD for stream segment geometry ---
    try:
        nldi_query = NLDI()
        flowlines_gdf = nldi_query.navigate_byid(
            fsource="comid",
            fid=str(comid),
            navigation="upstreamMain",
            source="flowlines",
            distance=9999
        )
        flowlines_geojson = json.loads(flowlines_gdf.to_crs(epsg=4326).to_json())
        segment_layer = GeoJSON(
            data=flowlines_geojson,
            style={'color': 'red', 'weight': 5, 'fillOpacity': 0}
        )
        map_widget.add_layer(segment_layer)
    except Exception as e:
        print(f"PyNHD stream segment retrieval failed: {e}")

    # --- 2. Fetch Full Watershed Boundary ---
    watershed_boundary_url = f"https://api.water.usgs.gov/nldi/linked-data/comid/{comid}/basin?f=geojson"
    try:
        response_watershed_boundary = requests.get(watershed_boundary_url)
        response_watershed_boundary.raise_for_status()
        watershed_boundary_data = response_watershed_boundary.json()
        watershed_boundary_layer = GeoJSON(
            data=watershed_boundary_data,
            style={'color': 'purple', 'weight': 3, 'fillOpacity': 0.1, 'dashArray': '5, 5'}
        )
        map_widget.add_layer(watershed_boundary_layer)
    except Exception as e:
        print(f"Error fetching watershed boundary: {e}")

    # --- 3. Fetch Full Watershed Stream Network ---
    watershed_flowlines_url = (
        f"https://api.water.usgs.gov/nldi/linked-data/comid/{comid}/navigation/UT/flowlines?distance=9999&f=geojson"
    )
    try:
        response_watershed_flines = requests.get(watershed_flowlines_url)
        response_watershed_flines.raise_for_status()
        watershed_flines_data = response_watershed_flines.json()
        watershed_flines_layer = GeoJSON(
            data=watershed_flines_data,
            style={'color': 'blue', 'weight': 2, 'fillOpacity': 0}
        )
        map_widget.add_layer(watershed_flines_layer)
    except Exception as e:
        print(f"Error fetching watershed flowlines: {e}")

    # --- 5. FETCHING STREAMGAGES WITH PyNHD ---
    try:
        nldi_query = NLDI()
        gages_gdf = nldi_query.navigate_byid(
            fsource="comid",
            fid=str(comid),
            navigation="downstreamMain",
            source="nwissite",
            distance=9999
        )
        gages_geojson = json.loads(gages_gdf.to_crs(epsg=4326).to_json())
        gages_layer = GeoJSON(
            data=gages_geojson,
            point_style={'radius': 6, 'color': 'black', 'fillColor': 'yellow', 'fillOpacity': 0.6}
        )
        map_widget.add_layer(gages_layer)

        # Add popups to each gage
        for feature in gages_geojson['features']:
            gage = feature['properties']
            popup_content = create_enhanced_popup_content(gage)
            popup = Popup(
                location=(feature['geometry']['coordinates'][1], feature['geometry']['coordinates'][0]),
                child=HTML(popup_content),
                close_button=True,
                auto_close=False,
                close_on_escape_key=False
            )
            map_widget.add_layer(popup)

    except Exception as e:
        print(f"PyNHD streamgages retrieval failed: {e}")

def handle_map_click(event, **kwargs):
    """Handles map click, retrieves COMID from NLDI, fetches Watershed Report, and displays formatted report and map layers."""
    if kwargs.get('type') == 'click':
        latlng = kwargs.get('coordinates')
        latitude = latlng[0]
        longitude = latlng[1]

        # NLDI API URL for COMID
        nldi_url = f"https://api.water.usgs.gov/nldi/linked-data/comid/position?coords=POINT({longitude} {latitude})"
        api_key = 'grRcWoOIWpPgTCG40v4MFRxR1MtxPfNOrkltHvY8'  # Your API key

        try:
            response_nldi = requests.get(url=nldi_url, headers={'accept': 'application/json'})
            response_nldi.raise_for_status()
            nldi_data = response_nldi.json()
            comid = None
            features = nldi_data.get('features', [])
            if features:
                properties = features[0].get('properties', {})
                comid = properties.get('comid')

            if comid:
                print(f"Clicked at Latitude: {latitude}, Longitude: {longitude}")
                print(f"NLDI COMID: {comid}")

                # --- EPA WATERS API Request (Watershed Report v2.5) ---
                waters_api_url = f"https://api.epa.gov/waters/v2_5/nhdplus_json?pcomid={comid}&f=json"
                headers = {'X-Api-Key': api_key}
                try:
                    # Debug prints: ensure we see response details
                    print(f"[DEBUG] Requesting WATERS at {waters_api_url} ...")
                    response_waters = requests.get(waters_api_url, headers=headers)
                    print(f"[DEBUG] WATERS response status code: {response_waters.status_code}")
                    response_waters.raise_for_status()

                    waters_data = response_waters.json()
                    # Print some debug info about the returned JSON
                    print(f"[DEBUG] WATERS response keys: {list(waters_data.keys())}")

                    # Format and Display the Watershed Report
                    formatted_report = format_watershed_report(waters_data)
                    display(formatted_report)

                    # --- Fetch and display map layers ---
                    display_map_layers(comid, usa_map)

                except requests.exceptions.RequestException as e_waters:
                    print(f"Error: Failed to connect to EPA WATERS API (v2.5). {e_waters}")
                except json.JSONDecodeError:
                    print(f"Error: Could not decode JSON response from EPA WATERS API (v2.5).")

            else:
                print("Error: COMID not found in NLDI response. Cannot proceed to WATERS API.")

        except requests.exceptions.RequestException as e_nldi:
            print(f"Error: Failed to connect to NLDI API. {e_nldi}")
        except json.JSONDecodeError:
            print("Error: Could not decode JSON response from NLDI API.")
        except Exception as e:
            print(f"An unexpected error occurred: {e}")

usa_map.on_interaction(handle_map_click)

print("Click on the map to get NLDI COMID, Watershed data (v2.5), and Streamgage popup info!")

# cell 2 format streamcat report
def format_streamcat_report(api_url):
    """
    Fetches StreamCat CSV data and returns a Markdown object
    formatted similarly to the watershed report in cell 3. 
    """
    import requests
    import csv
    from io import StringIO
    from collections import defaultdict
    from IPython.display import Markdown

    try:
        response = requests.get(api_url)
        response.raise_for_status()
        all_lines = response.text.splitlines()

        # Skip the first 9 metadata lines
        lines = all_lines[9:]
        reader = csv.DictReader(lines)

        # Group rows by "Landscape Layer"
        grouped_data = defaultdict(list)
        for row in reader:
            grouped_data[row["Landscape Layer"]].append(row)

        # Build a Markdown string similar to cell 3's approach
        output_md = "### StreamCat Data Report\n\n"

        for layer, rows in grouped_data.items():
            output_md += f"#### Landscape Layer: {layer}\n"
            # Create a table heading
            output_md += "| Metric Description | Metric Value | AOI Percent Covered |\n"
            output_md += "|---|---|---|\n"

            for row in rows:
                desc = row["Metric Description"]
                val_with_unit = f"{row['Metric Value']}{row['Metric Unit of Measure']}"
                aoi_covered = row["AOI Percent Covered"]
                output_md += f"| {desc} | {val_with_unit} | {aoi_covered} |\n"
            output_md += "\n"

        return Markdown(output_md)

    except Exception as e:
        # Return a simple Markdown error message to match consistent styling
        return Markdown(f"**Error:** Could not format StreamCat report data. Details: {e}")
    
    # cell 3  -api call for streamcat report

api_url = "https://api.epa.gov/waters/v2_5/streamcat_csv?pcomid=23997390&f=json&api_key=grRcWoOIWpPgTCG40v4MFRxR1MtxPfNOrkltHvY8"
formatted_streamcat_report = format_streamcat_report(api_url)
display(formatted_streamcat_report)
# CELL 1: Full, corrected code with the needed import and function call

from ipyleaflet import Map, basemaps, Marker, GeoJSON, Popup
from IPython.display import display, Markdown, HTML
import requests
import json

# PyNHD import for flowlines and streamgages
from pynhd import NLDI

# Import streamgage popup module
from gage_popup_utils import create_enhanced_popup_content

# Import our StreamCat reporting function
from streamcat_data import display_streamcat_report_for_comid

# Assume these functions are defined in other cells (format_watershed_report, display_map_layers)
# so we do not modify them

# 1. Create Interactive Map
center_usa = (47.897, -123.111)  # Approximate center of USA
zoom_level = 9

usa_map = Map(center=center_usa, zoom=zoom_level, basemap=basemaps.Esri.WorldStreetMap)
display(usa_map)

def handle_map_click(event, **kwargs):
    """Handles map click, retrieves COMID from NLDI,
    fetches Watershed Report, and displays formatted report and map layers.
    Afterward, it also displays the StreamCat report."""
    if kwargs.get('type') == 'click':
        latlng = kwargs.get('coordinates')
        latitude = latlng[0]
        longitude = latlng[1]

        # NLDI API URL for COMID
        nldi_url = f"https://api.water.usgs.gov/nldi/linked-data/comid/position?coords=POINT({longitude} {latitude})"
        api_key = 'grRcWoOIWpPgTCG40v4MFRxR1MtxPfNOrkltHvY8'  # Your API key

        try:
            response_nldi = requests.get(url=nldi_url, headers={'accept': 'application/json'})
            response_nldi.raise_for_status()
            nldi_data = response_nldi.json()
            comid = None
            features = nldi_data.get('features', [])
            if features:
                properties = features[0].get('properties', {})
                comid = properties.get('comid')

            if comid:
                print(f"Clicked at Latitude: {latitude}, Longitude: {longitude}")
                print(f"NLDI COMID: {comid}")

                # --- EPA WATERS API Request (Watershed Report v2.5) ---
                waters_api_url = f"https://api.epa.gov/waters/v2_5/nhdplus_json?pcomid={comid}&f=json"
                headers = {'X-Api-Key': api_key}
                try:
                    # Debug prints: ensure we see response details
                    print(f"[DEBUG] Requesting WATERS at {waters_api_url} ...")
                    response_waters = requests.get(waters_api_url, headers=headers)
                    print(f"[DEBUG] WATERS response status code: {response_waters.status_code}")
                    response_waters.raise_for_status()

                    waters_data = response_waters.json()
                    # Print some debug info about the returned JSON
                    print(f"[DEBUG] WATERS response keys: {list(waters_data.keys())}")

                    # Format and Display the Watershed Report
                    formatted_report = format_watershed_report(waters_data)
                    display(formatted_report)

                    # --- Fetch and display map layers ---
                    display_map_layers(comid, usa_map)

                    # --- Display the StreamCat report for this COMID ---
                    display_streamcat_report_for_comid(comid)

                except requests.exceptions.RequestException as e_waters:
                    print(f"Error: Failed to connect to EPA WATERS API (v2.5). {e_waters}")
                except json.JSONDecodeError:
                    print("Error: Could not decode JSON response from EPA WATERS API (v2.5).")

            else:
                print("Error: COMID not found in NLDI response. Cannot proceed to WATERS API.")

        except requests.exceptions.RequestException as e_nldi:
            print(f"Error: Failed to connect to NLDI API. {e_nldi}")
        except json.JSONDecodeError:
            print("Error: Could not decode JSON response from NLDI API.")
        except Exception as e:
            print(f"An unexpected error occurred: {e}")

usa_map.on_interaction(handle_map_click)

print("Click on the map to get NLDI COMID, Watershed data (v2.5), Streamgage popup info, and StreamCat report!")

