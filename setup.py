from setuptools import setup, find_packages
with open('README.rst') as f:
    readme = f.read()
setup(name='git-ftp',
      version="1.3.0-dev.30"
      author='Peter van der Does',
      author_email='peter@avirtualhome.com',
      license='MIT',
      description='Quick and efficient publishing of Git repositories over FTP',
      long_description=readme,
      packages=find_packages())