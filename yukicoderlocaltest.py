#! /usr/bin/env python3
import os
import sys
import shutil
import time
import urllib
import http
import http.cookiejar
from datetime import datetime, timedelta
from zipfile import ZipFile, ZIP_STORED
from subprocess import Popen, PIPE

g_crdir = os.path.dirname(__file__) + "/"
g_testdir = "testcase/"
g_sampledir = "samplecase/"
g_builddir = "build/"
g_in = "test_in/"
g_out = "test_out/"
# g_compilerpath = "C:/MinGW/bin" + ";" + "C:/Program Files (x86)/MSBuild/14.0/bin"
g_timeout = 5
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
        g_cmdc["cpp"] = ["g++", "-std=c++11", "-static-libgcc", "-static-libstdc++", "-o", "[o]", "[i]"]
        g_cmdc["cs"] = ["csc", "/out:[o]", "[i]"]
        g_cls = "cls"
    else:
        # g_cmdi["go"] = ["go", "run", "[i]"]
        g_cmdc["go"] = ["go", "build", "-o", "[o]", "[i]"]
        g_cmdc["c"] = ["gcc", "-o", "[o]", "[i]"]
        g_cmdc["cpp"] = ["g++", "-std=c++11", "-o", "[o]", "[i]"]
        g_cmdc["cs"] = ["mcs", "/out:[o]", "[i]"]
        g_cls = "clear"

class Test():
    def __init__(self, num, ext, progpath):
        cmd = g_cmdi[ext] if ext in g_cmdi else ["[i]"]
        self.cmd = raplace_cmd(cmd, progpath)
        self.data = {}
        self.zippath = g_crdir + g_testdir + zipname(num)
        self.filelist = []
        with ZipFile(self.zippath, 'r') as z:
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
            if jadge(out, data_out):
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
        with ZipFile(self.zippath, 'r') as z:
            return z.read(path).decode("utf-8")

def jadge(v1, v2):
    if v1 == v2 : return True
    sp1 = v1.split("\n")
    sp2 = v2.split("\n")
    if len(sp1) != len(sp2) : return False
    for i in range(len(sp1)):
        if sp1[i] != sp2[i]:
            try:
                if round(float(sp1[i]), 3) != round(float(sp2[i]), 3):
                    return False
            except:
                return False
    return True

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

def zipname(num):
    return "No{:0>4}.zip".format(num)
    
def problemnumber(filename):
    num = ""
    for i in filename:
        if i in "0123456789":
            num += i
        elif len(num) > 0:
            if i == "." : break
            num = ""
    if len(num) > 4:
        num = num[-4:]
    return num if len(num) > 0 else None

def raplace_cmd(cmd, progpath):
    r = []
    for i in cmd:
        i = i.replace("[i]", progpath)
        i = i.replace("[o]", g_crdir + g_builddir + "test.exe")
        r += [i]
    return r

def testcase_download(num):
    if os.path.exists(g_crdir + g_testdir + zipname(num)) : return
    print("TestCase Download...")
    try:
        cj = http.cookiejar.LWPCookieJar()
        cj.load(g_crdir + "cookie.txt")
        opener = urllib.request.build_opener(urllib.request.HTTPCookieProcessor(cj))
        url = "http://yukicoder.me/problems/no/" + num + "/testcase.zip"
        with opener.open(url) as r:
            with open(g_crdir + g_testdir + zipname(num), "wb") as f:
                f.write(r.read())
        print("TestCase Download Completed")
    except:
        print("TestCase Download Failed")

def samplecase_download(num):
    if os.path.exists(g_crdir + g_sampledir + zipname(num)) : return
    print("SampleCase Download...")
    try:
        data_in_list = []
        data_out_list = []
        ht = urllib.request.urlopen('http://yukicoder.me/problems/no/' + num).read().decode('utf-8')
        for i in ht.split("<h6>入力</h6>")[1:]:
            s = i.split("<pre>")[1].split("</pre>")[0]
            data_in_list += [s + "\n"]
        for i in ht.split("<h6>出力</h6>")[1:]:
            s = i.split("<pre>")[1].split("</pre>")[0]
            data_out_list += [s + "\n"]
        print("SampleCase Download Completed")
        sampledir = g_crdir + g_sampledir
        provisionaldir = sampledir + zipname(num).split(".")[0] + "/"
        try_mkdir(provisionaldir)
        try_mkdir(provisionaldir + g_in)
        try_mkdir(provisionaldir + g_out)
        with ZipFile(sampledir + zipname(num), "w", ZIP_STORED) as z:
            for i in range(len(data_in_list)):
                filename = "sample{:0>2}".format(i) + ".txt"
                with open(provisionaldir + g_in + filename, "wb") as f:
                    f.write(data_in_list[i].encode('utf-8'))
                z.write(provisionaldir + g_in + filename, g_in + filename)
                with open(provisionaldir + g_out + filename, "wb") as f:
                    f.write(data_out_list[i].encode('utf-8'))
                z.write(provisionaldir + g_out + filename, g_out + filename)
        shutil.rmtree(provisionaldir)
    except:
        print("SampleCase Download Failed")

def testcase_test(test):
    print("Run >>>", " ".join(test.cmd))
    for i, j, k in test.tests():
        print(i, j, k)
    rm = g_crdir + g_builddir + "test.exe"
    if os.path.exists(rm):
        print("Remove >>>", g_builddir + "test.exe")
        os.remove(rm)

def testcase_view(test):
    n = 0
    while 1:
        i = test.filelist[n]
        tw, th = os.get_terminal_size()
        w = tw // 3 - 1
        h = th - 6
        lin = tolist(test.data[i][2], w, h)
        lout = tolist(test.data[i][3], w, h)
        lprg = tolist(test.data[i][4], w, h)
        os.system(g_cls)
        print(test.data[i][0], test.data[i][1])
        print(" ".join([lenfixed("data_in", w), lenfixed("data_out", w), lenfixed("program_output", w)]))
        for y in range(h):
            print("|".join([lin[y], lout[y], lprg[y]]))
        print("-"*(tw-1))
        print(lenfixed("Next : [ENTER]     Quit : [Q]", w*2+2) + lenfixed(i, w))
        s = input()
        if s == "":
            n = (n+1) % len(test.filelist)
        if s == "q":
            break

def program_select():
    tpp = input("TestProgram Path = ").replace('"', '')
    opd = os.path.dirname(tpp)
    testprog = (os.getcwd() + tpp if opd == "" else tpp).replace("\\", "/")
    opbsp = os.path.basename(tpp).split(".")
    ext = opbsp[1] if len(opbsp) > 1 else None
    num = problemnumber(testprog)
    if num == None :
        num = problemnumber(input("Problem Number = "))
    if ext in g_cmdc:
        g_cmdc[ext] = raplace_cmd(g_cmdc[ext], testprog)
        print("Build >>>", " ".join(g_cmdc[ext]))
        os.system(" ".join(g_cmdc[ext]))
        ext = "exe"
        testprog = g_crdir + g_builddir + "test.exe"
    return (num, ext, testprog)

def try_mkdir(dir):
    try:
        if not os.path.exists(dir) : os.mkdir(dir)
    except:
        pass

def make_cookie():
    if os.path.exists(g_crdir + "cookie.txt") : return
    session = input("REVEL_SESSION = ")
    try:
        expires = (datetime.today() + timedelta(days=30)).strftime("%Y-%m-%d %H:%M:%S")
        with open(g_crdir + "cookie.txt", "w") as f:
            w = '#LWP-Cookies-2.0\nSet-Cookie3: REVEL_SESSION="%s"; path="/"; domain="yukicoder.me"; path_spec; expires="%s"; version=0'%(session, expires)
            f.write(w)
    except:
        pass

def view_quit_loop(test):
    print("TestCase View : [ENTER]     Quit : [Q]")
    while 1:
        s = input()
        if s == "":
            testcase_view(test)
            break
        if s == "q":
            break

def main():
    os.system(g_cls)
    try_mkdir(g_crdir + g_testdir)
    try_mkdir(g_crdir + g_sampledir)
    try_mkdir(g_crdir + g_builddir)
    make_cookie()
    if os.path.exists(g_crdir + "cookie.txt"):
        num, ext, testprog = program_select()
        if num != None:
            testcase_download(num)
            samplecase_download(num)
    if num == None or ext == None or testprog == None:
        return
    if os.path.exists(g_crdir + g_testdir + zipname(num)) and os.path.exists(testprog):
        t = Test(num, ext, testprog)
        testcase_test(t)
        view_quit_loop(t)
    else:
        pass

if __name__ == '__main__':
    setenv()
    main()
