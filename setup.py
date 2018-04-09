from distutils.core import setup

setup(
    name='Sirang',
    version='0.1.0',
    author='Simon Haxby',
    author_email='simon.haxby@gmail.com',
    url='https://github.com/avicennax/sirang',
    packages=['sirang'],
    license='MIT',
    description='Module for storing and retrieve experiment parameters',
    python_requires='>=3.4',
    long_description=open('README.md').read(),
    install_requires=open('requirements.txt').read().split('\n')[:-1]
)
