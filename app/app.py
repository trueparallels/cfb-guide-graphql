from flask import Flask
from flask_graphql import GraphQLView
from schema import schema
from waitress import serve
import sys
from logging.config import dictConfig

dictConfig({
    'version': 1,
    'formatters': {'default': {
        'format': '[%(asctime)s] %(levelname)s in %(module)s: %(message)s',
    }},
    'handlers': {'wsgi': {
        'class': 'logging.StreamHandler',
        'stream': 'ext://sys.stdout',
        'formatter': 'default'
    }},
    'root': {
        'level': 'INFO',
        'handlers': ['wsgi']
    }
})

app = Flask(__name__)
# app.debug = True

app.add_url_rule('/graphql', view_func=GraphQLView.as_view('graphql', schema=schema, graphiql=True))

@app.route('/ok')
def ok():
    app.logger.info("health check passed")
    return "ok"

if __name__ == "__main__":
    app.logger.info("app started")
    serve(app, host='0.0.0.0', port=3003)
