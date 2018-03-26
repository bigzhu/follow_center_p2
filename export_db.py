# !/usr/bin/env python
# encoding=utf-8
import sys
sys.path.append("../lib_p_bz")

import sys
reload(sys)
sys.setdefaultencoding('utf-8')
import time_bz
import os

import ConfigParser
config = ConfigParser.ConfigParser()
with open('conf/db.ini', 'r') as cfg_file:
    config.readfp(cfg_file)
    host = config.get('db', 'host')
    port = config.get('db', 'port')
    db_name = config.get('db', 'db_name')
    user = config.get('db', 'user')
    password = config.get('db', 'password')


def main():
    now_day = time_bz.getYearMonthDay()
    file_name = 'db_bak/%s.%s.dump' % (db_name, now_day)
    command = '''
    PGPASSWORD="%s" pg_dump -T 'tumblr_blog' -T 'instagram_media' -T 'github_message' -T 'twitter_message' -h %s -p %s -U %s -F c -b -v -f %s %s
    ''' % (password, host, port, user, file_name, db_name)

    print command
    os.system(command)

if __name__ == '__main__':
    main()
