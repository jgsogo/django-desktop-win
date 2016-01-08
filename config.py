
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
    DOWNLOAD_URL = 'http://downloads.sourceforge.net/project/winpython/WinPython_%(python_version)s/%(python_version)s.%{winpython_minor}.%{winpython_build}/%(basename)s.exe'

    regex_name = 'WinPython-{architecture}-{python_version}.(\d).(\d)Zero'
    
    python_version = None
    architecture = None
    
    def __init__(self, parsed_args, interactive=True):
        self.interactive = True
        self.get_python_version(parsed_args)
        self.get_architecture(parsed_args)
        
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
        
            m = [re.search(pattern, str(line), re.IGNORECASE) for line in urlopen(MD5_SHA1_FILE).readlines()]
            if not len(m):
                raise ValueError("Cannot find a WinPython version for architecture '%s' and Python '%s'" % (self.architecture, self.python_version))
            if len(m) > 1:
                raise ValueError("More than one WinPython matches requested version: '%s'" % "', '".join([it.group(0) for it in m]))
            
            setattr(self, '_basename', m[0].group(0))
            setattr(self, '_winpython_version', "%d.%d" % (m[0].group(1), m[0].group(2)))
        return getattr(self, '_basename')
            
    @property
    def winpython_version(self):
        basename = self.basename  # Just to get the values
        return getattr(self, '_winpython_version')
        
            
    def download_to(self, filename):
        DOWNLOAD_URL = 'http://downloads.sourceforge.net/project/winpython/WinPython_{python_version}/{winpython_version}/{basename}.exe'
        url = DOWNLOAD_URL.format(python_version=self.python_version, 
                                  winpython_version=self.winpython_version,
                                  winpython_build='1',
                                  basename=self.basename)
        print(url)
        
""""        
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
"""
        
class ConfigScript():
    iss_defines = {}
    
    def parse_args(self):
        parser = argparse.ArgumentParser(description='Configure django-desktop-win.')
        parser.add_argument('mode', metavar='mode', type=str, nargs='?', default='develop', help='working mode')
        parser.add_argument('--python', nargs='?', help='python version to work with: 2.7, 3.4,...')
        parser.add_argument('--arch', nargs='?', choices=['x64', 'x86'], help='target architecture (Win32)')
        parser.add_argument('--django_dir', nargs='?', help='Path to a self contained Django project')
        args = parser.parse_args()
        
        # WinPython
        winpython = WinPythonConfig(parsed_args=args)
        winpython.download_to('here')
        
        # Run in desired mode
        self.mode = args.mode
        
        """
        # Install winpython
        python_exe, pip_exe, env_bat = get_winpython_version(architecture, py_version)
        """
        
    
    def develop(self):
        print("Entering DEVELOP mode")
    
    def run(self, *args, **kwargs):
        print("Gather input data")
        self.parse_args()

        print("Run in %s mode" % self.mode.upper())
        if self.mode == 'develop':
            self.develop()
        else:
            raise ValueError("Unrecognized mode '%s'" % args.mode)

        
if __name__ == '__main__':
    script = ConfigScript()
    script.run()
