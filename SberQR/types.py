from enum import Enum


class CancelType(Enum):
    REFUND = 'REFUND'
    REVERSE = 'REVERSE'


class RegistryType(Enum):
    REGISTRY = 'REGISTRY'
    QUANTITY = 'QUANTITY'
