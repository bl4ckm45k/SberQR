import base64
from datetime import datetime
from logging import getLogger
from random import choices
from string import hexdigits
from typing import Union, List, Dict

from requests_pkcs12 import post
from .scope import Scope
from .types import CancelType, RegistryType

logger = getLogger(__name__)


class SyncSberQR(object):
    member_id: str
    id_qr: str
    tid: str
    client_id: str
    client_secret: str
    pkcs12_filename: str
    pkcs12_password: str

    def __init__(
            self,
            member_id: str, id_qr: str, tid: str, client_id: str, client_secret: str,
            pkcs12_filename: str, pkcs12_password: str,
    ):
        self._member_id = member_id
        self._id_qr = id_qr
        self._tid = tid
        self._client_id = client_id
        self._client_secret = client_secret
        self._pkcs12_filename = pkcs12_filename
        self._pkcs12_password = pkcs12_password
        self._sbp_member_id = "100000000111"

    def token(self, scope: Scope):
        url = 'https://api.sberbank.ru:8443/prod/tokens/v2/oauth'
        auth = base64.b64encode(f'{self._client_id}:{self._client_secret}'.encode('utf-8')).decode('utf-8')
        headers = {
            'Accept': 'application/json',
            'Authorization': f'Basic {auth}',
            'Content-Type': 'application/x-www-form-urlencoded',
            'rquid': ''.join(choices(hexdigits, k=32)),
            'x-ibm-client-id': self._client_id,
        }
        response = post(
            url,
            data={'grant_type': 'client_credentials', 'scope': scope.value},
            headers=headers,
            pkcs12_filename=self._pkcs12_filename,
            pkcs12_password=self._pkcs12_password
        )

        logger.info(response.status_code)
        logger.info(response.text)
        result = response.json()

        return result['access_token']

    def creation(self, description: str, order_sum: int, order_number: str, positions: Union[List, Dict]):
        """
        Создает новый динамический QR код
        """
        url = 'https://api.sberbank.ru:8443/prod/qr/order/v3/creation'
        rq_uid = ''.join(choices(hexdigits, k=32))
        now = datetime.utcnow()
        dt = f'{now.isoformat(timespec="seconds")}Z'
        access_token = self.token(Scope.create)

        headers = {
            'Accept': 'application/json',
            'Authorization': f'Bearer {access_token}',
            'RqUID': rq_uid,
            'x-ibm-client-id': self._client_id,
        }
        if isinstance(positions, dict):
            positions = [positions]
        data = {
            "rq_uid": rq_uid,
            "rq_tm": dt,
            "member_id": self._member_id,
            "order_number": order_number,
            "order_create_date": dt,
            "order_params_type": positions,
            "id_qr": self._id_qr,
            "order_sum": order_sum,
            "currency": "643",
            "description": description,
        }
        is_sbp = True if self._tid == self._id_qr else False
        if is_sbp:
            data['sbp_member_id'] = self._sbp_member_id

        response = post(
            url,
            json=data,
            headers=headers,
            pkcs12_filename=self._pkcs12_filename,
            pkcs12_password=self._pkcs12_password
        )
        logger.info(response.status_code)
        logger.info(response.text)

        result = response.json()
        return result

    def status(self, order_id: str, partner_order_number: str):
        url = 'https://api.sberbank.ru:8443/prod/qr/order/v3/status'
        rq_uid = ''.join(choices(hexdigits, k=32))
        access_token = self.token(Scope.status)
        data = {
            "rq_uid": rq_uid,
            "rq_tm": f'{datetime.utcnow().isoformat(timespec="seconds")}Z',
            "order_id": order_id,
            "tid": self._tid,
            "partner_order_number": partner_order_number
        }

        response = post(
            url,
            headers={
                'Accept': 'application/json',
                'Authorization': f'Bearer {access_token}',
                'RqUID': rq_uid,
                'x-ibm-client-id': self._client_id,
            },
            json=data,
            pkcs12_filename=self._pkcs12_filename,
            pkcs12_password=self._pkcs12_password
        )
        logger.info(response.status_code)
        logger.info(response.text)

        return response.json()

    def revoke(self, order_id: str):
        url = 'https://api.sberbank.ru:8443/prod/qr/order/v3/revocation'
        rq_uid = ''.join(choices(hexdigits, k=32))
        access_token = self.token(Scope.revoke)

        response = post(
            url,
            headers={
                'Accept': 'application/json',
                'Authorization': f'Bearer {access_token}',
                'RqUID': rq_uid,
                'x-ibm-client-id': self._client_id,
            },
            json={
                "rq_uid": rq_uid,
                "rq_tm": f'{datetime.utcnow().isoformat(timespec="seconds")}Z',
                "order_id": order_id,
            },
            pkcs12_filename=self._pkcs12_filename,
            pkcs12_password=self._pkcs12_password
        )
        logger.info(response.status_code)
        logger.info(response.text)
        return response.json()

    def cancel(
            self, order_id: str, operation_id: str, cancel_operation_sum: int, auth_code: str,
            operation_type=CancelType.REVERSE,
    ):
        """
        Отмена/возврат
        """
        url = 'https://api.sberbank.ru:8443/prod/qr/order/v3/cancel'
        rq_uid = ''.join(choices(hexdigits, k=32))
        access_token = self.token(Scope.cancel)

        response = post(
            url,
            headers={
                'Accept': 'application/json',
                'Authorization': f'Bearer {access_token}',
                'RqUID': rq_uid,
                'x-ibm-client-id': self._client_id,
            },
            json={
                "rq_uid": rq_uid,
                "rq_tm": f'{datetime.utcnow().isoformat(timespec="seconds")}Z',
                "operation_id": operation_id,
                "order_id": order_id,
                "id_qr": self._id_qr,
                "cancel_operation_sum": cancel_operation_sum,
                "operation_currency": "643",
                "auth_code": auth_code,
                "tid": self._tid,
                "operation_type": operation_type.value
            },
            pkcs12_filename=self._pkcs12_filename,
            pkcs12_password=self._pkcs12_password
        )
        logger.info(response.status_code)
        logger.info(response.text)

        return response.json()

    def registry(self, start_period: datetime, end_period: datetime, registry_type: RegistryType = RegistryType.REGISTRY):
        """
        Запрос реестра операций
        """
        url = 'https://api.sberbank.ru:8443/prod/qr/order/v3/registry'
        rq_uid = ''.join(choices(hexdigits, k=32))
        access_token = self.token(Scope.registry)

        response = post(
            url,
            headers={
                'Accept': 'application/json',
                'Authorization': f'Bearer {access_token}',
                'RqUID': rq_uid,
                'x-ibm-client-id': self._client_id,
            },
            json={
                "rqUid": rq_uid,
                "rqTm": f'{datetime.utcnow().isoformat(timespec="seconds")}Z',
                "idQR": self._id_qr,
                "startPeriod": f'{start_period.isoformat(timespec="seconds")}Z',
                "endPeriod": f'{end_period.isoformat(timespec="seconds")}Z',
                "registryType": registry_type.value
            },
            pkcs12_filename=self._pkcs12_filename,
            pkcs12_password=self._pkcs12_password
        )
        logger.info(response.status_code)
        logger.info(response.text)

        return response.json()
