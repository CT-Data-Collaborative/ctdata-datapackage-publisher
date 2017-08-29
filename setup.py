import os
import codecs
from setuptools import setup

def read(fname):
    file_path = os.path.join(os.path.dirname(__file__), fname)
    return codecs.open(file_path, encoding='utf-8').read()

setup(
    name='ctdata_ckan_publish',
    description='CLI tool for publishing CTData datasets to CKAN',
    long_description=read('README.rst'),
    url='https://github.com/CT-Data-Collaborative/ctdata-datapackage-publisher',
    author='Sasha Cuerda',
    author_email='scuerda@ctdata.org',
    license='MIT',
    version='0.1',
    py_modules=['ctdata_ckan_publish'],
    install_requires=[
        'click>=6.7',
        'requests>=2.13.0',
        'ckanapi>=4.0',
        'datapackage>=0.8.6,<1.0'],
    entry_points={
        'console_scripts': [
            'publish = ctdata_ckan_publish.__main__:main',
            ]
        },
    )
