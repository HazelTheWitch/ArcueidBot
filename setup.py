from setuptools import setup, find_packages


setup(
    name='arcueid',
    version='1.0.0',
    package_dir={'': 'src'},
    packages=find_packages(where='src'),
    python_requires='>=3.10, <4',
    install_requires=[
        'discord.py[voice]',
        'click',
        'pytz'
    ],
    entry_points={
        'console_scripts': [
            'arcueid_settings=arcueid.__main__:generateSettings',
            'arcueid=arcueid.__main__:launch'
        ]
    }
)
