"""
Пример использования SberQR.py
"""
from datetime import datetime
from time import sleep

import qrcode

from SberQR import SberQR

member_id = '00000105'  # выдается через почту support@ecom.sberbank.ru
tid = '24601234'  # ID  терминала/Точки. Получить в ЛК Сбрербанк бизнес на странице Информация о точке
id_qr = '1000301234'  # Номер наклейки с QR-кодом. Получить в ЛК Сбрербанк бизнес Информация о точке/список оборудования
client_id = '6e7254e2-6de8-4074-b458-b7238689772b'  # получить на api.developer.sber.ru
client_secret = '3a0ea8cb-886c-4efa-ac45-e3d36aaba335'  # получить на api.developer.sber.ru
pkcs12_filename = 'key/key.p12'  # Файл сертификат. Получается на api.developer.sber.ru
pkcs12_password = 'SomeSecret'  # Пароль от файла сертификат. Получается на api.developer.sber.ru

sber_qr = SberQR(member_id, id_qr, tid, client_id, client_secret, pkcs12_filename, pkcs12_password)

operation_sum = 150
data = sber_qr.creation('Кофе', operation_sum, is_sbp=False)
print(data)

# Сохраним QR в файл qr.png
qrcode.make(data['order_form_url']).save("qr.png")


# # отмена до оплаты
# data_revoke = sber_qr.revoke(data['order_id'])
# print(data_revoke)

while True:
    sleep(1)
    data_status = sber_qr.status(data['order_id'], data['order_number'])
    print(data_status)

    if data_status['order_state'] == 'PAID':
        print('Оплачено')
        break

# Отмена/возврат
data_cancel = sber_qr.cancel(
    data_status['order_id'],
    data_status['order_operation_params'][0]['operation_id'],
    operation_sum,
    data_status['order_operation_params'][0]['auth_code'],
)
print(data_cancel)

data = sber_qr.registry(datetime(2022, 4, 13), datetime(2022, 4, 14))
print(data)
