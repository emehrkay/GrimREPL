import argparse
import asyncio
import cmd
import copy
import json
import pprint
import uuid
import websockets

from terminaltables import AsciiTable


PROMPT = 'GrimREPL > '


class Request:

    def __init__(self, uri, port=8182, three_two=True):
        gremlin = '/gremlin' if three_two else ''
        self.uri = uri
        self.port = port
        self.three_two = three_two
        self.ws_uri = 'ws://{}:{}{}'.format(uri, port, gremlin)

    def message(self, script, params=None, rebindings=None, op='eval',
                processor=None, language='gremlin-groovy', session=None):
        message = {
            'requestId': str(uuid.uuid4()),
            'op': op,
            'processor': processor or '',
            'args': {
                'gremlin': script,
                'bindings': params,
                'language': language,
                'rebindings': rebindings or {},
            }
        }

        if session:
            message['op'] = 'session'
            message['session'] = session

        return json.dumps(message)

    async def query(self, script=None, params=None, rebindings=None, op='eval',
                    processor=None, language='gremlin-groovy', session=None):
        try:
            connection = websockets.connect(self.ws_uri)

            async with connection as ws:
                message = self.message(script=script, params=params,
                                       rebindings=rebindings, op=op,
                                       processor=processor, language=language,
                                       session=session)

                await ws.send(message)

                response = await ws.recv()

                return json.loads(response)
        except Exception as e:
            raise e


class Tabulate:

    def __init__(self, response):
        self.response = response
        self.tables = []
        self.request_id = response.get('requestId', None)
        self.status = response.get('status', {})
        self.result = response.get('result', {})
        self.data = self.result.get('data', [])

        headers = ['Request ID', 'Status']
        self.table(headers, [[self.request_id, self.status]])

    def table(self, headers, data):
        data = [headers] + data
        table = AsciiTable(data)
        table.inner_row_border = False
        self.tables.append(table.table)
        self.tables.append('\n\n')

        return self

    def draw(self):
        print(self.data)

    def draw(self):
        if not self.data:
            return ''

        rows = []

        for i, data in enumerate(self.data):
            data = copy.deepcopy(data)
            headers = []
            row_data = []

            if isinstance(data, dict):
                _id = data.get('id', None)
                _label = data.get('label', None)
                _type = data.get('type', None)
                properties = data.get('properties', {})

                if _id is not None:
                    headers.append('id')
                    row_data.append(_id)
                    del data['id']

                if _label is not None:
                    headers.append('label')
                    row_data.append(_label)
                    del data['label']

                if _type is not None:
                    headers.append('type')
                    row_data.append(_type)
                    del data['type']

                if properties:
                    for pname, pval in properties.items():
                        prop_values = []

                        headers.append(pname)

                        if not isinstance(pval, (list, set)):
                            pval = [pval,]

                        for val in pval:
                            if not isinstance(val, dict):
                                prop_values.append(str(val))
                                continue

                            value = val.get('value', '$$$')
                            pproperties = val.get('properties', None)

                            prop_values.append(str(value))

                            if pproperties:
                                pv = '    {}'.format(pproperties)
                                prop_values.append(pv)

                        row_data.append('\n'.join(prop_values))

                if 'properties' in data:
                    del data['properties']

                for k, v in data.items():
                    headers.append(k)
                    row_data.append(v)

                headers = tuple(headers)
            else:
                headers = ('Result',)
                row_data = [data,]

            try:
                if rows[-1][0] == headers:
                    rows[-1][1].append(row_data)
                else:
                    raise
            except:
                rows.append((headers, [row_data,]))

        for col in rows:
            self.table(col[0], col[1])

        tables = ''.join(self.tables)
        total = len(self.data)

        if total:
            tables += '(total: {})\n'.format(total)

        return tables


class GremREPL(cmd.Cmd):

    def __init__(self, request):
        cmd.Cmd.__init__(self)
        self.request = request
        self.prompt = PROMPT

    def default(self, line, *args, **kwargs):
        async def query():
            data = await self.request.query(line)
            table = Tabulate(data)

            print(table.draw())

        asyncio.get_event_loop().run_until_complete(query())


def cli(uri, port):
    try:
        while True:
            request = Request(uri=uri, port=port)
            repl = GremREPL(request)

            repl.cmdloop()
    except Exception as e:
        raise e


if __name__ == '__main__':
    parser = argparse.ArgumentParser(('GremREPL'))

    parser.add_argument('-u', '--uri', default='localhost',
        help='The uri for the Gremlin Server. Defaults to localhost.')
    parser.add_argument('-p', '--port', default=8182,
        help='The port for the Gremlin Server. Defaults to 8182.')

    args = parser.parse_args()

    cli(args.uri, args.port)
