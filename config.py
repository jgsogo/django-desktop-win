
import re
import os
import sys
import argparse
import urllib2


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
    u = urllib2.urlopen(url)
    f = open(file_name, 'wb')
    meta = u.info()
    file_size = int(meta.getheaders("Content-Length")[0])
    sys.stdout.write("Downloading: %s Bytes: %s\n" % (file_name, file_size))
    
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
    r = open('./deploy/winpython.txt', 'r')
    #r = urllib2.urlopen('http://winpython.github.io/md5_sha1.txt')
    for line in r:
        m = re.search(base_name, line)
        if m:
            break
    if not m:
        sys.stderr.write("Winpython for architecture='%s' and python version='%s' not found. Query was '%s'.\n" % (architecture, py_version, base_name))
        
    # Go for file
    sys.stdout.write("WinPython found: %s\n" % m.group(0))
    base_url = 'http://sourceforge.net/projects/winpython/files/WinPython_' + py_version + '/' + py_version + '.' + m.group(1) + '.' + m.group(2) + '/' + m.group(0) + '/download'
    filename = os.path.join(os.path.realpath(__file__), 'tmp', base_name)
    download(base_url, filename)
    
    # Install
    # TODO: exec installer    
        

if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='Configure django-desktop-win.')
    parser.add_argument('mode', metavar='mode', type=str, nargs=1, help='working mode: develop')
    parser.add_argument('--python', nargs='?', help='python version to work with: 2.7, 3.4,...')
    parser.add_argument('--arch', nargs='?', choices=['x64', 'x86'], help='target architecture (Win32)')
    
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
    get_winpython_version(architecture, py_version)
    
    # Install requirements for django projects
    
    # Buil ISS script with all this data.
    # - substitute python version strings
    # - add django project to ISS (it may be in a different folder)

