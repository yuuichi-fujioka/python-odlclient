import json

import click
import six

from odlclient import client
from odlclient import cmdutils


@click.group()
@click.option('--debug/--no-debug', default=False,
              help='Displays http request/response')
@click.option('--verbose/--no-verbose', default=False,
              help='Displays http response body')
@click.pass_context
def cmd(ctx, debug, verbose):
    ctx.obj = {'debug': debug, 'verbose': verbose}


def _get_odl_client():
    odl_client = client.ODL.get_client_with_env()
    ctx = click.get_current_context()
    odl_client.debug = ctx.obj['debug']
    odl_client.verbose = ctx.obj['verbose']
    return odl_client


@cmd.group(help='Nodes')
def node():
    pass


_node_formatter = {
    'table_count': lambda x: len([t for t in x.tables if len(t.flows)]),
    'connector_count': lambda x: len(x.connectors),
}


@node.command(help='Displays node list')  # noqa
def list():
    odl = _get_odl_client()
    nodes = odl.nodes.list_all()
    columns = ['id', 'ip_address', 'connector_count', 'table_count',
               'hardware', 'software']
    cmdutils.print_list(columns, nodes, formatter=_node_formatter)


@node.command(help='Displays Node details')
@click.argument('node-id')
def show(node_id):
    odl = _get_odl_client()
    node = odl.nodes.get(node_id)
    columns = ['id', 'ip_address', 'connector_count', 'table_count',
               'hardware', 'software', 'switch_features', 'description',
               'meter_features', 'manufacturer', 'serial_number']
    cmdutils.print_desc(columns, node, formatter=_node_formatter)


@cmd.group(help='Node Connectors')
def connector():
    pass


@connector.command(help='Displays Node connector list')  # noqa
@click.argument('node-id')
def list(node_id):
    odl = _get_odl_client()
    connectors = odl.nodes.get(node_id).connectors
    cmdutils.print_list(['port_number', 'name', 'id', 'state'], connectors)


@connector.command(help='Displays Node connector details')  # noqa
@click.argument('node-id')
@click.argument('port-number')
def show(node_id, port_number):
    odl = _get_odl_client()
    connectors = odl.nodes.get(node_id).connectors
    connector = [c for c in connectors if c.port_number == port_number][0]
    columns = [
        "id", "port_number", "name", "current_speed",
        "flow_capable_node_connector_statistics", "advertised_features",
        "configuration", "hardware_address", "maximum_speed", "state",
        "supported", "current_feature", "peer_features"]
    cmdutils.print_desc(columns, connector)


@cmd.group(help='Table')
def table():
    pass


_flow_formatter = {
    'flow_count': lambda x: len(x.flows)
}


@table.command(help='Displays Table list')  # noqa
@click.argument('node-id')
def list(node_id):
    odl = _get_odl_client()
    node = odl.nodes.get(node_id)
    cmdutils.print_list(
        ['id', 'flow_count'],
        sorted([t for t in node.tables if len(t.flows)], key=lambda x: x.id),
        formatter=_flow_formatter)


@table.command(help='Displays Table details')  # noqa
@click.argument('node-id')
@click.argument('table-id', type=int)
def show(node_id, table_id):
    odl = _get_odl_client()
    node = odl.nodes.get(node_id)
    t = [t for t in node.tables if t.id == table_id][0]
    columns = ['id', 'flow_count', 'flow_hash_id_map',
               'aggregate_flow_statistics', 'flow_table_statistics']
    cmdutils.print_desc(columns, t, formatter=_flow_formatter)


@cmd.group(help='Flows')
def flow():
    pass


def format_dict(d):
    return ', '.join(
        [': '.join([k, json.dumps(v)]) for k, v in six.iteritems(d)])


def match_formatter(x):
    return format_dict(x.match)


def instruction_formatter(x):
    actions = []
    if not x.instructions:
        return 'Drop'
    for instruction in sorted(
            x.instructions['instruction'], key=lambda i: i['order']):
        del instruction['order']
        if 'apply-actions' in instruction:
            for action in sorted(
                    instruction['apply-actions']['action'],
                    key=lambda a: a['order']):
                del action['order']
                actions.append(format_dict(action))
        else:
            actions.append(format_dict(instruction))
    return ', '.join(actions)


@flow.command(help='Displays Flow list')  # noqa
@click.argument('node-id')
def list(node_id):
    odl = _get_odl_client()
    node = odl.nodes.get(node_id)
    flows = []
    for table in node.tables:
        flows += table.flows
    cmdutils.print_list(
        ['id', 'table_id', 'priority', 'match', 'instructions'],
        sorted(flows, key=lambda f: (f.table_id, -f.priority)),
        formatter={'match': match_formatter,
                   'instructions': instruction_formatter})


class InstructionKeys(object):
    def __init__(self):
        self.actions = {}

    def __call__(self, key):
        def deco(func):
            self.actions[key] = func
            return func
        return deco

    def gen(self, key, value, order):
        return self.actions[key](value, order)


instruction_keys = InstructionKeys()


@instruction_keys('output')
def _output(value, order):
    return {'output-action': {
        'output-node-connector': int(value)}, 'order': order}


def _parse_instructions(instructions):
    if not instructions:
        return None

    actions = []
    order = 0
    for instruction in instructions.split(','):
        key, v = instruction.strip().split(':', 1)
        actions.append(instruction_keys.gen(key, v, order))
        order += 1
    return {
        'instruction': [
            {'apply-actions': {'action': actions}, 'order': 0}]
    }


def _parse_mac(mac_addr):
    if '/' in mac_addr:
        addr, mask = mac_addr.split('/')
    else:
        addr = mac_addr
        mask = 'ff:ff:ff:ff:ff:ff'
    return {
        'address': addr,
        'mask': mask,
    }


@flow.command(help='Creates a Flow')
@click.argument('node-id')
@click.argument('table-id')
@click.argument('flow-id')
@click.option('--priority', type=int)
@click.option('--in-port', help='Input Port Number(Match)')
@click.option('--dl-src',
              help='Ethernet Source Address(Match). xx:xx:xx:xx:xx:xx/xx:xx:xx:xx:xx:xx or xx:xx:xx:xx:xx:xx')  # noqa
@click.option('--dl-dst',
              help='Ethernet Destination Address(Match). e.g. xx:xx:xx:xx:xx:xx/xx:xx:xx:xx:xx:xx or xx:xx:xx:xx:xx:xx')  # noqa
@click.option('--tun-id', help='tunnel ID')
@click.option('--instructions',
              help='Instructions. e.g. output:1,outpu:2')
def create(node_id, table_id, flow_id, priority, in_port, dl_src, dl_dst,
           tun_id, instructions):
    odl = _get_odl_client()

    # Match Ruel
    match = {}
    if in_port:
        match['in-port'] = in_port
    if dl_src or dl_dst:
        dl = {}
        if dl_src:
            dl['ethernet-source'] = _parse_mac(dl_src)
        if dl_dst:
            dl['ethernet-destination'] = _parse_mac(dl_dst)
        match['ethernet-match'] = dl
    if tun_id:
        match['tunnel'] = {'tunnel-id': tun_id}

    # Instructions
    parsed_instructions = _parse_instructions(instructions)

    # Create a Flow
    data = odl.flows.create(
        node_id, table_id, flow_id, priority, match=match,
        instructions=parsed_instructions
    )
    print data


def main():
    cmd()


if __name__ == '__main__':
    main()
