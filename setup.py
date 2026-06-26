from setuptools import setup, find_packages

setup(
    name="rigor-cli",
    version="2.0.0",
    description="12-Role AI Engineering Team - CLI and Modules",
    python_requires=">=3.6",
    packages=find_packages(where="src"),
    package_dir={"": "src"},
    install_requires=[
        "click>=7.0",
        "pyyaml>=5.0",
        "requests>=2.20",
    ],
    entry_points={
        "console_scripts": [
            "rigor=rigor.cli:main",
        ],
    },
)
