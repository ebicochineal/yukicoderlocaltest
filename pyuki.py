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

g_crdir = os.path.dirname(__file__).replace("\\", "/") + "/"
g_testdir = "testcase/"
g_sampledir = "samplecase/"
g_builddir = "build/"
g_in = "test_in/"
g_out = "test_out/"
g_workingdir = ""
g_browser = ""
g_timeout = 2
g_cmdc = {}
g_cmdi = {}
g_op = ""
g_cls = ""

def setenv():
    global g_workingdir,g_browser, g_timeout, g_op, g_cls
    sp = ";"
    if len(sys.argv) > 1 : g_op = sys.argv[1].replace("\\", "/")
    if "win" in sys.platform and "darwin" != sys.platform:
        g_cls = "cls"
    else:
        g_cls = "clear"
        sp = ":"
    with open(g_crdir + "setting.ini", encoding="UTF-8") as f:
        mode = ""
        for i in f.readlines():
            s = i.strip()
            if len(i) > 1 and i[:2] != "//":
                if s[0] == "[":
                    mode = s
                else:
                    s = s.replace("\\", "/")
                    if mode == "[path]":
                        os.environ["PATH"] = os.environ["PATH"] + sp + s
                    if mode == "[workingdirectory]":
                        g_workingdir = s
                    if mode == "[browser]":
                        g_browser = s
                    if mode == "[tle]":
                        g_timeout = int(s)
                    if mode == "[compile]":
                        ext, cmd = splitcmd(s)
                        g_cmdc[ext] = cmd.split()
                    if mode == "[script]":
                        ext, cmd = splitcmd(s)
                        g_cmdi[ext] = cmd.split()

class Test():
    def __init__(self, num, ext, prog, case):
        cmd = g_cmdi[ext] if ext in g_cmdi else ["[i]"]
        self.cmd = cmdio(cmd, prog)
        self.data = {}
        self.case = case
        self.filelist = []
        with ZipFile(self.case, 'r') as z:
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
        with ZipFile(self.case, 'r') as z:
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

def splitcmd(s):
    ext = ""
    cmd = ""
    f = 0
    for i in s:
        if i != ":" or f:
            if f:
                cmd += i
            else:
                ext += i
        if i == ":" : f = 1
    return (ext.strip(), cmd.strip())

def lenfixed(s, n):
    if n <= 3:
        s = s[:n]
    elif len(s) > n:
        s = s[:n-3] + "..."
    return ("{: <" + str(n) + "}").format(s)

def zipname(num):
    return "No{:0>4}.zip".format(num)

def trimsample(s):
    if len(s) > 0:
        if s[-1] != "\n":
            s += "\n"
        if s[0] == "\n":
            s = s[1:]
        return s
    else:
        return s

def cmdio(cmd, prog):
    r = []
    for i in cmd:
        i = i.replace("[i]", prog)
        i = i.replace("[o]", g_crdir + g_builddir + "test.exe")
        r += [i]
    return r

def path_to_nep(s):
    s = s.replace('"', '')
    basename = os.path.basename(s)
    cwd = g_workingdir + "/" if os.path.dirname(s) == "" else ""
    prog = (cwd + s).replace("\\", "/")
    ext = to_ext(basename)
    num = to_num(basename)
    return (num, ext, prog)

def view_ior(test):
    n = 0
    while 1:
        i = test.filelist[n]
        tw, th = os.get_terminal_size()
        w = tw // 3 - 1
        h = th - 6
        lin = to_list(test.data[i][2], w, h)
        lout = to_list(test.data[i][3], w, h)
        lprg = to_list(test.data[i][4], w, h)
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

def to_ext(s):
    sp = s.split(".")
    return sp[-1] if len(sp) > 1 else None

def to_num(s):
    num = ""
    for i in s:
        if i in "0123456789":
            num += i
        elif len(num) > 0:
            if i == "." : break
            num = ""
    if len(num) > 4:
        num = num[-4:]
    return num if len(num) > 0 else None

def to_list(s, w, h):
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

def try_build(ext, prog):
    try:
        os.system(" ".join(cmdio(g_cmdc[ext], prog)))
        return True
    except:
        return False

def try_mkdir(dir):
    try:
        if not os.path.exists(dir) : os.mkdir(dir)
    except:
        pass

def try_testcase_download(num):
    try:
        cj = http.cookiejar.LWPCookieJar()
        cj.load(g_crdir + "cookie.txt")
        opener = urllib.request.build_opener(urllib.request.HTTPCookieProcessor(cj))
        url = "http://yukicoder.me/problems/no/" + num + "/testcase.zip"
        with opener.open(url) as r:
            with open(g_crdir + g_testdir + zipname(num), "wb") as f:
                f.write(r.read())
        return True
    except:
        return False

def try_samplecase_download(num):
    try:
        data_in_list = []
        data_out_list = []
        ht = urllib.request.urlopen("http://yukicoder.me/problems/no/" + num).read().decode("utf-8")
        for i in ht.split("<h6>入力</h6>")[1:]:
            s = i.split("<pre>")[1].split("</pre>")[0]
            data_in_list += [trimsample(s)]
        for i in ht.split("<h6>出力</h6>")[1:]:
            s = i.split("<pre>")[1].split("</pre>")[0]
            data_out_list += [trimsample(s)]
        sampledir = g_crdir + g_sampledir
        provisionaldir = sampledir + zipname(num).split(".")[0] + "/"
        try_mkdir(provisionaldir)
        try_mkdir(provisionaldir + g_in)
        try_mkdir(provisionaldir + g_out)
        with ZipFile(sampledir + zipname(num), "w", ZIP_STORED) as z:
            for i in range(len(data_in_list)):
                filename = "sample{:0>2}".format(i) + ".txt"
                with open(provisionaldir + g_in + filename, "wb") as f:
                    f.write(data_in_list[i].encode("utf-8"))
                z.write(provisionaldir + g_in + filename, g_in + filename)
                with open(provisionaldir + g_out + filename, "wb") as f:
                    f.write(data_out_list[i].encode("utf-8"))
                z.write(provisionaldir + g_out + filename, g_out + filename)
        shutil.rmtree(provisionaldir)
        return True
    except:
        return False

def try_makecookie(session):
    try:
        expires = (datetime.today() + timedelta(days=30)).strftime("%Y-%m-%d %H:%M:%S")
        with open(g_crdir + "cookie.txt", "w") as f:
            w = '#LWP-Cookies-2.0\nSet-Cookie3: REVEL_SESSION="%s"; path="/"; domain="yukicoder.me"; path_spec; expires="%s"; version=0'%(session, expires)
            f.write(w)
        return True
    except:
        return False

def y_download(num):
    if num == None : return
    if not os.path.exists(g_crdir + g_testdir + zipname(num)) and os.path.exists(g_crdir + "cookie.txt"):
        print("TestCase Download...")
        if try_testcase_download(num):
            print("TestCase Download Completed")
        else:
            print("TestCase Download Failed")
    if not os.path.exists(g_crdir + g_sampledir + zipname(num)):
        print("SampleCase Download...")
        if try_samplecase_download(num):
            print("SampleCase Download Completed")
        else:
            print("SampleCase Download Failed")

def y_test(num, ext, prog, case):
    t = Test(num, ext, prog, case)
    print("Run >>>", " ".join(t.cmd))
    for i, j, k in t.tests():
        print(i, j, k)
    m = "     goto Yukicoder Page : [P]"
    m = m if g_browser else ""
    print("TestCase View : [ENTER]" + m + "     Quit : [Q]")
    while 1:
        c = input()
        if c == "":
            view_ior(t)
            break
        if c == "q":
            break
        if c == "p" and m:
            Popen([g_browser, "http://yukicoder.me/problems/no/" + num])

def y_cookie():
    if os.path.exists(g_crdir + "cookie.txt") : return
    session = input("REVEL_SESSION = ")
    if session != "":
        if try_makecookie(session):
            print("Make cookie.txt")
        else:
            print("Failed")
    else:
        print("Skip REVEL_SESSION")
        print("SampleCase Only")

def y_exeremove():
    rm = g_crdir + g_builddir + "test.exe"
    if os.path.exists(rm):
        print("Remove >>>", g_builddir + "test.exe")
        os.remove(rm)

def main():
    os.system(g_cls)
    testdir = g_crdir + g_testdir
    sampledir = g_crdir + g_sampledir
    builddir = g_crdir + g_builddir
    try_mkdir(testdir)
    try_mkdir(sampledir)
    try_mkdir(builddir)
    y_cookie()
    s = input("TestProgram Path = ") if g_op == "" else g_op
    num, ext, prog = path_to_nep(s)
    if ext in g_cmdc:
        print("Build >>>", " ".join(cmdio(g_cmdc[ext], prog)))
        if try_build(ext, prog):
            ext = "exe"
            prog = builddir + "test.exe"
    if num == None:
        num = to_num(input("Problem Number = "))
    y_download(num)
    if all([num, ext, prog]):
        samplecase = sampledir + zipname(num)
        testcase = testdir + zipname(num)
        cs = os.path.exists(samplecase)
        ct = os.path.exists(testcase)
        cp = os.path.exists(prog)
        if all([ct, cp]):
            y_test(num, ext, prog, testcase)
        if all([cs, not ct, cp]):
            y_test(num, ext, prog, samplecase)
    y_exeremove()

if __name__ == '__main__':
    setenv()
    main()
