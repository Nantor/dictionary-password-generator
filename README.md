# Dictonary passwort generator

```
usage: wordlist.py [-h] [-b] [-c COUNT] [-f] [-g MAX] [-l MIN] [-n]
                   [-o OUTPUT] [-p PATH] [-r REGEX] [-s SEPARATOR] [-t TOSSES]
                   DIC

The programme will generate a random password based on words. The advantage
over standard random generated password is, that it easy to remember and in
general harder to crack.

positional arguments:
  DIC                   the name of the dictionary or word list that should be
                        used in the given directory

optional arguments:
  -h, --help            show this help message and exit
  -b, --basic           use only the base words, without any affixes
  -c COUNT, --count COUNT
                        number of words in the passwords, default is 4
  -f, --force           force to use dictionary files, if a word list file
                        exist it will overwritten
  -g MAX, --max MAX     the max. length for a chosen word, -1 for no limit,
                        default is -1
  -l MIN, --min MIN     the min. length for a chosen word, default is 0
  -n, --negate          invert the regular expression filter
  -o OUTPUT, --output OUTPUT
                        specify a file for write in, instead of terminal
                        printout
  -p PATH, --path PATH  path to dictionary files and/or word list file,
                        default is the current directory
  -r REGEX, --regex REGEX
                        filter the possible words with a regular expression
  -s SEPARATOR, --separator SEPARATOR
                        is the string between the words, default is a single
                        space " "
  -t TOSSES, --tosses TOSSES
                        number of passwords that should generated, default is
                        3

The name of the DIC parameter specifies the filename without the extension for
the dictionary or word list. That means if you want to use the en-GB.aff and
en-GB.dic to generate a password. You type for the DIC parameter "en-GB". This
also applies to a corresponding word list file (.wrd). If both types exist, a
word list file (DIC.wrd) and dictionary files (DIC.aff, DIC.dic), the word
file will be used.
```
