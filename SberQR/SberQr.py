import asyncio
import base64
from datetime import datetime
from logging import getLogger
from random import choices
from string import hexdigits
from typing import Optional, Union, List, Dict

import requests
from redis.client import Redis
from requests.adapters import HTTPAdapter
from urllib3.util.ssl_ import create_urllib3_context

from .api_sync import make_request, Methods
from .payload import generate_payload
from .scope import Scope
from .types import RegistryType, CancelType

logger = getLogger(__name__)


class SberQR:

    def __init__(self, member_id: str, id_qr: str, tid: str,
                 client_id: str, client_secret: str,
                 crt_file_path: str, key_file_path: str,
                 pkcs12_password: str,
                 russian_crt: str,
                 redis: Union[str, Redis] = None,
                 loop: Optional[Union[asyncio.BaseEventLoop, asyncio.AbstractEventLoop]] = None,
                 timeout: Optional[Union[int, float, requests.Timeout]] = None):
        """

        :param member_id:
        :param id_qr:
        :param tid:
        :param client_id:
        :param client_secret: l
        i]
        :param crt_file_path:
        :param key_file_path:
        :param pkcs12_password:
        :param redis:
        :param loop:
        :param timeout:
        """

        self._main_loop = loop

        self._member_id = member_id
        self._sbp_member_id = "100000000111"
        self._id_qr = id_qr
        self._tid = tid
        self._client_id = client_id
        self._client_secret = client_secret

        self._currency = "643"
        self._redis = None

        class SSLAdapter(HTTPAdapter):
            def init_poolmanager(self, *args, **kwargs):
                context = create_urllib3_context()
                context.load_cert_chain(certfile=crt_file_path, keyfile=key_file_path, password=pkcs12_password)
                context.load_verify_locations(cafile=russian_crt)
                kwargs['ssl_context'] = context
                return super().init_poolmanager(*args, **kwargs)

        self._session: Optional[requests.Session] = None
        self._https_class = SSLAdapter()
        if isinstance(redis, Redis):
            self._redis = redis
        elif isinstance(redis, str):
            self._redis = Redis(redis, decode_responses=True)

        self.timeout = timeout

    def get_new_session(self) -> requests.Session:
        session = requests.Session()
        session.mount("https://", self._https_class)
        return session

    @property
    def loop(self) -> Optional[asyncio.AbstractEventLoop]:
        return self._main_loop

    def get_session(self) -> Optional[requests.Session]:
        if self._session is None:
            self._session = self.get_new_session()

        return self._session

    def close(self):
        """
        Close all client sessions
        """
        if self._session:
            self._session.close()

    def request(self, method, headers, data):
        headers = {**headers, **{'Accept': 'application/json', 'x-ibm-client-id': self._client_id}}
        return make_request(self.get_session(), method, headers, data)

    def get_token_from_redis(self, scope):
        """
        Возвращает токен, если он не истек
        :param scope Область токена
        :return: token string
        """
        return self._redis.get(f'{self._client_id}token_{scope.value}')

    def token(self, scope: Scope):
        redis_token = self.get_token_from_redis(scope) if self._redis else None
        if redis_token is not None:
            return redis_token
        else:
            auth = base64.b64encode(f'{self._client_id}:{self._client_secret}'.encode('utf-8')).decode('utf-8')
            headers = {'Authorization': f'Basic {auth}',
                       'Content-Type': 'application/x-www-form-urlencoded',
                       'rquid': ''.join(choices(hexdigits, k=32))}
            data = {'grant_type': 'client_credentials', 'scope': scope.value}
            token_data = self.request(Methods.oauth, headers, data)
            if self._redis:
                self._redis.set(f'{self._client_id}token_{scope.value}', token_data['access_token'],
                                int(token_data['expires_in']) - 10)
            return token_data['access_token']

    def creation(self, description: str, order_sum: int, order_number: str, positions: Union[List, Dict]):
        """
        Создание заказа
        """
        dt = f'{datetime.utcnow().isoformat(timespec="seconds")}Z'
        rq_uid = ''.join(choices(hexdigits, k=32))
        headers = {'Authorization': f'Bearer {self.token(Scope.create)}', 'RqUID': rq_uid}

        rq_tm, order_create_date = dt, dt
        member_id, id_qr, currency = self._member_id, self._id_qr, self._currency

        sbp_member_id = self._sbp_member_id if self._tid == self._id_qr else None

        if isinstance(positions, dict):
            order_params_type = [positions]
        else:
            order_params_type = positions
        del positions
        payload = generate_payload(exclude=['dt', 'headers'], **locals())
        return self.request(Methods.creation, headers, payload)

    def status(self, order_id: str, partner_order_number: str):
        rq_uid = ''.join(choices(hexdigits, k=32))
        headers = {'Authorization': f'Bearer {self.token(Scope.status)}', 'RqUID': rq_uid}
        tid = self._tid
        rq_tm = f'{datetime.utcnow().isoformat(timespec="seconds")}Z'
        payload = generate_payload(exclude=['headers'], **locals())
        return self.request(Methods.status, headers, payload)

    def revoke(self, order_id: str):
        rq_uid = ''.join(choices(hexdigits, k=32))
        headers = {'Authorization': f'Bearer {self.token(Scope.revoke)}', 'RqUID': rq_uid}

        rq_tm = f'{datetime.utcnow().isoformat(timespec="seconds")}Z'
        payload = generate_payload(exclude=['headers'], **locals())
        return self.request(Methods.revocation, headers, payload)

    def cancel(
            self, order_id: str, operation_id: str, cancel_operation_sum: int, auth_code: str,
            operation_type: CancelType = CancelType.REVERSE, sbp_payer_id: str = None
    ):
        """
        Отмена/возврат
        """
        rq_uid = ''.join(choices(hexdigits, k=32))
        headers = {'Authorization': f'Bearer {self.token(Scope.cancel)}', 'RqUID': rq_uid}

        rq_tm = f'{datetime.utcnow().isoformat(timespec="seconds")}Z'
        id_qr, tid, operation_currency = self._id_qr, self._tid, self._currency
        operation_type = operation_type.value
        payload = generate_payload(exclude=['headers'], **locals())
        return self.request(Methods.cancel, headers, payload)

    def registry(self, start_period: datetime, end_period: datetime,
                 registry_type: RegistryType = RegistryType.REGISTRY):
        """
        Запрос реестра операций
        """
        rq_uid = ''.join(choices(hexdigits, k=32))
        headers = {'Authorization': f'Bearer {self.token(Scope.registry)}', 'RqUID': rq_uid}
        payload = {"rqUid": rq_uid,
                   "rqTm": f'{datetime.utcnow().isoformat(timespec="seconds")}Z',
                   "idQR": self._id_qr,
                   "startPeriod": f'{start_period.isoformat(timespec="seconds")}Z',
                   "endPeriod": f'{end_period.isoformat(timespec="seconds")}Z',
                   "registryType": registry_type.value}

        return self.request(Methods.registry, headers, payload)
