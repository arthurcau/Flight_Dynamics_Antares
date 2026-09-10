from setuptools import setup, find_packages

setup(
    name="antares-fd",
    version="0.1.0",
    package_dir={
        "antares_fd": "source/antares_fd",
        "MAGI": "MAGI"
    },
    packages=["antares_fd", "MAGI"],
)
