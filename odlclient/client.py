from __future__ import print_function

import os
import json

import requests
import six


_BASE_ODL_URL = 'http://%(host)s:%(port)s/restconf/operational/'


class ODL(object):

    def __init__(self, url, user, password):
        self.url = url
        self.user = user
        self.password = password

        self.nodes = NodeManager(self)

        self.debug = False
        self.verbose = False

    @classmethod
    def get_client_with_env(clazz):
        return clazz(
            os.environ.get('ODL_URL',
                           _BASE_ODL_URL % {
                               'host': os.environ.get('ODL_HOST', 'localhost'),
                               'port': os.environ.get('ODL_PORT', 8181)}),
            os.environ.get('ODL_USER', 'admin'),
            os.environ.get('ODL_PASS', 'admin'))

    def _log_http(self, url, headers, resp):

        if not self.debug:
            return

        msg = ('DEBUG(request): curl -i %(headers)s -u "%(user)s:%(password)s"'
               ' -X GET "%(url)s"')
        formatted_headers = ' '.join(
            ['-H "' + ': '.join([k, v]) + '"'
             for k, v in six.iteritems(headers)])
        print(msg % {
            'headers': formatted_headers,
            'user': self.user,
            'password': self.password,
            'url': url,
        })

        print('DEBUG(response):')
        print("HTTP/1.1 %(status_code)s %(status_msg)s" % {
            'status_code': resp.status_code, 'status_msg': resp.reason})
        for k, v in six.iteritems(resp.headers):
            print(k + ': ' + v)
        print()
        if self.verbose:
            print(resp.content)
        else:
            print(('(HTTP Response Body is truncated(%d Chars).'
                   ' If you want to show it,'
                   'you may use --verbose option.)') % len(resp.content))

    def get(self, resource):
        headers = {
            'Content-Type': 'application/json',
            'Accept': 'application/json',
        }
        url = '/'.join([self.url, resource])
        resp = requests.get(
            url,
            auth=(self.user, self.password),
            headers=headers)

        self._log_http(url, headers, resp)

        # TODO Error
        return resp


class ResourceManager(object):
    def __init__(self, odl):
        self.odl = odl

    def list_all(self, *args, **kwargs):
        resp = self.odl.get(self.resource_type(*args, **kwargs))
        data_text = resp.text
        return self._as_objects(json.loads(data_text))

    def get(self, id, *args, **kwargs):
        resp = self.odl.get('/'.join([self.resource_type(args, **kwargs),
                            self.resource, id]))
        data_text = resp.text
        return self._as_object(json.loads(data_text))

    def _as_objects(self, data):
        return data

    def _as_object(self, data):
        return data


class NodeManager(ResourceManager):

    def resource_type(self, *args, **kwargs):
        return 'opendaylight-inventory:nodes'

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
        obj.connectors = [Connector.from_dict(c) for c in d["node-connector"]]
        obj.serial_number = d["flow-node-inventory:serial-number"]
        obj.switch_features = d["flow-node-inventory:switch-features"]
        obj.hardware = d["flow-node-inventory:hardware"]
        obj.software = d["flow-node-inventory:software"]
        obj.description = d["flow-node-inventory:description"]
        obj.meter_features = d["opendaylight-meter-statistics:meter-features"]
        obj.ip_address = d["flow-node-inventory:ip-address"]
        obj.manufacturer = d["flow-node-inventory:manufacturer"]
        return obj

    def __repr__(self):
        return 'Node[%(id)s]' % {
            'id': self.id
        }


class Connector(object):
    @classmethod
    def from_dict(clazz, d):
        obj = clazz()
        obj.id = d['id']
        obj.port_number = d["flow-node-inventory:port-number"]
        obj.current_speed = d["flow-node-inventory:current-speed"]
        obj.flow_capable_node_connector_statistics = d[
            "opendaylight-port-statistics:flow-capable-node-connector-statistics"]  # noqa
        obj.advertised_features = d["flow-node-inventory:advertised-features"]
        obj.configuration = d["flow-node-inventory:configuration"]
        obj.name = d["flow-node-inventory:name"]
        obj.hardware_address = d["flow-node-inventory:hardware-address"]
        obj.maximum_speed = d["flow-node-inventory:maximum-speed"]
        obj.state = d["flow-node-inventory:state"]
        obj.supported = d["flow-node-inventory:supported"]
        obj.current_feature = d["flow-node-inventory:current-feature"]
        obj.peer_features = d["flow-node-inventory:peer-features"]

        return obj


class Table(object):
    @classmethod
    def from_dict(clazz, d):
        obj = clazz()
        obj.id = d['id']
        obj.flows = [Flow.from_dict(f) for f in d.get('flow', [])]
        obj.flow_hash_id_map = d.get("flow-hash-id-map")
        obj.aggregate_flow_statistics = d.get(
            "opendaylight-flow-statistics:aggregate-flow-statistics")
        obj.flow_table_statistics = d.get(
            "opendaylight-flow-table-statistics:flow-table-statistics")
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
