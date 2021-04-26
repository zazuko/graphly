from setuptools import find_packages, setup

setup(
    name="graphly",
    version="0.1",
    long_description=__doc__,
    packages=find_packages(),
    include_package_data=True,
    zip_safe=False,
    install_requires=[
        "requests>=2.25.1",
        "networkx>=2.5.1",
        "matplotlib>=3.4.1",
        "geopandas>=0.9.0",
        "pandas>=1.2.4"
    ],
    extras_require={
        'dev': [
            'pytest',
            'pytest-cov'
        ]
    }
)
