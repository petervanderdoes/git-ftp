#!/usr/bin/env python

"""
git-ftp: painless, quick and easy working copy syncing over FTP
"""

# Standard Library
import ftplib
import getpass
import logging
import optparse
import os.path
import sys
import textwrap
from distutils.version import LooseVersion
from io import BytesIO

# Third Party
import pathspec
from git import (
    Git,
    InvalidGitRepositoryError,
    Repo,
    __version__ as git_version
)

# gitftp
import gitftp.common
import gitftp.upload

try:
    import configparser as ConfigParser
except ImportError:
    import ConfigParser

__version__ =  '1.3.0'

# Note about Tree.path/Blob.path: *real* Git trees and blobs don't
# actually provide path information, but the git-python bindings, as a
# convenience keep track of this if you access the blob from an index.
# This ends up considerably simplifying our code, but do be careful!


if LooseVersion(git_version) < '0.3.0':
    print('git-ftp requires git-python 0.3.0 or newer; {0!s} provided.'.format(git_version))
    exit(1)


class BranchNotFound(Exception):
    pass


class FtpDataOldVersion(Exception):
    pass


class FtpSslNotSupported(Exception):
    pass


class SectionNotFound(Exception):
    pass


def main():
    Git.git_binary = 'git'  # Windows doesn't like env

    options, args = parse_args()

    configure_logging(options)

    if options.show_version:
        print("git-ftp version {0!s} ".format(__version__))
        sys.exit(0)

    if args:
        cwd = args[0]
    else:
        cwd = "."
    repo = get_repo(cwd)

    options.branch = get_value(options.branch, repo.active_branch.name)
    options.section = get_value(options.section, options.branch)

    get_ftp_creds(repo, options)

    if repo.is_dirty() and not options.commit:
        logging.warning("Working copy is dirty; uncommitted changes will NOT be uploaded")

    base = options.ftp.remotepath
    branch = get_branch(base, options, repo)

    options.commit = get_value(options.commit, branch)
    commit = repo.commit(options.commit)

    tree = commit.tree
    ftp = get_ftp_class(options)
    ftp.cwd(base)

    gitftpignore = os.path.join(repo.working_dir, options.ftp.gitftpignore)
    spec = None
    if os.path.isfile(gitftpignore):
        with open(gitftpignore, 'r') as ftpignore:
            spec = pathspec.PathSpec.from_lines(pathspec.GitIgnorePattern, ftpignore)

    # Check revision
    oldtree = get_old_tree(ftp, options, repo)

    if oldtree.hexsha == tree.hexsha:
        logging.info('Nothing to do!')
    else:
        upload = gitftp.upload.Upload(repo, oldtree, tree, ftp, [base], spec)
        upload.diff()
        ftp.storbinary('STOR git-rev.txt', BytesIO(commit.hexsha.encode('utf-8')))

    ftp.quit()


def get_branch(base, options, repo):
    logging.info("Base directory is %s", base)
    try:
        branch = next(h for h in repo.heads if h.name == options.branch)
    except StopIteration:
        raise BranchNotFound
    return branch


def get_repo(cwd):
    try:
        repo = Repo(cwd)
    except InvalidGitRepositoryError:
        logging.error('No git repository found')
        exit()
    return repo


def get_value(option, default):
    if not option:
        return default
    return option


def get_ftp_class(options):
    if options.ftp.ssl:
        if hasattr(ftplib, 'FTP_TLS'):  # SSL new in 2.7+
            ftp = ftplib.FTP_TLS(options.ftp.hostname, options.ftp.username, options.ftp.password)
            ftp.prot_p()
            logging.info("Using SSL")
        else:
            raise FtpSslNotSupported(
                "Python is too old for FTP SSL. Try using Python 2.7 or later.")
    else:
        ftp = ftplib.FTP(options.ftp.hostname, options.ftp.username, options.ftp.password)
    return ftp


def get_old_tree(ftp, options, repo):
    """Get the tree to which we are comparing the new tree too"""
    hash = options.revision
    if not options.force and not hash:
        hashFile = BytesIO()
        try:
            ftp.retrbinary('RETR git-rev.txt', hashFile.write)
            hash = hashFile.getvalue().decode('utf-8').strip()
        except ftplib.error_perm:
            pass
    if not hash:
        # Diffing against an empty tree will cause a full upload.
        oldtree = gitftp.common.get_empty_tree(repo)
    else:
        oldtree = repo.commit(hash).tree
    return oldtree


def parse_args():
    usage = 'usage: %prog [OPTIONS] [DIRECTORY]'
    desc = """\
           This script uploads files in a Git repository to a
           website via FTP, but is smart and only uploads file
           that have changed.
           """
    parser = optparse.OptionParser(usage, description=textwrap.dedent(desc))
    parser.add_option('-f', '--force', dest="force", action="store_true", default=False,
                      help="force the reupload of all files")
    parser.add_option('-q', '--quiet', dest="quiet", action="store_true", default=False,
                      help="quiet output")
    parser.add_option('-r', '--revision', dest="revision", default=None,
                      help="use this revision instead of the server stored one")
    parser.add_option('-b', '--branch', dest="branch", default=None,
                      help="use this branch instead of the active one")
    parser.add_option('-c', '--commit', dest="commit", default=None,
                      help="use this commit instead of HEAD")
    parser.add_option('--version', action="store_true", dest="show_version",
                      default=False, help='displays the version number')
    parser.add_option('-s', '--section', dest="section", default=None,
                      help="use this section from ftpdata instead of branch name")
    options, args = parser.parse_args()

    if len(args) > 1:
        parser.error("too many arguments")

    return options, args


def configure_logging(options):
    logger = logging.getLogger()
    if not options.quiet:
        logger.setLevel(logging.INFO)
    ch = logging.StreamHandler(sys.stderr)
    formatter = logging.Formatter("%(levelname)s: %(message)s")
    ch.setFormatter(formatter)
    logger.addHandler(ch)


class FtpData():
    password = None
    username = None
    hostname = None
    remotepath = None
    ssl = None
    gitftpignore = None


def get_ftp_creds(repo, options):
    """
    Retrieves the data to connect to the FTP from .git/ftpdata
    or interactively.

    ftpdata format example:

        [branch]
        username=me
        password=s00perP4zzw0rd
        hostname=ftp.hostname.com
        remotepath=/htdocs
        ssl=yes
        gitftpignore=.gitftpignore

    Please note that it isn't necessary to have this file,
    you'll be asked for the data every time you upload something.
    """

    ftpdata = os.path.join(repo.git_dir, "ftpdata")
    options.ftp = FtpData()
    cfg = ConfigParser.ConfigParser()
    if os.path.isfile(ftpdata):
        get_ftp_creds_from_file(cfg, ftpdata, options, repo)
    else:
        print("Please configure settings for branch '{0!s}'".format(options.section))
        options.ftp.username = input('FTP Username: ')
        options.ftp.password = getpass.getpass('FTP Password: ')
        options.ftp.hostname = input('FTP Hostname: ')
        options.ftp.remotepath = input('Remote Path: ')
        if hasattr(ftplib, 'FTP_TLS'):
            options.ftp.ssl = ask_ok('Use SSL? ')
        else:
            logging.warning("SSL not supported, defaulting to no")

        # set default branch
        if ask_ok("Should I write ftp details to .git/ftpdata? "):
            cfg.add_section(options.section)
            cfg.set(options.section, 'username', options.ftp.username)
            cfg.set(options.section, 'password', options.ftp.password)
            cfg.set(options.section, 'hostname', options.ftp.hostname)
            cfg.set(options.section, 'remotepath', options.ftp.remotepath)
            cfg.set(options.section, 'ssl', options.ftp.ssl)
            f = open(ftpdata, 'w')
            cfg.write(f)


def get_ftp_creds_from_file(cfg, ftpdata, options, repo):
    logging.info("Using .git/ftpdata")
    cfg.read(ftpdata)
    git_config = repo.config_reader()
    if not cfg.has_section(options.section):
        handle_gitflow_wildcard_branches(git_config, options)

    if (not cfg.has_section(options.section)):
        if cfg.has_section('ftp'):
            raise FtpDataOldVersion("Please rename the [ftp] section to [branch]. " +
                                    "Take a look at the README for more information")
        else:
            raise SectionNotFound("Your .git/ftpdata file does not contain a section " +
                                  "named '{0!s}'".format(options.section))

    # just in case you do not want to store your ftp password.
    try:
        options.ftp.password = cfg.get(options.section, 'password')
    except ConfigParser.NoOptionError:
        options.ftp.password = getpass.getpass('FTP Password: ')

    options.ftp.username = cfg.get(options.section, 'username')
    options.ftp.hostname = cfg.get(options.section, 'hostname')
    options.ftp.remotepath = cfg.get(options.section, 'remotepath')
    try:
        options.ftp.ssl = boolish(cfg.get(options.section, 'ssl'))
    except ConfigParser.NoOptionError:
        options.ftp.ssl = False
    try:
        options.ftp.gitftpignore = cfg.get(options.section, 'gitftpignore')
    except ConfigParser.NoOptionError:
        options.ftp.gitftpignore = '.gitftpignore'


def handle_gitflow_wildcard_branches(git_config, options):
    if git_config.has_section('gitflow "prefix"'):
        gitflow_branches = ['feature',
                            'hotfix',
                            'release',
                            'support',
                            'bugfix']

        for gitflow_branch in gitflow_branches:
            if (git_config.has_option('gitflow "prefix"', gitflow_branch) and
                    options.branch.startswith(git_config.get('gitflow "prefix"', gitflow_branch))):
                options.section = git_config.get('gitflow "prefix"', gitflow_branch) + '/*'
                break


def boolish(s):
    if s in ('1', 'true', 'y', 'ye', 'yes', 'on'):
        return True
    if s in ('0', 'false', 'n', 'no', 'off'):
        return False
    return None


def ask_ok(prompt, retries=4, complaint='Yes or no, please!'):
    while True:
        ok = input(prompt).lower()
        r = boolish(ok)
        if r is not None:
            return r
        retries = retries - 1
        if retries < 0:
            raise IOError('Wrong user input.')
        print(complaint)


if __name__ == "__main__":
    main()
