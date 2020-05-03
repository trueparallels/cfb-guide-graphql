from flask import Flask
from flask_graphql import GraphQLView
from schema import schema
from waitress import serve

app = Flask(__name__)
# app.debug = True

app.add_url_rule('/graphql', view_func=GraphQLView.as_view('graphql', schema=schema, graphiql=True))

@app.route('/ok')
def ok():
    return "ok"

if __name__ == "__main__":
    serve(app, host='0.0.0.0', port=3003)
