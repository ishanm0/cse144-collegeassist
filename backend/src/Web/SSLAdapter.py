import ssl

from requests.adapters import HTTPAdapter

# from requests.packages.urllib3.util.ssl_ import create_urllib3_context
from urllib3.util.ssl_ import create_urllib3_context

# Create a custom SSL context
context = ssl.create_default_context()
context.set_ciphers("DEFAULT:@SECLEVEL=1")


class SSLAdapter(HTTPAdapter):
    """An HTTPS Transport Adapter that uses an arbitrary SSL version."""

    def __init__(self, ssl_version=None, **kwargs):
        self.ssl_version = ssl_version
        self.ssl_context = create_urllib3_context(ciphers="DEFAULT@SECLEVEL=1")
        super().__init__(**kwargs)

    def init_poolmanager(self, *args, **kwargs):
        kwargs["ssl_context"] = self.ssl_context
        super().init_poolmanager(*args, **kwargs)

    def proxy_manager_for(self, *args, **kwargs):
        kwargs["ssl_context"] = self.ssl_context
        return super().proxy_manager_for(*args, **kwargs)
