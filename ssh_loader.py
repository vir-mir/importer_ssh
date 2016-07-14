import subprocess
import sys

import types


class SSHHooks:
    cache = {}

    def __init__(self, path):
        if path not in SSHHooks.cache:
            SSHHooks.cache[path] = None
            self.files = set()
            self._ssh, self._path = self._hooks(path)
            self._get_file()

    def _get_file(self):
        ssh = subprocess.Popen(
            ['ssh', self._ssh, 'ls %s' % self._path],
            shell=False,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE
        )

        self.files = set(x.decode().strip() for x in ssh.stdout.readlines())

    def _hooks(self, path):
        ssh, path = path.split(':')
        return ssh, path

    def find_module(self, fullname, path=None):
        if '%s.py' % fullname not in self.files:
            return None

        if not SSHHooks.cache['%s:%s' % (self._ssh, self._path)]:
            SSHHooks.cache['%s:%s' % (self._ssh, self._path)] = SSHLoader(self._ssh, self._path)

        return SSHHooks.cache['%s:%s' % (self._ssh, self._path)]


class SSHLoader:
    def __init__(self, _ssh, _path):
        self._ssh, self._path = _ssh, _path

    def get_source(self, fullname):
        ssh = subprocess.Popen(
            ['ssh', self._ssh, 'cat %s/%s.py' % (self._path, fullname)],
            shell=False,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE
        )

        return ssh.stdout.read()

    def __repr__(self):
        return '%s:%s' % (self._ssh, self._path)

    def load_module(self, fullname):
        source = self.get_source(fullname)
        context = {}
        mod = types.ModuleType(fullname)
        exec(source, context)
        mod.__dict__.update(context)
        sys.modules[fullname] = mod


sys.path_hooks.append(SSHHooks)


def add_path(pach):
    sys.path.append(pach)
