"""
    List nearby places
"""

import logging

from flask import Flask, request, jsonify, render_template

import article_network

logging.basicConfig(level=logging.DEBUG)

app = Flask(__name__)
app.config['TEMPLATES_AUTO_RELOAD'] = True

DEBUG = True
NUM_NEARBY = 30


@app.route('/', methods=['GET', 'POST'])
def index():
    """ Displays the index page accessible at '/'
    """

    print(request)
    if request.method == "POST":

        user_input = request.get_json()
        print(user_input)

        anet = article_network.ArticleNetwork()
        print(anet)

        logging.debug('Data sent to POST endpoint: %s', user_input)

        logging.info('Adding nearby nodes')
        anet.add_nearby(
            user_input['latitude'],
            user_input['longitude'],
            NUM_NEARBY
        )

        logging.info('Adding topic nodes')
        anet.add_topics(user_input['topics'])

        logging.debug('Pre-dilation article graph: %s', anet)
        logging.info('Dilating graph')
        anet.grow()
        logging.debug('Post-dilation article graph: %s', anet)

        logging.info('Searching for paths')
        anet.find_all_paths()

        return jsonify(**anet.get_nested_paths())

    return render_template('places.html')


if __name__ == '__main__':
    app.run(
        host='127.0.0.1',
        port=8080,
        debug=DEBUG
    )
