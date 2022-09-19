import logging

logger = logging.getLogger('payload')
DEFAULT_FILTER = ['self', 'cls']


def generate_payload(exclude=None, **kwargs):
    if exclude is None:
        exclude = ['headers', 'dt']
    data = dict()
    for k, v in kwargs.items():
        if k not in exclude + DEFAULT_FILTER and v is not None:
            data[k] = v
    logger.debug(data)
    return data
