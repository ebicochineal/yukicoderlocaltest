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

g_crdir = os.path.dirname(__file__) + "/"
g_zipdir = "testcase/"
g_builddir = "build/"
g_in = "test_in/"
g_out = "test_out/"
# g_compilerpath = "C:/MinGW/bin"
g_timeout = 3
g_cmdc = {}
g_cmdi = {}
g_cls = ""

def setenv():
    global g_cls
    # os.environ["PATH"] = os.environ["PATH"] + ";" + g_compilerpath
    if "win"in sys.platform:
        g_cmdi["py"] = ["C:/Windows/py.exe", "[i]"]
        # g_cmdi["go"] = ["go", "run", "[i]"]
        g_cmdc["go"] = ["go", "build", "-o", "[o]", "[i]"]
        g_cmdc["c"] = ["gcc", "-o", "[o]", "[i]"]
        g_cmdc["cpp"] = ["g++", "-o", "[o]", "[i]"]
        g_cmdc["cs"] = ["csc", "/out:[o]", "[i]"]
        g_cls = "cls"
    else:
        # g_cmdi["go"] = ["go", "run", "[i]"]
        g_cmdc["go"] = ["go", "build", "-o", "[o]", "[i]"]
        g_cmdc["c"] = ["gcc", "-o", "[o]", "[i]"]
        g_cmdc["cpp"] = ["g++", "-o", "[o]", "[i]"]
        g_cmdc["cs"] = ["mcs", "/out:[o]", "[i]"]
        g_cls = "clear"

class TestCase():
    def __init__(self, num, ext, progpath):
        cmd = g_cmdi[ext] if ext in g_cmdi else ["[i]"]
        self.cmd = raplace_cmd(cmd, progpath)
        self.data = {}
        self.zippath = g_crdir + g_zipdir + num_to_zipname(num)
        self.filelist = []
        with zipfile.ZipFile(self.zippath, 'r') as z:
            self.filelist = sorted([x.split(g_in)[1] for x in z.namelist() if g_in in x])
    def tests(self):
        for i in self.filelist:
            data_in = self.read(g_in + i)
            data_out = self.read(g_out + i)
            self.data[i] = self.run(i, data_in, data_out)
            yield (self.data[i][0], self.data[i][1], i)
    def run(self, filename, data_in, data_out):
        data_in_encode = data_in.encode('utf-8')
        din2k = lenfixed(data_in, 2000)
        dout2k = lenfixed(data_out, 2000)
        result = []
        start = time.time()
        p = Popen(self.cmd, stdout=PIPE, stdin=PIPE, stderr=PIPE)
        try:
            outerr = p.communicate(input=data_in_encode, timeout=g_timeout)
            etime = "%.3f"%(time.time() - start)
            out = outerr[0].decode("utf-8").replace("\r\n", "\n")
            err = outerr[1].decode("utf-8").replace("\r\n", "\n")
            if out == data_out:
                result = [green("AC "), etime, din2k, dout2k, out]
            elif err == "":
                result = [yellow("WA "), "-----", din2k, dout2k, out]
            else:
                result = [yellow("RE "), "-----", din2k, dout2k, err]
        except:
            p.kill()
            p.wait()
            result = [yellow("TLE"), "-----", din2k, dout2k, ""]
        return result
    def read(self, path):
        with zipfile.ZipFile(self.zippath, 'r') as z:
            return z.read(path).decode("utf-8")

def green(s):
    return "\033[42;30m" + s + "\033[0m"
    
def yellow(s):
    return "\033[43;30m" + s + "\033[0m"

def lenfixed(s, n):
    if n <= 3:
        s = s[:n]
    elif len(s) > n:
        s = s[:n-3] + "..."
    return ("{: <" + str(n) + "}").format(s)

def tolist(s, w, h):
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

def num_to_zipname(num):
    if len(num) > 4:
        num = num[-4:]
    return "No{:0>4}.zip".format(num)

def raplace_cmd(cmd, progpath):
    r = []
    for i in cmd:
        i = i.replace("[i]", progpath)
        i = i.replace("[o]", g_crdir + g_builddir + "test.exe")
        r += [i]
    return r

def create_cookiefile(session):
    try:
        expires = (datetime.datetime.today() + datetime.timedelta(days=30)).strftime("%Y-%m-%d %H:%M:%S")
        with open(g_crdir + "cookie.txt", "w") as f:
            w = '#LWP-Cookies-2.0\nSet-Cookie3: REVEL_SESSION="%s"; path="/"; domain="yukicoder.me"; path_spec; expires="%s"; version=0'%(session, expires)
            f.write(w)
        return True
    except:
        return False

def testcase_download(num):
    try:
        cj = http.cookiejar.LWPCookieJar()
        cj.load(g_crdir + "cookie.txt")
        opener = urllib.request.build_opener(urllib.request.HTTPCookieProcessor(cj))
        url = "http://yukicoder.me/problems/no/" + num + "/testcase.zip"
        with opener.open(url) as r:
            with open(g_crdir + g_zipdir + num_to_zipname(num), "wb") as f:
                f.write(r.read())
        return True
    except:
        return False

def testcase_test(testcase):
    print("Run >>>", " ".join(testcase.cmd))
    for i, j, k in testcase.tests():
        print(i, j, k)
    rm = g_crdir + g_builddir + "test.exe"
    if os.path.exists(rm):
        print("Remove >>>", g_builddir + "test.exe")
        os.remove(rm)
    print("TestCase View : [ENTER]     Quit : [Q]")

def testcase_view(testcase):
    n = 0
    while 1:
        i = testcase.filelist[n]
        tw, th = os.get_terminal_size()
        w = tw // 3 - 1
        h = th - 6
        lin = tolist(testcase.data[i][2], w, h)
        lout = tolist(testcase.data[i][3], w, h)
        lprg = tolist(testcase.data[i][4], w, h)
        os.system(g_cls)
        print(testcase.data[i][0], testcase.data[i][1])
        print(" ".join([lenfixed("data_in", w), lenfixed("data_out", w), lenfixed("program_output", w)]))
        for y in range(h):
            print("|".join([lin[y], lout[y], lprg[y]]))
        print("-"*(tw-1))
        print(lenfixed("Next : [ENTER]     Quit : [Q]", w*2+2) + lenfixed(i, w))
        s = input()
        if s == "" : n = (n+1) % len(testcase.filelist)
        if s == "q" : sys.exit()

def main():
    os.system(g_cls)
    if not os.path.exists(g_crdir + g_zipdir):
        os.mkdir(g_crdir + g_zipdir)
    if not os.path.exists(g_crdir + g_builddir):
        os.mkdir(g_crdir + g_builddir)
    if not os.path.exists(g_crdir + "cookie.txt"):
        session = input("REVEL_SESSION = ")
        create_cookiefile(session)
    if os.path.exists(g_crdir + "cookie.txt"):
        tpp = input("TestProgram Path = ").replace('"', '')
        opd = os.path.dirname(tpp)
        progpath = (os.getcwd() + tpp if opd == "" else tpp).replace("\\", "/")
        num, ext = os.path.basename(tpp).split(".")
        if ext in g_cmdc:
            g_cmdc[ext] = raplace_cmd(g_cmdc[ext], progpath)
            print("Build >>>", " ".join(g_cmdc[ext]))
            os.system(" ".join(g_cmdc[ext]))
            ext = "exe"
            progpath = g_crdir + g_builddir + "test.exe"
        if not os.path.exists(g_crdir + g_zipdir + num_to_zipname(num)):
            print("TestCase Download...")
            if testcase_download(num):
                print("Download Completed")
            else:
                print("Download Failed")
        if os.path.exists(g_crdir + g_zipdir + num_to_zipname(num)):
            t = TestCase(num, ext, progpath)
            testcase_test(t)
            while 1:
                s = input()
                if s == "" : testcase_view(t)
                if s == "q" : sys.exit()
    else:
        pass

if __name__ == '__main__':
    setenv()
    main()
