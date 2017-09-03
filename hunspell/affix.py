import math
import os
import re

from io import TextIOWrapper


class Rule:
    def __init__(self, stripping: str, affix: str, condition: str, morphological_fields: list = None):
        if morphological_fields is None:
            morphological_fields = []
        self.stripping = stripping
        self.affix = affix
        self.condition = condition
        self.morphological_fields = morphological_fields


class Afx:
    def __init__(self):
        self.cross_product = False
        self.type = ''
        self.rules = []


class Affix:
    def __init__(self, file: str):
        if not os.path.exists(file):
            raise FileNotFoundError(os.path.abspath(file))
        if not os.path.isfile(file):
            raise FileNotFoundError(os.path.abspath(file))

        self._parse_affix_file(file)

    def __init_fields__(self):
        self.encoding = None
        self.flag = 'ascii'
        self.complexprefixes = False
        self.lang = None
        self.ignore = None
        self.af = []
        self.am = []
        self.key = None
        self.try_chars = None
        self.nosuggest = None
        self.maxcpdsugs = None
        self.maxngramsugs = None
        self.maxdiff = 5
        self.onlymaxdiff = False
        self.nosplitsugs = False
        self.sugswithdots = False
        self.rep = {}
        self.map = {}
        self.phone = None
        self.warn = None
        self.forbidwarn = False
        self.breaking = []
        self.compoundrule = []
        self.compoundmin = 3
        self.compoundflag = None
        self.compoundbegin = None
        self.compoundlast = None
        self.compoundmiddle = None
        self.onlyincompound = None
        self.compoundpermitflag = None
        self.compoundforbidflag = None
        self.compoundroot = None
        self.compoundwordmax = math.inf
        self.checkcompounddup = False
        self.checkcompoundrep = False
        self.checkcompoundcase = False
        self.checkcompoundtriple = False
        self.checkcompoundpattern = []
        self.compoundsyllable = None
        self.syllablenum = None
        self.afx = {}
        self.circumfix = None
        self.forbiddenword = None
        self.fullstrip = False
        self.keepcase = None
        self.iconv = {}
        self.oconv = {}
        self.lemma_present = None
        self.needaffix = None
        self.pseudoroot = None
        self.substandard = None
        self.wordchars = None
        self.checksharps = False

    def _parse_affix_file(self, file: str, encoding: str = 'ASCII'):
        self.__init_fields__()
        self.encoding = encoding

        with open(file, 'r', encoding=self.encoding, errors='replace') as affix_file:
            line = self._get_next_not_empty_line(affix_file)

            while line is not None:
                line = line.strip()

                # AFFIX FILE GENERAL OPTIONS
                if line.startswith('SET'):
                    parts = line.split(maxsplit=1)
                    if self.encoding != parts[1].strip():
                        affix_file.close()
                        self._parse_affix_file(file, parts[1].strip())
                        return
                elif line.startswith('FLAG'):
                    parts = line.split(maxsplit=1)
                    self.flag = parts[1]
                elif line.startswith('COMPLEXPREFIXES'):
                    self.complexprefixes = True
                elif line.startswith('LANG'):
                    parts = line.split(maxsplit=1)
                    self.lang = parts[1]
                elif line.startswith('IGNORE'):
                    parts = line.split(maxsplit=1)
                    self.ignore = parts[1]
                elif line.startswith('AF'):
                    self._parse_flag(line, 'AF', affix_file, self.af)
                elif line.startswith('AM'):
                    self._parse_flag(line, 'AM', affix_file, self.am)

                # AFFIX FILE OPTIONS FOR SUGGESTION
                elif line.startswith('KEY'):
                    parts = line.split(maxsplit=1)
                    self.key = parts[1].split('|')
                elif line.startswith('TRY'):
                    parts = line.split(maxsplit=1)
                    self.try_chars = parts[1]
                elif line.startswith('NOSUGGEST'):
                    parts = line.split(maxsplit=1)
                    self.nosuggest = parts[1]
                elif line.startswith('MAXCPDSUGS'):
                    self.maxcpdsugs = self._parse_int_flag(line, 'MAXCPDSUGS', affix_file)
                elif line.startswith('MAXNGRAMSUGS'):
                    self.maxngramsugs = self._parse_int_flag(line, 'MAXNGRAMSUGS', affix_file)
                elif line.startswith('MAXDIFF'):
                    self.maxdiff = self._parse_int_flag(line, 'MAXDIFF', affix_file)
                    if not 1 <= self.maxdiff <= 10:
                        raise self._generate_syntax_error('MAXDIFF', affix_file.tell())
                elif line.startswith('ONLYMAXDIFF'):
                    self.onlymaxdiff = True
                elif line.startswith('NOSPLITSUGS'):
                    self.nosplitsugs = True
                elif line.startswith('SUGSWITHDOTS'):
                    self.sugswithdots = True
                elif line.startswith('REP'):
                    rep_count = self._parse_int_flag(line, 'REP', affix_file)
                    while rep_count > 0:
                        line = self._get_next_not_empty_line(affix_file)
                        if line is None:
                            raise self._generate_syntax_error('REP', affix_file.tell())
                        line = line.strip()
                        if not line.startswith('REP'):
                            raise self._generate_syntax_error('REP', affix_file.tell())
                        parts = line.split(maxsplit=2)
                        self.rep[parts[1]] = parts[2]
                        rep_count = rep_count - 1
                    if rep_count != 0:
                        raise self._generate_syntax_error('REP', affix_file.tell())
                elif line.startswith('MAP'):
                    map_count = self._parse_int_flag(line, 'MAP', affix_file)
                    while map_count > 0:
                        line = self._get_next_not_empty_line(affix_file)
                        if line is None:
                            raise self._generate_syntax_error('MAP', affix_file.tell())
                        line = line.strip()
                        if not line.startswith('MAP'):
                            raise self._generate_syntax_error('MAP', affix_file.tell())
                        parts = line.split(maxsplit=1)
                        mapping = re.findall('(\([^\d\s.\-)(\]\[\\\/]+\)|\w)', parts[1])
                        if len(mapping) != 2 or not mapping[0] or not mapping[1]:
                            raise self._generate_syntax_error('MAP', affix_file.tell())
                        mapping[0] = mapping[0][1:-1] if len(mapping[0]) > 1 else mapping[0]
                        mapping[1] = mapping[1][1:-1] if len(mapping[1]) > 1 else mapping[1]
                        self.map[mapping[0]] = mapping[1]
                        map_count = map_count - 1
                    if map_count != 0:
                        raise self._generate_syntax_error('MAP', affix_file.tell())
                elif line.startswith('PHONE'):
                    parts = line.split(maxsplit=1)
                    self.phone = parts[1].strip()
                elif line.startswith('WARN'):
                    parts = line.split(maxsplit=1)
                    self.warn = parts[1].strip()
                elif line.startswith('FORBIDWARN'):
                    self.forbidwarn = True

                # OPTIONS FOR COMPOUNDING
                elif line.startswith('BREAK'):
                    self._parse_flag(line, 'BREAK', affix_file, self.breaking)
                elif line.startswith('COMPOUNDRULE'):
                    self._parse_flag(line, 'COMPOUNDRULE', affix_file, self.compoundrule)
                elif line.startswith('COMPOUNDMIN'):
                    self.compoundmin = self._parse_int_flag(line, '', affix_file)
                elif line.startswith('COMPOUNDFLAG'):
                    parts = line.split(maxsplit=1)
                    self.compoundflag = parts[1].strip()
                elif line.startswith('COMPOUNDBEGIN'):
                    parts = line.split(maxsplit=1)
                    self.compoundbegin = parts[1].strip()
                elif line.startswith('COMPOUNDLAST'):
                    parts = line.split(maxsplit=1)
                    self.compoundlast = parts[1].strip()
                elif line.startswith('COMPOUNDMIDDLE'):
                    parts = line.split(maxsplit=1)
                    self.compoundmiddle = parts[1].strip()
                elif line.startswith('ONLYINCOMPOUND'):
                    parts = line.split(maxsplit=1)
                    self.onlyincompound = parts[1].strip()
                elif line.startswith('COMPOUNDPERMITFLAG'):
                    parts = line.split(maxsplit=1)
                    self.compoundpermitflag = parts[1].strip()
                elif line.startswith('COMPOUNDFORBIDFLAG'):
                    parts = line.split(maxsplit=1)
                    self.compoundforbidflag = parts[1].strip()
                elif line.startswith('COMPOUNDROOT'):
                    parts = line.split(maxsplit=1)
                    self.compoundroot = parts[1].strip()
                elif line.startswith('COMPOUNDWORDMAX'):
                    self.compoundwordmax = self._parse_int_flag(line, '', affix_file)
                elif line.startswith('CHECKCOMPOUNDDUP'):
                    self.checkcompounddup = True
                elif line.startswith('CHECKCOMPOUNDREP'):
                    self.checkcompoundrep = True
                elif line.startswith('CHECKCOMPOUNDCASE'):
                    self.checkcompoundcase = True
                elif line.startswith('CHECKCOMPOUNDTRIPLE'):
                    self.checkcompoundtriple = True
                elif line.startswith('SIMPLIFIEDTRIPLE'):
                    self.simplifiedtriple = True
                elif line.startswith('CHECKCOMPOUNDPATTERN'):
                    checkcompoundpattern_count = self._parse_int_flag(line, 'CHECKCOMPOUNDPATTERN', affix_file)
                    while checkcompoundpattern_count > 0:
                        line = self._get_next_not_empty_line(affix_file)
                        if line is None:
                            raise self._generate_syntax_error('CHECKCOMPOUNDPATTERN', affix_file.tell())
                        line = line.strip()
                        if not line.startswith('CHECKCOMPOUNDPATTERN'):
                            raise self._generate_syntax_error('CHECKCOMPOUNDPATTERN', affix_file.tell())
                        parts = line.split(maxsplit=2)
                        self.checkcompoundpattern.append(tuple(parts[2].split()))
                        checkcompoundpattern_count = checkcompoundpattern_count - 1
                    if checkcompoundpattern_count != 0:
                        raise self._generate_syntax_error('CHECKCOMPOUNDPATTERN', affix_file.tell())
                elif line.startswith('FORCEUCASE'):
                    parts = line.split(maxsplit=1)
                    self.forceucase = parts[1].strip()
                elif line.startswith('COMPOUNDSYLLABLE'):
                    parts = line.split(maxsplit=1)
                    self.compoundsyllable = parts[1].strip()
                elif line.startswith('SYLLABLENUM'):
                    parts = line.split(maxsplit=1)
                    self.syllablenum = parts[1].strip()

                # AFFIX FILE OPTIONS FOR AFFIX CREATION
                elif line.startswith('PFX'):
                    self._parse_affix_flag(line, 'PFX', affix_file)
                elif line.startswith('SFX'):
                    self._parse_affix_flag(line, 'SFX', affix_file)

                # AFFIX FILE OTHER OPTIONS
                elif line.startswith('CIRCUMFIX'):
                    parts = line.split(maxsplit=1)
                    self.circumfix = parts[1].strip()
                elif line.startswith('FORBIDDENWORD'):
                    parts = line.split(maxsplit=1)
                    self.forbiddenword = parts[1].strip()
                elif line.startswith('FULLSTRIP'):
                    self.fullstrip = True
                elif line.startswith('KEEPCASE'):
                    parts = line.split(maxsplit=1)
                    self.keepcase = parts[1].strip()
                elif line.startswith('ICONV'):
                    iconv_count = self._parse_int_flag(line, 'ICONV', affix_file)
                    while iconv_count > 0:
                        line = self._get_next_not_empty_line(affix_file)
                        if line is None:
                            raise self._generate_syntax_error('ICONV', affix_file.tell())
                        line = line.strip()
                        if not line.startswith('ICONV'):
                            raise self._generate_syntax_error('ICONV', affix_file.tell())
                        parts = line.split(maxsplit=2)
                        self.iconv[parts[1]] = parts[2]
                        iconv_count = iconv_count - 1
                    if iconv_count != 0:
                        raise self._generate_syntax_error('ICONV', affix_file.tell())
                elif line.startswith('OCONV'):
                    oconv_count = self._parse_int_flag(line, 'OCONV', affix_file)
                    while oconv_count > 0:
                        line = self._get_next_not_empty_line(affix_file)
                        if line is None:
                            raise self._generate_syntax_error('OCONV', affix_file.tell())
                        line = line.strip()
                        if not line.startswith('OCONV'):
                            raise self._generate_syntax_error('OCONV', affix_file.tell())
                        parts = line.split(maxsplit=2)
                        self.oconv[parts[1]] = parts[2]
                        oconv_count = oconv_count - 1
                    if oconv_count != 0:
                        raise self._generate_syntax_error('OCONV', affix_file.tell())
                elif line.startswith('LEMMA_PRESENT'):
                    parts = line.split(maxsplit=1)
                    self.lemma_present = parts[1].strip()
                elif line.startswith('NEEDAFFIX'):
                    parts = line.split(maxsplit=1)
                    self.needaffix = parts[1].strip()
                elif line.startswith('PSEUDOROOT'):
                    parts = line.split(maxsplit=1)
                    self.pseudoroot = parts[1].strip()
                elif line.startswith('SUBSTANDARD'):
                    parts = line.split(maxsplit=1)
                    self.substandard = parts[1].strip()
                elif line.startswith('WORDCHARS'):
                    parts = line.split(maxsplit=1)
                    self.wordchars = parts[1].strip()
                elif line.startswith('CHECKSHARPS'):
                    self.checksharps = True

                line = self._get_next_not_empty_line(affix_file)

    def _parse_affix_flag(self, line: str, pattern: str, file: TextIOWrapper):
        pattern, flag, cross_product, count = self._parse_affix_header(line, pattern, file)

        afx = Afx()
        afx.type = pattern

        afx.cross_product = cross_product
        while count > 0:
            line = self._get_next_not_empty_line(file)
            if line is None:
                raise self._generate_syntax_error(pattern, file.tell())
            line = line.strip()

            pattern, flag2, stripping, affix, condition, morphological_fields \
                = self._parse_affix_body(line, pattern, file)

            if flag != flag2 or afx.type != pattern:
                raise self._generate_syntax_error(pattern, file.tell())
            afx.rules.append(Rule(stripping, affix, condition, morphological_fields))
            count = count - 1
        if count != 0:
            raise self._generate_syntax_error(pattern, file.tell())
        self.afx[flag] = afx

    def _parse_affix_header(self, line: str, pattern: str, file: TextIOWrapper) -> tuple:
        parts = line.split()
        if parts[0] != pattern or len(parts) != 4:
            raise self._generate_syntax_error(pattern, file.tell())

        option_name = parts[0]
        flag = parts[1]
        if parts[2] == 'Y':
            cross_product = True
        elif parts[2] == 'N':
            cross_product = False
        else:
            raise self._generate_syntax_error(pattern, file.tell())

        if not parts[3].isdigit():
            raise self._generate_syntax_error(pattern, file.tell())
        number = int(parts[3])

        return option_name, flag, cross_product, number

    def _parse_affix_body(self, line: str, pattern: str, file: TextIOWrapper) -> tuple:
        parts = line.split(maxsplit=6)
        if parts[0] != pattern or len(parts) < 4:
            raise self._generate_syntax_error(pattern, file.tell())

        option_name = parts[0]
        flag = parts[1]
        if self.flag.lower() == 'long' and len(flag) != 2 or self.flag.lower() != 'long' and len(flag) != 1:
            raise self._generate_syntax_error(pattern, file.tell())

        stripping = parts[2]
        affix = parts[3]
        condition = parts[4] if len(parts) > 4 else None
        morphological_fields = parts[5].split() if len(parts) > 5 else []

        return option_name, flag, stripping, affix, condition, morphological_fields

    def _parse_int_flag(self, line: str, pattern, file: TextIOWrapper):
        parts = line.split(maxsplit=1)
        if not parts[1].isdigit():
            raise self._generate_syntax_error(pattern, file.tell())
        return int(parts[1].strip())

    def _parse_flag(self, line: str, pattern: str, file: TextIOWrapper, array: list):
        count = self._parse_int_flag(line, pattern, file)
        while count > 0:
            line = self._get_next_not_empty_line(file)
            if line is None:
                raise self._generate_syntax_error(pattern, file.tell())
            line = line.strip()
            if not line.startswith(pattern):
                raise self._generate_syntax_error(pattern, file.tell())
            parts = line.split(maxsplit=1)
            array.append(parts[1].strip())
            count = count - 1
        if count != 0:
            raise self._generate_syntax_error(pattern, file.tell())

    @staticmethod
    def _get_next_not_empty_line(file_handler: TextIOWrapper) -> str or None:
        line = file_handler.readline()
        while line and line.isspace():
            line = file_handler.readline()
        if not line:
            return None
        return line

    @staticmethod
    def _generate_syntax_error(component: str, pos: int) -> SyntaxError:
        template = 'The file does not fit the format at parsing component \'{0}\' at pos {1:d}.'
        return SyntaxError(template.format(component, pos))
