"""
    List interesting nearby places
"""
from typing import Optional
import folium

from flask import (
    Flask, Response, request, session, jsonify, render_template, make_response
)

app = Flask(__name__)
app.config['TEMPLATES_AUTO_RELOAD'] = True
app.secret_key = "OHnM3KAkTEhsI&j6"

MAP_DEFAULT = {
    "location": [41.850033, -87.6500523],
    "zoom_start": 3,
    "tiles": "cartodb positron"
}


def _create_folium_map() -> folium.Map:

    # Create a Folium map centered at a specific location
    m = folium.Map(**MAP_DEFAULT)

    # Add a marker to the map
    folium.Marker(
        location=[37.7749, -122.4194],
        popup='San Francisco',
        icon=folium.Icon(color='blue')
    ).add_to(m)

    return m


def _render_folium_map(folium_map: folium.Map, title: Optional[str] = None) -> None:

    # Create a custom HTML overlay for the article_id
    overlay_html = f"""
    <div style="position: fixed; top: 10px; left: 50%; z-index: 1000; background: white; padding: 10px; border-radius: 5px;">
        <h3>{title}</h3>
    </div>
    """

    # Add the overlay to the map
    if title:
        folium_map.get_root().html.add_child(folium.Element(overlay_html))

    return folium_map.get_root().render()


@app.route('/')
def map_view():
    article_id = request.args.get("article_id")
    folium_map = _create_folium_map()
    return _render_folium_map(folium_map, article_id)


if __name__ == '__main__':
    app.run(
        host='127.0.0.1',
        port=8080,
        debug=True
    )
