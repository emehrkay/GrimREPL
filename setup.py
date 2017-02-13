from setuptools import setup, find_packages

exec(open('gremrepl/version.py').read())

install_requires = [
    'terminaltables',
    'websockets'
]

setup(
    name='gremrepl',
    author='Mark Henderson',
    email='emehrkay@gmail.com',
    version=__version__,
    install_requires = install_requires,
)
