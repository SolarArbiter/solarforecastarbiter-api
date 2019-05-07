from setuptools import setup, find_packages
from os import path


import versioneer


with open(path.join(path.abspath(path.dirname(__file__)), 'README.md')) as f:
    long_description = f.read()


setup(
    name='sfa-api',
    version=versioneer.get_version(),
    cmdclass=versioneer.get_cmdclass(),
    description='The backend API for Solar Forecast Arbiter',
    long_description=long_description,
    long_description_content_type='text/markdown',
    url='https://github.com/solararbiter/solarforecastarbiter-api',
    author='Solar Forecast Arbiter Team',
    author_email='info@solarforecastarbiter.org',
    classifiers=[
        'Development Status :: 3 - Alpha',
        'Intended Audience :: Developers',
        'License :: OSI Approved :: MIT License',
        'Programming Language :: Python :: 3.6',
        'Programming Language :: Python :: 3.7',
    ],
    packages=find_packages(),
    include_package_data=True,
    install_requires=[
        'flask',
        'apispec',
        'marshmallow',
        'pandas',
        'sqlalchemy',
        'pymysql',
        'solarforecastarbiter'
    ],
    extra_requires={
        'test': ['pytest', 'coverage']
    },
    project_urls={
        'Bug Reports': 'https://github.com/solararbiter/solarforecastarbiter-api/issues',  # NOQA,
        'Source': 'https://github.com/solararbiter/solarforecastarbiter-api'
    }
)
