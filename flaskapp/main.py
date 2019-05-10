"""
    List nearby places
"""

import api_interface
from flask import Flask, request, render_template, jsonify

WIKI_URL = "https://en.wikipedia.org/wiki/{}"

APP = Flask(__name__)
APP.config['TEMPLATES_AUTO_RELOAD'] = True

TARGETS = ['Ernest_Shackleton']

nearby_finder = api_interface.NearbyFinder()
il_finder = api_interface.InLinkFinder()
ol_finder = api_interface.OutLinkFinder()

def expand_graph(seed_nodes, max_depth=1, in_cutoff=5000, out_cutoff=500):

    nodes = set(seed_nodes)
    nodes_visited = set()

    for d in range(0, max_depth):
        for n in nodes - nodes_visited:
            in_links = il_finder.get_links(n, cutoff=in_cutoff)
            out_links = ol_finder.get_links(n, cutoff=out_cutoff)
            nodes.update(in_links)
            nodes.update(out_links)
            nodes_visited.add(n)
    return nodes


@APP.route('/', methods=['GET', 'POST'])
def index():
    """ Displays the index page accessible at '/'
    """
    if request.method == "POST":
        data = request.get_json()
        latitude, longitude = data['latitude'], data['longitude']
        nearby_places = nearby_finder.get_links(latitude, longitude)
        print(0)

        #latitude, longitude = 44.8113, -91.4985
        # Build an actual graph, connect nodes, select best paths

        # expand to find political boundaries, not just POI nearby
        nearby_concepts = expand_graph(nearby_places)
        print(1)

        target_concepts = expand_graph(TARGETS)
        print(2)

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



