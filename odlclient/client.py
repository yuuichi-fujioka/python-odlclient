from __future__ import print_function

import os
import json

import requests
import six
import xmltodict


_BASE_ODL_URL = 'http://%(host)s:%(port)s/restconf/'


class ODL(object):

    def __init__(self, url, user, password):
        self.url = url
        self.user = user
        self.password = password

        self.nodes = NodeManager(self)
        self.flows = FlowManager(self)

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

    def _log_http(self, url, headers, resp, method='GET', body=None):

        if not self.debug:
            return

        msg = ('DEBUG(request): curl -i %(headers)s -u "%(user)s:%(password)s"'
               ' -X %(method)s "%(url)s"')

        formatted_headers = ' '.join(
            ['-H "' + ': '.join([k, v]) + '"'
             for k, v in six.iteritems(headers)])
        msg_data = {
            'headers': formatted_headers,
            'user': self.user,
            'password': self.password,
            'url': url,
            'method': method,
        }

        if body is not None:
            msg += " -d '%(body)s'"
            if isinstance(body, (list, dict)):
                msg_data['body'] = json.dumps(body)
            else:
                msg_data['body'] = body

        print(msg % msg_data)

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
        url = ''.join([self.url, 'operational/', resource])
        resp = requests.get(
            url,
            auth=(self.user, self.password),
            headers=headers)

        self._log_http(url, headers, resp)

        # TODO Error
        return resp

    def put(self, resource, body):
        headers = {
            'Content-Type': 'application/xml',
            'Accept': 'application/json',
        }
        url = ''.join([self.url, 'config/', resource])
        data = body
        resp = requests.put(
            url,
            auth=(self.user, self.password),
            headers=headers,
            data=data)

        self._log_http(url, headers, resp, method='PUT', body=data)

        # TODO Error
        return resp


class ResourceManager(object):
    def __init__(self, odl):
        self.odl = odl

    def list_all(self, *args, **kwargs):
        resp = self.odl.get(self.resource_type(*args, **kwargs))
        data_text = resp.text
        return self._as_objects(json.loads(data_text))

    def _gen_url(self, id, *args, **kwargs):
        return '/'.join([
            self.resource_type(*args, **kwargs),
            self.resource,
            id])

    def get(self, id, *args, **kwargs):
        resp = self.odl.get(self._gen_url(id, *args, **kwargs))
        data_text = resp.text
        return self._as_object(json.loads(data_text))

    def create(self, id, body, *args, **kwargs):
        resp = self.odl.put(self._gen_url(id, *args, **kwargs), body)
        return resp.status_code / 100 == 2

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


class FlowManager(ResourceManager):

    def resource_type(self, node_id, table_id, *args, **kwargs):
        return ('opendaylight-inventory:nodes/node/%s/'
                'flow-node-inventory:table/%s') % (node_id, table_id)

    resource = 'flow'

    def create(self, node_id, table_id, flow_id,
               priority=None, match=None, instructions=None):
        body = {'id': flow_id, 'table_id': table_id}
        if priority is not None:
            body['priority'] = priority
        if match:
            body['match'] = match
        if instructions:
            body['instructions'] = instructions
        # TODO fix way to gen xml
        data = (
            '<?xml version="1.0" encoding="utf-8"?>'
            '<flow xmlns="urn:opendaylight:flow:inventory">'
            '%s'
            '</flow>'
        ) % (
            xmltodict.unparse(body, full_document=False)
        )
        return super(FlowManager, self).create(
            flow_id, data, node_id, table_id)


class Node(object):

    @classmethod
    def from_dict(clazz, d):
        obj = clazz()
        obj.id = d['id']
        obj.tables = [
            Table.from_dict(t) for t in d['flow-node-inventory:table']]
        obj.connectors = [Connector.from_dict(c) for c in d["node-connector"]]
        obj.serial_number = d.get("flow-node-inventory:serial-number")
        obj.switch_features = d.get("flow-node-inventory:switch-features")
        obj.hardware = d.get("flow-node-inventory:hardware")
        obj.software = d.get("flow-node-inventory:software")
        obj.description = d.get("flow-node-inventory:description")
        obj.meter_features = d.get(
            "opendaylight-meter-statistics:meter-features")
        obj.ip_address = d.get("flow-node-inventory:ip-address")
        obj.manufacturer = d.get("flow-node-inventory:manufacturer")
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
        obj.port_number = d.get("flow-node-inventory:port-number")
        obj.current_speed = d.get("flow-node-inventory:current-speed")
        obj.flow_capable_node_connector_statistics = d.get(
            "opendaylight-port-statistics:flow-capable-node-connector-statistics")  # noqa
        obj.advertised_features = d.get(
            "flow-node-inventory:advertised-features")
        obj.configuration = d.get("flow-node-inventory:configuration")
        obj.name = d.get("flow-node-inventory:name")
        obj.hardware_address = d.get("flow-node-inventory:hardware-address")
        obj.maximum_speed = d.get("flow-node-inventory:maximum-speed")
        obj.state = d.get("flow-node-inventory:state")
        obj.supported = d.get("flow-node-inventory:supported")
        obj.current_feature = d.get("flow-node-inventory:current-feature")
        obj.peer_features = d.get("flow-node-inventory:peer-features")

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
