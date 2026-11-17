from setuptools import setup, find_packages
from pathlib import Path


source_packages = find_packages(where="source")
magi_packages = find_packages(where="MAGI")
packages = source_packages + ["MAGI"] + [f"MAGI.{package}" for package in magi_packages]
# MAGI's test suite and some downstream scripts use `magi.*` imports, while
# the application uses `MAGI.magi.*`; ship both supported import paths.
packages += ["magi"] + [
    f"magi.{package.removeprefix('magi.')}"
    for package in magi_packages
    if package.startswith("magi.")
]

setup(
    name="antares-fd",
    version="0.2.0",
    package_dir={"": "source", "MAGI": "MAGI", "magi": "MAGI/magi"},
    packages=packages,
    python_requires=">=3.12",
    package_data={"antares_fd.reporting": ["data/*.yaml"], "antares_fd.gui": ["static/*.html", "static/*.js", "static/*.css"]},
    install_requires=[
        line.strip()
        for line in Path(__file__).with_name("requirements.txt").read_text().splitlines()
        if line.strip() and not line.startswith(("#", "pytest"))
    ],
    extras_require={"dev": ["pytest>=7", "pytest-cov>=4", "ruff==0.17.5"],
                    "notebook": ["nbformat>=5"], "gui-test": ["playwright==1.65.2"]},
    entry_points={"console_scripts": ["antares-fd=antares_fd.cli:main"]},
)
