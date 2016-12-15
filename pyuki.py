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

p = os.path.dirname(__file__).replace("\\", "/") + "/"
g_crdir = "" if p == '/' else p
g_testdir = "testcase/"
g_sampledir = "samplecase/"
g_compiledir = "compile/"
g_in = "test_in/"
g_out = "test_out/"
g_browser = ""
g_timeout = 2
g_cmdc = {}
g_cmdi = {}
g_op = ""
g_cls = ""
g_getch = None

def setenv():
    global g_browser, g_timeout, g_op, g_cls, g_getch
    sp = ";"
    if len(sys.argv) > 1 : g_op = sys.argv[1].replace("\\", "/")
    if "win" in sys.platform and "darwin" != sys.platform:
        g_cls = "cls"
        g_getch = getch_win
    else:
        g_cls = "clear"
        g_getch = getch_unix
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
                    if mode == "[browser]":
                        g_browser = s
                    if mode == "[tle]":
                        g_timeout = int(s)
                    if mode == "[compile]":
                        lang, cmd = map(lambda x : x.strip(), s.split(":", 1))
                        g_cmdc[lang] = cmd.split()
                    if mode == "[interpreter]":
                        lang, cmd = map(lambda x : x.strip(), s.split(":", 1))
                        g_cmdi[lang] = cmd.split()


def getch_unix():
    import sys, tty, termios
    fd = sys.stdin.fileno()
    try:
        tty.setraw(sys.stdin.fileno())
        return sys.stdin.read(1)
    except:
        termios.tcsetattr(fd, termios.TCSADRAIN, termios.tcgetattr(fd))

def getch_win():
    import msvcrt
    try:
        return msvcrt.getch().decode('utf8')
    except:
        return ''

class Test():
    def __init__(self, num, lang, prog, case):
        cmd = g_cmdi[lang] if lang in g_cmdi else ["[i]"]
        self.cmd = cmdio(cmd, prog)
        self.data = {}
        self.case = case
        self.filelist = []
        self.num = num
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
        din2k = limitstr(data_in, 2000)
        dout2k = limitstr(data_out, 2000)
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
                result = [yellow("WA "), etime, din2k, dout2k, out]
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

def view_ior(test):
    retry = False
    n = 0
    num = test.num
    m = "   problempage:[P]"
    m = m if g_browser else ""
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
        print(" ".join([limitstr("data_in", w), limitstr("data_out", w), limitstr("program_output", w)]))
        for y in range(h):
            print("|".join([lin[y], lout[y], lprg[y]]))
        print("-"*(tw-1))
        print(limitstr("next:[ENTER]" + m + "   retry:[R]" + "   quit:[Q]", w*2+2) + limitstr(i, w))
        c = g_getch()
        if c == "\r":
            n = (n+1) % len(test.filelist)
        if c == "q":
            break
        if c == "r":
            retry = True
            break
        if c == "p" and m:
            Popen([g_browser, "http://yukicoder.me/problems/no/" + num])
    return retry

def jadge(v1, v2):
    if v1 == v2 : return True
    if v1.strip() == v2.strip() : return True
    sp1 = v1.split("\n")
    sp2 = v2.split("\n")
    if len(sp1) != len(sp2) : return False
    for i in range(len(sp1)):
        s1, s2 = sp1[i], sp2[i]
        if s1 != s2:
            try:
                if (s1[0] == "+" or s2[0] == "+") and s1[0] != s2[0]:
                    return False
                if round(float(s1), 3) != round(float(s2), 3):
                    return False
            except:
                return False
    return True

def green(s):
    return "\033[42;30m" + s + "\033[0m"
    
def yellow(s):
    return "\033[43;30m" + s + "\033[0m"

def limitstr(s, n):
    if n <= 3:
        s = s[:n]
    elif len(s) > n:
        s = s[:n-3] + "..."
    return s.ljust(n, " ")

def zipname(num):
    return "No{:0>4}.zip".format(num)

def cmdio(cmd, prog):
    r = []
    for i in cmd:
        i = i.replace("[i]", prog)
        i = i.replace("[c]", prog.split("/")[-1].split(".")[0])
        i = i.replace("[o]", g_crdir + g_compiledir + "test.exe")
        i = i.replace("[d]", g_crdir + g_compiledir)
        r += [i]
    return r

def path_to_nlp(s):
    s = s.replace('"', '')
    basename = os.path.basename(s)
    prog = s.replace("\\", "/")
    lang = to_lang(basename)
    num = to_num(basename)
    return (num, lang, prog)

def to_lang(s):
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
        if mlen(i) > w:
            b = ""
            bw = 0
            for j in i:
                c = 2 if ord(j) > 255 else 1
                if bw + c > w:
                    r += [b]
                    b = ""
                    bw = 0
                b += j
                bw += c
            r += [b]
        else:
            r += [i]
    if len(r) < h : r += [""] * (h-len(r))
    if len(r) > h : r = r[:h]
    for i in range(h):
        r[i] = r[i] + " " * (w-mlen(r[i]))
    return r

def mlen(s):
    c = 0
    for i in s:
        if ord(i) > 255:
            c += 2
        else:
            c += 1
    return c

def try_compile(lang, prog):
    try:
        os.system(" ".join(cmdio(g_cmdc[lang], prog)))
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
            data_in_list += [s.strip() + "\n"]
        for i in ht.split("<h6>出力</h6>")[1:]:
            s = i.split("<pre>")[1].split("</pre>")[0]
            data_out_list += [s.strip() + "\n"]
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

def y_test(num, lang, prog, case):
    retry = False
    t = Test(num, lang, prog, case)
    print("Run >>>", " ".join(t.cmd))
    for i, j, k in t.tests():
        print(i, j, k)
    m = "   problempage:[P]"
    m = m if g_browser else ""
    print("testcase view:[ENTER]" + m + "   retry:[R]" + "   quit:[Q]")
    while 1:
        c = g_getch()
        if c == "\r":
            retry = view_ior(t)
            break
        if c == "q":
            break
        if c == "r":
            retry = True
            break
        if c == "p" and m:
            Popen([g_browser, "http://yukicoder.me/problems/no/" + num])
    return retry

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

def compile_file_remove(dir):
    try:
        for i in os.listdir(dir):
            if i[:4] == "test":
                os.remove(dir + i)
    except:
        pass

def compile_file_path(dir):
    return dir + "test.exe"

def check_lang(lang):
    if any([lang in g_cmdc, lang in g_cmdi, lang == "exe"]):
        return lang
    else:
        return None

def path_d(str):
    return str.replace('\"', '').replace('\'', '').lstrip().rstrip()

def main():
    os.system(g_cls)
    testdir = g_crdir + g_testdir
    sampledir = g_crdir + g_sampledir
    compiledir = g_crdir + g_compiledir
    try_mkdir(testdir)
    try_mkdir(sampledir)
    try_mkdir(compiledir)
    y_cookie()
    s = path_d(input("TestProgram Path = ") if g_op == "" else g_op)
    retry = True
    while retry:
        retry = False
        os.system(g_cls)
        compile_file_remove(compiledir)
        num, lang, prog = path_to_nlp(s)
        lang = check_lang(lang)
        if lang == None:
            print(list(set(list(g_cmdc) + list(g_cmdi))))
            lang = check_lang(input("Source Language = ").strip())
        if num == None:
            num = to_num(input("Problem Number = "))
        if lang in g_cmdc:
            print("compile >>>", " ".join(cmdio(g_cmdc[lang], prog)))
            if try_compile(lang, prog):
                lang = "exe" if "[o]" in g_cmdc[lang] else lang
                prog = compile_file_path(compiledir)
        y_download(num)
        if all([num, lang, prog]):
            samplecase = sampledir + zipname(num)
            testcase = testdir + zipname(num)
            cs = os.path.exists(samplecase)
            ct = os.path.exists(testcase)
            cp = os.path.exists(prog)
            if all([ct, cp]):# download testcase
                retry = y_test(num, lang, prog, testcase)
            if all([cs, not ct, cp]):# samplecase
                retry = y_test(num, lang, prog, samplecase)

if __name__ == '__main__':
    setenv()
    main()
