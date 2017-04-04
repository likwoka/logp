#!/usr/bin/env python
"""
logpc -- a library of coroutines for parsing log files.

FILEPAT rules:
* matches everything
? matches any single character
[seq] matches any character in seq
[!seq] matches any character not in seq

PAT rules:
http://www.amk.ca/python/howto/regex/

See logp.py for the generator version of this.
"""
import os
import fnmatch
import gzip
import bz2
import zipfile
import re
import time

__VERSION__ = "0.2"
__AUTHOR__ = "Alex Li (likwoka@gmail.com)"

def coroutine(func):
    def start_cr(*args, **kwargs):
        cr = func(*args, **kwargs)
        cr.next()
        return cr
    return start_cr

def cfind(filepat, rootpaths, cr):
    for rootpath in rootpaths:
        for path, dirlist, filelist in os.walk(rootpath):
            for name in fnmatch.filter(filelist, filepat):
                cr.send(os.path.join(path, name))

@coroutine
def copen(cr):
    while 1:
        path = (yield)
        if path.endswith(".gz"):
            cr.send(gzip.open(path))
        elif path.endswith(".bz2"):
            cr.send(bz2.BZ2File(path))
        elif path.endswith(".zip"):
            zf = zipfile.ZipFile(path)
            names = zf.namelist()
            for name in names:
                cr.send(zf.open(name))
        else:
            cr.send(open(path))

@coroutine
def ccat(cr, just_data=False):
    if just_data:
        f = (yield)
        for line in f:
            cr.send(line)
    else:
        f = (yield)
        for linenum, line in enumerate(f):
            cr.send(f.name, linenum+1, line)

@coroutine
def cgrep(pat, cr, just_data=False):
    patc = re.compile(pat)
    if just_data:
        while 1:
            line = (yield)
            if patc.search(line):
                cr.send(line)
    else:
        while 1:
            fname, linenum, line = (yield)
            if patc.search(line):
                cr.send((fname, linenum, line))

@coroutine
def cprint():
    while 1:
        line_tuple = (yield)
        print "[%s] %" % (time.asctime(), "|".join(line_tuple))

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

    # ADM Server Message Log.
    ROOT_DIR = "GRO\\LogFiles\\ADMServer"
    FILEPAT  = "PETMSG*.txt"
    PAT      = "TSNA"
    servers = occ_adm + gcc_adm

    # Practice Account Audit Log.
#    ROOT_DIR = "GRO\\Logs\\RBCTradeService\\Orders"
#    FILEPAT = "*.log"
#    PAT = "PRAC1F3C362F"
#    servers = occ_adm + gcc_adm + occ_mt + gcc_mt

    rootpaths = ["\\\\" + os.path.join(s, ROOT_DIR) for s in servers]

    print "Finding pattern <%s> in files <%s> from folders" \
          " (and their subfolders):" % (PAT, FILEPAT)
    for rootpath in rootpaths:
        print rootpath
    print "[%s] Start searching...\n" % time.asctime()

    paths = cfind(FILEPAT, rootpaths, copen(cat(cgrep(PAT, cprint()))))

    print "\n[%s] Finished." % time.asctime()
