import json

import prettytable


def print_list(columns, data, formatter=None):
    table = prettytable.PrettyTable(columns)
    for column in columns:
        table.align[column] = 'l'

    def _get_value(datum, column):
        if formatter is not None and column in formatter:
            value = formatter[column](datum)
        else:
            value = getattr(datum, column)

        if isinstance(value, (dict, list)):
            return json.dumps(value)
        else:
            return value

    for datum in data:
        table.add_row(
            [_get_value(datum, column) for column in columns])
    print table


def print_desc(columns, data):
    table_columns = ['name', 'value']
    table = prettytable.PrettyTable(table_columns)
    for column in table_columns:
        table.align[column] = 'l'

    for column in columns:
        table.add_row(
            [column, getattr(data, column)])
    print table
