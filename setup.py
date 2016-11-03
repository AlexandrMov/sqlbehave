from setuptools import setup, find_packages
from codecs import open
from os import path

here = path.abspath(path.dirname(__file__))

with open(path.join(here, 'README.md'), encoding='utf-8') as f:
    long_description = f.read()

setup(
    name="sqlbehave",
    version="0.0.2.dev1",
    description='sqlbehave is behaviour-driven development based on Behave package',
    long_description=long_description,
    url="https://github.com/AlexandrMov/sqlbehave",
    author='Alexandr Movsunov',
    author_email='sqlfuse@gmail.com',
    license='MIT',
    classifiers=[
        "Development Status :: 1 - Planning",
        "License :: OSI Approved :: MIT License",
        "Topic :: Software Development :: Testing",
        "Programming Language :: SQL",
        "Programming Language :: Python :: 3 :: Only"
    ],
    keywords='bdd behave sql development testing',
    install_requires=["behave>=1.2.5", "sqlalchemy>=1.1"],
    packages=find_packages(),
    package_data={
        'scripts': ['mssql'],
    },
    include_package_data=True,
    scripts=['sqlbehave/bin/sqlbehave-admin.py'],
)
