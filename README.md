# Плати QR Сбербанк и СБП

Библиотека для работы со Сбер Банк QR.

Позволяет создавать динамический QR и проверять статус платежа.

Поддерживает синхронное (requests) и асинхронное взаимодействие (aiohttp)

## Пример (sync)

```python
from SberQR import SyncSberQR

sber_qr = SyncSberQR(member_id, id_qr, tid, client_id, client_secret, pkcs12_filename, pkcs12_password)
positions = [{"position_name": 'Товар ра 10 рублей',
              "position_count": 1,
              "position_sum": 1000,
              "position_description": 'Какой-то товар за 10 рублей'}
             ]
data = sber_qr.creation(description=f'Оплата заказа 3', order_sum=1000, order_number="3", positions=positions)
print(data)
```

> Если при инициализации классов `AsyncSberQR` и `SyncSberQR` переданы одинаковые `tid` и `id_qr`, то будет создан
> платеж через СБП, иначе через ПлатиQR.
## Пример (async)

```python
import asyncio
from SberQR import AsyncSberQR

sber_qr = AsyncSberQR(member_id, id_qr, tid, client_id, client_secret,
                      path_crt_from_pkcs12, path_key_from_pkcs12, pkcs12_password)
positions = [{"position_name": 'Товар ра 10 рублей',
              "position_count": 1,
              "position_sum": 1000,
              "position_description": 'Какой-то товар за 10 рублей'}
             ]
async def creation_qr():
    data = await sber_qr.creation(description=f'Оплата заказа 3', order_sum=1000, order_number="3", positions=positions)
    print(data)
if __name__ == '__main__':
    asyncio.run(creation_qr())
```

Для работы потребуется получить от банка следующие параметры
```python
member_id = '00000105'  # выдается через почту support@ecom.sberbank.ru 
tid = '24601234'  # ID  терминала/Точки. Получить в ЛК Сбрербанк бизнес на странице Информация о точке
id_qr = '1000301234'  # Номер наклейки с QR-кодом. Получить в ЛК Сбрербанк бизнес Информация о точке/список оборудования
client_id = '6e7254e2-6de8-4074-b458-b7238689772b'  # получить на api.developer.sber.ru
client_secret = '3a0ea8cb-886c-4efa-ac45-e3d36aaba335'  # получить на api.developer.sber.ru
pkcs12_filename = 'key/key.p12'  # Файл сертификат. Получается на api.developer.sber.ru
pkcs12_password = 'SomeSecret'  # Пароль от файла сертификат. Получается на api.developer.sber.ru
```

## Отличия асинхронной версии от синхронной
>В Отличии от синхронной версии, асинхронная требуется распаковать сертификат самостоятельно с помощью openssl.

[Инструкция от ssl.com](https://www.ssl.com/ru/how-to/export-certificates-private-key-from-pkcs12-file-with-openssl/ "SSL.com") - для Windows обратите внимание на Cygwin в инструкции

```
Откройте командную строку, перейдите в папку, где лежит архив сертификата с расширением .p12. Выполните команду:

openssl pkcs12 -in <название_архива>.p12 -nodes -nocerts -out private.key

Появится запрос пароля. Введите пароль, который вы вводили при создании приложения, нажмите Enter.

Далее аналогично выполните команду:

openssl pkcs12 -in <название_архива>.p12 -clcerts -nokeys -out client_cert.crt

В итоге вы получите приватный ключ в файле private.key и клиентский сертификат в файле client_cert.crt в папке, где лежит архив сертификата.
````
## Ссылки
Для использования требуется аккаунт Сбер Банк бизнес.
https://sbi.sberbank.ru:9443/ic/dcb/#/

Далее необходимо Авторизоваться
https://api.developer.sber.ru/

Процесс подключения описан в инструкции
https://api.developer.sber.ru/product/PlatiQR/doc/v1/QR_API_doc3