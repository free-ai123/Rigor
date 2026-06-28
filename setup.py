from setuptools import find_packages, setup

setup(
    name="rigor-cli",
    version="2.0.0",
    description="12-Role AI Engineering Team - CLI and Modules",
    python_requires=">=3.10",
    packages=find_packages(where="src"),
    package_dir={"": "src"},
    package_data={"rigor.tui": ["*.tcss"]},
    install_requires=[
        "click>=8.0",
        "pyyaml>=6.0.1",
        "requests>=2.31.0",
        "rich>=13.0",
    ],
    extras_require={
        "dev": ["pytest>=7.0", "pytest-cov>=5.0", "ruff>=0.5.0", "pre-commit>=3.5", "textual>=0.40.0"],
        "security": ["pip-audit>=2.7"],
        "tui": ["textual>=0.40.0"],
    },
    entry_points={
        "console_scripts": [
            "rigor=rigor.cli:main",
        ],
    },
)
