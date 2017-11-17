from setuptools import setup
import os


def _read(fn):
    path = os.path.join(os.path.dirname(__file__), fn)
    return open(path).read()

setup(
    name='vision2018',
    version='0.0.1',
    packages=['vision2018'],
    entry_points={'console_scripts': ['vision2018 = vision2018.__main__:main']},
    install_requires=[
        'zmq',
        'numpy',
        'flask'
    ],
    include_package_data=True,
    long_description=_read('README.md'),
)
