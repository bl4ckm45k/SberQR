from .api import check_result, Methods


def make_request(session, method, headers, data, **kwargs):
    url = f'https://mc.api.sberbank.ru/prod/{method}'

    if method != Methods.oauth:
        with session.post(url, json=data, headers=headers) as response:
            try:
                body = response.json()
            except Exception:
                body = response.text
            return check_result(method, response.headers.get('Content-Type'), response.status_code, body)
    else:
        with session.post(url, data=data, headers=headers) as response:
            try:
                body = response.json()
            except Exception:
                body = response.text
            return check_result(method, response.headers.get('Content-Type'), response.status_code, body)
