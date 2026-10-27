"""API has no Docker privileges; bounded operations travel over a private Unix socket."""
import httpx

class Broker:
    def __init__(self, path: str):
        self.client = httpx.Client(transport=httpx.HTTPTransport(uds=path), base_url='http://runner', timeout=190)

    def call(self, action: str, **data):
        try:
            response = self.client.post('/' + action, json=data)
            response.raise_for_status()
            return response.json()
        except (httpx.HTTPError, ValueError) as exc:
            raise RuntimeError('Lab servisine erişilemiyor') from exc

    def kapasite(self):
        try:
            return self.call('capacity')
        except RuntimeError:
            return {'uygun': False, 'neden': 'runner-yok'}

    def baslat(self, slug, oid, flag):
        return self.call('start', slug=slug, oid=oid, flag=flag)

    def durdur(self, slug, oid):
        return self.call('stop', slug=slug, oid=oid)

    def uzat(self, slug, oid):
        return self.call('extend', slug=slug, oid=oid)

    def komut(self, slug, oid, command):
        return self.call('command', slug=slug, oid=oid, command=command)

    def dogrula(self, slug, oid):
        return self.call('verify', slug=slug, oid=oid)
