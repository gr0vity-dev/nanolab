from setuptools import setup, find_packages

with open("README.md", "r") as fh:
    long_description = fh.read()

setup(name="nanolab",
      version="0.0.12",
      author="gr0vity",
      description="testing tool using nanomock",
      long_description=long_description,
      long_description_content_type="text/markdown",
      url="https://github.com/gr0vity-dev/nanolab",
      packages=find_packages(exclude=["unit_tests"]),
      include_package_data=True,
      install_requires=["nanomock>=0.0.14", "sqlalchemy", "aiohttp", "nanolog_parser"],
      entry_points={
          'console_scripts': [
              'nanolab=nanolab.main:main',
          ],
      })
