#!/usr/bin/env python
"""
SCTR a tool for reporting tagged comments.

Copyright (C) 2015  Alessandro Pischedda

This program is free software; you can redistribute it and/or
modify it under the terms of the GNU General Public License
as published by the Free Software Foundation; either version 2
of the License.

This program is distributed in the hope that it will be useful,
but WITHOUT ANY WARRANTY; without even the implied warranty of
MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
GNU General Public License for more details.

You should have received a copy of the GNU General Public License
along with this program; if not, write to the Free Software
Foundation, Inc., 51 Franklin Street, Fifth Floor, Boston, MA  02110-1301, USA.
   
"""

__author__ = "Alessandro Pischedda"
__license__ = "GPL"
__version__ = "0.9"
__maintainer__ = "Alessandro Pischedda"
__email__ = "alessandro.pischedda@gmail.com"

import sys
import os
import re
import readline
import json

# check for argparse library
try:
    from argparse import ArgumentParser, RawDescriptionHelpFormatter
except ImportError:
    print "Library argparse is missing"
    sys.exit(-1)

try:
    from templite import Templite
except ImportError:
    print "Library templite is missing"
    sys.exit(-1) 

# TODO specify tags them in config.json,
# remove them as global and use as local
tags = None

filetype_comments = {}

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

# Parse command line arguments and options
def options():
    """print help menu and handle the options"""

    # TODO the output file can't has .html as extension.    
    # The RawDescriptionHelpFormatter is required to show the epilog
    parser = ArgumentParser(formatter_class=RawDescriptionHelpFormatter,
                            version="%prog 0.9")
    
    parser.add_argument("-o", "--output",
        metavar = "FILENAME",
        help = "Name of the html output file")

    parser.add_argument("-i", "--input",
        metavar = "FILENAME or DIR_NAME",
        default =" ",
        help = "Name of the file/directory that should be processed")

    parser.add_argument("-r", "--recursive",
        action="store_true",
        help = "If the input is a directory scan the directories recursively")

    parser.add_argument("-t", "--template",
        metavar = "FILENAME",
        help = "Name of the template you want to use")

    args = parser.parse_args()

    # Convert the list of options to a dictionary
    opts = args.__dict__

    if opts['input'] is "":
        parser.error("Input file is missing.")

    return opts




def get_text(expression, line):
    """Search for an expression and retun the text"""

    index = re.search(expression, line, flags=re.IGNORECASE)
    if index == None:
        return None

    return line[index.end():]



def parse_file(filename, comments):
    """open the file, read and parse it searching for tags"""

    results = {}

    # get file's extension
    extension = os.path.splitext(filename)[1] 

    # ignore this file if hasn't an extension or isn't in the list
    # no extension 
    if extension not in filetype_comments:
        return

    single_base, multi_start_base, multi_end_base = filetype_comments[extension] 

    src_file = open(filename, "r")

    # add the part to ignore multiple whitespace and escape the chars
    single_base = re.escape(single_base)+"\s*"
    multi_start_base = re.escape(multi_start_base)+"\s*"
    multi_end_base = re.escape(multi_end_base)

    # used to store in which line number we are, we start with line 1
    line_number = 1
   
    multi_comment = None

    # used to remember which was the last tag founded, it will be used to
    # complete a multiline comment or a multi singleline comment
    previous_tag = None

    for line in src_file:

        found = False
        comment_body = None

        if multi_comment == "single":
            comment_body = get_text(single_base, line)
            if comment_body:
                #retrieve old body comment and add the new line
                last_cmt = len(results[previous_tag]) -1
                old_line, old_comment = results[previous_tag][last_cmt]
                new_comment = old_comment + comment_body
                results[previous_tag][last_cmt] = (old_line, new_comment)  
                continue

        elif multi_comment == "multi":
            last_cmt = len(results[previous_tag]) -1
            old_line, old_comment = results[previous_tag][last_cmt]

            index = re.search(multi_end_base, line, flags=re.IGNORECASE)
            # the multiline comment is ended
            if index != None:
                new_comment = old_comment + line[:index.start()]
                multi_comment = None
            else: # the multiline comment is still continuing
                new_comment = old_comment + line

            # ok write the new content
            results[previous_tag][last_cmt] = (old_line, new_comment)
            continue

        multi_comment = None

        for tag in tags:
            pattern_single = single_base + tag
            comment_body = get_text(pattern_single, line)

            if comment_body != None:
                multi_comment = "single"
                found = True
                previous_tag = tag
                break
            
            # multiline comment 
            pattern_multi = multi_start_base + tag
            comment_body = get_text(pattern_multi, line)
            if comment_body != None:
                index = re.search(multi_end_base, comment_body)
                found = True         
                if index == None:
                    multi_comment = "multi"
                    previous_tag = tag
                else:
                    comment_body = comment_body[: index.start()]
                    multi_comment = None
                break

        if found:
            if tag not in results:
                results[tag] = []
            results[tag].append( (line_number, comment_body) )

        
        line_number = line_number + 1

    # it is time to close the file
    src_file.close()

    # modify the comments data only if we've found at least one tag
    if results != {}:
        comments[filename] = results
    return




"""def parse_file(filename, comments):

    results_local = {}

    # get file's extension
    extension = os.path.splitext(filename)[1] 

    # ignore this file if hasn't an extension or isn't in the list
    # no extension 
    if extension not in filetype_comments:
        return

    single_base, multi_start_base, multi_end_base = filetype_comments[extension] 

    src_file = open(filename, "r")

    # add the part to ignore multiple whitespace and escape the chars
    single_base = re.escape(single_base)+"\s*"
    multi_start_base = re.escape(multi_start_base)+"\s*"
    multi_end_base = re.escape(multi_end_base)

    # used to store in which line number we are, we start with line 1
    line_number = 1
   
    # used to check possible multiline comment divided in different
    # single line comment. If True means that the previous line was a 
    # singleline comment with one of TAGs.
    # EXAMPLE (C++) 
    #  // TODO I'm a multiline comment
    #  // composed of multi single comment
    #
    multi_single_comment = False
    multiline_comment = False

    # used to remember which was the last tag founded, it will be used to
    # complete a multiline comment or a multi singleline comment
    old_tag = ""

    for line in src_file:

        # check if we have already found a single or multiline comment tag
        if multi_single_comment:
            index = re.search(single_base, line, flags=re.IGNORECASE)
            if index_tag != None:
                    #retrieve old body comment and add the new line
                    last_cmt = len(results_local[old_tag]) -1
                    old_line, old_comment = results_local[old_tag][last_cmt]
                    new_comment = old_comment + line[index.end():]
                    results_local[old_tag][last_cmt] = (old_line, new_comment)  
                    continue

        elif multiline_comment:
            last_cmt = len(results_local[old_tag]) -1
            old_line, old_comment = results_local[old_tag][last_cmt]

            index = re.search(multi_end_base, line, flags=re.IGNORECASE)
            # the multiline comment is ended
            if index != None:
                new_comment = old_comment + line[:index.start()]
                multiline_comment = False
            else: # the multiline comment is still continuing
                new_comment = old_comment + line

            # ok write the new content
            results_local[old_tag][last_index] = (old_line, new_comment)
            continue

        found = False

        for tag in tags:
            pattern_single = single_base + tag
            pattern_multi = multi_start_base + tag

            index_single = re.search(pattern_single, line, flags=re.IGNORECASE)

            index_multi_start = None
            # so the multiline part is empty "", means that does not exists
            if multi_start_base != '\s*':
                index_multi_start = re.search(pattern_multi, line, flags=re.IGNORECASE)

            comment_body = ""

            if index_single != None:
                if tag not in results_local:
                    results_local[tag] = []
                comment_body = line[index_single.end():]
                results_local[tag].append((line_number, comment_body))
                multi_single_comment = True
                old_tag = tag
                found = True                
                break # ok go to the new line

            elif index_multi_start != None:
                if tag not in results_local:
                    results_local[tag] = []
        
                comment_body = ""
                index_multi_end = re.search(multi_end_base, line, flags=re.IGNORECASE)
                if index_multi_end != None:
                   multiline_comment = False
                   comment_body = line[index_multi_start.end(): index_multi_end.start()]
                else:
                   multiline_comment = True
                   comment_body = line[index_multi_start.end():]
                results_local[tag].append((line_number, comment_body))

                old_tag = tag
                break # ok go to the new line

        # NEW VERSION
        for tag in tags:
            pattern_single = single_base + tag
            pattern_multi = multi_start_base + tag
            index_tag = re.search(pattern_single, line, flags=re.IGNORECASE)    
            single_comment = True
            if index_tag == None:
                single_comment = False
                if multi_start_base != '\s*':
                    index_tag = re.search(pattern_multi, line, flags=re.IGNORECASE)

            if index_tag != None:
                if tag not in results_local:
                    results_local[tag] = []
                comment_body = line[index_tag.end():]
                results_local[tag].append( (line_number, comment_body) )
                old_tag = tag
                found = True

                # TODO si puo ancora migliorare
                if single_comment:
                    multi_single_comment = True
                else:
                    multiline_comment = True
                break
        # END NEW VERSION

        if not found:
            multi_single_comment = False

        line_number += 1

    # it is time to close the file
    src_file.close()

    # modify the comments data only if we've found at least one tag
    if results_local != {}:
        comments[filename] = results_local
    return"""


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
    

if __name__ == '__main__':

    output_filename = None;   
    comments_list = {}
 
    # Retrieve command line arguments and options
    opts = options()
	
    # read the configuration file
    with open('conf.json') as config_file:    
        data = json.load(config_file)

    filetype_comments = data["exts"]
    tags = data["tags"]

    if opts['output'] != None:
        output_filename = opts['output']
    else:
        output_filename = data['output']
    
    if opts['template'] != None:
        template_filename = opts['template']
    else:
        template_filename = data['template']


    # check the IN/OUT file
    check_filename(opts["input"])
    check_filename(template_filename)
    check_output(output_filename)


    # if the input is :
    #   a directory, use the recursive option
    #   a file, parse it directly
    if(os.path.isdir(opts["input"])):
        handle_dir(opts["input"], opts["recursive"], comments_list)
    elif(os.path.isfile(opts["input"])):
        parse_file(opts["input"], comments_list)
    
    # use the template file
    file_template = Templite(None, template_filename)
    new_content = file_template.render(comments=comments_list)

    # time to write down 
    report_file = open(output_filename, "w")
    report_file.write(new_content)
    report_file.close()
