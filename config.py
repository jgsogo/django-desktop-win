
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
    p.communicate()

if __name__ == '__main__':
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

        with open('start_server.bat', 'w') as f:
            f.write('%s & %s %s runserver' % (env_bat, python_exe, manage_script))
    # Buil ISS script with all this data.
    # - substitute python version strings
    # - add django project to ISS (it may be in a different folder)

