import asyncio
import base64
import ssl
from datetime import datetime
from logging import getLogger
from random import choices
from string import hexdigits
from typing import Optional, Type, Union, List, Dict

import aiohttp
import ujson as json

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
                 loop: Optional[Union[asyncio.BaseEventLoop, asyncio.AbstractEventLoop]] = None,
                 connections_limit: int = None,
                 timeout: Optional[Union[int, float, aiohttp.ClientTimeout]] = None):
        """

        :param member_id:
        :param id_qr:
        :param tid:
        :param client_id:
        :param client_secret:
        :param crt_file_path:
        :param key_file_path:
        :param pkcs12_password:
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

        self._currency = "643"
        ssl_context = ssl.create_default_context()
        ssl_context.load_cert_chain(certfile=crt_file_path,
                                    keyfile=key_file_path,
                                    password=pkcs12_password)
        self._session: Optional[aiohttp.ClientSession] = None
        self._connector_class: Type[aiohttp.TCPConnector] = aiohttp.TCPConnector
        self._connector_init = dict(limit=connections_limit, ssl=ssl_context)

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

    async def token(self, scope: Scope):
        auth = base64.b64encode(f'{self._client_id}:{self._client_secret}'.encode('utf-8')).decode('utf-8')
        headers = {'Authorization': f'Basic {auth}',
                   'Content-Type': 'application/x-www-form-urlencoded',
                   'rquid': ''.join(choices(hexdigits, k=32))}
        data = {'grant_type': 'client_credentials', 'scope': scope.value}
        return await self.request(Methods.oauth, headers, data)

    async def creation(self, description: str, order_sum: int, order_number: str, positions: Union[List, Dict]):
        """
        Создает новый динамический QR код
        """
        now = datetime.utcnow()
        dt = f'{now.isoformat(timespec="seconds")}Z'
        access_token = await self.token(Scope.create)
        rq_uid = ''.join(choices(hexdigits, k=32))
        headers = {'Authorization': f'Bearer {access_token["access_token"]}', 'RqUID': rq_uid}

        rq_tm, order_create_date = dt, dt
        member_id, id_qr, currency = self._member_id, self._id_qr, self._currency

        is_sbp = True if self._tid == self._id_qr else False
        if is_sbp:
            sbp_member_id = self._sbp_member_id

        if isinstance(positions, dict):
            order_params_type = [positions]
        else:
            order_params_type = positions
        del positions
        payload = generate_payload(exclude=['now', 'dt', 'headers', 'access_token', 'is_sbp'], **locals())
        return await self.request(Methods.creation, headers, payload)

    async def status(self, order_id: str, partner_order_number: str):
        rq_uid = ''.join(choices(hexdigits, k=32))
        access_token = await self.token(Scope.status)
        headers = {'Authorization': f'Bearer {access_token["access_token"]}', 'RqUID': rq_uid}
        tid = self._tid
        rq_tm = f'{datetime.utcnow().isoformat(timespec="seconds")}Z'
        payload = generate_payload(exclude=['headers', 'access_token'], **locals())
        return await self.request(Methods.status, headers, payload)

    async def revoke(self, order_id: str):
        rq_uid = ''.join(choices(hexdigits, k=32))
        access_token = await self.token(Scope.revoke)
        headers = {'Authorization': f'Bearer {access_token["access_token"]}', 'RqUID': rq_uid}

        rq_tm = f'{datetime.utcnow().isoformat(timespec="seconds")}Z'
        payload = generate_payload(exclude=['headers', 'access_token'], **locals())
        return await self.request(Methods.revocation, headers, payload)

    async def cancel(
            self, order_id: str, operation_id: str, cancel_operation_sum: int, auth_code: str,
            operation_type: CancelType = CancelType.REVERSE,
    ):
        """
        Отмена/возврат
        """
        rq_uid = ''.join(choices(hexdigits, k=32))
        access_token = await self.token(Scope.cancel)
        headers = {'Authorization': f'Bearer {access_token["access_token"]}', 'RqUID': rq_uid}

        rq_tm = f'{datetime.utcnow().isoformat(timespec="seconds")}Z'
        id_qr, tid, operation_currency = self._id_qr, self._tid, self._currency
        operation_type = operation_type.value
        payload = generate_payload(exclude=['headers', 'access_token'], **locals())
        return await self.request(Methods.cancel, headers, payload)

    async def registry(self, start_period: datetime, end_period: datetime,
                       registry_type: RegistryType = RegistryType.REGISTRY):
        """
        Запрос реестра операций
        """
        rq_uid = ''.join(choices(hexdigits, k=32))
        access_token = await self.token(Scope.registry)
        headers = {'Authorization': f'Bearer {access_token["access_token"]}', 'RqUID': rq_uid}
        payload = {"rqUid": rq_uid,
                   "rqTm": f'{datetime.utcnow().isoformat(timespec="seconds")}Z',
                   "idQR": self._id_qr,
                   "startPeriod": f'{start_period.isoformat(timespec="seconds")}Z',
                   "endPeriod": f'{end_period.isoformat(timespec="seconds")}Z',
                   "registryType": registry_type.value}

        return await self.request(Methods.registry, headers, payload)
