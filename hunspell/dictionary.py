import os
import re
import sys
from collections import deque
from io import IOBase

from hunspell.affix import Afx, Affix, Rule


class Word:
    def __init__(self, line, flag_type: str = 'ascii', input_conversion=None, output_conversion=None):
        if output_conversion is None:
            output_conversion = {}
        if input_conversion is None:
            input_conversion = {}
        self.word = ''
        self.__word = None
        self.flags = []
        self.data_fields = {}
        self.flag_type = flag_type
        self._output_conversion = output_conversion
        self._parse_line(line, input_conversion)

    def get_word(self) -> str:
        if self.__word is None:
            self.__word = self._replace(self.word, self._output_conversion)
        return self.__word

    @staticmethod
    def _replace(word: str, dic: dict) -> str:
        for k in dic:
            word = word.replace(k, dic[k])
        return word

    def _parse_line(self, line, conversion):
        parts = line.split('/')

        self.word = self._replace(parts[0].strip(), conversion)
        data_fields = []

        if len(parts) > 1 and len(parts[1].strip()) > 0:
            data_fields = parts[1].split()
            parts[1] = data_fields.pop(0)
            if self.flag_type.lower() == 'long':
                self.flags = list(map(''.join, zip(*[iter(parts[1].strip())] * 2)))
            else:
                self.flags = list(iter(parts[1].strip()))

        for data_field in data_fields:
            comp = data_field.split(':')
            print(comp[0].strip())
            if self.data_fields.get(comp[0].strip(), None) is None:
                self.data_fields[comp[0].strip()] = []
            self.data_fields[comp[0].strip()].append(comp[1].strip())

    def update_data_fields(self, data_fields: dict):
        for k, v in data_fields:
            self.data_fields[k] = v if self.data_fields[k] is None else self.data_fields[k] + v


def _generate_affix_word(word: Word, afx: Afx, input_conversion=None, output_conversion=None) -> deque:
    if output_conversion is None:
        output_conversion = {}
    if input_conversion is None:
        input_conversion = {}
    words = deque()
    if afx.type == 'SFX':
        for rule in afx.rules:
            if isinstance(rule, Rule):
                if re.search(rule.condition + '$', word.get_word()) is not None:
                    if rule.stripping == '0':
                        new_str = word.get_word() + rule.affix
                    elif word.get_word().endswith(rule.stripping):
                        new_str = word.get_word()[:-len(rule.stripping)] + rule.affix
                    else:
                        continue
                else:
                    continue
                new_word = Word(new_str, word.flag_type, input_conversion, output_conversion)
                new_word.update_data_fields(word.data_fields)
                words.append(new_word)
    elif afx.type == 'PFX':
        for rule in afx.rules:
            if isinstance(rule, Rule):
                if re.search('^' + rule.condition, word.get_word()) is not None:
                    parts = rule.affix.split('/')
                    if len(parts) == 1:
                        parts.append('')
                    elif len(parts) != 2:
                        raise ValueError('The Affix {} has a invalid affix {}.'.format(afx.type, rule.affix))
                    if rule.stripping == '0':
                        new_str = parts[0] + word.get_word() + '/' + parts[1]
                    elif word.get_word().endswith(rule.stripping):
                        new_str = parts[0] + word.get_word()[len(rule.stripping):0] + '/' + parts[1]
                    else:
                        continue
                else:
                    continue
                new_word = Word(new_str, word.flag_type, input_conversion, output_conversion)
                new_word.update_data_fields(word.data_fields)
                words.append(new_word)
    else:
        raise ValueError('{} is not a valid affix.'.format(afx.type))
    return words


def _generate_affix_words(word: Word, affix: Affix) -> deque:
    words = deque()
    for flag in word.flags:
        afx = affix.afx.get(flag, None)
        if afx is None:
            continue
        if isinstance(afx, Afx):
            new_words = _generate_affix_word(word, afx)
            for new_word in new_words:
                words.append(new_word)
                if afx.cross_product:
                    for flag2 in word.flags[word.flags.index(flag):]:
                        afx2 = affix.afx.get(flag2, None)
                        if afx2 is None:
                            continue
                        if isinstance(afx2, Afx):
                            if afx2.cross_product and afx.type != afx2.type:
                                new_words_2 = _generate_affix_word(new_word, afx2)
                                for new_word_2 in new_words_2:
                                    words.append(new_word_2)

    return words


def word_list(aff: str, dic: str, base_words_only: bool = False, print_out: bool = True) -> set:
    file = sys.stdout if print_out else IOBase()
    print('Start parse affix file ...', file=file)
    affix = Affix(aff)
    print('Finished parsing affix file', file=file)
    print('Start parse dictionary file ...', file=file)
    dictionary = parse_dictionary(dic, affix.encoding, affix.flag, affix.iconv, affix.oconv)
    print('Finished parsing dictionary file', file=file)
    if base_words_only:
        out = map(lambda d: d.get_word(), dictionary)
    else:
        print('Start generating word list ...', file=file)
        out = deque()
        queue = dictionary
        while len(queue) > 0:
            print('\rnot processed words: {:<10d}'.format(len(queue)), end='', file=file)
            word = queue.popleft()
            if isinstance(word, Word):
                out.append(word.get_word())
                words = _generate_affix_words(word, affix)
                for w in words:
                    queue.append(w)
            else:
                raise ValueError('Invalid Word: {} is type of {}.'.format(word, type(word)))
        print('\rnot processed words: {:<10d}'.format(len(queue)), file=file)
        print('Finished generating word list', file=file)

    word_set = set(out)
    print('generate Words: {:d}'.format(len(word_set)), file=file)
    print(file=file)
    return word_set


def parse_dictionary(file: str,
                     encoding: str = 'ASCII',
                     flag_type: str = 'ASCII',
                     input_conversion: dict or None = None,
                     output_conversion: dict or None = None) -> iter:
    if output_conversion is None:
        output_conversion = {}
    if input_conversion is None:
        input_conversion = {}
    if not os.path.exists(file):
        raise FileNotFoundError()
    if not os.path.isfile(file):
        raise FileNotFoundError()
    words = deque()

    with open(file, encoding=encoding) as dic:
        for line in dic:
            if line.isspace() or line.startswith(('#', ' ', '\t')) or line.strip().isdigit():
                continue

            word = Word(line, flag_type, input_conversion, output_conversion)

            words.append(word)

    return words
