git-ftp.py: quick and efficient publishing of Git repositories over FTP
=======================================================================

Introduction
------------

Some web hosts only give you FTP access to the hosting space, but
you would still like to use Git to version the contents of your
directory.  You could upload a full tarball of your website every
time you update but that's wasteful.  git-ftp.py only uploads the
files that changed.

This fork has been adapted to work with [git-flow (AVH Edition)](http://bit.ly/S2k1S2).

Installation
------------
Requirements: [git-python 0.3.x](http://gitorious.org/git-python)  
it can be installed with `easy_install gitpython`

`sudo make Makefile`

Usage
-----
Usage: `git ftp`

Note: If you run git-ftp.py for the first time on an existing project and you
already have files on the FTP server, you can execute
`git ftp -r <revision-on-ftp>` to only upload changes since that revision. That
avoids a full upload of all files, that might be unnecessary. If you are using
another git repository as a proxy, it might be easier to place a `git-rev.txt`
on the server. It should contain the SHA1 of the last commit which is already
present there.

Storing the FTP credentials
---------------------------

You can place FTP credentials in `.git/ftpdata`, as such:

    [master]
    username=me
    password=s00perP4zzw0rd
    hostname=ftp.hostname.com
    remotepath=/htdocs
    ssl=yes

    [develop]
    username=me
    password=s00perP4zzw0rd
    hostname=ftp.hostname.com
    remotepath=/htdocs/develop
    ssl=no

    [release/*]
    username=me
    password=s00perP4zzw0rd
    hostname=ftp.hostname.com
    remotepath=/htdocs/staging
    ssl=no

Each section corresponds to a git branch. FTP SSL support needs Python
2.7 or later.

For git-flow there are four special wildcard sections. Each of the wildcard 
section corresponds with a branch as used by git-flow. If a section is found 
with the full name that section will be used.

The sections are named:
- feature/*
- release/*
- hotfix/*
- support/*

**Example:**

The following is setup in `.git/ftpdata`
 
    [feature/*]
    username=me
    password=s00perP4zzw0rd
    hostname=ftp.hostname1.com
    remotepath=/htdocs/testing
    ssl=no

    [feature/lots-of-work]
    username=me
    password=s00perP4zzw0rd
    hostname=ftp.hostname2.com
    remotepath=/htdocs/testing
    ssl=no

If you are on the branch `feature/new-feature` and do a `git ftp`, it will be 
uploaded to `ftp.hostname1.com` as defined in the section `feature/*`. If you 
are on the branch `feature/lots-of-work` and do a `git ftp`, it will be 
uploaded to `ftp.hostname2.com` as defined in the 
section `feature/lots-of-work`.

Exluding certain files from uploading
-------------------------------------

Similarly to `.gitignore` you can specify files which you do not wish to upload.
The default file with ignore patterns is `.gitftpignore` in project root directory,
however you can specify your own for every branch in .git/ftpdata:

    [branch]
    ... credentials ...
    gitftpignore=.my_gitftpignore

Used syntax is same as .gitignore's.

Using a bare repository as a proxy
----------------------------------

An additional script post-receive is provided to allow a central bare repository
to act as a proxy between the git users and the ftp server.
Pushing on branches that don't have an entry in the `ftpdata` configuration file
will have the default git behavior (`git-ftp.py` doesn't get called).
One advantage is that **users do not get to know the ftp credentials** (perfect for interns).
This is how the workflow looks like:

    User1 --+                          +--> FTP_staging
             \                        /
    User2 -----> Git bare repository -----> FTP_master
             /                        \
    User3 --+                          +--> FTP_dev

This is how the setup looks like (One `ftpdata` configuration file, and a symlink to the update hook):

    root@server:/path-to-repo/repo.git# ls
    HEAD  ORIG_HEAD  branches  config  description  ftpdata  hooks  info  objects  packed-refs  refs
    root@server:/path-to-repo/repo.git# ls hooks -l
    total 0
    lrwxr-xr-x 1 root    root      29 Aug 19 17:17 post-receive -> /path-to-git-ftp/post-receive


License
--------

Permission is hereby granted, free of charge, to any person
obtaining a copy of this software and associated documentation
files (the "Software"), to deal in the Software without
restriction, including without limitation the rights to use,
copy, modify, merge, publish, distribute, sublicense, and/or sell
copies of the Software, and to permit persons to whom the
Software is furnished to do so, subject to the following
conditions:

The above copyright notice and this permission notice shall be
included in all copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND,
EXPRESS OR IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES
OF MERCHANTABILITY, FITNESS FOR A PARTICULAR PURPOSE AND
NONINFRINGEMENT. IN NO EVENT SHALL THE AUTHORS OR COPYRIGHT
HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER LIABILITY,
WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING
FROM, OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR
OTHER DEALINGS IN THE SOFTWARE.
