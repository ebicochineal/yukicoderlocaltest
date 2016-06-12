#! /usr/bin/env python3
import os
import sys
import time
import datetime
import zipfile
import urllib
import http
import http.cookiejar
from subprocess import Popen, PIPE

gpath = os.path.dirname(__file__) + "/"
gtimeout = 2
gcom = {}
gcls = ""

def setenv():
    global gcls
    if "win"in sys.platform:
        gcom["py"] = ["C:/Windows/py.exe"]
        gcom["go"] = ["go", "run"]
        gcls = "cls"
    else:
        gcom["go"] = ["go", "run"]
        gcls = "clear"

class TestCaseZip():
    def __init__(self, testnum):
        self.path = gpath + "testcase/" + tozipname(testnum)
        self.filelist = []
        with zipfile.ZipFile(self.path, 'r') as z:
            self.filelist = sorted([x.split("test_in/")[1] for x in z.namelist() if "test_in/" in x])
    def read(self, path):
        with zipfile.ZipFile(self.path, 'r') as z:
            r = z.read(path).decode("utf-8")
            return r

class TestCase():
    def __init__(self, testnum, ext, path):
        self.com = (gcom[ext] if ext in gcom else []) + [path]
        self.zip = TestCaseZip(testnum)
        self.result = {}
    def tests(self):
        print(" ".join(self.com))
        for i in self.zip.filelist:
            self.result[i] = self.run(i)
            r = self.result[i]
            print(self.stcolor(r[0]), r[1], fixedlen(i, 14))
    def run(self, filename):
        data_in = self.zip.read("test_in/" + filename)
        data_out = self.zip.read("test_out/" + filename)
        data_in_encode = data_in.encode('utf-8')
        start = time.time()
        p = Popen(self.com, stdout=PIPE, stdin=PIPE, stderr=PIPE)
        try:
            outputs = p.communicate(input=data_in_encode, timeout=gtimeout)
            executiontime = time.time() - start
            out = outputs[0].decode("utf-8").replace("\r\n", "\n")
            err = outputs[1].decode("utf-8").replace("\r\n", "\n")
            if out == data_out:
                return ("AC", "%.3f"%(executiontime), out)
            elif err == "":
                return ("WA", "-----", out)
            else:
                return ("RE", "-----", err)
        except:
            p.kill()
            p.wait()
            return ("TLE", "-----", "")
    def stcolor(self, status):
        s = fixedlen(status, 3)
        if status == "AC":
            return "\033[42;30m" + s + "\033[0m"
        else:
            return "\033[43;30m" + s + "\033[0m"
    def view(self):
        n = 0
        m = len(self.zip.filelist)
        timer = time.time()
        while 1:
            i = self.zip.filelist[n]
            r = self.result[i]
            data_in = self.zip.read("test_in/" + i)
            data_out = self.zip.read("test_out/" + i)
            g = os.get_terminal_size()
            w = g.columns // 3 - 1
            h = g.lines - 6
            
            lin = strlist(fixedlen(data_in, 2000), w, h)
            lout = strlist(fixedlen(data_out, 2000), w, h)
            lprg = strlist(fixedlen(r[2], 2000), w, h)
            
            os.system(gcls)
            print(self.stcolor(r[0]), r[1])
            print(fixedlen("data_in", w+1) + fixedlen("data_out", w+1) + fixedlen("program_output", w))
            
            for y in range(h):
                print(lin[y] + '|' + lout[y] + '|' + lprg[y])
            print("-"*(g.columns-1))
            print(fixedlen("Next : [ENTER]     Quit : [Q]", w*2+2) + fixedlen(i, 14))
            while 1:
                s = input()
                if s == "" and time.time() - timer > 0.4:
                    timer = time.time()
                    n += 1
                    if n >= m : n = 0
                    break
                if s == "q" : quit()

def fixedlen(s, n):
    if n <= 3:
        s = s[:n]
    else:
        if len(s) > n:
            s = s[:n-3] + "..."
    return ("{: <" + str(n) + "}").format(s)

def strlist(s, w, h):
    r = []
    for i in s.split("\n"):
        if len(i) > w:
            for j in range(len(i)//w):
                r += [i[j*w:j*w+w]]
            if len(i)%w:
                r += [i[(len(i)//w)*w:]]
        else:
            r += [i]
    if len(r) < h : r += [""] * (h-len(r))
    if len(r) > h : r = r[:h]
    for i in range(h):
        r[i] = r[i] + " " * (w-len(r[i]))
    return r

def create_cookiefile(session):
    try:
        expires = (datetime.datetime.today() + datetime.timedelta(days=30)).strftime("%Y-%m-%d %H:%M:%S")
        with open(gpath + "cookie.txt", "w") as f:
            w = '#LWP-Cookies-2.0\nSet-Cookie3: REVEL_SESSION="%s"; path="/"; domain="yukicoder.me"; path_spec; expires="%s"; version=0'%(session, expires)
            f.write(w)
        return True
    except:
        return False

def testcase_download(testnum):
    try:
        cj = http.cookiejar.LWPCookieJar()
        cj.load(gpath + "cookie.txt")
        opener = urllib.request.build_opener(urllib.request.HTTPCookieProcessor(cj))
        url = "http://yukicoder.me/problems/no/" + testnum + "/testcase.zip"
        with opener.open(url) as r:
            with open(gpath + "testcase/" + tozipname(testnum), "wb") as f:
                f.write(r.read())
        return True
    except:
        return False
        
def tozipname(testnum):
    if len(testnum) > 4:
        testnum = testnum[-4:]
    return "No{:0>4}.zip".format(testnum)

def main():
    os.system(gcls)
    
    if not os.path.exists(gpath + "cookie.txt"):
        session = input("REVEL_SESSION = ")
        create_cookiefile(session)
    tpp = input("Test Program PATH = ").replace('"', '')
    opd = os.path.dirname(tpp)
    testpath = (os.getcwd() + tpp if opd == "" else tpp).replace("\\", "/")
    tpath = tpp
    testnum = os.path.basename(tpp).split(".")[0]
    testext = os.path.basename(tpp).split(".")[1]
    
    if os.path.exists(gpath + "cookie.txt"):
        if not os.path.exists(gpath + "testcase"):
            os.mkdir(gpath + "testcase")
        if not os.path.exists(gpath + "testcase/" + tozipname(testnum)):
            print("Test Case  Download...")
            if testcase_download(testnum):
                print("Download Completed")
            else:
                print("Download Failed")
        if os.path.exists(gpath + "testcase/" + tozipname(testnum)):
            os.system(gcls)
            t = TestCase(testnum, testext, testpath)
            t.tests()
            print("TestCaseView : [ENTER]     Quit : [Q]")
            while 1:
                s = input()
                if s == "" : t.view()
                if s == "q" : quit()
    else:
        pass

if __name__ == '__main__':
    setenv()
    main()



