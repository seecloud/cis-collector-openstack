import leveldb
import sys
import json
from flask import Flask
from flask import jsonify
from flask_responses import json_response
from flask import request

app = Flask(__name__)
leveldb.DestroyDB('./db')
db = leveldb.LevelDB('./db')

@app.route('/api/<component>', methods=['GET'])
def get_keystone(component):
    service_data = {}
    code = 200
    try:
        service_data['data'] = db.Get(component)
        print service_data
        if service_data['data'] == 'null':
            raise KeyError
        return jsonify(service_data)
    except KeyError:
        print "No data found in db"
        service_data['data'] = {}
        code = 400
    return jsonify(service_data)

@app.route('/api/<component>/<service>', methods=['POST'])
def post_keystone(component, service):
    data = request.get_json(silent=True, force=True)
    component_data = {}
    try:
        component_data[component] = json.loads(db.Get(component))
    except KeyError:
        print "No data for {0} component found in db. Add new.".format(component)
        component_data[component] = {}

    component_data[component][service] = data 
    db.Put(component, json.dumps(component_data[component]))
    print "Data submitted to {0}:{1} index".format(component, service)
    return json_response({'response':'Success'}, status_code=201)

if __name__ == '__main__':
    app.run(host='0.0.0.0')
