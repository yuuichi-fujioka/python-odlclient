import json

import click
import six

from odlclient import client
from odlclient import cmdutils


@click.group()
def cmd():
    pass


@cmd.group()
def node():
    pass


@node.command()  # noqa
def list():
    odl = client.ODL.get_client_with_env()
    nodes = odl.nodes.list_all()
    cmdutils.print_list(
        ['id', 'table_count'], nodes,
        formatter={'table_count': lambda x: len(x.tables)})


@node.command()
@click.argument('id')
def show(id):
    odl = client.ODL.get_client_with_env()
    node = odl.nodes.get(id)
    cmdutils.print_desc(['id'], node)


@cmd.group()
def table():
    pass


@table.command()  # noqa
@click.argument('node_id')
def list(node_id):
    odl = client.ODL.get_client_with_env()
    node = odl.nodes.get(node_id)
    cmdutils.print_list(
        ['id', 'flow_count'],
        sorted(node.tables, key=lambda x: x.id),
        formatter={'flow_count': lambda x: len(x.flows)})


@cmd.group()
def flow():
    pass


def format_dict(d):
    return ', '.join(
        [': '.join([k, json.dumps(v)]) for k, v in six.iteritems(d)])


def match_formatter(x):
    return format_dict(x.match)


def instruction_formatter(x):
    actions = []
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


@flow.command()  # noqa
@click.argument('node_id')
def list(node_id):
    odl = client.ODL.get_client_with_env()
    node = odl.nodes.get(node_id)
    flows = []
    for table in node.tables:
        flows += table.flows
    cmdutils.print_list(
        ['id', 'table_id', 'priority', 'match', 'instructions'],
        sorted(flows, key=lambda f: (f.table_id, -f.priority)),
        formatter={'match': match_formatter,
                   'instructions': instruction_formatter})


def main():
    cmd()


if __name__ == '__main__':
    main()
