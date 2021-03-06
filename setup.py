# Third Party
from setuptools import setup

# gitftp
from gitftp import __version__

setup(name='gitftp',
      version=__version__,
      author='Peter van der Does',
      author_email='peter@avirtualhome.com',
      license='MIT',
      description='Quick and efficient publishing of Git repositories over FTP',
      packages=['gitftp'],
      include_package_data=True,
      entry_points={'console_scripts': ['git-ftp = git-ftp:main', ], },
      package_data={'': ['README.rst']},
      install_requires=['pathspec>=0.4.0',
                        'GitPython>=2.0.8',
                        ],
      classifiers=['Development Status :: 4 - Beta',
                   'Environment :: Console',
                   'Intended Audience :: Developers',
                   'License :: OSI Approved :: MIT License',
                   'Operating System :: OS Independent',
                   'Programming Language :: Python :: 2.7',
                   'Programming Language :: Python :: 3.3',
                   'Programming Language :: Python :: 3.4',
                   'Programming Language :: Python :: 3.5',
                   'Programming Language :: Python :: 3.6',
                   'Topic :: Software Development',
                   ]
      )
