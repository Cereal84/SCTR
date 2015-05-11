"""
This file contains utils
"""

__author__ = "Alessandro Pischedda"
__email__ = "alessandro.pischedda@gmail.com"


import sys
import os

def check_filename(filename):
    """Check if the input file exist and it is a valid file"""

    if not os.path.exists(filename):
        print str(filename)+" not exists."
        sys.exit(-1)

def check_output(filename):

    # TODO check if the name has .html as extension, if not add it 
    # and then check if exists 
    if os.path.exists(filename):
        print str(filename)+" already exists."
        response = raw_input('Do you want to overwrite it?[Y/n]: ')
        if response != 'Y' and response != '':  
            sys.exit(-1)


def get_files_dirs( path ):
    """From the path get the list of files and dirs"""
    files = []
    dirs = []

    list_new = os.path.join(os.listdir(path))

    # retrieve all the directories and files on 
    # the current path
    for f in os.listdir(path):
        filename_complete = os.path.join(path, f)
        if os.path.isfile(filename_complete):
            files.append(filename_complete)
        elif os.path.isdir(filename_complete):
            dirs.append(filename_complete)

    return files, dirs


def handle_dir(directory, recursive, comments):
    
    files, dirs = get_files_dirs(directory)

    # parse every file 
    for f in files:
        parse_file(f, comments)

    #recall yourself for each subdirectory if recursive is True
    if recursive:
        for directory in dirs:
            handle_dir(directory, recursive, comments)


def determine_path():
    """Try to get the root path"""

    try:
        root = __file__
        if os.path.islink(root):
            root = os.path.realpath(root)

        return os.path.dirname(os.path.abspath(root))

    except:
        print "I'm sorry, but something is wrong."
        print "There is no __file__ variable. Please contact the author."
        sys.exit()

