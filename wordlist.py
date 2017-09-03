import os
import re
import sys
from argparse import ArgumentParser, FileType
from collections import deque
from io import IOBase
from os import path

try:
    from secrets import choice
except ImportError:
    from random import choice

from hunspell import dictionary


class __Param:
    def __init__(self, error_print: callable):
        self.__error_print = error_print
        self.count = 4
        self.force = False
        self.max = -1
        self.min = 0
        self.negate = False
        self.output = sys.stdout
        self.path = '.'
        self.regex = '.*'
        self.separator = ' '
        self.tosses = 5
        self.DIC = None

        self.wrd = None
        self.dic = None
        self.aff = None

    def check(self):
        if self.count < 0:
            self.__error_print('the count parameter has to be greater than 0')
        if self.min < 0:
            self.__error_print('the min parameter has to be greater or equal than 0')
        if self.max != -1 or -1 < self.max < self.min:
            self.__error_print('the max parameter has to be greater than min parameter or -1')
        if self.output is None or not isinstance(self.output, IOBase):
            self.__error_print('invalid output source')
        if not path.exists(self.path) or not path.isdir(self.path):
            self.__error_print('path to dictionary files and/or word list file not found')
        try:
            re.compile(self.regex)
        except re.error:
            self.__error_print('the filter option regex is a invalid regular expression')

        if self.tosses < 1:
            self.__error_print('the number of tosses has to be a positive number')

        self.aff = path.normpath(path.join(self.path, self.DIC + '.aff'))
        self.dic = path.normpath(path.join(self.path, self.DIC + '.dic'))
        self.wrd = path.normpath(path.join(self.path, self.DIC + '.wrd'))

        aff_exist = path.exists(self.aff) and path.isfile(self.aff)
        dic_exist = path.exists(self.dic) and path.isfile(self.dic)
        wrd_exist = path.exists(self.wrd) and path.isfile(self.wrd)

        if self.force and not aff_exist:
            self.__error_print('No affix file found: {}'.format(path.abspath(self.aff)))

        if self.force and not aff_exist:
            self.__error_print('No dictionary file found: {}'.format(path.abspath(self.dic)))

        if not self.force and not dic_exist and not wrd_exist:
            self.__error_print(
                'No dictionary or word list file found: {}, {}'.format(path.abspath(self.dic), path.abspath(self.wrd))
            )

        if not self.force and not aff_exist and not wrd_exist:
            self.__error_print(
                'No affix or word list file found: {}, {}'.format(path.abspath(self.aff), path.abspath(self.wrd))
            )

    def __repr__(self):
        type_name = type(self).__name__
        arg_strings = []
        for name, value in self._get_kwargs():
            arg_strings.append('%s=%r' % (name, value))
        return '%s(%s)' % (type_name, ', '.join(arg_strings))

    def _get_kwargs(self):
        return sorted(self.__dict__.items())


def main():
    param = parse_args()
    param.check()

    wrd_exist = path.exists(param.wrd) and path.isfile(param.wrd)

    if param.force or not wrd_exist:
        word_deque = dictionary.word_list(param.aff, param.dic)
        with open(param.wrd, 'w') as wrd_file:
            wrd_file.write(os.linesep.join(word_deque))
    else:
        with open(param.wrd) as wrd:
            word_deque = deque(wrd)

    if param.regex == '.*':
        if param.max == -1:
            if param.min == 0:
                pass
            else:
                word_deque = filter(lambda w: param.min < len(w), word_deque)
        else:
            if param.min == 0:
                word_deque = filter(lambda w: len(w) < param.max, word_deque)
            else:
                word_deque = filter(lambda w: param.min < len(w) < param.max, word_deque)
    else:
        reg = re.compile(param.regex)
        reg_filter = (lambda w: reg.search(w) is None) if param.negate else (lambda w: reg.search(w) is not None)
        if param.max == -1:
            if param.min == 0:
                word_deque = filter(lambda w: reg_filter(w), word_deque)
            else:
                word_deque = filter(lambda w: reg_filter(w) and param.min < len(w), word_deque)
        else:
            if param.min == 0:
                word_deque = filter(lambda w: reg_filter(w) and len(w) < param.max, word_deque)
            else:
                word_deque = filter(lambda w: reg_filter(w) and param.min < len(w) < param.max, word_deque)

    word_list = list(word_deque)

    for _ in range(param.tosses):
        words = [choice(word_list).strip() for _ in range(param.count)]
        print(param.separator.join(words), end=os.linesep, file=param.output)


def parse_args() -> (callable, __Param):
    parser = ArgumentParser(
        description='The programme will generate a random password based on words. '
                    'The advantage over standard random generated password is, '
                    'that it easy to remember and in general harder to crack.',
        epilog='The name of the DIC parameter specifies the filename without the extension for the dictionary or word'
               ' list. That means if you want to use the en-GB.aff and en-GB.dic to generate a password. You type for'
               ' the DIC parameter "en-GB". This also applies to a corresponding word list file (.wrd). If both types'
               ' exist, a word list file (DIC.wrd) and dictionary files (DIC.aff, DIC.dic), the word file will be used.'
    )
    parser.add_argument('-c', '--count',
                        type=int,
                        help='number of words in the passwords, default is 4')
    parser.add_argument('-f', '--force',
                        action='store_true',
                        help='force to use dictionary files, if a word list file exist it will overwritten')
    parser.add_argument('-g', '--max',
                        type=int,
                        help='the max. length for a chosen word, -1 for no limit, default is -1')
    parser.add_argument('-l', '--min',
                        type=int,
                        help='the min. length for a chosen word, default is 0')
    parser.add_argument('-n', '--negate',
                        action='store_true',
                        help='invert the regular expression filter')
    parser.add_argument('-o', '--output',
                        type=FileType('a'),
                        help='specify a file for write in, instead of terminal printout')
    parser.add_argument('-p', '--path',
                        help='path to dictionary files and/or word list file, default is the current directory')
    parser.add_argument('-r', '--regex',
                        help='filter the possible words with a regular expression')
    parser.add_argument('-s', '--separator',
                        help='is the string between the words, default is a single space " "')
    parser.add_argument('-t', '--tosses',
                        type=int,
                        help='number of passwords that should generated, default is 3')
    parser.add_argument('DIC',
                        help='the name of the dictionary or word list that should be used in the given directory')

    param = __Param(parser.error)
    parser.parse_args(namespace=param)

    return param


if __name__ == '__main__':
    os.chdir(os.path.dirname(os.path.realpath(__file__)))

    main()
