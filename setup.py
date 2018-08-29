from setuptools import setup, find_packages

setup(
    name='minv',
    version='0.1.0',
    packages=find_packages(),
    install_requires=['invoke'],
    entry_points={
        'console_scripts': ['minv=minv.main:program.run']
    }
)
