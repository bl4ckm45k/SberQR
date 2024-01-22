import sys

if sys.version_info < (3, 7):
    raise RuntimeError('Your Python version {0} is not supported, please install '
                       'Python 3.7+'.format('.'.join(map(str, sys.version_info[:3]))))

from .AsyncSberQR import AsyncSberQR
from .SberQr import SberQR
from .api import make_request, Methods
from .exceptions import (NetworkError, SberQrAPIError)

__author__ = 'bl4ckm45k'
__version__ = '2.0.0'
__email__ = 'bl4ckm45k@gmail.com'
