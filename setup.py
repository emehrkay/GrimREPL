from setuptools import setup, find_packages

setup(
    name='gremrepl',
    author='Mark Henderson',
    email='emehrkay@gmail.com',
    version='0.1.0',
    entry_points={
        'console_scripts': ['gremrepl=gremrepl.repl:cli'],
    }
)
