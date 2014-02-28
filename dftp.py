#!/usr/bin/env python
# -*- coding: utf-8 -*-

'''
File: ftputil.py
Author: tdoly
Description: ftp util
'''
import os
import sys
import socket
import re
from ftplib import FTP

import pdb

reload(sys)
sys.setdefaultencoding('gbk')

class DFTP(object):
    def __init__(self, host, username, passwd, remoteDir, port=21):
        '''
        the args init
        '''
        self.host = host
        self.username = username
        self.passwd = passwd
        self.remoteDir = remoteDir
        self.port = port
        self.ftp = FTP()
        self.remotepathsep = '/'
        self.file_dict = {}
        # self.ftp.set_debuglevel(2)

    def __del__(self):
        self.ftp.close()
        # self.ftp.set_debuglevle(0)

    def _dir(self, path):
        '''
        call dir() on path,return list of lines
        '''
        dir_list = []
        try:
            self.ftp.dir(path, dir_list.append)
        except Exception:
            raise FTPException('Access denied for path %s' % path)
        return dir_list

    def _cleanpath(self, path):
        """
        Clean up path - remove repeated and trailing separators. 
        """
        slashes = self.remotepathsep*2
        while slashes in path:
            path = path.replace(slashes,self.remotepathsep)
        if path.endswith(self.remotepathsep):
            path = path[:-1]
        return path

    def parsedir(self, path):
        '''
        parse the lines returned by the dir()
        '''
        dirlines = self._dir(path)
        dirdict = parse_unix(dirlines)
        return dirdict

    def login(self):
        '''
        ftp login
        '''
        ftp = self.ftp
        try:
            timeout = 300
            socket.setdefaulttimeout(timeout)
            ftp.set_pasv(True)
            ftp.connect(self.host, self.port)
            print 'connect success...'
            ftp.login(self.username, self.passwd)
            print 'login success...'
            debug_print(ftp.getwelcome())
        except Exception:
            raise FTPException('connect or login ERROR')
        try:
            ftp.cwd(self.remoteDir)
        except Exception:
            raise FTPException('the dir is ERROR')

    def downloadFile(self, localFile, remoteFile):
        '''
        download file
        '''
        if len(remoteFile) < 1:
            raise FTPException('the file [%s]is not found...' % remoteFile)
        if os.path.exists(localFile):
            '''if the file exists, don't download'''
            #raise FTPException('the file [%s] is exists!' % localFile)
            debug_print("*************the file [%s] is exists!********************" % localFile)
            return
        dir_file = os.path.split(localFile)
        if not os.path.exists(dir_file[0]):
            os.makedirs(dir_file[0])

        debug_print('>>>>>download file: %s' % remoteFile)
        bufsize = 1024
        fileHandler = open(localFile, 'wb')
        self.ftp.retrbinary('RETR %s' % remoteFile, fileHandler.write, bufsize) # download file
        fileHandler.close()
        debug_print('>>>>>100%>>>>>')

    def downloadFiles(self, localDir='./', remoteDir='./'):
        '''
        download files
        '''
        try:
            self.ftp.cwd(remoteDir)
        except:
            raise FTPException('Not Exists %s' % remoteDir)
        #debug_print('change dir to %s' % self.ftp.pwd())

        filenames = self.rnlst(remoteDir)

        for item in filenames:
            localDir = self._cleanpath(localDir)
            local = localDir + item
            dir_file = os.path.split(local)
            if not os.path.exists(dir_file[0]):
                os.makedirs(dir_file[0])
            self.downloadFile(local, item)

        self.ftp.cwd('..')
        #debug_print('go top dir %s' % self.ftp.pwd())

    def _rnlst(self, path, file_list):
        '''
        Return a list of filenames under path.
        '''
        if path is None:
            path = self.remoteDir
        path = self._cleanpath(path)
        dirdict = self.parsedir(path)
        trycwds = dirdict.get('trycwds', [])
        names = dirdict.get('names', [])

        for trycwd, name in zip(trycwds, names):
            if not name:
                continue
            try:
                if trycwd:
                    filedir = self.remotepathsep.join([path, name])
                    self._rnlst(filedir, file_list)
                else:
                    filepath = self.remotepathsep.join([path, name])
                    file_list.append(filepath)
            except:
                 raise FTPException('generate filelist error')
        return file_list

    def rnlst(self, path=None):
        file_list = []
        return self._rnlst(path, file_list)

    def rndict(self, path=None):
        '''
        Return a dict of filenames under path.
        '''
        if path is None:
            path = self.remoteDir
        path = self._cleanpath(path)
        dirdict = self.parsedir(path)
        trycwds = dirdict.get('trycwds', [])
        names = dirdict.get('names', [])

        for trycwd, name in zip(trycwds, names):
            if not name:
                continue
            try:
                if trycwd:
                    filedir = self.remotepathsep.join([path, name+'/'])
                    self.setpath(name, filedir)
                    self.rndict(filedir)
                else:
                    filepath = self.remotepathsep.join([path, name])
                    self.setpath(name, filepath)
            except:
                 raise FTPException('generate filedict error')
        return self.file_dict

    def setpath(self, name, path):
        '''set the path in file_dict'''
        values = []
        if self.file_dict.has_key(name):
            values = self.file_dict[name]
        values.append(path)
        self.file_dict[name] = values


class FTPException(Exception):
    pass

def debug_print(s):
    print s

def parse_unix(dirlines,startindex=0):
    """
    Parse the lines returned by ftplib.FTP.dir(), when called
    on a UNIX ftp server. May not work for all servers, but it
    works for the ones I need to connect to.
    """

    dirlines = dirlines[startindex:]
    if not dirlines:
        return dict()
    pattern = re.compile('(.)(.*?)\s+(.*?)\s+(.*?)\s+(.*?)\s+'
                         '(.*?)\s+(.*?\s+.*?\s+.*?)\s+(.*)')

    fields = 'trycwds tryretrs inodes users groups sizes dates names'.split()

    getmatches = lambda s:pattern.search(s)
    matches = filter(getmatches, dirlines)

    getfields = lambda s:pattern.findall(s)[0]
    lists = zip(*map(getfields, matches))
    # change the '-','d','l' values to booleans, where names referring
    # to directories get True, and others get False.
    lists[0] = ['d' == s for s in lists[0]]
    assert len(lists) == len(fields)
    return dict(zip(fields, lists))

def find_keyword(filedict, keyword):
    '''found the keyword and return the file path'''
    result_list = []
    if filedict:
        for fl in filedict.keys():
            if keyword in fl:
                d_value = filedict[fl]
                result_list.extend(d_value)
    return result_list

def download(local, filelist, dftp):
    for fl in filelist:
        if str(fl).endswith('/'):
            dftp.downloadFiles(local, fl)
        else:
            dftp.downloadFile(local+str(fl), fl)

def main():

    host = 'localhost'
    username = 'ftp'
    passwd = 'tdoly'
    #port = '21'
    dir_local = '/home/dong/Desktop/ftp/'
    dir_remote = '/Algorithm-Implementations'
    #dir_remote = '/'

    dftp = DFTP(host, username, passwd, dir_remote)
    dftp.login()

    keyword = 'tdoly'
    fdict = dftp.rndict(dir_remote)
    k_result = find_keyword(fdict, keyword)
    download(dir_local, k_result, dftp)

    #print dftp.rndict('/Algorithm-Implementations').get('tags')
    #print dftp.rnlst('/Algorithm-Implementations/String_to_int/')
    #print dftp.parsedir('/')
    #dftp.downloadFile(dir_local+'test.py', '/Algorithm-Implementations/String_to_int/tags')
    #dftp.downloadFiles(dir_local, '/Algorithm-Implementations/String_to_int/')


if __name__ == '__main__':
    main()
