#!python
# -*- coding: utf-8 -*-
import os
import github
import yaml
import pygit2
import shutil
import tempfile
import time


GHCLIENT = None
CURDIR = os.path.dirname(__file__)
TOKEN = None


def find_git_repos(directory, bare=True, tree=True):
    # type: (str, bool, bool) -> List[pygit2.Repository]
    git_repos = list()
    for dirpath, dirnames, filenames in os.walk(directory):
        try:
            git_repos.append(pygit2.Repository(dirpath))
            dirnames.clear()
        except pygit2.GitError:
            pass
    return git_repos


def get_github_auth():
    yamlpath = r'C:\Users\talha.ahmed\AppData\Roaming\GitHub CLI\hosts.yml'
    with open(yamlpath) as _file:
        data = yaml.safe_load(_file)
    return data 


def github_login():
    global GHCLIENT, TOKEN
    TOKEN = get_github_auth()['github.com']['oauth_token']
    GHCLIENT = github.Github(TOKEN)


def ensure_github(func):
    def _wrapper(*args, **kwargs):
        if GHCLIENT is None:
            github_login()
        return func(*args, **kwargs)
    return _wrapper


@ensure_github
def github_repo(localrepo):
    # type: (pygit2.Repository) -> github.Repository.Repository
    global GHCLIENT
    gh = GHCLIENT
    name = os.path.basename(localrepo.path.strip('/')) 
    organization = gh.get_organization('iceanimations')
    try:
        ghrepo = organization.get_repo(name)
        return ghrepo
    except github.UnknownObjectException:
        ghrepo = organization.create_repo(name)
        return ghrepo
    return ghrepo


def add_as_remote(localrepo, ghrepo):
    # type: (pygit2.Repository, github.Repository.Repository) -> pygit2.remote.Remote
    remote = None
    try:
        remote = localrepo.remotes['github']
    except KeyError:
        remote = localrepo.remotes.create('github', ghrepo.clone_url)
    return remote


def check_for_file(localrepo, filename):
    # type: (pygit2.Repository) -> bool
    return filename in [e.name
            for e in localrepo.revparse_single('master').tree
                     if e.type == 3]


def add_opensource_license(localrepo):
    # type: (pygit2.Repository) -> bool
    reponame = os.path.basename(localrepo.path.strip('/'))
    clone_path = os.path.join('D:/', 'clones', reponame)
    if os.path.isdir(clone_path):
        shutil.rmtree(clone_path)
    else:
        try:
            os.makedirs(os.path.join('D:/', 'clones'))
        except FileExistsError:
            pass

    clone_repo = pygit2.clone_repository(localrepo.path, clone_path)
    clone_repo.remotes.set_url('origin', localrepo.path)

    index = clone_repo.index
    shutil.copy(
        os.path.join(CURDIR, 'LICENSE'),
        clone_path
    )

    readme_path = os.path.join(clone_path, 'README.md')
    if not os.path.isfile(readme_path):
        shutil.copy('README.md', clone_path)
    else:
        with open(os.path.join(CURDIR, 'README.md')) as _readme:
            text = _readme.read()
        with open(readme_path, 'a') as _readme:
            _readme.write(text)

    index.add_all()
    index.add('LICENSE')
    index.add('README.md')
    index.write()

    author = pygit2.Signature('Talha Ahmed', 'talha.ahmed@gmail.com')
    committer = pygit2.Signature('Talha Ahmed', 'talha.ahmed@gmail.com')
    tree = index.write_tree()
    clone_repo.create_commit(
        'refs/heads/master',
        author,
        committer,
        'Adding LICENSE info',
        tree,
        [clone_repo.head.target]
    )

    remote = clone_repo.remotes['origin']
    remote.push(['refs/heads/master'])
    return True


def push_to_github(localrepo):
    cred = pygit2.UserPass(TOKEN, 'x-oauth-basic')
    callbacks = pygit2.RemoteCallbacks(credentials=cred)
    remote = localrepo.remotes['github']
    remote.push(['refs/heads/master'], callbacks=callbacks)


def opensource_repo(localrepo):
    # type: (pygit2.Repository) -> github.Repository.Repository
    ghrepo = github_repo(localrepo)
    add_as_remote(localrepo, ghrepo)
    print('push {} to {}'.format(localrepo.path, localrepo.remotes['github'].url))
    if check_for_file(localrepo, 'LICENSE'):
        add_opensource_license(localrepo)
    push_to_github(localrepo)
    return ghrepo


def main():
    repos = find_git_repos(r'r:\Pipe_Repo\Projects\repos')
    while repos:
        for repo in repos[:]:
            try:
                opensource_repo(repo)
                repos.remove(repo)
            except (pygit2.GitError, github.GithubException):
                pass


if __name__ == '__main__':
    main()
