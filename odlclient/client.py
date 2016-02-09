import os
import json

import requests


_BASE_ODL_URL = 'http://%(host)s:%(port)s/restconf/config/'  # noqa


class ODL(object):

    def __init__(self, url, user, password):
        self.url = url
        self.user = user
        self.password = password

        self.nodes = NodeManager(self)

    @classmethod
    def get_client_with_env(clazz):
        return clazz(
            os.environ.get('ODL_URL',
                           _BASE_ODL_URL % {
                               'host': os.environ.get('ODL_HOST', 'localhost'),
                               'port': os.environ.get('ODL_PORT', 8181)}),
            os.environ.get('ODL_USER', 'admin'),
            os.environ.get('ODL_PASS', 'admin'))

    def get(self, resource):
        headers = {
            'Content-Type': 'application/json',
            'Accept': 'application/json',
        }

        resp = requests.get(
            '/'.join([self.url, resource]),
            auth=(self.user, self.password),
            headers=headers)
        # TODO Error
        return resp


class ResourceManager(object):
    def __init__(self, odl):
        self.odl = odl

    def list_all(self):
        resp = self.odl.get(self.resource_type)
        data_text = resp.text
        return self._as_objects(json.loads(data_text))

    def get(self, id):
        resp = self.odl.get('/'.join([self.resource_type, self.resource, id]))
        data_text = resp.text
        return self._as_object(json.loads(data_text))

    def _as_objects(self, data):
        return data

    def _as_object(self, data):
        return data


class NodeManager(ResourceManager):

    resource_type = 'opendaylight-inventory:nodes'
    resource = 'node'

    def _as_objects(self, data):
        return [Node.from_dict(d) for d in data['nodes']['node']]

    def _as_object(self, data):
        return Node.from_dict(data['node'][0])


class Node(object):

    @classmethod
    def from_dict(clazz, d):
        obj = clazz()
        obj.id = d['id']
        obj.tables = [
            Table.from_dict(t) for t in d['flow-node-inventory:table']]
        return obj

    def __repr__(self):
        return 'Node[%(id)s, %(tables)s]' % {
            'id': self.id,
            'tables': self.tables
        }


class Table(object):
    @classmethod
    def from_dict(clazz, d):
        obj = clazz()
        obj.id = d['id']
        obj.flows = [Flow.from_dict(f) for f in d.pop('flow')]
        return obj

    def __repr__(self):
        return 'Table[%(id)s, %(flows)s]' % {
            'id': self.id,
            'flows': self.flows
        }


class Flow(object):
    @classmethod
    def from_dict(clazz, d):
        obj = clazz()
        obj.id = d['id']
        obj.hard_timeout = d.get('hard_timeout')
        obj.barrier = d.get('barrier')
        obj.idle_timeout = d.get('idle_timeout')
        obj.priority = d.get('priority', 32768)
        obj.strict = d.get('strict')
        obj.table_id = d.get('table_id')
        obj.flow_name = d.get('flow_name')
        obj.match = d.get('match')
        obj.instructions = d.get('instructions')
        return obj

    def __repr__(self):
        return ('Flow[%(id)s, %(flow_name)s ,%(table_id)s ,%(hard_timeout)s ,'
                '%(idle_timeout)s ,%(barrier)s ,%(strict)s ,%(priority)s ,'
                '%(match)s ,%(instructions)s]') % {
            'id': self.id,
            'hard_timeout': self.hard_timeout,
            'barrier': self.barrier,
            'idle_timeout': self.idle_timeout,
            'priority': self.priority,
            'strict': self.strict,
            'table_id': self.table_id,
            'flow_name': self.flow_name,
            'match': json.dumps(self.match),
            'instructions': json.dumps(self.instructions),
        }
