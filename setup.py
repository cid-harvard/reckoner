from setuptools import setup

setup(
    name="reckoner",
    version="v0.0.1",
    author="Mali Akmanalp <Harvard CID>",
    description=("Tools to validate dataset quality."),
    url="http://github.com/cid-harvard/reckoner/",
    packages=["reckoner"],
    package_dir={
        "reckoner": "."
    }
)
