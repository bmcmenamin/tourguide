"""
    List nearby places
"""
import collections
import logging
import uuid

from flask import Flask, request, jsonify, render_template

import article_network

logging.basicConfig(level=logging.INFO)

app = Flask(__name__)
app.config['TEMPLATES_AUTO_RELOAD'] = True

DEBUG = True
NUM_NEARBY = 30

REQUEST_STATUSES = collections.defaultdict(list)


@app.route('/queryStatus', methods=['POST'])
def query_status():
    request_id = request.get_json()['request_id']
    status_dict = {"query_status": REQUEST_STATUSES[request_id]}
    return jsonify(status_dict)


@app.route('/runQuery', methods=['POST'])
def run_query():
    """ Displays the index page accessible at '/'
    """
    user_input = request.get_json()
    user_latlon = (user_input['latitude'], user_input['longitude'])
    output = {}
    logging.debug('Data received as POST endpoint: %s', user_input)

    anet = article_network.ArticleNetwork(user_latlon)

    REQUEST_STATUSES[user_input['request_id']] = ["Starting search"]

    # Add nearby
    logging.info('Adding nearby nodes')
    anet.add_nearby(NUM_NEARBY)
    output['nearby_seeds'] = list(sorted(anet.nearby.seed_nodes))
    REQUEST_STATUSES[user_input['request_id']].append(
        "Using {} points of interest near ({:.2f}, {:.2f})".format(
            len(output['nearby_seeds']), user_latlon[0], user_latlon[1]
        )
    )

    # Add topics
    logging.info('Adding topic nodes')
    anet.add_topics(user_input['topics'])
    output['topic_seeds'] = list(sorted(anet.topics.seed_nodes))
    REQUEST_STATUSES[user_input['request_id']].append(
        "Found {} topic(s) of interest".format(
            len(output['topic_seeds'])
        )
    )

    logging.debug('Pre-dilation article graph: %s', anet)

    # Dilate
    logging.info('Dilating graph')
    REQUEST_STATUSES[user_input['request_id']].append(
        "Looking for connections (be patient)"
    )
    anet.grow()
    logging.debug('Post-dilation article graph: %s', anet)

    logging.info('Searching for paths')
    REQUEST_STATUSES[user_input['request_id']].append(
        "... almost done"
    )
    anet.find_all_paths()

    REQUEST_STATUSES.pop(user_input['request_id'], None)
    output['path_status'] = anet.path_status()
    output.update(anet.get_nested_paths())

    logging.info('Returning output %s', output)
    return jsonify(**output)


@app.route('/', methods=['GET'])
def index():
    """ Displays the index page accessible at '/'
    """
    return render_template('places.html')


if __name__ == '__main__':
    app.run(
        host='127.0.0.1',
        port=8080,
        debug=DEBUG
    )
