"""Utility functions for creating USGS streamgage popup content."""

from ipyleaflet import Popup
from ipywidgets import HTML

def create_enhanced_popup_content(gage):
    """
    Create enhanced popup content with additional information about a streamgage.
    """
    popup_content = f"""
    <div style="font-size: 8px; line-height: 1;">
        <b>Site No.:</b> {gage.get('identifier', 'N/A')}<br>
        <b>Station Name:</b> {gage.get('name', 'N/A')}<br>
        <b>Coordinates:</b> ({gage.get('shape', {}).get('coordinates', ['N/A', 'N/A'])[1]}, 
                            {gage.get('shape', {}).get('coordinates', ['N/A', 'N/A'])[0]})<br>
        <a href="https://waterdata.usgs.gov/nwis/inventory/?site_no={gage.get('identifier', '')}"
           target="_blank">More on USGS Website</a>
    </div>
    """
    return popup_content

def attach_gage_popups(map_widget, gages_layer):
    """
    Attach hover events to the gages_layer to display popups on mouseover.
    Using the ipyleaflet callback signature: (event, feature, id, properties, ...)
    """

    def on_gages_hover(event, feature, id, properties, **kwargs):
        print(f"[DEBUG] Hover event: {event}, feature: {feature}, id: {id}, coords: {kwargs.get('coordinates')}")

        if event == 'mouseover':
            coords = kwargs.get('coordinates', [0, 0])
            # Swap order, because ipyleaflet wants (lat, lon)
            lon, lat = coords[0], coords[1]

            # Prepare the popup content
            popup_content = create_enhanced_popup_content(properties or {})
            popup = Popup(
                location=(lat, lon),
                child=HTML(popup_content),
                close_button=False,
                auto_close=True,
                close_on_escape_key=True,
                auto_pan=False,  # Prevent map from jumping to this location
            )
            map_widget.add_layer(popup)
            properties['popup'] = popup

        elif event == 'mouseout':
            popup = properties.get('popup')
            if popup:
                map_widget.remove_layer(popup)
                del properties['popup']

    gages_layer.on_hover(on_gages_hover)