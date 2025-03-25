"""Setup script for pytui."""

from setuptools import setup, find_packages

setup(
    name='pytui',
    version='0.1.0',
    description='Python Terminal UI',
    author='Your Name',
    author_email='your.email@example.com',
    packages=find_packages(),
    install_requires=[
        'click>=7.0',
        'rich>=10.0.0',
        'pytest>=6.0.0',
        'pytest-asyncio>=0.14.0',
        'psutil>=5.8.0',  # For process management
    ],
    entry_points={
        'console_scripts': [
            'pytui=pytui.cli:cli',
        ],
    },
)