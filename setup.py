from setuptools import setup, find_packages

exec(open('gremlinpy/version.py').read())

setup(
    name='gremrepl',
    author='Mark Henderson',
    email='emehrkay@gmail.com',
    version=__version__,
)
