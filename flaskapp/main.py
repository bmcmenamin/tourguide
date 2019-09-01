"""
    List nearby places
"""
import collections
import uuid

from flask import (
    Flask, Response, request, session, jsonify, render_template, make_response
)

import article_network


app = Flask(__name__)
app.config['TEMPLATES_AUTO_RELOAD'] = True
app.secret_key = "OHnM3KAkTEhsI&j6"


NUM_NEARBY = 15


@app.route('/clearSession', methods=['POST'])
def clear_session():
    session.clear()
    session.modified = True
    app.logger.info('Hit endpoint /clearSession')
    return make_response(jsonify({}), 200)


@app.route('/setLocation', methods=['POST'])
def set_location():
    user_input = request.get_json()

    session['latlon'] = (
        round(user_input['latitude'], 4),
        round(user_input['longitude'], 4)
    )

    app.logger.info(
        'Data received at endpoint /setLocation: %s',
        session['latlon']
    )

    return make_response(jsonify(session['latlon']), 200)


@app.route('/setTopics', methods=['POST'])
def set_topics():
    session['topics'] = request.get_json()
    app.logger.info(
        'Data received at endpoint /setTopics: %s',
        session['topics']
    )
    return make_response(jsonify(session['topics']), 200)


@app.route('/runQuery', methods=['POST'])
def run_query():
    output = {}
    anet = article_network.ArticleNetwork(session['latlon'])

    # Add nearby
    app.logger.info('Adding nearby nodes')
    anet.add_nearby(NUM_NEARBY)
    output['nearby_seeds'] = list(sorted(anet.nearby.seed_nodes))

    # Add topics
    app.logger.info('Adding topic nodes')
    anet.add_topics(session['topics'])
    output['topic_seeds'] = list(sorted(anet.topics.seed_nodes))

    app.logger.info('Pre-dilation article graph: %s', anet)

    # Dilate
    app.logger.info('Dilating graph')
    anet.grow()
    app.logger.info('Post-dilation article graph: %s', anet)

    app.logger.info('Searching for paths')
    anet.find_all_paths()

    output['path_status'] = anet.path_status()
    output.update(anet.get_nested_paths())

    app.logger.info('Returning output %s', output)
    return make_response(jsonify(**output), 200)


@app.route('/', methods=['GET'])
def index():
    """ Displays the index page accessible at '/'
    """
    return render_template('places.html')


if __name__ == '__main__':
    app.run(
        host='127.0.0.1',
        port=8080,
        debug=True
    )
