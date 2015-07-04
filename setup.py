import os.path, codecs, re

from setuptools import setup


with codecs.open(os.path.join(os.path.dirname(__file__), 'carreralib', '__init__.py'),
                 encoding='utf8') as f:
    metadata = dict(re.findall(r"__([a-z]+)__ = '([^']+)", f.read()))


setup(
    name='carreralib',
    version=metadata['version'],
    author='Thomas Kemmer',
    author_email='tkemmer@computer.org',
    url='https://github.com/tkem/carreralib',
    license='MIT',
    description='Python library for communication with Carrera Digital 124/132 Control Unit',
    long_description=open('README.rst').read(),
    keywords='carrera digital control unit slotcar',
    classifiers=[
        'Development Status :: 5 - Production/Stable',
        'Environment :: Other Environment',
        'Intended Audience :: Developers',
        'License :: OSI Approved :: MIT License',
        'Operating System :: OS Independent',
        'Programming Language :: Python',
        'Programming Language :: Python :: 2',
        'Programming Language :: Python :: 2.7',
        'Topic :: Software Development :: Libraries :: Python Modules'
    ],
    packages=['carreralib'],
    test_suite='tests'
)
