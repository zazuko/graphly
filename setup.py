from setuptools import find_packages, setup

setup(
    name="graphly",
    version="0.1",
    long_description=__doc__,
    packages=find_packages(),
    include_package_data=True,
    zip_safe=False,
    install_requires=[
        "requests>=2.22.0",
        "pandas>=1.1.3",
        "networkx>=2.5",
        "matplotlib>=3.3.2"
    ]
)
