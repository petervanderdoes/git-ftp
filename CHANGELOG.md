[petervanderdoes]: https://github.com/petervanderdoes "Peter van der Does on github"
[umeku]: https://github.com/umeku
[niklasf]: https://github.com/niklasf

# Changelog

#### 1.4.0.dev1
* Preparation for new development cycle.

#### 1.3.0
[Peter van der Does][petervanderdoes]
* Modify for Python3 usage
* Implement full use of wildmatch pattern for .gitftpignore.
  Previously the pattern you could use for .gitftpignore was not fully compatible
  with the wildmatch pattern, used by gitignore. For example you could not use negate.
* Using gitflow branches with non default prefix does not work.

#### 1.2.0
* Update from upstream

#### 1.1.0
[Peter van der Does][petervanderdoes]
* Handle execution in a non git repository.
* Merge with git-ftp repository from [Niklas Fiekas][niklasf]    
  Introduces several improvements over the original repository. Including the
  ability for excluding certain files from uploading.

[umeku][umeku]
* Handle executing on a non-configured branch.
* Allow git-rev.txt to have a newline after hash.

#### 1.0.0
* Introduce wildcard sections

#### 0.0.0
* Original fork.
