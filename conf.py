#!/usr/bin/env python
# -*- coding: utf-8 -*-
import configparser
config = configparser.ConfigParser()
config.read('conf/config.ini')
cookie_secret = config.get('tornado', 'cookie_secret')
if __name__ == '__main__':
    import doctest
    doctest.testmod(verbose=False, optionflags=doctest.ELLIPSIS)
