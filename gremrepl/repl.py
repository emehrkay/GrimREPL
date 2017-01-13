import asyncio
import cmd
import json
import uuid
import websockets

from terminaltables import AsciiTable


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

        return json.dumps(message)

    async def query(self, script=None, params=None, rebindings=None, op='eval',
                    processor=None, language='gremlin-groovy'):
        try:
            connection = websockets.connect(self.ws_uri)

            async with connection as ws:
                message = self.message(script=script, params=params,
                                       rebindings=rebindings, op=op,
                                       processor=processor, language=language)

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

        self.headers = ['Request ID', 'Status']
        self.table([self.request_id, self.status])

    def table(self, data):
        data = [self.headers, data,]
        table = AsciiTable(data)

        self.tables.append(table.table)
        self.tables.append('\n\n')

        return self

    def draw(self):
        if not self.data:
            return ''

        for data in self.data:
            table_rows = []

            if isinstance(data, dict):
                headers = []
                row_data = []
                _id = data.get('id', None)
                _label = data.get('label', None)
                _type = data.get('type', None)
                properties = data.get('properties', {})

                if _id:
                    headers.append('id')
                    row_data.append(_id)

                if _label:
                    headers.append('label')
                    row_data.append(_label)

                if _type:
                    headers.append('type')
                    row_data.append(_type)

                if properties:
                    headers += list(properties.keys())
                    row_data += list(properties.values())

                table_rows.append(row_data)

                if not self.headers or self.headers != headers:
                    self.headers = headers
                    self.table(row_data)
            elif isinstance(data, (list, set)):
                print(data)
            else:
                self.headers = ['Result']
                self.table([data,])

        return ''.join(self.tables)


class GremREPL(cmd.Cmd):

    def __init__(self, request):
        cmd.Cmd.__init__(self)
        self.request = request

    def default(self, line, *args, **kwargs):
        async def query():
            data = await self.request.query(line)
            table = Tabulate(data)

            print(table.draw())

        asyncio.get_event_loop().run_until_complete(query())


def cli():
    try:
        while True:
            request = Request('localhost')
            repl = GremREPL(request)

            repl.cmdloop()
    except Exception as e:
        raise e


if __name__ == '__main__':
    cli()
