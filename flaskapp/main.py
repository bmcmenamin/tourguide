"""
    List nearby places
"""

import api_interfaces
import graph_builder

from flask import Flask, request, render_template, jsonify

WIKI_URL = "https://en.wikipedia.org/wiki/{}"

APP = Flask(__name__)
APP.config['TEMPLATES_AUTO_RELOAD'] = True

TARGETS = ['Ernest_Shackleton']

nearby_finder = api_interfaces.NearbyFinder()
il_finder = api_interfaces.InLinkFinder()
ol_finder = api_interfaces.OutLinkFinder()



@APP.route('/', methods=['GET', 'POST'])
def index():
    """ Displays the index page accessible at '/'
    """
    if request.method == "POST":
        data = request.get_json()
        latitude, longitude = data['latitude'], data['longitude']
        nearby_places = nearby_finder.get_links((latitude, longitude))

        #latitude, longitude = 44.8113, -91.4985
        # Build an actual graph, connect nodes, select best paths

        # expand to find political boundaries, not just POI nearby
        nearby_concepts = expand_graph(nearby_places)

        target_concepts = expand_graph(TARGETS)

        # Add another connection layer that doesn't do full fan-out
        # so we get to depth (geo) - (geo+1) - (target + 1) - (target)
        dicts_nearby = [
            {"title": t, "url": WIKI_URL.format(t)}
            for t in nearby_concepts.intersection(target_concepts)
        ]

        return jsonify(results=dicts_nearby)

    return render_template('places.html')

if __name__ == '__main__':

    APP.run(debug=True)



