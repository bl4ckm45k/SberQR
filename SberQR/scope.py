from enum import Enum


class Scope(Enum):
    create = 'https://api.sberbank.ru/qr/order.create'
    status = 'https://api.sberbank.ru/qr/order.status'
    revoke = 'https://api.sberbank.ru/qr/order.revoke'
    cancel = 'https://api.sberbank.ru/qr/order.cancel'
    registry = 'auth://qr/order.registry'
    notify = 'auth://qr/order.notify'
