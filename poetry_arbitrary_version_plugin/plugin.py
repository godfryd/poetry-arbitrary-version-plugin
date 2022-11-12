import os
import re
import pathlib
import tempfile

from cleo.helpers import option
from poetry.console.application import Application
from poetry.console.commands.build import BuildCommand
from poetry.console.commands.publish import PublishCommand
from poetry.plugins.application_plugin import ApplicationPlugin

from poetry.core.masonry.builders.sdist import SdistBuilder
from poetry.core.masonry.builders.builder import BuildIncludeFile


MY_VERSION = None


def set_new_version(app, new_version, io):
    global MY_VERSION
    old_version = app.poetry.package.version.text
    app.poetry.package.version = new_version
    io.write_line("Overriden project version from %s to %s" % (old_version, new_version))
    MY_VERSION = new_version


def my_handle(self):
    # check if --override-version is used, if so then override project version
    new_version = self.option('override-version')
    if new_version:
        set_new_version(self.application, new_version, self.io)
    else:
        # if --override-version is not used
        # then check if PROJECT_OVERRIDE_VERSION environment variable is used
        # if so then override project version
        new_version = os.environ.get('PROJECT_OVERRIDE_VERSION', None)
        if new_version:
            set_new_version(self.application, new_version, self.io)

    # run original handle method
    self.handle_orig()


class MyBuildIncludeFile(BuildIncludeFile):
    def relative_to_source_root(self):
        return pathlib.Path('pyproject.tml')


def my_find_files_to_add(self, exclude_build=False):
    files = self.find_files_to_add_orig(exclude_build)
    files2 = []
    for f in files:
        if f.path.name == 'pyproject.toml':
            proj_txt = f.path.read_text()
            ver_line = 'version="%s"' % MY_VERSION
            proj_txt_patched = re.sub('^version.*=.*$', ver_line, proj_txt, flags=re.M)
            fp = tempfile.NamedTemporaryFile("w", delete=False)
            fp.write(proj_txt_patched)
            fp.flush()
            f = MyBuildIncludeFile(path=fp.name, project_root=self._path, source_root=self._path)
        files2.append(f)
    return files2


class ArbitraryVersionPlugin(ApplicationPlugin):
    def activate(self, application):
        for cmd_cls in [BuildCommand, PublishCommand]:
            # add new --override-version option to a command
            cmd_cls.options.append(option("override-version",
                                          description="Override project version defined in pyproject.toml with your arbitrary version.",
                                          flag=False))

            # hijack a handle method to capture new --override-version option
            # and if used then override project version
            cmd_cls.handle_orig = cmd_cls.handle
            cmd_cls.handle = my_handle

        SdistBuilder.find_files_to_add_orig = SdistBuilder.find_files_to_add
        SdistBuilder.find_files_to_add = my_find_files_to_add
