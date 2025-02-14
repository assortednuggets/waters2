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
    Using the newer ipyleaflet callback signature: (event, feature, id, properties, ...)
    """

    def on_gages_hover(event, feature, id, properties, **kwargs):
        # Print out everything for debugging:
        print(f"[DEBUG] Hover event: {event}, feature: {feature}, id: {id}, coords: {kwargs.get('coordinates')}")

        if event == 'mouseover':
            # Create the popup content
            popup_content = create_enhanced_popup_content(properties or {})
            popup = Popup(
                location=kwargs.get('coordinates', (0, 0)),
                child=HTML(popup_content),
                close_button=False,
                auto_close=True,
                close_on_escape_key=True
            )
            map_widget.add_layer(popup)
            # Store the popup object so we can remove it later
            properties['popup'] = popup

        elif event == 'mouseout':
            popup = properties.get('popup')
            if popup:
                map_widget.remove_layer(popup)
                del properties['popup']

    gages_layer.on_hover(on_gages_hover)