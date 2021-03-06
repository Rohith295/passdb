#!/usr/bin/python
"""
Securely retrieve secret and copy to clipboard (needs xerox module)
Run directly to use the cli, or import the Passdb class.
"""
import os
import imp
import yaml
import getpass
import gnupg
import urllib2
import argparse


class Passdb(object):
    """
    Provides simple access to the secret gpg file
    e.g. :

    >>> from passdb import Passdb
    >>> p = Passdb()
    >>> p.get('root')
    [u'blahblah']
    >>> p.get('console')
    [u'balh1', u'blah2', u'blah3']
    >>>

    """
    _home = os.environ['HOME']
    _gpghome = '%s/.gnupg/' % _home
    _config_path = os.path.expanduser('~/.passdb.cfg')
    _passdbfile = os.path.expanduser('~/.passdb.gpg')

    def log(self, msg):
        if self.debug:
            print "DEBUG: %s" % msg

    def __init__(self, passphrase=None, debug=False):
        self.passphrase = passphrase
        self.debug = debug
        self.load_config()
        self.log("Using configuration file %s" % self._config_path)

    def load_config(self):
        try:
            config = imp.load_source('config', self._config_path)
            self._path = config.path
        except IOError:
            self._path = raw_input("Please enter passdb source (http/file): ")
            with open(self._config_path, 'w') as config:
                config.write('path="{0}"'.format(self._path))

    def update(self):
        passdbfile = urllib2.urlopen(self._path)
        output = open(self._passdbfile, 'wb')
        output.write(passdbfile.read())
        output.close()

    def get(self, key):
        gpg = gnupg.GPG(gnupghome=self._gpghome)

        try:
            with open(self._passdbfile, 'rb') as f:
                crypt = gpg.decrypt_file(f)
                if crypt.status == 'need passphrase':
                    if not self.passphrase:
                        self.passphrase = getpass.getpass('Passphrase needed: ')
                    with open(self._passdbfile, 'rb') as f:
                        crypt = gpg.decrypt_file(f, passphrase=self.passphrase)
        except IOError:
            self.update()
            self.get(key)

        y = yaml.load(crypt.data)
        try:
            return y[key]
        except KeyError:
            return
        except TypeError:
            raise ValueError("Could not get valid passdb data")


def main():
    parser = argparse.ArgumentParser(description="Securely retrieve password \
                                                 and copy to clipboard")
    parser.add_argument("-u", "--update", action='store_true',
                        help="Update local caceh with remote passwords")
    parser.add_argument("-d", "--display", action='store_true',
                        help="Dispaly on screen")
    parser.add_argument("type", nargs="?", help="console or root")

    args = parser.parse_args()
    if not args.type and not args.update:
        parser.print_help()
        exit(1)

    passdb = Passdb()

    if args.update:
        passdb.update()

    elif args.type:
        if args.display:
            clipboard = False
        else:
            try:
                import xerox
                clipboard = True
            except ImportError:
                clipboard = False

        passwd = passdb.get(args.type)
        if isinstance(passwd, list):
            if clipboard:
                xerox.copy(passwd[0])
            for pw in passwd:
                print pw
        else:
            if clipboard:
                xerox.copy(passwd)
            print passwd

if __name__ == '__main__':
    main()
