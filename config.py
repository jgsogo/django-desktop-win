
import re
import os
import sys
import argparse
import subprocess
import glob

try:
    from urllib.request import urlopen
except ImportError:
    from urllib2 import urlopen

try:
    raw_input = input
except NameError:
    pass

def user_input(msg, choices=None, quit='Q'):
    data = None
    while not data:
        input = raw_input(msg + ': ')
        
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
    
def get_winpython_version(architecture, py_version, suffix='zero'):
    # Base name for winpython download
    arch = None
    if architecture == 'x64':
        arch = '64bit'
    elif architecture == 'x86':
        arch = '32bit'
    else:
        raise ValueError("Architecture '%s' not recognized" % architecture)
    
    # Search for full version
    base_name = 'winpython-' + arch + '-' + py_version + '.(\d).(\d)' + suffix + '.exe'
    #r = open('./deploy/winpython.txt', 'r')
    r = urlopen('http://winpython.github.io/md5_sha1.txt').readlines()
    for line in r:
        m = re.search(base_name, str(line))
        if m:
            break
    if not m:
        sys.stderr.write("Winpython for architecture='%s' and python version='%s' not found. Query was '%s'.\n" % (architecture, py_version, base_name))
        
    # Go for file
    sys.stdout.write("WinPython found: %s\n" % m.group(0))
    base_name_url = 'WinPython-' + arch + '-' + py_version + '.' + m.group(1) + '.' + m.group(2) + suffix.capitalize() + '.exe'
    base_url = 'http://downloads.sourceforge.net/project/winpython/WinPython_' + py_version + '/' + py_version + '.' + m.group(1) + '.' + m.group(2) + '/' + base_name_url
    filename = os.path.join(os.path.dirname(__file__), m.group(0))
    download(base_url, filename)
    
    # Install
    sys.stdout.write("Installin WinPython, this can take a little...\n")
    sys.stdout.flush()
    #p = subprocess.Popen([filename, '/S'])

    #p.communicate()  # Wait subprocess (install winpython) to finish
    
    # Return path to python.exe and pip.exe
    dirname = os.path.abspath(os.path.join('.', base_name_url.rsplit('.',1)[0]))
    python_exe = find_file('python.exe', dirname)[0]
    pip_exe = find_file('pip.exe', dirname)[0]
    env_bat = find_file('env.bat', dirname)[0]
    return python_exe, pip_exe, env_bat
        

def inspect_django_dir(dir):
    # Look for 'manage.py' and 'requirements.py'
    manage_script = find_file('manage.py', dir)
    requirements_file = find_file('requirements.txt', dir)
    if len(manage_script) != 1 or len(requirements_file) > 1:
        raise ValueError('django_dir must point to just one single project')
    req = requirements_file[0] if len(requirements_file) > 0 else None
    return manage_script[0], req
        
def run_env_command(command, env_bat):
    if isinstance(command, list):
        command = ' '.join(command)
    full_cmd = env_bat + '& ' + command
    p = subprocess.Popen(full_cmd, stdout=sys.stdout, shell=True)
    return p.communicate()

if __name__ == '__main__-':
    parser = argparse.ArgumentParser(description='Configure django-desktop-win.')
    parser.add_argument('mode', metavar='mode', type=str, nargs=1, help='working mode: develop')
    parser.add_argument('--python', nargs='?', help='python version to work with: 2.7, 3.4,...')
    parser.add_argument('--arch', nargs='?', choices=['x64', 'x86'], help='target architecture (Win32)')
    parser.add_argument('--django_dir', nargs='?', help='Path to a self contained Django project')
    
    # Get needed data
    args = parser.parse_args()    
    mode = args.mode[0]
    
    sys.stdout.write("Configure django-desktop-win\n")
    sys.stdout.write(" - running mode '%s'\n" % mode)
    
    architecture = args.arch or user_input(">> target architecture (Win32) [x64|x86]", choices=['x64', 'x86'])
    sys.stdout.write(" - architecture '%s'\n" % architecture)

    py_version = args.python or user_input(">> python version to work with [2.7|3.5|...]")
    sys.stdout.write(" - python version '%s'\n" % py_version)

    # Install winpython
    python_exe, pip_exe, env_bat = get_winpython_version(architecture, py_version)
    
    # Inspect django project directory
    django_dir = os.path.abspath(args.django_dir)
    if not os.path.isabs(django_dir):
        print("*"*20)
        django_dir = os.path.join(os.paht.dirname(__file__), django_dir)
        
    if django_dir:
        sys.stdout.write(" - install for django at: %s\n" % args.django_dir)
        manage_script, requirements_file = inspect_django_dir(args.django_dir)
    
        # Install requirements for django projects
        if requirements_file:
            sys.stdout.write(" - installing requirements.\n")
            sys.stdout.flush()
            run_env_command([pip_exe, 'install', '-r', requirements_file], env_bat)

        # Create run_server batch script
        with open('start_server.bat', 'w') as f:
            f.write('%s & %s %s runserver' % (env_bat, python_exe, manage_script))
            
        # Check it works
        
    # Buil ISS script with all this data.
    with open('defines.iss', 'w') as f:       
        # Application name
        name = 'MyAppName'
        f.write('#define MyAppName "%s"\n' % name)
        
        # WinPython stuff
        f.write('#define PythonVersion "%s"\n' % py_version)
        f.write('#define WinPythonArchitecture "%s"\n' % architecture)
        f.write('#define WinPythonFullName "#WinPythonFullName"\n')
        f.write('#define WinPythonDownload "#WinPythonDownload"\n')
        
        # Django stuff
        f.write('#define DjangoDir "%s"\n' % django_dir)
        

class WinPythonConfig():
    ARCH_CHOICES = ['x64', 'x86']
    MD5_SHA1_FILE = 'http://winpython.github.io/md5_sha1.txt'
    DOWNLOAD_URL = 'http://downloads.sourceforge.net/project/winpython/WinPython_{python_version}/{winpython_version}/{basename}.exe'

    regex_name = 'WinPython-{architecture}-{python_version}.(\d).(\d)Zero'
    
    python_version = None
    architecture = None
    
    def __init__(self, parsed_args, interactive=True):
        self.interactive = True
        self.get_python_version(parsed_args)
        self.get_architecture(parsed_args)
        
        self.python_exe = None
        self.pip_exe = None
        self.env_bat = None

        
    def get_python_version(self, parsed_args):
        if parsed_args.python:
            self.python_version = parsed_args.python
        elif not self.python_version and self.interactive:
            self.python_version = user_input("   >> python version to work with [2.7|3.5|...]")
        else:
            raise ValueError("Use '--python' argument to provide a python version.")
        
        # Validation
        if not re.match(r'\d.\d', self.python_version):
            raise ValueError("Python version not well formed: '%s'" % self.python_version)
            
        print(" - python version: %s" % self.python_version)
    
    def get_architecture(self, parsed_args):
        if parsed_args.arch:
            self.architecture = parsed_args.arch
        elif not self.architecture and self.interactive:
            self.architecture = user_input("   >> target architecture (Win32) %s" % self.ARCH_CHOICES, choices=self.ARCH_CHOICES)
        else:
            raise ValueError("Use '--arch' argument to provide a architecture.")
            
        # Validation
        if not self.architecture in self.ARCH_CHOICES:
            raise ValueError("Invalid architecture type. Valid types are %s" % self.ARCH_CHOICES)
            
        print(" - architecture: %s" % self.architecture)
    
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
    
    def install(self, filename, async=True):
        print("Installing WinPython, this can take a little...")
        install_process = subprocess.Popen([filename, '/S'])
        
        def do_install():
            print("Finishing WinPython installation")
            install_process.communicate()
            
            # Look for python.exe and pip.exe
            dirname = os.path.abspath(filename.rsplit('.',1)[0])
            self.python_exe = find_file('python.exe', dirname)[0]
            self.pip_exe = find_file('pip.exe', dirname)[0]
            self.env_bat = find_file('env.bat', dirname)[0]
            print(" - python.exe: %s" % self.python_exe)
            print(" - pip.exe   : %s" % self.pip_exe)
            print(" - env.bat   : %s" % self.env_bat)
            
        if async:
            self._on_cleanup.append(do_install)
        else:
            do_install()
            
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
    
    def __init__(self, parsed_args, interactive=True):
        self.interactive = interactive
        self.get_django_dir(parsed_args)

    def get_django_dir(self, parsed_args):
        if parsed_args.django_dir:
            self.django_dir = parsed_args.django_dir
        elif not self.django_dir and self.interactive:
            self.django_dir = user_input("   >> django directory")
        else:
            raise ValueError("Use '--django_dir' argument to inform about Django project")
        
        if not os.path.exists(self.django_dir):
            raise ValueError("Provided Django directory (%s) does not exist or it is inaccesible" % self.django_dir)
        
        print(" - django_dir: %s" % self.django_dir)
        
    def install(self):
        print("Installing Django project and requirements, this can take a little...")
        
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
    iss_defines = {}
    
    def parse_args(self):
        parser = argparse.ArgumentParser(description='Configure django-desktop-win.')
        parser.add_argument('mode', metavar='mode', type=str, nargs='?', default='develop', help='working mode')
        parser.add_argument('--python', nargs='?', help='python version to work with: 2.7, 3.4,...')
        parser.add_argument('--arch', nargs='?', choices=['x64', 'x86'], help='target architecture (Win32)')
        parser.add_argument('--django_dir', nargs='?', help='Path to a self contained Django project')
        args = parser.parse_args()
        # Run in desired mode
        self.mode = args.mode
        return args
        
    def develop(self, args):
        base_path = os.path.dirname(__file__)
        
        # WinPython
        print("Gathering input data for WinPython")
        winpython = WinPythonConfig(parsed_args=args)
        filename = winpython.download_to(base_path)
        winpython.install(filename, async=False)
        
        # Django
        print("\nGathering input data for Django project")
        django = DjangoConfig(parsed_args=args)
        django.install()
        
        if django.requirements_file:
            print("Installing requirements")
            winpython.run_python([winpython.pip_exe, 'install', '-r', django.requirements_file, '--upgrade'], async=False)
            
        # Create stuff
        # - start_server.bat
        with open(os.path.join(base_path, 'start_server.bat'), 'w') as f:
            f.write('%s & %s %s runserver' % (winpython.env_bat, winpython.python_exe, django.manage_script))
        # - defines.iss
        with open(os.path.join(base_path, 'defines.iss'), 'w') as f:
            f.write('#define MyAppName "%s"\n' % "MyAppName")
            f.write('#define DjangoDir "%s"\n' % django.django_dir)
            f.write('#define PythonVersion "%s"\n' % winpython.python_version)
            f.write('#define WinPythonArchitecture "%s"\n' % winpython.architecture)
            f.write('#define WinPythonBasename "%s"\n' % winpython.basename)
            f.write('#define WinPythonDownload "%s"\n' % winpython.download_url)
        
    def run(self, *args, **kwargs):
        args = self.parse_args()

        if self.mode == 'develop':
            self.develop(args)
        else:
            raise ValueError("Unrecognized mode '%s'" % args.mode)

        
if __name__ == '__main__':
    script = ConfigScript()
    script.run()
