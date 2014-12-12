HOST = '0.0.0.0'
LOGIN = 'login'
PASSWORD = 'password'
PORT = 2775
SMSCOUNT = 10


try:
    from local_settings import *
except ImportError:
    pass