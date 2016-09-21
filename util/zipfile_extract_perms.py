"""
NSAptr - a Non-Sketchy Android Platform Tools Retriever
Extend built-in zipfile.ZipFile to include permissions extraction functionality
Implements part of the functionality described at:
  https://bugs.python.org/issue15795
  https://bugs.python.org/file34873/issue15795_cleaned.patch

Some of the code was copied verbatim from the application of the patch to Python 3.5.1's 'lib/zipfile.py'
It is assumed that the patch and original code are distributed under the Python Software Foundation License (Version 2)
Please see "LICENSE_PSFv2" for the applicable license text.
For that code, the following applies:

   Copyright (c) 2001, 2002, 2003, 2004 Python Software Foundation; All Rights Reserved

For original code contained in this file, the following applies:

   Copyright 2016 adpoliak

      Licensed under the Apache License, Version 2.0 (the "License");
      you may not use this file except in compliance with the License.
      You may obtain a copy of the License at

          http://www.apache.org/licenses/LICENSE-2.0

      Unless required by applicable law or agreed to in writing, software
      distributed under the License is distributed on an "AS IS" BASIS,
      WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
      See the License for the specific language governing permissions and
      limitations under the License.
"""
import os
import shutil
from zipfile import *

# Enum choices for ZipFileMod.extractall preserve_permissions argument
PERMS_PRESERVE_NONE, PERMS_PRESERVE_SAFE, PERMS_PRESERVE_ALL = range(3)


class ZipFileMod(ZipFile):
    def __init__(self, *args, **kwargs):
        ZipFile.__init__(self, *args, **kwargs)

    def _RealGetContents(self):
        return super()._RealGetContents()

    def _extract_member(self, member, targetpath, pwd, preserve_permissions=PERMS_PRESERVE_NONE):
        """Extract the ZipInfo object 'member' to a physical
           file on the path targetpath.
        """
        # build the destination pathname, replacing
        # forward slashes to platform specific separators.
        arcname = member.filename.replace('/', os.path.sep)

        if os.path.altsep:
            arcname = arcname.replace(os.path.altsep, os.path.sep)
        # interpret absolute pathname as relative, remove drive letter or
        # UNC path, redundant separators, "." and ".." components.
        arcname = os.path.splitdrive(arcname)[1]
        invalid_path_parts = ('', os.path.curdir, os.path.pardir)
        arcname = os.path.sep.join(x for x in arcname.split(os.path.sep)
                                   if x not in invalid_path_parts)
        if os.path.sep == '\\':
            # filter illegal characters on Windows
            arcname = self._sanitize_windows_name(arcname, os.path.sep)

        targetpath = os.path.join(targetpath, arcname)
        targetpath = os.path.normpath(targetpath)

        # Create all upper directories if necessary.
        upperdirs = os.path.dirname(targetpath)
        if upperdirs and not os.path.exists(upperdirs):
            os.makedirs(upperdirs)

        if member.filename[-1] == '/':
            if not os.path.isdir(targetpath):
                os.mkdir(targetpath)
            return targetpath

        with self.open(member, pwd=pwd) as source, \
                open(targetpath, "wb") as target:
            shutil.copyfileobj(source, target)

        if preserve_permissions in [PERMS_PRESERVE_SAFE, PERMS_PRESERVE_ALL]:
            bitmask = 0x1FF if preserve_permissions == PERMS_PRESERVE_SAFE else 0xFFF
            mode = member.external_attr >> 16 & bitmask
            os.chmod(targetpath, mode)

        return targetpath

    def extract(self, member, path=None, pwd=None,
                preserve_permissions=PERMS_PRESERVE_NONE):
        """Extract a member from the archive to the current working directory,
           using its full name. Its file information is extracted as accurately
           as possible. `member' may be a filename or a ZipInfo object. You can
           specify a different directory using `path'.
        """
        if not isinstance(member, ZipInfo):
            member = self.getinfo(member)

        if path is None:
            path = os.getcwd()

        return self._extract_member(member, path, pwd, preserve_permissions)

    def extractall(self, path=None, members=None, pwd=None,
                   preserve_permissions=PERMS_PRESERVE_NONE):
        """Extract all members from the archive to the current working
           directory. `path' specifies a different directory to extract to.
           `members' is optional and must be a subset of the list returned by
           namelist(). `preserve_permissions` controls whether permissions of
           zipped files are preserved or not. Default is PERMS_PRESERVE_NONE -
           do not preserve any permissions. Other options are to preserve safe
           subset of permissions PERMS_PRESERVE_SAFE or all permissions
           PERMS_PRESERVE_ALL.
        """
        if members is None:
            members = self.namelist()

        for zipinfo in members:
            self.extract(zipinfo, path, pwd, preserve_permissions)
