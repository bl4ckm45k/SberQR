import asyncio
import base64
import ssl
from datetime import datetime
from logging import getLogger
from random import choices
from string import hexdigits
from typing import Optional, Type, Union, List, Dict

import aiohttp
import certifi
import ujson as json
from redis.asyncio import Redis

from .api import make_request, Methods
from .payload import generate_payload
from .scope import Scope
from .types import RegistryType, CancelType

logger = getLogger(__name__)


class AsyncSberQR:

    def __init__(self, member_id: str, id_qr: str, tid: str,
                 client_id: str, client_secret: str,
                 crt_file_path: str, key_file_path: str,
                 pkcs12_password: str,
                 russian_crt: str,
                 redis: Union[str, Redis] = None,
                 loop: Optional[Union[asyncio.BaseEventLoop, asyncio.AbstractEventLoop]] = None,
                 connections_limit: int = None,
                 timeout: Optional[Union[int, float, aiohttp.ClientTimeout]] = None):
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
        :param connections_limit:
        :param timeout:
        """

        self._main_loop = loop

        self._member_id = member_id
        self._sbp_member_id = "100000000111"
        self._id_qr = id_qr
        self._tid = tid
        self._client_id = client_id
        self._client_secret = client_secret
        self._redis = None

        self._currency = "643"
        ssl_context = ssl.create_default_context(cafile=certifi.where())

        ssl_context.load_cert_chain(certfile=crt_file_path,
                                    keyfile=key_file_path,
                                    password=pkcs12_password)
        ssl_context.load_verify_locations(cafile=russian_crt)

        self._session: Optional[aiohttp.ClientSession] = None
        self._connector_class: Type[aiohttp.TCPConnector] = aiohttp.TCPConnector
        self._connector_init = dict(limit=connections_limit, ssl=ssl_context)
        if isinstance(redis, Redis):
            self._redis = redis
        elif isinstance(redis, str):
            self._redis = Redis(host=redis, decode_responses=True)

        self.timeout = timeout

    async def get_new_session(self) -> aiohttp.ClientSession:
        return aiohttp.ClientSession(
            connector=self._connector_class(**self._connector_init),
            json_serialize=json.dumps
        )

    @property
    def loop(self) -> Optional[asyncio.AbstractEventLoop]:
        return self._main_loop

    async def get_session(self) -> Optional[aiohttp.ClientSession]:
        if self._session is None or self._session.closed:
            self._session = await self.get_new_session()

        if not self._session._loop.is_running():
            await self._session.close()
            self._session = await self.get_new_session()

        return self._session

    async def close(self):
        """
        Close all client sessions
        """
        if self._session:
            await self._session.close()

    async def request(self, method, headers, data):
        headers = {**headers, **{'Accept': 'application/json', 'x-ibm-client-id': self._client_id}}
        return await make_request(await self.get_session(), method, headers, data)

    async def get_token_from_redis(self, scope):
        """
        Возвращает токен, если он не истек
        :param scope Область токена
        :return: token string
        """
        return await self._redis.get(f'{self._client_id}token_{scope.value}')

    async def token(self, scope: Scope):
        redis_token = await self.get_token_from_redis(scope) if self._redis else None
        if redis_token:
            return redis_token
        else:
            auth = base64.b64encode(f'{self._client_id}:{self._client_secret}'.encode('utf-8')).decode('utf-8')
            headers = {'Authorization': f'Basic {auth}',
                       'Content-Type': 'application/x-www-form-urlencoded',
                       'rquid': ''.join(choices(hexdigits, k=32))}
            data = {'grant_type': 'client_credentials', 'scope': scope.value}
            token_data = await self.request(Methods.oauth, headers, data)
            if self._redis:
                await self._redis.set(f'{self._client_id}token_{scope.value}', token_data['access_token'],
                                      int(token_data['expires_in']) - 10)
            return token_data['access_token']

    async def creation(self, description: str, order_sum: int, order_number: str, positions: Union[List, Dict]):
        """
        Создание заказа
        """
        dt = f'{datetime.utcnow().isoformat(timespec="seconds")}Z'
        rq_uid = ''.join(choices(hexdigits, k=32))
        headers = {'Authorization': f'Bearer {await self.token(Scope.create)}', 'RqUID': rq_uid}

        rq_tm, order_create_date = dt, dt
        member_id, id_qr, currency = self._member_id, self._id_qr, self._currency

        sbp_member_id = self._sbp_member_id if self._tid == self._id_qr else None

        if isinstance(positions, dict):
            order_params_type = [positions]
        else:
            order_params_type = positions
        del positions
        payload = generate_payload(exclude=['dt', 'headers'], **locals())
        return await self.request(Methods.creation, headers, payload)

    async def status(self, order_id: str, partner_order_number: str):
        rq_uid = ''.join(choices(hexdigits, k=32))
        headers = {'Authorization': f'Bearer {await self.token(Scope.status)}', 'RqUID': rq_uid}
        tid = self._tid
        rq_tm = f'{datetime.utcnow().isoformat(timespec="seconds")}Z'
        payload = generate_payload(exclude=['headers'], **locals())
        return await self.request(Methods.status, headers, payload)

    async def revoke(self, order_id: str):
        rq_uid = ''.join(choices(hexdigits, k=32))
        headers = {'Authorization': f'Bearer {await self.token(Scope.revoke)}', 'RqUID': rq_uid}

        rq_tm = f'{datetime.utcnow().isoformat(timespec="seconds")}Z'
        payload = generate_payload(exclude=['headers'], **locals())
        return await self.request(Methods.revocation, headers, payload)

    async def cancel(
            self, order_id: str, operation_id: str, cancel_operation_sum: int, auth_code: str,
            operation_type: CancelType = CancelType.REVERSE, sbp_payer_id: str = None
    ):
        """
        Отмена/возврат
        """
        rq_uid = ''.join(choices(hexdigits, k=32))
        headers = {'Authorization': f'Bearer {await self.token(Scope.cancel)}', 'RqUID': rq_uid}

        rq_tm = f'{datetime.utcnow().isoformat(timespec="seconds")}Z'
        id_qr, tid, operation_currency = self._id_qr, self._tid, self._currency
        operation_type = operation_type.value
        payload = generate_payload(exclude=['headers'], **locals())
        return await self.request(Methods.cancel, headers, payload)

    async def registry(self, start_period: datetime, end_period: datetime,
                       registry_type: RegistryType = RegistryType.REGISTRY):
        """
        Запрос реестра операций
        """
        rq_uid = ''.join(choices(hexdigits, k=32))
        headers = {'Authorization': f'Bearer {await self.token(Scope.registry)}', 'RqUID': rq_uid}
        payload = {"rqUid": rq_uid,
                   "rqTm": f'{datetime.utcnow().isoformat(timespec="seconds")}Z',
                   "idQR": self._id_qr,
                   "startPeriod": f'{start_period.isoformat(timespec="seconds")}Z',
                   "endPeriod": f'{end_period.isoformat(timespec="seconds")}Z',
                   "registryType": registry_type.value}

        return await self.request(Methods.registry, headers, payload)