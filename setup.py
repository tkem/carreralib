import codecs
import os.path
import re

from setuptools import setup

initpath = os.path.join(os.path.dirname(__file__), 'carreralib', '__init__.py')

with codecs.open(initpath, encoding='utf8') as f:
    metadata = dict(re.findall(r"__([a-z]+)__ = '([^']+)", f.read()))

setup(
    name='carreralib',
    version=metadata['version'],
    author='Thomas Kemmer',
    author_email='tkemmer@computer.org',
    url='https://github.com/tkem/carreralib',
    license='MIT',
    description='Python interface to Carrera(R) DIGITAL 124/132 slotcar systems',  # noqa
    long_description=open('README.rst').read(),
    keywords='carrera digital slotcar control unit cu',
    classifiers=[
        'Development Status :: 3 - Alpha',
        'Environment :: Other Environment',
        'Intended Audience :: Developers',
        'License :: OSI Approved :: MIT License',
        'Operating System :: POSIX :: Linux',
        'Programming Language :: Python',
        'Programming Language :: Python :: 2',
        'Programming Language :: Python :: 2.7',
        'Programming Language :: Python :: 3',
        'Programming Language :: Python :: 3.3',
        'Programming Language :: Python :: 3.4',
        'Programming Language :: Python :: 3.5',
        'Topic :: Software Development :: Libraries :: Python Modules'
    ],
    install_requires=['bluepy', 'pyserial'],
    packages=['carreralib'],
    test_suite='tests'
)
