# Плати QR Сбербанк и СБП

Python Класс для работы со Сбер Банк QR.
Позволяет создавать динамический QR и проверять статус платежа

## Пример
```python
sber_qr = SberQR(member_id, id_qr, tid, client_id, client_secret, pkcs12_filename, pkcs12_password)
data = sber_qr.creation('Кофе', operation_sum=110, is_sbp=False)
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

## Ссылки
Для использования требуется аккаунт Сбер Банк бизнес.
https://sbi.sberbank.ru:9443/ic/dcb/#/

Далее необходимо Авторизоваться
https://api.developer.sber.ru/

Процесс подключения описан в инструкции
https://api.developer.sber.ru/product/PlatiQR/doc/v1/QR_API_doc3