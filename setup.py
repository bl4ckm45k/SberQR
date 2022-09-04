import sys

from setuptools import setup

if sys.version_info < (3, 6):
    raise RuntimeError('Your Python version {0} is not supported, please install '
                       'Python 3.6+'.format('.'.join(map(str, sys.version_info[:3]))))
requirements = ["aiohttp>=3.8.1", "certifi>=2022.6.15", "ujson>=5.3.0", "pytz==2022.1", "qrcode[pil]==7.3.1",
                "requests==2.27.1", "requests-pkcs12==1.13"]

setup(
    name='SberQR',
    version='1.0.0',
    author='Doncode',
    author_email='your_email@doncode.com',
    description='Библиотека для работы со Сбер Банк QR.',
    long_description_content_type="text/markdown",
    url="https://github.com/Doncode/sber-qr",
    license="MIT",
    packages=['SberQR'],
    install_requires=requirements,
    classifiers=[
        'Programming Language :: Python :: 3.6',
        'Programming Language :: Python :: 3.7',
        'Programming Language :: Python :: 3.8',
        'Programming Language :: Python :: 3.9',
        'Programming Language :: Python :: 3.10',
        'Framework :: AsyncIO',
        'Intended Audience :: Developers',
        'License :: OSI Approved :: MIT License',
        'Operating System :: OS Independent',

    ],
    python_requires='>=3.6'
)
