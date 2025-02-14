import requests
import json

# ipyleaflet imports
from ipyleaflet import GeoJSON
from IPython.display import Markdown, display
from pynhd import NLDI
from ipywidgets import HTML

# Import the popup content creator and hover logic
from gage_popup_utils import create_enhanced_popup_content, attach_gage_popups

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
                else:
                    if "attributes" in category_data and category_data["attributes"]:
                        output_md += "| Attribute | Value | Unit |\n"
                        output_md += "|---|---|---|\n"
                        for attr in category_data["attributes"]:
                            display_name = attr.get("display_name", "N/A")
                            value = attr.get("value", "N/A")
                            unit = attr.get("unit_of_measure", "N/A")
                            output_md += f"| {display_name} | {value} | {unit} |\n"
                        output_md += "\n"

        # Status Section
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
    """Fetches and displays watershed map layers (Stream Segment, Watershed, Flowlines, Streamgages) on the map."""
    nldi_query = NLDI()

    # 1. Using PyNHD for stream segment geometry
    try:
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

    # 2. Fetch Full Watershed Boundary
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

    # 3. Fetch Full Watershed Stream Network
    watershed_flowlines_url = (
        f"https://api.water.usgs.gov/nldi/linked-data/comid/{comid}/navigation/UT/flowlines"
        "?distance=9999&f=geojson"
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

    # 4. Fetching Streamgages with PyNHD
    try:
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

        # Attach hover-based popups for each gage
        attach_gage_popups(map_widget, gages_layer)

    except Exception as e:
        print(f"PyNHD streamgages retrieval failed: {e}")