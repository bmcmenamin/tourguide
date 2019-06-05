"""
    List nearby places
"""
import os
import collections

import graph_builder

from flask import Flask, request, render_template, jsonify

APP = Flask(__name__)
APP.config['TEMPLATES_AUTO_RELOAD'] = True


TARGET_FILE = os.path.join(
    os.path.curdir,
    'targets.txt'
)

DEBUG = False

def load_targets():

    target_list = []
    with open(TARGET_FILE, 'rt') as file:
        for line in file:
            target_list.append(
                line.strip().replace(" ", "_")
            )

    return target_list


def lols_to_dods(lols):
    temp_dict = collections.defaultdict(list)
    for l in lols:
        if len(l) > 1:
            temp_dict[l[0]].append(l[1:])

    if temp_dict:
        return {
            key: lols_to_dods(val)
            for key, val in temp_dict.items()
        }

    return sorted([l[0] for l in lols])


def dod_to_nestedlists(in_dod):

    if isinstance(in_dod, list):
        return in_dod

    return [
        [key, dod_to_nestedlists(val)]
        for key, val in in_dod.items()
    ]


@APP.route('/', methods=['GET', 'POST'])
def index():
    """ Displays the index page accessible at '/'
    """
    if request.method == "POST":

        data = request.get_json()
        article_graph = graph_builder.ArticleGraph()

        if DEBUG:
            latitude, longitude = 44.8113, -91.4985
            target_list = ['Green_Bay_Packers', 'Indie_rock']
        else:
            latitude, longitude = data['latitude'], data['longitude']
            target_list = load_targets()[]

        article_graph.add_nearby(latitude, longitude, 20)
        article_graph.add_targets(target_list)
        article_graph.grow()

        article_graph = article_graph.find_all_paths()

        dods_by_loc = lols_to_dods(
            path
            for pathlist in article_graph.all_paths.values()
            for path in pathlist
        )

        dods_by_topic = lols_to_dods(
            path[::-1]
            for pathlist in article_graph.all_paths.values()
            for path in pathlist
        )

        return jsonify(
            nested_lists_by_loc=dod_to_nestedlists(dods_by_loc),
            nested_lists_by_topic=dod_to_nestedlists(dods_by_topic)
        )

    return render_template('places.html')

if __name__ == '__main__':
    APP.run(debug=DEBUG)



