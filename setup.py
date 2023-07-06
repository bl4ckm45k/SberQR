import sys

from setuptools import setup

if sys.version_info < (3, 7):
    raise RuntimeError('Your Python version {0} is not supported, please install '
                       'Python 3.7+'.format('.'.join(map(str, sys.version_info[:3]))))
requirements = ["aiohttp>=3.8.4", "certifi>=2023.5.7", "ujson>=5.8.0", "pytz==2022.1", "qrcode[pil]>=7.3.1",
                "aioredis>=2.0.1"]

setup(
    name='SberQR',
    version='1.0.3',
    author='bl4ckm45k',
    author_email='nonpowa@gmail.com',
    description='Асинхронная библиотека для работы с SberPay QR/Плати QR.',
    long_description_content_type="text/markdown",
    url="https://github.com/bl4ckm45k/SberQR",
    license="MIT",
    packages=['SberQR'],
    install_requires=requirements,
    classifiers=[
        'Programming Language :: Python :: 3.7',
        'Programming Language :: Python :: 3.8',
        'Programming Language :: Python :: 3.9',
        'Programming Language :: Python :: 3.10',
        'Framework :: AsyncIO',
        'Intended Audience :: Developers',
        'License :: OSI Approved :: MIT License',
        'Operating System :: OS Independent',
        'Topic :: Office/Business :: Financial'

    ],
    python_requires='>=3.7'
)
