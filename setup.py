from setuptools import setup, find_packages


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
    version="0.1.0",
    package_dir={"": "source", "MAGI": "MAGI", "magi": "MAGI/magi"},
    packages=packages,
    entry_points={"console_scripts": ["antares-fd=antares_fd.cli:main"]},
)
