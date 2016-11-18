#    Copyright 2016 Mirantis, Inc.
#
#    Licensed under the Apache License, Version 2.0 (the "License"); you may
#    not use this file except in compliance with the License. You may obtain
#    a copy of the License at
#
#         http://www.apache.org/licenses/LICENSE-2.0
#
#    Unless required by applicable law or agreed to in writing, software
#    distributed under the License is distributed on an "AS IS" BASIS, WITHOUT
#    WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied. See the
#    License for the specific language governing permissions and limitations
#    under the License.


import json
import logging

import flask
import flask_responses
import leveldb


app = flask.Flask(__name__)
leveldb.DestroyDB('./db')
db = leveldb.LevelDB('./db')

logger = logging.getLogger("cis-server")
logger.setLevel(logging.DEBUG)


@app.route('/api/<component>', methods=['GET'])
def get_keystone(component):
    service_data = {}
    try:
        service_data['data'] = db.Get(component)
        logger.debug(service_data)
        if service_data['data'] == 'null':
            raise KeyError
        return flask.jsonify(service_data)
    except KeyError:
        logger.debug("No data found in db")
        service_data['data'] = {}
    return flask.jsonify(service_data)


@app.route('/api/<component>/<service>', methods=['POST'])
def post_keystone(component, service):
    data = flask.request.get_json(silent=True, force=True)
    component_data = {}
    try:
        component_data[component] = json.loads(db.Get(component))
    except KeyError:
        logger.debug("No data for {0} component found in db. Add new."
                     .format(component))
        component_data[component] = {}

    component_data[component][service] = data
    db.Put(component, json.dumps(component_data[component]))
    logger.debug("Data submitted to {0}:{1} index"
                 .format(component, service))
    return flask_responses.json_response({'response': 'Success'},
                                         status_code=201)


if __name__ == '__main__':
    app.run(host='0.0.0.0')
