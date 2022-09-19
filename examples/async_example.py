"""
Пример использования AsyncSberQR.py
"""
import asyncio
import logging
import os
from typing import List, Dict, Union

import qrcode

# import aioredis
from SberQR import AsyncSberQR
from SberQR.types import CancelType

logger = logging.getLogger(__name__)
member_id = '00000105'  # выдается через почту support@ecom.sberbank.ru
tid = '24601234'  # ID  терминала/Точки. Получить в ЛК Сбрербанк бизнес на странице Информация о точке
id_qr = '1000301234'  # Номер наклейки с QR-кодом. Получить в ЛК Сбрербанк бизнес Информация о точке/список оборудования
client_id = '6e7254e2-6de8-4074-b458-b7238689772b'  # получить на api.developer.sber.ru
client_secret = '3a0ea8cb-886c-4efa-ac45-e3d36aaba335'  # получить на api.developer.sber.ru

#
crt_from_pkcs12 = f'{os.getcwd()}/cert.crt'  # Для асинхронной версии требуется распаковать сертификат
key_from_pkcs12 = f'{os.getcwd()}/private.key'  # Для асинхронной версии требуется распаковать приватный ключ
pkcs12_password = 'SomeSecret'  # Пароль от файла сертификат. Получается на api.developer.sber.ru

# Без использования Redis
sber_qr = AsyncSberQR(member_id, id_qr=tid, tid=tid, client_id=client_id, client_secret=client_secret,
                      crt_file_path=crt_from_pkcs12, key_file_path=key_from_pkcs12, pkcs12_password=pkcs12_password)


# Если требуется передайте аргумент redis= (str or Redis obj)
# redis = aioredis.from_url("redis://localhost", decode_responses=True)
# redis = "redis://localhost"
async def main_func(order_sum, order_number, positions: Union[List, Dict]):
    data = await sber_qr.creation(
        description=f'Оплата заказа {order_number}',
        order_sum=order_sum,
        order_number=order_number,
        positions=positions)
    logger.info(f'{data}')
    # Сохраним QR в файл qr.png
    qrcode.make(data['order_form_url']).save("qr.png")
    await check_paid(data['order_id'], order_number)


async def check_paid(order_id, order_number):
    data_status = await sber_qr.status(order_id, order_number)
    if data_status['order_state'] != 'PAID':
        print('Заказ не оплачен, отменяем')
        await revoke_payment(order_id)
    else:
        await sber_qr.cancel(order_id,
                             operation_id=data_status[0]['operation_id'],
                             cancel_operation_sum=data_status[0]['operation_sum'],
                             auth_code=data_status[0]['auth_code'],
                             operation_type=CancelType.REVERSE,
                             sbp_payer_id=None)  # sbp_payer_id номер телефона клиента в формате +79998887766, если возврат по СБП
        # CancelType.REVERSE - Если прошло менее 24 часов с оплаты
        # CancelType.REFUND - Если прошло более 24 часов с оплаты


async def revoke_payment(order_id):
    data_revoke = await sber_qr.revoke(order_id)
    logger.info(f'Revoke result: {data_revoke}')


if __name__ == '__main__':
    positions = [
        {"position_name": "Что-то а 10 рублей",
         "position_count": 1,
         "position_sum": 1000,
         "position_description": "Какой-то товар за 10 рублей"}]
    asyncio.run(main_func(1000, "4", positions))
