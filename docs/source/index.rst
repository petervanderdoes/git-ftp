GIT-FTP(1)
==========

NAME
----
git-ftp - Quick and efficient publishing of Git repositories over FTP

SYNOPSIS
--------

::

	git ftp [(--force | -f)] [(--quiet | -q)]
       		[(--revision | -r) <commit>] [(--commit | -c) <commit>]
       		[(--branch | -b) <branch>] [(--section | -s) <section>]

DESCRIPTION
-----------
Some web hosts only give you FTP access to the hosting space, but you would
still like to use Git to version the contents of your directory. You could
upload a full tarball of your website every time you update, but that's
wasteful. git ftp only uploads the files that changed.

OPTIONS
-------
``-f --force``
	Force the reupload of all files instead of just the changed ones.

``-q --quiet``
    Display only errors and warnings.

``-r <commit> --revision=<commit>``
	The SHA of the current revision is stored in git-rev.txt on the server.
	Use this revision instead of the server stored one, to determine which
	files have changed.

``-c <commit> --commit=<commit>``
	Upload this commit instead of HEAD or the tip of the selected branch.

``-b <branch> --branch=<branch>``
	Use this branch instead of the active one.

``-s <section> --section=<section>``
	Use this section of the ftpdata file instead of the active branch name.

FTP CREDENTIALS
---------------
You can place FTP credentials in `.git/ftpdata`, as such:

::

	[master]
	username=me
	password=s00perP4zzw0rd
	hostname=ftp.hostname.com
	remotepath=/htdocs
	ssl=yes

	[staging]
	username=me
	password=s00perP4zzw0rd
	hostname=ftp.hostname.com
	remotepath=/htdocs/staging
	ssl=no

Each section corresponds to a Git branch. If you don't create the
configuration file, git ftp will interactively prompt you.

FTP SSL support needs Python 2.7 or later.

EXCLUDING FILES FROM UPLOADING
------------------------------
Similarly to .gitignore you can exclude files from uploading.

The default file with ignore patterns is .gitftpignore in project root,
however you can specify your own for every branch in `.git/ftpdata`:

::

	[branch]
	... credentials ...
	gitftpignore=.my_gitftpignore

Used syntax is the same as used by gitignore.

USING A BARE REPOSITORY AS A PROXY
----------------------------------
An additional script post-recieve is provided to allow a central bare
repository to act as a proxy between the git users and the ftp server.

Pusing on branches that don't have an entry in the ftpdata configuration file
will have the default Git behaviour - nothing will be pushed over ftp.

One advantage is that users do not get to know the ftp credentials (perfect for interns).

This is how the workflow looks like:

::

	User 1 --+                              +--> FTP Staging
	          \                            /
	User 2 -------> Bare Git repository -------> FTP Master
	          /                            \
	User 3 --+                              +--> FTP Dev

This is how the setup looks like (one ftpdata configuration file and a symlink to the update hook):

::

	user@server:/path-to-repo/repo.git$ ls
	HEAD  ORIG_HEAD  branches  config  description  ftpdata  hooks  info

	user@server:/path-to-repo/repo.git/hooks$ ls -l
	lrwxr-xr-x 1  user user  post-recieve -> /path-to-git-ftp/post-recieve

REPORTING BUGS
--------------
Report bugs in the issue queue on Github `<https://github.com/petervanderdoes/git-ftp>`.

GIT
---
Used as a part of the :manpage:`git(1)` suite.
