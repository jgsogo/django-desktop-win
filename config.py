
from __future__ import unicode_literals

import re
import os
import sys
import argparse
import subprocess
import glob
import shutil

from slugify import slugify

# Python 2 vs 3 conditional imports and auxiliary functions
try:
    from urllib.request import urlopen
except ImportError:
    from urllib2 import urlopen

if sys.version_info < (3,):
    import codecs
    def u(x):
        return codecs.unicode_escape_decode(x)[0]
else:
    raw_input = input
    def u(x):
        return x


# Actual code
    
BASE_DIR = os.path.abspath(os.path.dirname(__file__))
    
# Just reimplement waitress.serve function to flush sys.stdout
waitress_server = """
import sys

sys.path.append(r"{manage_path}")

from waitress.server import create_server
import logging

def waitress_serve(app, **kw):
    _server = kw.pop('_server', create_server) # test shim
    _quiet = kw.pop('_quiet', False) # test shim
    _profile = kw.pop('_profile', False) # test shim
    if not _quiet: # pragma: no cover
        # idempotent if logging has already been set up
        logging.basicConfig()
    server = _server(app, **kw)
    if not _quiet: # pragma: no cover
        sys.stdout.write('serving on http://%s:%s\\n' % (server.effective_host,
                                                         server.effective_port))
        sys.stdout.flush()
    if _profile: # pragma: no cover
        profile('server.run()', globals(), locals(), (), False)
    else:
        server.run()
        
from {wsgi_dir}.wsgi import application
waitress_serve(application, host='127.0.0.1', port=0)

"""
    
    
def user_input(msg, default=None, choices=None, quit='Q'):
    data = None
    while not data:
        if default:
            msg = msg + ' [%s]' % default
        r = raw_input(msg + ': ')
        input = u(r.replace('\\', '/'))
        if not len(input):
            input = default
        
        if input == quit:
            return None

        if choices and (not any([it==input for it in choices])):
            sys.stdout.write("Invalid value '%s', valid choices are '%s'. (enter '%s' to quit)\n" % (input, "', '".join(choices), quit))
        else:
            data = input
            
    return data

    
def download(url, filename):
    u = urlopen(url)
    meta = u.info()
    try:
        file_size = int(meta.get("Content-Length"))
    except AttributeError:
        file_size = int(meta.getheaders("Content-Length")[0])
    sys.stdout.write("Downloading: %s Bytes: %s\n" % (filename, file_size))

    if os.path.exists(filename):
        # TODO: Check size!
        return
    
    # Start download
    f = open(filename, 'wb')
    file_size_dl = 0
    block_sz = 8192
    while True:
        buffer = u.read(block_sz)
        if not buffer:
            break

        file_size_dl += len(buffer)
        f.write(buffer)
        status = r"%10d  [%3.2f%%]" % (file_size_dl, file_size_dl * 100. / file_size)
        status = status + chr(8)*(len(status)+1)
        sys.stdout.write(status)

    f.close()
    
    
def find_file(lookup, basedir):
    ret = []
    for root, dirnames, filenames in os.walk(basedir):
        for filename in filenames:
            if filename == lookup:
                ret.append(os.path.abspath(os.path.join(root, filename)))
    return ret
            

class WinPythonConfig():
    ARCH_CHOICES = ['x64', 'x86']
    MD5_SHA1_FILE = 'http://winpython.github.io/md5_sha1.txt'
    DOWNLOAD_URL = 'http://downloads.sourceforge.net/project/winpython/WinPython_{python_version}/{winpython_version}/{basename}.exe'

    regex_name = 'WinPython-{architecture}-{python_version}.(\d).(\d)Zero'
    
    python_version = None
    architecture = None
    
    def __init__(self, python, arch, interactive=True):
        self.interactive = True
        self.get_python_version(python)
        self.get_architecture(arch)
        
        self.python_exe = None
        self.pip_exe = None
        self.env_bat = None

        
    def get_python_version(self, python):
        if python:
            self.python_version = python
        elif not self.python_version and self.interactive:
            self.python_version = user_input("   >> python version to work with [2.7|3.5|...]")
        else:
            raise ValueError("Use '--python' argument to provide a python version.")
        
        # Validation
        if not re.match(r'\d.\d', self.python_version):
            raise ValueError("Python version not well formed: '%s'" % self.python_version)
            
        print(" - python version: %s" % self.python_version)
        return self.python_version
    
    def get_architecture(self, arch):
        if arch:
            self.architecture = arch
        elif not self.architecture and self.interactive:
            self.architecture = user_input("   >> target architecture (Win32) %s" % self.ARCH_CHOICES, choices=self.ARCH_CHOICES)
        else:
            raise ValueError("Use '--arch' argument to provide a architecture.")
            
        # Validation
        if not self.architecture in self.ARCH_CHOICES:
            raise ValueError("Invalid architecture type. Valid types are %s" % self.ARCH_CHOICES)
            
        print(" - architecture: %s" % self.architecture)
        return self.architecture
    
    @property
    def basename(self):
        if not hasattr(self, '_basename'):
            if self.architecture == 'x64':
                arch = '64bit'
            elif self.architecture == 'x86':
                arch = '32bit'
            else:
                raise ValueError("Architecture '%s' not recognized" % architecture)
            pattern = self.regex_name.format(architecture=arch, python_version=self.python_version)
            
            m = [re.search(pattern, str(line), re.IGNORECASE) for line in urlopen(self.MD5_SHA1_FILE).readlines()]
            m = [x for x in m if x is not None]
            if not len(m):
                raise ValueError("Cannot find a WinPython version for architecture '%s' and Python '%s'" % (self.architecture, self.python_version))
            if len(m) > 1:
                raise ValueError("More than one WinPython matches requested version: '%s'" % "', '".join([it.group(0) for it in m]))

            # Keep cases
            basename = self.regex_name.format(architecture=arch, python_version=self.python_version)
            basename = basename.replace('(\d)', m[0].group(1), 1)
            basename = basename.replace('(\d)', m[0].group(2), 1)
            setattr(self, '_basename', basename)
            setattr(self, '_winpython_version', "%s.%s.%s" % (self.python_version, m[0].group(1), m[0].group(2)))
        return getattr(self, '_basename')
            
    @property
    def winpython_version(self):
        basename = self.basename  # Just to get the values
        return getattr(self, '_winpython_version')
        
    @property
    def download_url(self):
        return self.DOWNLOAD_URL.format(python_version=self.python_version, 
                                        winpython_version=self.winpython_version,
                                        basename=self.basename)
            
    def download_to(self, path):
        filename = os.path.join(path, self.basename + '.exe')
        download(self.download_url, filename)        
        return filename
                
    _on_cleanup = []
    
    def install(self, filename, target_dir, async=True):
        print("Installing WinPython, this can take a little...")
        target_filename = os.path.join(target_dir, os.path.basename(filename))
        dirname = os.path.dirname(target_filename)
        
        if not self.find_exes(dirname):
            shutil.copy2(filename, target_filename)
            install_process = subprocess.Popen([target_filename, '/S'])
            
            def do_install():
                print("Finishing WinPython installation")
                install_process.communicate()
                
                # Look for python.exe and pip.exe
                self.find_exes(dirname)

                os.remove(target_filename)
                
            if async:
                self._on_cleanup.append(do_install)
            else:
                do_install()
    
    def find_exes(self, dirname):
        try:
            # Look for python.exe and pip.exe
            self.python_exe = find_file('python.exe', dirname)[0]
            self.pip_exe = find_file('pip.exe', dirname)[0]
            self.env_bat = find_file('env.bat', dirname)[0]
            print(" - python.exe: %s" % self.python_exe)
            print(" - pip.exe   : %s" % self.pip_exe)
            print(" - env.bat   : %s" % self.env_bat)
            return True
        except IndexError:
            return False        
    
    def run_python(self, command, stdout=sys.stdout, async=True):
        if isinstance(command, list):
            command = ' '.join(command)
        full_cmd = self.env_bat + '& ' + command
        p = subprocess.Popen(full_cmd, stdout=stdout, shell=True)
        if async:
            self._on_cleanup.append(p.communicate)
        else:
            p.communicate()

    def __del__(self):
        for clean_action in self._on_cleanup:
            clean_action()


class DjangoConfig():
    django_dir = None
    home = None
        
    def __init__(self, django_dir, home, interactive=True):
        self.interactive = interactive
        self.get_django_dir(django_dir)
        self.get_home_url(home)

    def get_django_dir(self, django_dir):
        if django_dir:
            self.django_dir = django_dir
        elif not self.django_dir and self.interactive:
            self.django_dir = user_input("   >> django directory")
        else:
            raise ValueError("Use '--django_dir' argument to inform about Django project")
        
        if not os.path.exists(self.django_dir):
            raise ValueError("Provided Django directory (%s) does not exist or it is inaccesible" % self.django_dir)
        
        print(" - django_dir: %s" % self.django_dir)
        return self.django_dir
        
    def get_home_url(self, home):
        if not home:
            home = user_input("   >> Home URL for application", default='/')
            home = home.replace('\\', '/')
            if not home.startswith("/"):
                home = '/' + home
        self.home = home
        return self.home
        
    def install(self):
        print("Looking for Django project files: manage.py and requirements...")
        
        # Look for 'manage.py' and 'requirements.py'
        manage_script = find_file('manage.py', self.django_dir)
        requirements_file = find_file('requirements.txt', self.django_dir)
        if len(manage_script) != 1 or len(requirements_file) > 1:
            raise ValueError('django_dir must point to just one single project')
        self.requirements_file = requirements_file[0] if len(requirements_file) > 0 else None
        self.manage_script = manage_script[0]        
        print(" - manage.py       : %s" % self.manage_script)
        print(" - requirements.txt: %s" % self.requirements_file)
        
        
class ConfigScript():
    app_id = None
    cfg_filename = None
    
    def _get_cfg_filename(self, args):
        filenames = []
        if args['config_ini'] is not None:
            filename, file_extension = os.path.splitext(args['config_ini'])
            if file_extension:
                return [os.path.abspath(args['config_ini'])]
            return os.path.join(BASE_DIR, args['config_ini'], 'config.ini')
        
        return None
    
    def parse_args(self):
        parser = argparse.ArgumentParser(description='Configure django-desktop-win.')
        parser.add_argument('config_ini', nargs='?', help='configuration file')
        parser.add_argument('--python', nargs='?', help='python version to work with: 2.7, 3.4,...')
        parser.add_argument('--arch', nargs='?', choices=['x64', 'x86'], help='target architecture (Win32)')
        parser.add_argument('--django_dir', nargs='?', help='Path to a self contained Django project')
        args = vars(parser.parse_args())

        # Read data from config file
        self.cfg_filename = self._get_cfg_filename(args)
        if self.cfg_filename:
            args = self.read_ini(args)
            self.app_id = slugify(args['appName'])
        else:
            name_default = None
            if args['django_dir'] is not None:
                name_default = os.path.basename(args['django_dir'])
            args['appName'] = user_input("   >> Application Name", default=name_default)
            self.app_id = slugify(args['appName'])
            dirpath = os.path.join(BASE_DIR, self.app_id)
            if not os.path.exists(dirpath):
                os.makedirs(dirpath)
            self.cfg_filename = os.path.join(dirpath, 'config.ini')
                
        return args
        
    def save_ini(self, args):
        with open(self.cfg_filename, 'w') as f:
            for key, value in args.items():
                if value is not None:
                    f.write('%s=%s\n' % (key, value))
        
    def read_ini(self, args):
        with open(self.cfg_filename, 'r') as f:
            for line in f.readlines():
                if len(line.strip()):
                    item = line.split('=')
                    if item[0] not in args or args[item[0]] is None:
                        args[item[0]] = item[1].strip()
        return args
        
    def run(self, *args, **kwargs):
        args = self.parse_args()
                    
        # WinPython
        print("Gathering input data for WinPython")
        winpython = WinPythonConfig(args['python'], args['arch'])
        args['python'] = winpython.python_version
        args['arch'] = winpython.architecture
        
        # Django
        print("\nGathering input data for Django project")
        django = DjangoConfig(args['django_dir'], home=args.get('home', None))
        django.install()
        args['django_dir'] = django.django_dir

        # Create stuff
        # - config.ini: store configuration
        self.save_ini(args)

        # Perform actions
        app_dir = os.path.dirname(self.cfg_filename)

        filename = winpython.download_to(BASE_DIR)
        winpython.install(filename, app_dir, async=False)
        
        if django.requirements_file:
            print("Installing requirements")
            winpython.run_python([winpython.pip_exe, 'install', '-r', django.requirements_file, '--upgrade'], async=False)
            winpython.run_python([winpython.pip_exe, 'install', 'waitress', '--upgrade'], async=False)
            
                    
        # - run.py: file to run django using waitress (local)
        run_py = os.path.abspath(os.path.join(app_dir, 'run.py'))
        with open(run_py, 'w') as f:
            wsgi = find_file('wsgi.py', django.django_dir)[0]
            wsgi_paths = os.path.split(os.path.dirname(wsgi))
            f.write(waitress_server.format(manage_path=os.path.dirname(django.manage_script), wsgi_dir=wsgi_paths[-1]))
        
        # - run.py: file to run django using waitress (deploy)
        #with open(os.path.abspath(os.path.join(BASE_DIR, 'deploy', 'run.py')), 'w') as f:
        #    wsgi = find_file('wsgi.py', django.django_dir)[0]
        #    wsgi_paths = os.path.split(os.path.dirname(wsgi))
        #    f.write(waitress_server.format(manage_path='', wsgi_dir=wsgi_paths[-1]))
        
        # - requirements.txt: 
        with open(os.path.join(app_dir, 'requirements.txt'), 'w') as f:
            waitress = False
            for line in open(django.requirements_file, 'r').readlines():
                waitress = waitress or 'waitress' in line
                f.write(line)
            if not waitress:
                f.write('waitress')
        
        # - start.bat: start CEF, for local development (local)
        deploy_dir = os.path.abspath(os.path.join(BASE_DIR, 'deploy', 'bin64' if args['arch'] == 'x64' else 'bin32'))
        with open(os.path.join(app_dir, 'start.bat'), 'w') as f:
            cef_exe = find_file('cefsimple.exe', deploy_dir)
            if not len(cef_exe):
                print("cefsimple.exe not found at '%s'. You have to compile CEF and call config again." % deploy_dir)
            else:
                f.write('"%s" --python="%s" --manage="%s" --url=%s' % (cef_exe[0], winpython.python_exe, run_py, django.home))
        
        """        
        # - defines.iss
        with open(os.path.join(BASE_DIR, 'defines.iss'), 'w') as f:
            f.write('#define MyAppName "%s"\n' % args['appName'])
            f.write('#define Architecture "%s"\n' % args['arch'])
            f.write('#define DeployDir "%s"\n' % deploy_dir)
            f.write('#define Home "%s"\n' % args['home'])
            
            f.write('#define DjangoDir "%s"\n' % django.django_dir)
            f.write('#define PythonVersion "%s"\n' % winpython.python_version)
            f.write('#define WinPythonArchitecture "%s"\n' % winpython.architecture)
            f.write('#define WinPythonBasename "%s"\n' % winpython.basename)
            f.write('#define WinPythonDownload "%s"\n' % winpython.download_url)
            
            f.write('#define WinPythonRelPath "%s"\n' % os.path.relpath(os.path.dirname(winpython.python_exe), BASE_DIR))
            f.write('#define WinPythonRelExe "%s"\n' % os.path.relpath(winpython.python_exe, BASE_DIR))
            f.write('#define WinPythonPipRelPath "%s"\n' % os.path.relpath(winpython.pip_exe, BASE_DIR))
            f.write('#define WinPythonEnvRelPath "%s"\n' % os.path.relpath(winpython.env_bat, BASE_DIR))
            
            f.write('#define ManagePyPath "%s"\n' % os.path.relpath(django.manage_script, django.django_dir))
            f.write('#define ManagePyRelPath "%s"\n' % os.path.relpath(os.path.dirname(django.manage_script), django.django_dir))
        """

        
if __name__ == '__main__':
    script = ConfigScript()
    script.run()
