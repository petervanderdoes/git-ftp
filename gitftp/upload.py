import ftplib
import logging
import posixpath

from git import Blob, Submodule

import gitftp.common


class Upload:
    def __init__(self, repo, oldtree, tree, ftp, base, spec):
        self.ftp = ftp
        self.repo = repo
        self.oldtree = oldtree
        self.tree = tree
        self.base = base
        self.ignore = spec

    def diff(self):
        diff = self.repo.git.diff("--name-status", "--no-renames", "-z", self.oldtree.hexsha, self.tree.hexsha)
        diff = iter(diff.split("\0"))

        for line in diff:
            if not line:
                continue
            status, file = line, next(diff)
            assert status in ['A', 'D', 'M']
            self.handle_line(status, file)

    def handle_line(self, status, file):
        filepath = posixpath.join(*(self.base[1:] + [file]))
        if self.is_ignored_path(filepath):
            logging.info('Skipped ' + filepath)
            return

        if status == "D":
            self.remove_file(file)
            return

        node = self.tree[file]
        if status == "A":
            # try building up the parent directory
            self.build_directory(file, node)

        # The node is a file so upload it.
        if isinstance(node, Blob):
            self.upload(node)
            return

        self.handle_submodule(file, node, status)

    def handle_submodule(self, file, node, status):
        module = node.module()
        module_tree = module.commit(node.hexsha).tree

        if status == "A":
            module_oldtree = gitftp.common.get_empty_tree(module)
        else:
            oldnode = self.oldtree[file]
            assert isinstance(oldnode, Submodule)  # TODO: What if not?
            module_oldtree = module.commit(oldnode.hexsha).tree

        module_base = self.base + [node.path]
        logging.info('Entering submodule %s', node.path)
        self.ftp.cwd(posixpath.join(*module_base))
        upload = Upload(module, module_oldtree, module_tree, self.ftp, module_base, self.ignore)
        upload.diff()
        logging.info('Leaving submodule %s', node.path)
        self.ftp.cwd(posixpath.join(*self.base))

    def build_directory(self, file, node):
        subtree = self.tree

        if isinstance(node, Blob):
            directories = file.split("/")[:-1]
        else:
            # for submodules also add the directory itself
            assert isinstance(node, Submodule)
            directories = file.split("/")

        for c in directories:
            subtree = subtree / c
            try:
                self.ftp.mkd(subtree.path)
            except ftplib.error_perm:
                pass

    def remove_file(self, file):
        """Remove the file from the server"""
        try:
            self.ftp.delete(file)
            logging.info('Deleted ' + file)
        except ftplib.error_perm:
            logging.warning('Failed to delete ' + file)

        # Now let's see if we need to remove some subdirectories
        self.remove_subdirectories(file)

    def remove_subdirectories(self, file):
        """Remove potential sub directories"""
        for directory in self.generate_parent_dirs(file):
            try:
                # unfortunately, dir in tree doesn't work for subdirs
                self.tree[directory]
            except KeyError:
                try:
                    self.ftp.rmd(directory)
                    logging.debug('Cleaned away ' + directory)
                except ftplib.error_perm:
                    logging.info('Did not clean away ' + directory)
                    break

    @staticmethod
    def generate_parent_dirs(x):
        # invariant: x is a filename
        while '/' in x:
            x = posixpath.dirname(x)
            yield x

    def is_ignored_path(self, path, quiet=False):
        """Returns true if a filepath is ignored by gitftpignore."""
        if self.is_special_file(path):
            return True
        if self.ignore is not None:
            if self.match_file(path):
                return True
        return False

    def match_file(self, file_path):
        return len(list(self.ignore.match_files([file_path]))) > 0  # This should not be so complicated

    @staticmethod
    def is_special_file(name):
        """Returns true if a file is some special Git metadata and not content."""
        return posixpath.basename(name) in ['.gitignore', '.gitattributes', '.gitmodules', '.gitftpignore']

    def upload(self, blob, quiet=False):
        """
        Uploads a blob.  Pre-condition on ftp is that our current working
        directory is the root directory of the repository being uploaded
        (that means DON'T use ftp.cwd; we'll use full paths appropriately).
        """
        if not quiet:
            logging.info('Uploading ' + blob.path)
        try:
            self.ftp.delete(blob.path)
        except ftplib.error_perm:
            pass
        self.ftp.storbinary('STOR ' + blob.path, blob.data_stream)
        try:
            self.ftp.voidcmd('SITE CHMOD ' + gitftp.common.format_mode(blob.mode) + ' ' + blob.path)
        except ftplib.error_perm:
            # Ignore Windows chmod errors
            logging.warning('Failed to chmod ' + blob.path)
            pass
