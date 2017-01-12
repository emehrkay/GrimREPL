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

    async def query(self, script=None, params=None, update_entities=None,
                   rebindings=None, op='eval', processor=None,
                   language='gremlin-groovy', session=None):
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


class GremREPL(cmd.Cmd):

    def __init__(self, request):
        cmd.Cmd.__init__(self)
        self.request = request

    def default(self, line, *args, **kwargs):
        print(args)
        print('---')
        print(kwargs)
        cmd, arg, line = self.parseline(line)
        print(cmd, 'arg', arg, '----', line)
        return
        async def query():
            data = await self.request.query(line)
            rows = []

            for d in data['result']['data']:
                for n, v in d['properties'].items():
                    rows.append(v)
            table = AsciiTable(rows)

            import pprint 
            pprint.pprint(data)
            print(table.table)
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
