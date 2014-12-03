HOST = '127.0.0.1'
LOGIN = 'login'
PASSWORD = 'password'
PORT = '2775'
try:
    from local_client_settings import *
except ImportError:
    pass