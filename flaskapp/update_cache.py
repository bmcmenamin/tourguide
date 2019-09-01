"""
    Update from top pages
"""

from flask import Flask, jsonify, make_response
import wikidata_interfaces as wi


app = Flask(__name__)
app.config['TEMPLATES_AUTO_RELOAD'] = True
app.secret_key = "OHnM3KAkTEhsI&j6"


BATCH_SIZE = 200
MAX_PAGES = 10000


@app.route('/update-cache', methods=['GET'])
def run_update(batch_size=BATCH_SIZE):

    for offset in range(0, MAX_PAGES, batch_size):
        page_titles = wi.MostViewedFinder().get_payload(batch_size, offset)
        wi.OutLinkFinder().get_payload(page_titles)
        wi.InLinkFinder().get_payload(page_titles)
        wi.CategoryFinder().get_payload(page_titles)

    return make_response(jsonify(page_titles), 200)


if __name__ == '__main__':
    app.run(
        host='127.0.0.1',
        port=8080,
        debug=True
    )