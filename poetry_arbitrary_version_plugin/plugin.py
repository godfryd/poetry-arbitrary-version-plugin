import os

from cleo.helpers import option
from poetry.console.application import Application
from poetry.console.commands.build import BuildCommand
from poetry.plugins.application_plugin import ApplicationPlugin


def set_new_version(app, new_version, io):
    old_version = app.poetry.package.version.text
    app.poetry.package.version = new_version
    io.write_line("Overriden project version from %s to %s" % (old_version, new_version))


def my_build_handle(self):
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

    # run original build handle method
    self.handle_orig()


class ArbitraryVersionPlugin(ApplicationPlugin):
    def activate(self, application):
        # add new --override-version option to build command
        BuildCommand.options.append(option("override-version",
                                           description="Override project version defined in pyproject.toml with your arbitrary version.",
                                           flag=False))

        # hijack build handle method to capture new --override-version option
        # and if used then override project version
        BuildCommand.handle_orig = BuildCommand.handle
        BuildCommand.handle = my_build_handle
