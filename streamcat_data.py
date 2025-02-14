import requests
import csv
from io import StringIO
from collections import defaultdict
from IPython.display import display, Markdown

def format_streamcat_report(api_url):
    """
    Fetches StreamCat CSV data and returns a Markdown object
    formatted similarly to the watershed report approach.
    """
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

        # Build a Markdown string
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


def display_streamcat_report_for_comid(comid):
    """
    Dynamically fetches a StreamCat CSV for the given COMID,
    formats it using the format_streamcat_report function,
    and displays the result as Markdown.
    """
    # Construct the StreamCat API URL using the provided COMID
    api_url = (
        "https://api.epa.gov/waters/v2_5/streamcat_csv"
        f"?pcomid={comid}&f=json&api_key=grRcWoOIWpPgTCG40v4MFRxR1MtxPfNOrkltHvY8"
    )

    # Format and display the resulting report
    formatted_report = format_streamcat_report(api_url)
    display(formatted_report)
