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

import re
import readline
import json
from utils import *

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


if __name__ == '__main__':

    output_filename = None;   
    comments_list = {}
 
    # Retrieve command line arguments and options
    opts = options()
	
    root = determine_path()

    # read the configuration file
    with open(root+'/conf.json') as config_file:    
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
        template_filename = root+"/"+data['template']


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
