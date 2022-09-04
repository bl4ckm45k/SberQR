import sys

if sys.version_info < (3, 6):
    raise RuntimeError('Your Python version {0} is not supported, please install '
                       'Python 3.6+'.format('.'.join(map(str, sys.version_info[:3]))))

from .SberQR import SyncSberQR
from .AsyncSberQR import AsyncSberQR
from .api import make_request, Methods
from .exceptions import (NetworkError, SberQrAPIError)

__author__ = 'Doncode'
__version__ = '1.0.0'
__email__ = 'your_email@doncode.com'
