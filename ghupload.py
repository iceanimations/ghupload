#!python
# -*- coding: utf-8 -*-
import os


bare_repo_subdirs = ['hooks', 'info', 'objects', 'refs']
tree_repo_subdirs = ['.git']


def find_git_repos(directory, bare=True, tree=True):
    git_repos = list()
    for dirpath, dirnames, filenames in os.walk(directory):
        if bare and all((_dir in dirnames for _dir in bare_repo_subdirs)):
            name = os.path.basename(dirpath)
            git_repos.append( {'name': name, 'repo_type': 'bare', 'path': dirpath} )
            dirnames.clear()
        elif tree and all((_dir in dirnames for _dir in tree_repo_subdirs)):
            git_repos.append( {'name': name, 'repo_type': 'tree', 'path': dirpath} )
            dirnames.clear()
    return git_repos


def main():
    print(find_git_repos(r'r:\Pipe_Repo\Projects\repos'))


if __name__ == '__main__':
    main()
