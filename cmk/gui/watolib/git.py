#!/usr/bin/env python
# -*- coding: utf-8 -*-
# Copyright (C) 2019 tribe29 GmbH - License: GNU General Public License v2
# This file is part of Checkmk (https://checkmk.com). It is subject to the terms and
# conditions defined in the file COPYING, which is part of this source code package.

import errno
import glob
import os
import subprocess
import six

import cmk.utils

import cmk.gui.config as config
from cmk.gui.globals import g
from cmk.gui.i18n import _
from cmk.gui.exceptions import MKGeneralException
from cmk.gui.log import logger


def add_message(message):
    _git_messages().append(message)


def _git_messages():
    """Initializes the request global data structure and returns it"""
    return g.setdefault("wato_git_messages", [])


def do_git_commit():
    author = "%s <%s>" % (config.user.id, config.user.email)
    git_dir = cmk.utils.paths.default_config_dir + "/.git"
    if not os.path.exists(git_dir):
        logger.debug("GIT: Initializing")
        _git_command(["init"])

        # Set git repo global user/mail. seems to be needed to prevent warning message
        # on at least ubuntu 15.04: "Please tell me who you are. Run git config ..."
        # The individual commits by users override the author on their own
        _git_command(["config", "user.email", "check_mk"])
        _git_command(["config", "user.name", "check_mk"])

        _write_gitignore_files()
        _git_add_files()
        _git_command([
            "commit", "--untracked-files=no", "--author", author, "-m",
            _("Initialized GIT for Check_MK")
        ])

    if _git_has_pending_changes():
        logger.debug("GIT: Found pending changes - Update gitignore file")
        _write_gitignore_files()

    # Writing the gitignore files might have reverted the change. So better re-check.
    if _git_has_pending_changes():
        logger.debug("GIT: Still has pending changes")
        _git_add_files()

        message = ", ".join(_git_messages())
        if not message:
            message = _("Unknown configuration change")

        _git_command(["commit", "--author", author, "-m", message])


def _git_add_files():
    path_pattern = os.path.join(cmk.utils.paths.default_config_dir, "*.d/wato")
    rel_paths = [
        os.path.relpath(p, cmk.utils.paths.default_config_dir) for p in glob.glob(path_pattern)
    ]
    _git_command(["add", "--all", ".gitignore"] + rel_paths)


def _git_command(args):
    command = ["git"] + [six.ensure_str(a) for a in args]
    logger.debug("GIT: Execute in %s: %s", cmk.utils.paths.default_config_dir,
                 subprocess.list2cmdline(command))
    try:
        p = subprocess.Popen(command,
                             cwd=cmk.utils.paths.default_config_dir,
                             stdout=subprocess.PIPE,
                             stderr=subprocess.STDOUT)
    except OSError as e:
        if e.errno == errno.ENOENT:
            raise MKGeneralException(
                _("Error executing GIT command <tt>%s</tt>:<br><br>%s") %
                (subprocess.list2cmdline(command), e))
        raise

    status = p.wait()
    if status != 0:
        out = u"" if p.stdout is None else six.ensure_text(p.stdout.read())
        raise MKGeneralException(
            _("Error executing GIT command <tt>%s</tt>:<br><br>%s") %
            (subprocess.list2cmdline(command), out.replace("\n", "<br>\n")))


def _git_has_pending_changes():
    try:
        p = subprocess.Popen(["git", "status", "--porcelain"],
                             cwd=cmk.utils.paths.default_config_dir,
                             stdout=subprocess.PIPE)
        return p.stdout is not None and p.stdout.read() != ""
    except OSError as e:
        if e.errno == errno.ENOENT:
            return False  # ignore missing git command
        raise


# TODO: Use cmk.store
def _write_gitignore_files():
    """Make sure that .gitignore-files are present and uptodate

    Only files below the "wato" directories should be under git control. The files in
    etc/check_mk/*.mk should not be put under control."""
    open(cmk.utils.paths.default_config_dir + "/.gitignore",
         "w").write("# This file is under control of Check_MK. Please don't modify it.\n"
                    "# Your changes will be overwritten.\n"
                    "\n"
                    "*\n"
                    "!*.d\n"
                    "!.gitignore\n"
                    "*swp\n"
                    "*.mk.new\n")

    for subdir in os.listdir(cmk.utils.paths.default_config_dir):
        if subdir.endswith(".d"):
            open(cmk.utils.paths.default_config_dir + "/" + subdir + "/.gitignore",
                 "w").write("*\n"
                            "!wato\n")

            if os.path.exists(cmk.utils.paths.default_config_dir + "/" + subdir + "/wato"):
                open(cmk.utils.paths.default_config_dir + "/" + subdir + "/wato/.gitignore",
                     "w").write("!*\n")
