from setuptools import setup, find_packages

setup(
    name="bac-hunter",
    version="0.1.0",
    packages=find_packages(),
    install_requires=["aiohttp>=3.9", "pyyaml>=6.0"],
    entry_points={"console_scripts": ["bac-hunter=bac_hunter.cli:main"]},
    python_requires=">=3.10",
)
