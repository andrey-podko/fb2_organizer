import os
import sys
import errno

__license__     = 'GPL v2'
__copyright__   = '2015. Podko Andrew <podko.andrew at gmail.com>'


color_code = {'red': '\033[01;31m', 'green': '\033[01;32m',
              'yellow': '\033[01;33m', 'default': '\033[0m'}
langs = {'rus': 'ru', 'eng': 'en', 'ukr': 'uk', 'bel': 'by'}

""" Load fix names """
_fix_names_fd = open('fix_names_list.txt', mode='r')
_fix_names_header = _fix_names_fd.readline()
_fix_names = {}
_fix_names_row = _fix_names_fd.readline()
while _fix_names_row != '':
    _fix_names_row = _fix_names_row.strip()
    _fix_names_cols = _fix_names_row.split(sep=';')
    _fix_names[_fix_names_cols[0]] = [_fix_names_cols[1], _fix_names_cols[2]]
    _fix_names_row = _fix_names_fd.readline()


def clear_empty_dirs(dir_list):
    """ list -> NoneType

    Remove empty directory by dir_list

    >>> clear_empty_dirs(['/tmp/111'])

    """
    """ reverse dir_list do delete dirs after delete all it subdirs"""
    if len(dir_list) > 1:
        dir_list.reverse()
    for trydir in dir_list:
        try:
            os.rmdir(trydir)
        except OSError as ex:
            if ex.errno == errno.ENOTEMPTY:
                colored_error('green', "Directory is not empty: " + trydir)
            if ex.errno == errno.EACCES:
                colored_error('yellow', "Insufficient rights for delete: " + trydir)


def get_value(doc, nametype):
    """ class 'xml.dom.minidom.Document',str -> str

    Return requested values from XML document
    First,Last name of Author, book title, book language

    Precondition: type can have value 'first-name', 'last-name',
                                      'lang', 'book-title'

    >>> get_value(fb2,'first-name')
    "Isaac"
    >>> get_value(fb2,'last-name')
    "Asimov"
    >>> get_value(fb2,'book-title')
    "Robot Visions"

    """
    for node_name in doc.getElementsByTagName(nametype):
            for name_value in node_name.childNodes:
                if name_value.nodeType == name_value.TEXT_NODE:
                    result = name_value.data.strip().strip(',')
                    result = result.replace('ё', 'е').replace('Ё', 'Е')
                    return result.replace('  ', ' ').replace(' \t', ' ') 


def _get_authors(doc,lang):
    """ class 'xml.dom.minidom.Document', str -> list

    Return array of authors name

    >>> get_authors(fb2,'en')
    ["Asimov", "Isaac"]
    >>> get_authors(fb2,'en')
    [None, None]

    """
    result = []
    for node_author in doc.getElementsByTagName("author"):
        first_name = get_value(node_author, 'first-name')
        last_name = get_value(node_author, 'last-name')
        if not first_name is None and not last_name is None:
            first_name = first_name.strip().title()
            last_name = last_name.strip().title()
            check_name = lang + ' ' + last_name + ' ' + first_name
            if check_name in _fix_names:
                correct_names = _fix_names[check_name]
            else:
                correct_names = [last_name, first_name]
            result.append(correct_names)
    return result


def get_authors_list(doc,lang):
    """ class 'xml.dom.minidom.Document', str -> list

    Return array of valid authors name, using 'title-info'

    >>> get_authors_list(fb2,'en')
    ["Asimov", "Isaac"]

    """
    for title_info in doc.getElementsByTagName("title-info"):
        title_names = _get_authors(title_info,lang)
    if None in title_names or title_names == []:
        return None
    else:
        return title_names


def _clean_sequence_name(sequence_name):
    """ str -> list

    Return clean sequence for author's books

    """
    if 'Зарубежная фантастика' in sequence_name:
        return ''
    sequence_name = sequence_name.replace('(изд-во Мир)', '')
    sequence_name = sequence_name.replace('The International Bestseller 2901', '')
    sequence_name = sequence_name.replace('(сборник рассказов)', '')
    sequence_name = sequence_name.replace('(Сборник)', '')
    return sequence_name.strip()


def get_sequence(doc):
    """ class 'xml.dom.minidom.Document' -> list

    Return sequence name and number

    >>> get_sequence(fb2)
    ["Собрание сочинений", 9]

    """
    for title_info in doc.getElementsByTagName("title-info"):
        for sequence_node in title_info.getElementsByTagName("sequence"):
            sequence_number = sequence_node.getAttribute('number')
            if sequence_number.isdigit:
                sequence_number = sequence_number.lstrip('0')
            sequence_name = sequence_node.getAttribute('name')
            sequence_name = _clean_sequence_name(sequence_name)
            if sequence_name == '':
                return None
            return [sequence_name, sequence_number]
    return None


def get_valid_lang(doc):
    """ class 'xml.dom.minidom.Document' -> str

    Return validated language code
    >>> get_valid_lang('eng')
    en
    >>> get_valid_lang('en')
    en

    """
    lang = get_value(doc, 'lang')
    if lang is None:
        if doc.encoding.lower() == 'windows-1251':
            lang = 'ru'
        else:
            lang = 'unknown'
    lang = lang.lower()
    if lang in langs:
        lang = langs[lang]
    return lang


def delete_source(delete_path):
    """ str -> NoneType

    Delete source file
    >>> delete_source('/tmp/dfsdfds.fb2')

    """
    try:
        os.unlink(delete_path, dir_fd=None)
    except OSError as ex:
        if ex.errno == errno.EACCES:
            colored_error('green', "Insufficient rights for delete source file: " + delete_path)


def colored_error(color, message):
    """ str, str ->NoneType

    Outputs colored error message into STDERR

    >>>colored_error('red', 'Hello, World!')
    """
    sys.stderr.write(color_code[color] + message + color_code['default'] + '\n')
