#!/usr/bin/python3
# -*- coding: UTF-8 -*-

""" FB2 Book Files organizer.

Get metadata from FB2 files and try to move FB2 books into hierarchical
directory structure. Also it clean empty directories into source directory.

"""

import xml.dom.minidom
import shutil
import filecmp
import argparse
import sqlite3
from fb2_organizer_defs import *

__license__    = 'GPL v2'
__copyright__  = '2015. Podko Andrew <podko.andrew at gmail.com>'


""" Command line options setup """
parser = argparse.ArgumentParser(description='FB2 books organizer')
parser.add_argument('-v', '--verbose', dest='arg_verbose', action="store_true",
                    help='Print source and destination path in work mode')
parser.add_argument('--demo', dest='arg_demo', action="store_true",
                    help="""Only print source and destination path without real actions.
                    Override --delete and --verbose keys""")
parser.add_argument('--delete', dest='arg_delete_source', action="store_true",
                    help='Delete source files after copy to destination')
parser.add_argument('source',
                    help='Source folder')
parser.add_argument('destination',
                    help='Destination folder where books will placed')
parser.add_argument('--cn', type=int, default=3, nargs='?',
                    help="""If book authors count >= this number,
                    book interpreted as compilation
                    default 3""")
args = parser.parse_args()

arg_verbose = args.arg_verbose
arg_delete = args.arg_delete_source
arg_source_dir = os.path.abspath(args.source)
arg_destination_dir = os.path.abspath(args.destination)
arg_compilation_num = args.cn

""" some arguments parse """
if arg_source_dir == arg_destination_dir:
    print("""Error: source and destination are identical.
            Reorganize directory currently is not supported""")
    exit(errno.ENOSYS)
if args.arg_demo:
    arg_verbose = True
    arg_delete = False

""" build file list """
filelist = []
dirlist = [arg_source_dir]
for path, subdirs, files in os.walk(arg_source_dir):
    for filename in files:
        file_ext = os.path.splitext(filename)[1]
        if '.fb2' == file_ext.lower():
            filelist.append(os.path.join(path, filename))
    dirlist.append(path)

""" DB init """
#db_conn = sqlite3.connect('fb2_organizer.db')  # @UndefinedVariable
#db_cur = db_conn.cursor()
#db_cur.execute("""CREATE TABLE IF NOT EXISTS books
#    (title varchar, lang varchar, sequence_name varchar, sequence_num int, \
#    destination varchar)""")

""" processing """
processed_files_count = 0
mailformed_files_count = 0
noauthor_files_count = 0
exist_files_count = 0
exist_files_list = ''
for source_path in filelist:
    processed_files_count += 1
    try:
        print('\n', source_path)
    except UnicodeEncodeError:
        colored_error('red', "Can't display source file name")
    try:
        fb2 = xml.dom.minidom.parse(source_path)
    except xml.parsers.expat.ExpatError:  # @UndefinedVariable
            colored_error('red', 'Malformed FB2 file! Skip it.')
            mailformed_files_count += 1
            continue

    book_lang = get_valid_lang(fb2)

    authors_list = get_authors_list(fb2,book_lang)
    if authors_list is None:
        colored_error('red', 'Authors info not found, skip this file')
        noauthor_files_count += 1
        continue
    author_string = ''
    """ authordir_string contain a primary(first) author or 'Compilations' """
    authordir_string = authors_list[0][0] + ' ' + authors_list[0][1]
    for author in range(0, len(authors_list)):
        if author == arg_compilation_num:
            authordir_string = 'Compilations'
            break
        author_string += authors_list[author][0] + ' ' + authors_list[author][1] + ', '
    author_string = author_string.rstrip(', ')

    """ Адаптированные книги по методу Ильи Франка"""
    if ['Франк', 'Илья'] in authors_list:
        authordir_string = 'Адаптированные книги'

    book_title = get_value(fb2, 'book-title')
    if book_title is None:
        colored_error('red', "Book title not found, skip this file")
        continue
    
    """ if sequence >=arg_compilation_num skip sequence data in book filename """
    sequence = get_sequence(fb2)
    sequence_name = ''
    sequence_num = ''
    if sequence is None:
        sequence_path_data = ''
    elif author == arg_compilation_num:
        sequence_path_data = ''
    else:
        sequence_name = sequence[0]
        sequence_num = sequence[1]
        sequence_path_data = ' - ' + sequence_name + ' ' + sequence_num
        sequence_path_data = sequence_path_data.rstrip()
    sequence_path_data = sequence_path_data.replace('  ', ' ')

    """ create destination subdirectory """
    destination_subdir = os.path.join(arg_destination_dir, book_lang, authordir_string)
    if arg_verbose:
        print('destination_subdir\t', destination_subdir)
    if not args.arg_demo:
        try:
            os.makedirs(destination_subdir, exist_ok=True)
        except OSError as ex:
                if ex.errno == errno.EACCES:
                    colored_error('yellow', ex)
                    sys.exit(errno.EACCES)
                elif ex.errno == errno.ENOSPC:
                    colored_error('red', ex)
                    sys.exit(errno.ENOSPC)


    book_filename = author_string + sequence_path_data + ' - ' + book_title
    book_filename_len = len(book_filename.encode('utf-8'))
    while book_filename_len > 250 :
        book_filename = book_filename[:-1]
        book_filename_len = len(book_filename.encode('utf-8'))
    book_filename += '.fb2'

    destination_path = os.path.join(destination_subdir, book_filename)
    if arg_verbose:
        print('destination_path\t', destination_path)

    """ extended check already present files with sqlite """
#    db_cur.execute("INSERT INTO books VALUES (?, ?, ?, ?, ?)",
#                   [book_title, book_lang, sequence_name, sequence_num, destination_path])
#    db_conn.commit()
    # if not exist do copy and delete source file
    if os.access(destination_path, os.F_OK) is False:
        if not args.arg_demo:
            try:
                shutil.copy2(source_path, destination_path)
            except OSError as ex:
                if ex.errno == errno.EACCES:
                    colored_error('yellow', ex)
                elif ex.errno == errno.ENOSPC:
                    colored_error('red', ex)
                    sys.exit(errno.ENOSPC)
                else: print(ex)
    # if file successfully created, delete source
            if arg_delete:
                if os.access(destination_path, os.F_OK) is True:
                    try:
                        delete_source(source_path)
                    except OSError as ex:
                        if ex.errno == errno.EACCES:
                            colored_error('yellow', ex)
                else:
                    colored_error('red', "Something wrong :(")
    else:
        print('Destination file exist!')
        exist_files_count += 1
        if arg_delete:
            if filecmp.cmp(source_path, destination_path, shallow=False):
                delete_source(source_path)
                """ delete only EQ files """
        else:
            """ TODO:
        detail error "Something wrong :"
        extended duplicate check (through sqlite):
        xz organized files
        """
        exist_files_list += "'" + source_path + "'" + '\n' + "'" + destination_path + "'" + '\n'
if arg_delete:
    clear_empty_dirs(dirlist)
sys.stdout.write(color_code['green'] + 'Processed files count:     ' + str(processed_files_count) + color_code['default'] + '\n')
sys.stdout.write(color_code['green'] + 'Already Exist files count: ' + str(exist_files_count) + color_code['default'] + '\n')
sys.stdout.write(color_code['green'] + 'Mailformed files count:    ' + str(mailformed_files_count) + color_code['default'] + '\n')
sys.stdout.write(color_code['green'] + 'NO author data files count:' + str(noauthor_files_count) + color_code['default'] + '\n')
if arg_verbose:
        print(exist_files_list)
#db_conn.close()
