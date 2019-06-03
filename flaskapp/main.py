"""
    List nearby places
"""

import api_interfaces
import graph_builder

from flask import Flask, request, render_template, jsonify

WIKI_URL = "https://en.wikipedia.org/wiki/{}"

APP = Flask(__name__)
APP.config['TEMPLATES_AUTO_RELOAD'] = True

# TODO: Load this stuff from disk/read from user input
TARGETS = [
    'Huey Long',
    'Richard Nixon',
    '1912 United States presidential election',
    '1968 United States presidential election',
    '1972 United States presidential election',
    'Progressive Party (United States, 1924–34)',
    'Socialist Party of America',
    'Industrial Workers of the World',
    'List of incidents of civil unrest in the United States',
    'Jazz',
    'Indie rock',
    'Psychedelic rock',
    'Musician',
    'Green Bay Packers',
    'Wisconsin Badgers',
    'Minnesota Golden Gophers',
    'Rock and Roll Hall of Fame',
    'Mathematician',
    'Scientist',
    'National Academy of Engineering',
    'National Academy of Science',
    'List of Nobel laureates',
    'Natural history',
    'Fossil',
    'Computer science',
    'Conspiracy theory',
    'Cryptozoology',
    'Fearsome critters',
    'Sea_monster',
    'Hoax',
    'Unidentified flying object',
    'List of cryptids',
]


@APP.route('/', methods=['GET', 'POST'])
def index():
    """ Displays the index page accessible at '/'
    """
    if request.method == "POST":
        data = request.get_json()
        latitude, longitude = data['latitude'], data['longitude']
        #latitude, longitude = 44.8113, -91.4985

        # TODO: break this up to load cached results
        artical_graph = (
            graph_builder.
            ArticleGraph().
            add_nearby(latitude, longitude, 100).
            add_targets(TARGETS).
            grow().
            find_all_paths()
        )

        # TODO: TURN PATHS INTO HTML HERE

        dicts_nearby = [
            {"title": paths[1].replace('_', ' '), "url": WIKI_URL.format(paths[1])}
            for targ, paths in ag.all_paths.items():
        ]

        return jsonify(results=dicts_nearby)

    return render_template('places.html')

if __name__ == '__main__':

    APP.run(debug=True)



