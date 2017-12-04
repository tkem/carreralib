from setuptools import find_packages, setup


def get_version(filename):
    from re import findall
    with open(filename) as f:
        metadata = dict(findall("__([a-z]+)__ = '([^']+)'", f.read()))
    return metadata['version']


setup(
    name='carreralib',
    version=get_version('carreralib/__init__.py'),
    url='https://github.com/tkem/carreralib',
    license='MIT',
    author='Thomas Kemmer',
    author_email='tkemmer@computer.org',
    description='Python interface to Carrera(R) DIGITAL 124/132 slotcar systems',  # noqa
    long_description=open('README.rst').read(),
    keywords='carrera digital slotcar control unit cu',
    packages=find_packages(exclude=['tests', 'tests.*']),
    install_requires=['bluepy', 'pyserial'],
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
        'Programming Language :: Python :: 3.4',
        'Programming Language :: Python :: 3.5',
        'Programming Language :: Python :: 3.6',
        'Topic :: Software Development :: Libraries :: Python Modules'
    ]
)
