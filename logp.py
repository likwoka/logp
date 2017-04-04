#!/usr/bin/env python
"""
logp -- a library of generator functions for parsing log files.

FILEPAT rules:
* matches everything
? matches any single character
[seq] matches any character in seq
[!seq] matches any character not in seq

PAT rules:
http://www.amk.ca/python/howto/regex/

See logpc.py for the coroutine version of this.
"""
import os
import fnmatch
import gzip
import bz2
import zipfile
import re
import time

__VERSION__ = "0.5"
__AUTHOR__ = "Alex Li (likwoka@gmail.com)"


def gfind(filepat, rootpaths, onerror=None):
    """Return a generator of files that match pattern
    from root paths recursively.

    filepat -- a string of file pattern to match
    rootpaths -- a generator of root paths

    >>> fnames = gfind("*.txt", ["c:/",])
    >>> for name in fnames:
    >>>    print name
    """
    for rootpath in rootpaths:
        for path, dirlist, filelist in os.walk(rootpath, onerror=onerror):
            for name in fnmatch.filter(filelist, filepat):
                yield os.path.join(path, name)
                

def gopen(paths):
    """Return a generator of open files.

    paths -- a generator of file paths

    >>> files = gopen(paths)
    >>> for f in files:
    >>>     print f.readall()
    >>>     f.close()
    """
    for path in paths:
        if path.endswith(".gz"):
            yield gzip.open(path)
        elif path.endswith(".bz2"):
            yield bz2.BZ2File(path)
        elif path.endswith(".zip"):
            zf = zipfile.ZipFile(path)
            names = zf.namelist()
            for name in names:
                yield zf.open(name)
        else:
            yield open(path)

def gcat(files, data_only=False):
    """Return a generator of (filename, line number, line) of
    all files concatenated. If data_only is True, then
    return a generator of lines only.

    files -- a generator of opened files
    data_only -- true return just the line.  Default is false.

    >>> lines = gcat(files):
    >>> for line in lines:
    >>>     print line
    """
    for f in files:
        if data_only:
            for line in f:
                yield line
        else:
            for linenum, line in enumerate(f):
                yield (f.name, linenum+1, line)


def ggrep(pat, lines, data_only=False):
    """Return a generator of (filename, linenum, line)
    where the pattern matches the line.  If data_only
    is True, then return a generator of lines only.

    pat -- a string of regular expression pattern.
    lines -- a generator of lines to be matched.
    data_only -- true return just the line.  Default is false.

    >>> lines = ggrep("HELLO WORLD", lines):
    >>> for line in lines:
    >>>     print line
    """
    patc = re.compile(pat)
    if data_only:
        for line in lines:
            if patc.search(line):
                yield line
    else:
        for fname, linenum, line in lines:
            if patc.search(line):
                yield (fname, linenum, line)


def grep(servers, root_dir, filepat, pat):
    """Find and display the lines that match pattern.

    servers -- a list of string representing servers
    root_dir -- a string representing the root folder containing
                the files we would like to search
    filepat -- a string representing the file name pattern
    pat -- a string representing the pattern we are looking for
    """
    fmt = "%Y-%m-%d %I:%M:%S %p"
    def timestamp():
        return time.strftime(fmt)
    
    def error_handler(oserror):
        print "[%s] %s" % (timestamp(), oserror)

    print "Finding pattern <%s> in files <%s> from folders" \
          " (and their subfolders):" % (pat, filepat)
    rootpaths = ["\\\\" + os.path.join(s, root_dir) for s in servers]
    for rootpath in rootpaths:
        print rootpath
    print "[%s] Start searching..." % timestamp()

    paths = gfind(FILEPAT, rootpaths, onerror=error_handler)
    files = gopen(paths)
    lines = gcat(files)
    lines_found = ggrep(PAT, lines)

    cnt = 0
    for fname, linenum, line in lines_found:
        cnt += 1
        print "[%s] %s|%s|%s" % (timestamp(), fname, linenum, line.strip())

    print "[%s] %s entries found.  Finished." % (timestamp(), cnt)


if __name__ == "__main__":
    occ_adm = [
        "S3W06617",
        "S3W06618",
        "S3W06619",
        "S3W06620",]
    gcc_adm = [
        "S3W00875",
        "S3W00876",
        "S3W00877",
        "S3W00878",]
    occ_mt = [
        "S3W04798",
        "S3W04799",
        "SEW06146",
        "SEW06147",
        "SEW06148",
        "SEW06149",
        "SEW06150",
        "SEW06151",
        "SEW06152",
        "SEW06153",
        "SEW06154",
        "SEW06155",
        "SEW06156",
        "SEW06157",
        "SEW06158",]
    gcc_mt = [
        "S3W04800",
        "S3W04801",
        "SEW06159",
        "SEW06160",
        "SEW06161",
        "SEW06162",
        "SEW06163",
        "SEW06164",
        "SEW06165",
        "SEW06166",
        "SEW06167",
        "SEW06168",
        "SEW06169",
        "SEW06170",
        "SEW06171",]

    # ADM Server PETAPI Error Log.
    ROOT_DIR = "GRO\\LogFiles\\ADMServer"
    FILEPAT  = "PETERR????2009.txt"
    PAT      = "GetMessage"
    servers = occ_adm + gcc_adm

    ## ADM Server Message Log.
    #ROOT_DIR = "GRO\\LogFiles\\ADMServer"
    #FILEPAT  = "PETMSG*.txt"
    #PAT      = "TSNA"
    #servers = occ_adm + gcc_adm

    ## Search Practice Account audit log with a particular account.
    #ROOT_DIR = "GRO\\Logs\\RBCTradeService\\Orders"
    #FILEPAT = "*.log"
    #PAT = "PRAC1F3C362F"
    #servers = occ_adm + gcc_adm + occ_mt + gcc_mt

    grep(servers, ROOT_DIR, FILEPAT, PAT)
