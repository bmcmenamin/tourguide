"""
    List nearby places
"""
import collections
import logging

import graph_builder

from flask import Flask, request, render_template, jsonify

logging.basicConfig(level=logging.DEBUG)

app = Flask(__name__)
app.config['TEMPLATES_AUTO_RELOAD'] = True

DEBUG = True



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


@app.route('/', methods=['GET', 'POST'])
def index():
    """ Displays the index page accessible at '/'
    """

    if request.method == "POST":

        data = request.get_json()
        article_graph = graph_builder.ArticleGraph()
        logging.debug('Data sent to POST endpoint: %s', data)

        latitude, longitude = data['latitude'], data['longitude']
        topic_list = data['topics']

        logging.info('Adding nearby nodes')
        article_graph.add_nearby(latitude, longitude, 30)

        logging.info('Adding topic nodes')
        article_graph.add_topics(topic_list)

        logging.debug('Pre-dilation article graph: %s', article_graph)
        logging.info('Dilating graph')
        article_graph.grow()
        logging.debug('Post-dilation article graph: %s', article_graph)

        logging.info('Searching for paths')
        article_graph = article_graph.find_all_paths()

        dods_by_nearby = lols_to_dods(
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
            nested_lists_by_nearby=dod_to_nestedlists(dods_by_nearby),
            nested_lists_by_topic=dod_to_nestedlists(dods_by_topic)
        )

    return render_template('places.html')

if __name__ == '__main__':
    app.run(
        host='127.0.0.1',
        port=8080,
        debug=DEBUG
    )



