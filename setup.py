from setuptools import setup, find_packages

setup(
    name='sfa-dash',
    description=('Dashboard for interacting with Solar Forecast Arbiter'
                 'Backend'),
    url='https://github.com/SolarArbiter/solarforecastarbiter_dashboard',
    author='Solar Forecast Arbiter Team',
    author_email='info@solarforecastarbiter.org',
    packages=find_packages(),
    install_requires=['flask', 'requests', 'pandas'],
)
