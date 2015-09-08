#!/usr/bin/env python
#
# languages.py - Read language names from several sources and save them for E:S
#
#    Copyright (C) 2012 Rodrigo Silva (MestreLion) <linux@rodrigosilva.com>
#
#    This program is free software: you can redistribute it and/or modify
#    it under the terms of the GNU General Public License as published by
#    the Free Software Foundation, either version 3 of the License, or
#    (at your option) any later version.
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU General Public License for more details.
#
#    You should have received a copy of the GNU General Public License
#    along with this program. See <http://www.gnu.org/licenses/gpl.html>

'''Read language names from several sources and save them for E:S.

If run as a script, tries to read language names (in both English and
Native language) from several Locale info sources, like babel or PyICU. Then
merges this info with E:S' translation PO files headers, and save it by
updating a JSON file in data/languages.dat, which is later read by Options
Screen of E:S to present each one of the available languages in their own
native language.

This module is importable as well. In this case it only sets game's directory
and imports code.g. You can use the Locale class for all of its features.

In either case, modules 'icu', 'babel' and 'polib' are optional but highly
recommended.
'''

import sys
import os.path as osp
import json
import argparse

if __name__ == '__main__':
    myname = sys.argv[0]
    mydir  = osp.dirname(myname)
    esdir  = osp.abspath(osp.join(osp.dirname(myname), '..'))
    sys.path.insert(0,esdir)
else:
    myname = __file__
    mydir  = osp.dirname(myname)
    esdir  = osp.abspath(osp.join(osp.dirname(myname), '..'))
    sys.path.append(esdir)

try:
    import code.g as g
except ImportError:
    sys.exit("Could not find game's code.g")


class Locale(object):
    """Wrapper for a Locale object in various sources, like babel and pyicu"""

    @staticmethod
    def getAvailableSources():
        """Return a list of all available Locale info sources.

        First item is by definition the default source used when none is given.
        Last item is by definition the game's PO headers
        """
        return ['icu', 'babel', 'pofiles']

    @staticmethod
    def getGameTranslations():
        """Return a list of available game translations (both ll and ll_CC)

        Generated list is suitable to be used as a filter to
        getLanguages() method. Do not confuse with the languages
        data dict that is generated by this module.

        This function is just here as a reference, but I won't use this
        at all. You may even delete it, I truly don't care.
        """
        game_translations = set()
        for language in g.available_languages():
            game_translations.add(language)
            if "_" in language:
                game_translations.add(language.split("_",1)[0])
        return dict(game_translations)

    @classmethod
    def getLanguages(cls, locales=None, tupletype=True, source=None):
        """Return a languages dict of Locale info from a given source

        locales input is a list of locale codes to be selected among
        the available ones. Non-available codes are silently ignored.
        If locales is omitted or empty, output will have all available
        locales.

        Output languages dict has locale codes as keys, and either a
        2-tuple or a dict(English, native) as values.

        Values represent the Display Name of the language expressed
        in English and in native language for each locale code
        """
        if locales:
            locales = set(locales) & set(cls(source=source).getAvailableLocales())
        else:
            locales = cls(source=source).getAvailableLocales()

        output = {}
        for code in locales:
            locale = cls(code=code, source=source)
            if locale:
                english = locale.english_name
                native = locale.native_name
                if not (english or native): continue
                if native: native = native.title()
                if tupletype:
                    output[code] = (english, native)
                else:
                    output[code] = dict(english=english, native=native)

        return output

    @staticmethod
    def saveLanguagesData(languages, filename):
        """Docstring... for *this*? You gotta be kidding me...

        Ok... there it goes: Save a languages dict, like the one
        generated by getLanguages() method, to a JSON data file
        Happy now?
        """
        with open(filename, 'w') as fd:
            json.dump(languages, fd, indent=0, separators=(',', ': '),
                      sort_keys=True)
            fd.write('\n') # add EOF newline

    @staticmethod
    def loadLanguagesData(filename):
        """Again? Can't you read code?

        Ok, ok... Load and return a language dict from a JSON data file
        """
        with open(filename) as fd:
            return json.load(fd)

    @classmethod
    def dumpPythonCode(cls, languages=None, tupletype=True, align=True, fd=None):
        """Print languages dict as Python code, roughly the same as %r.

        If input languages dict is not given, build one with all
        available locales from the default source, using Tuple or
        Dict as values based on tuple boolean argument. If languages
        is not empty, its Tuple/Dict inner format is auto-detected
        and tupletype argument is ignored.

        With align, output code will be aligned with spaces for
        code keys and English and native values.

        fd is a file descriptor opened for reading. If none is
        given, prints to standard output
        """

        if not languages:
            # languages was not given. Build a full one in chosen format
            languages = cls.getLanguages(tupletype=tupletype)

        # Choose file descriptor
        if fd:
            #User-provided
            cls._dumpPyhonCode_real(languages, align, fd)
        else:
            #stdout
            import tempfile
            fd = tempfile.TemporaryFile('w+r')
            cls._dumpPyhonCode_real(languages, align, fd)
            fd.seek(0)
            print(fd.read())
            fd.close()

    @staticmethod
    def _dumpPyhonCode_real(languages, align, fd):
        # Do the hard work

        # Auto-detect languages format
        istuple = not isinstance(languages[languages.keys()[0]], dict)

        # Find paddings for code and english
        if align:
            padc = 3+max([len(padc) for padc in languages.keys()])
            pade = 3+max([len(languages[pade][0 if istuple else 'english'])
                                                for pade in languages])
        # Write header
        fd.write("# Generated by {0}\n".format(osp.relpath(myname,esdir)))

        # Loop dict entries
        fd.write("languages = {\n")
        for locale in sorted(languages):
            if align:
                key = "%-*r: " % (padc, locale)
                if istuple:
                    val = "(%-*r, %r)" % (pade,
                                          languages[locale][0],
                                          languages[locale][1])
                else:
                    val = "{'english':%-*r,'native':%r}" % (
                            pade,
                            languages[locale]['english'],
                            languages[locale]['native'])
                fd.write(key + val + ",\n")
            else:
                # So much easier...
                fd.write("%r,\n" % languages[locale])

        # Write footer
        fd.write("}\n")

    def __init__(self, code=None, source=None):
        """Initialize a Locale of the given code from the given source

        If source is blank or omitted, the default one from by
        getAvailableSources() is used.

        code must be string with ll or ll_CC format. If blank or
        omitted, only getAvailableLocales() method will work,
        all other attributes will be None.
        """

        # Attributes
        self.source       = source
        self.code         = code
        self.english_name = None
        self.native_name  = None

        # Handle source
        if not self.source: self.source = self.getAvailableSources()[0]
        if self.source not in self.getAvailableSources():
            raise ValueError("{0} is not a valid source."
                             " Available sources are: {1}".format(
                                source, ", ".join(self.getAvailableSources())))
        self.source = self.source.lower()

        # Override default attributes methods according to the given source

        if self.source == 'babel':
            try:
                import babel
            except ImportError:
                raise ImportError("'{0}' requires babel module".format(source))

            self.getAvailableLocales = babel.localedata.list
            if self.code:
                locale = babel.Locale.parse(self.code)
                self.english_name = locale.english_name
                self.native_name  = locale.get_display_name()

        if self.source == 'icu':
            try:
                import icu # new module name, 1.0 onwards
            except ImportError:
                try:
                    import PyICU as icu # old module name, up to 0.9
                except ImportError:
                    raise ImportError("'{0}' requires icu"
                                      " or PyICU module".format(source))

            self.getAvailableLocales = icu.Locale.getAvailableLocales().keys

            if self.code:
                locale = icu.Locale(self.code)
                self.english_name = locale.getDisplayName()
                self.native_name  = locale.getDisplayName(locale)

        if self.source == 'pofiles':
            import code.polib as polib
            import os
            self.getAvailableLocales = \
                lambda: [osp.splitext(filename)[0].split("_", 1)[1]
                         for filename in os.listdir(g.data_dir)
                            if filename.split("_", 1)[0] == "messages" and
                                osp.splitext(filename)[1] == ".po" and
                                osp.isfile(osp.join(g.data_dir, filename))]

            if self.code:
                po = polib.pofile(osp.join(g.data_dir,
                                           "messages_{0}.po".format(self.code)))
                self.english_name = po.metadata['Language-Name']
                self.native_name  = po.metadata['Language-Native-Name']

    def getAvailableLocales(self):
        """Return a list of all available locale codes for the given source"""
        return []


def main(argv=None):
    argparse.ArgumentParser(description=__doc__).parse_args(argv)

    # Get locale data from the first source that works
    languages = {}
    sources = Locale.getAvailableSources()
    for source in sources[:-1]: # we load 'pofiles' later
        try:
            languages = Locale.getLanguages(source=source)
            break
        except ImportError:
            continue

    datafile = osp.join(g.data_dir, 'languages.dat')

    try:
        # load current data file and merge it
        languages.update(Locale.loadLanguagesData(datafile))
    except IOError:
        pass

    # also merge with translations file
    languages.update(Locale.getLanguages(source=sources[-1]))

    try:
        # Save updated data file
        Locale.saveLanguagesData(languages, datafile)

        # Show python code
        #Locale.dumpPythonCode(languages) # Ok, it works, no need to show off

        print "{0:d} languages saved to {1}".format(len(languages),
                                                    osp.relpath(datafile))
    except IOError as reason:
        sys.stderr.write("Could not save languages data file:"
                         " {0}\n".format(reason))


if __name__ == '__main__':
    try:
        sys.exit(main(sys.argv[1:]))
    except Exception as e:
        print e
        sys.exit(1)
    except KeyboardInterrupt:
        pass
