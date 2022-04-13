import base64
from datetime import datetime
from logging import getLogger
from random import choices
from string import hexdigits

from requests_pkcs12 import post

from enum import Enum

logger = getLogger(__name__)


class Scope(Enum):
    create = 'https://api.sberbank.ru/qr/order.create'
    status = 'https://api.sberbank.ru/qr/order.status'
    revoke = 'https://api.sberbank.ru/qr/order.revoke'
    cancel = 'https://api.sberbank.ru/qr/order.cancel'
    registry = 'auth://qr/order.registry'


class CancelType(Enum):
    REFUND = 'REFUND'
    REVERSE = 'REVERSE'


class SberQR(object):
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
        self.member_id = member_id
        self.id_qr = id_qr
        self.tid = tid
        self.client_id = client_id
        self.client_secret = client_secret
        self.pkcs12_filename = pkcs12_filename
        self.pkcs12_password = pkcs12_password

    def token(self, scope: Scope):
        url = 'https://api.sberbank.ru:8443/prod/tokens/v2/oauth'
        auth = base64.b64encode(f'{self.client_id}:{self.client_secret}'.encode('utf-8')).decode('utf-8')
        headers = {
            'Accept': 'application/json',
            'Authorization': f'Basic {auth}',
            'Content-Type': 'application/x-www-form-urlencoded',
            'rquid': ''.join(choices(hexdigits, k=32)),
            'x-ibm-client-id': self.client_id,
        }
        response = post(
            url,
            data={'grant_type': 'client_credentials', 'scope': scope.value},
            headers=headers,
            pkcs12_filename=self.pkcs12_filename,
            pkcs12_password=self.pkcs12_password
        )

        logger.info(response.status_code)
        logger.info(response.text)
        result = response.json()

        return result['access_token']

    def creation(self, name: str, position_sum: int, is_sbp=True):
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
            'x-ibm-client-id': self.client_id,
        }
        data = {
            "rq_uid": rq_uid,
            "rq_tm": dt,
            "member_id": self.member_id,
            "order_number": now.strftime("%Y%m%d%H%M%S%f"),
            "order_create_date": dt,
            "order_params_type": [
                {
                    "position_name": name,
                    "position_count": 1,
                    "position_sum": position_sum,
                    "position_description": name
                }
            ],
            "id_qr": self.id_qr,
            "order_sum": position_sum,
            "currency": "643",
            "description": name,
        }
        if is_sbp:
            # data['sbp_member_id'] = "110000000111"  # Из доки
            data['sbp_member_id'] = "100000000111"  # из письма поддержки

        response = post(
            url,
            json=data,
            headers=headers,
            pkcs12_filename=self.pkcs12_filename,
            pkcs12_password=self.pkcs12_password
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
            "tid": self.tid,
            "partner_order_number": partner_order_number
        }

        response = post(
            url,
            headers={
                'Accept': 'application/json',
                'Authorization': f'Bearer {access_token}',
                'RqUID': rq_uid,
                'x-ibm-client-id': self.client_id,
            },
            json=data,
            pkcs12_filename=self.pkcs12_filename,
            pkcs12_password=self.pkcs12_password
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
                'x-ibm-client-id': self.client_id,
            },
            json={
                "rq_uid": rq_uid,
                "rq_tm": f'{datetime.utcnow().isoformat(timespec="seconds")}Z',
                "order_id": order_id,
            },
            pkcs12_filename=self.pkcs12_filename,
            pkcs12_password=self.pkcs12_password
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
                'x-ibm-client-id': self.client_id,
            },
            json={
                "rq_uid": rq_uid,
                "rq_tm": f'{datetime.utcnow().isoformat(timespec="seconds")}Z',
                "operation_id": operation_id,
                "order_id": order_id,
                "id_qr": self.id_qr,
                "cancel_operation_sum": cancel_operation_sum,
                "operation_currency": "643",
                "auth_code": auth_code,
                "tid": self.tid,
                "operation_type": operation_type.value
            },
            pkcs12_filename=self.pkcs12_filename,
            pkcs12_password=self.pkcs12_password
        )
        logger.info(response.status_code)
        logger.info(response.text)

        return response.json()

    def registry(self, start_period: datetime, end_period: datetime):
        """
        Отмена/возврат
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
                'x-ibm-client-id': self.client_id,
            },
            json={
                "rqUid": rq_uid,
                "rqTm": f'{datetime.utcnow().isoformat(timespec="seconds")}Z',
                "idQR": self.id_qr,
                "startPeriod": f'{start_period.isoformat(timespec="seconds")}Z',
                "endPeriod": f'{end_period.isoformat(timespec="seconds")}Z',
                "registryType": "REGISTRY"
            },
            pkcs12_filename=self.pkcs12_filename,
            pkcs12_password=self.pkcs12_password
        )
        logger.info(response.status_code)
        logger.info(response.text)

        return response.json()
