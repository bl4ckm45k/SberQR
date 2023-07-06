import logging
from http import HTTPStatus

from SberQR.exceptions import SberQrAPIError, NetworkError

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger('api')


def check_result(method_name: str, content_type: str, status_code: int, body):
    """
    Checks whether `result` is a valid API response.
    A result is considered invalid if:
    - The server returned an HTTP response code other than 200
    - The content of the result is invalid JSON.
    - The method call was unsuccessful (The JSON 'ok' field equals False)

    :param method_name: The name of the method called
    :param status_code: status code
    :param content_type: content type of result
    :param body: result body
    :return: The result parsed to a JSON dictionary
    :raises ApiException: if one of the above listed cases is applicable
    """
    logger.debug('Response for %s: [%d] "%r"', method_name, status_code, body)

    if content_type != 'application/json':
        raise NetworkError(f"Invalid response with content type {content_type}: \"{body}\"")

    if HTTPStatus.OK <= status_code <= HTTPStatus.IM_USED:
        return body
    elif status_code == HTTPStatus.BAD_REQUEST:
        raise SberQrAPIError(f"{body} [{status_code}]")
    elif status_code == HTTPStatus.NOT_FOUND:
        raise SberQrAPIError(f"{body} [{status_code}]")
    elif status_code == HTTPStatus.CONFLICT:
        raise SberQrAPIError(f"{body} [{status_code}]")
    elif status_code in (HTTPStatus.UNAUTHORIZED, HTTPStatus.FORBIDDEN):
        raise SberQrAPIError(f"{body} [{status_code}]")
    elif status_code >= HTTPStatus.INTERNAL_SERVER_ERROR:
        raise SberQrAPIError(f"{body} [{status_code}]")


async def make_request(session, method, headers, data, **kwargs):
    url = f'https://mc.api.sberbank.ru/prod/{method}'

    if method != Methods.oauth:
        async with session.post(url, json=data, headers=headers) as response:
            try:
                body = await response.json()
            except:
                body = response.text
            return check_result(method, response.content_type, response.status, body)
    else:
        async with session.post(url, data=data, headers=headers) as response:
            try:
                body = await response.json()
            except:
                body = response.text
            return check_result(method, response.content_type, response.status, body)


class Methods:
    oauth = 'tokens/v2/oauth'
    creation = 'qr/order/v3/creation'
    status = 'qr/order/v3/status'
    revocation = 'qr/order/v3/revocation'
    cancel = 'qr/order/v3/cancel'
    registry = 'qr/order/v3/registry'
