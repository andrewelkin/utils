import pyperclip
import sys, os

'''Takes GO func declaration from the clipboard and makes nice header with arguments and return values. Places this description into clipboard


command line args:
-s:<path>               -   path to recursively scan *.go files for existing descriptions
-o:<type>=<value>       -   add an output value type/description pair, example:  "-o:[]byte=raw JSON response."



Working example:

"  func (c *Controller) GetTransactionsPage(context *zaboutils.ExtendedContext, account *zaboresources.Account, cursor *string) ([]*zaboresources.AccountTransactionRes, *string, bool, *echo.HTTPError) {"

will be processed like this:

// GetTransactionsPage()
// --> Input:
// context     *zaboutils.ExtendedContext     .
// account     *zaboresources.Account         .
// cursor      *string                        .
// <-- Output:
// 1) []*zaboresources.AccountTransactionRes     .
// 2) *string                                    .
// 3) bool                                       .
// 4) *echo.HTTPError                            .


'''

odesc = {}
idesc = {}


## scans go files in the path tree and gets existing descriptions, so we don't need to enter it manually again.
def scan_one_file(fname):
    with open(fname) as f:

        inputs = False
        outputs = False
        for s in f:
            s = s.rstrip("\n")
            if not s.startswith("//"):
                inputs = False
                outputs = False
                continue

            if s.find("--> Input") >= 0:
                inputs = True
                outputs = False
                continue

            if s.find("<-- Output") >= 0:
                outputs = True
                inputs = False
                continue

            if inputs:
                s = s[2:].lstrip()
                ndx = s.find(" ")
                if ndx > 0:
                    a0 = s[:ndx]
                    a1 = s[ndx:].lstrip()
                    ndx = a1.find(' ')
                    if ndx > 0:
                        desc = a1[ndx + 1:].lstrip()
                        a1 = a1[:ndx]
                        idesc[a0 + a1] = desc
            #           print("I-->", a0,a1,desc)

            if outputs:
                s = s[2:].lstrip()
                ndx = s.find(")")
                if ndx > 0:
                    s = s[ndx + 1:].lstrip()
                    ndx = s.find(" ")
                    if ndx > 0:
                        a0 = s[:ndx]
                        desc = s[ndx + 1:].lstrip()
                        if a0.find(".") > 0:  ## only not simple types
                            odesc[a0] = desc
                            # print("O-->", a0, desc)


def scan_for_descriptions(rootDir):
    if rootDir is None: return 0
    n = 0
    for lists in os.listdir(rootDir):
        path = os.path.join(rootDir, lists)

        if path.endswith(".go"):
            scan_one_file(path)
            n += 1

        if os.path.isdir(path):
            n += scan_for_descriptions(path)

    return n


###################################################

def find_matching(f, lt='(', rt=')'):
    cnt = 0
    for i in range(len(f)):
        if f[i] == lt:
            cnt += 1
        elif f[i] == rt:
            cnt -= 1
            if cnt == 0:
                return i

    return -1


def do_header(func):
    ndx = func.find("func")
    if ndx < 0:
        return None
    func = func[ndx + 4:].lstrip().rstrip()
    ndx = func.find("{")
    if ndx > 0:
        func = func[:ndx - 1]

    if func[0] == '(':
        ndx = find_matching(func, "(", ")")
        func = func[ndx + 1:].lstrip()

    ndx = func.find("(")
    if ndx < 0:
        return None

    fname = func[:ndx].rstrip()
    args = func[ndx:].lstrip()

    ndx = find_matching(args)
    if ndx < 0:
        return None

    retr = args[ndx + 1:].lstrip()
    args = args[1:ndx]

    if retr[0] == '(':
        ndx = find_matching(retr)
        retr = retr[1:]
        if ndx > 0:
            retr = retr[:ndx - 1].rstrip()

    args = [f.lstrip().rstrip() for f in args.split(',')]
    retr = [f.lstrip().rstrip() for f in retr.split(',')]

    return fname, args, retr


def print_nice(name, args, retr):
    ret = ""

    mlen = 1
    mlen2 = 1
    nargs = []
    for a in args:
        ndx = a.find(" ")
        if ndx > 0:
            b = a[ndx + 1:].lstrip()
            nargs.append((a[:ndx], b))
            mlen = max(mlen, len(a[:ndx]))
            mlen2 = max(mlen2, len(b))
        else:
            nargs.append((a, ""))
            mlen = max(mlen, len(a))

    mlen += 4
    mlen2 += 4

    fstr = "// %%-%d.%ds %%-%d.%ds %%s\n" % (mlen, mlen, mlen2, mlen2)

    ret += "// %s()\n" % name
    ret += "// --> Input:\n"
    for a0, a1 in nargs:
        desc = idesc.get(a0 + a1, ".")
        ret += fstr % (a0, a1, desc)

    mlen = 1
    for r in retr:
        mlen = max(mlen, len(r))

    mlen += 4

    fstr = "// %%d) %%-%d.%ds %%s\n" % (mlen, mlen)

    ret += "// <-- Output:\n"
    i = 1
    for a in retr:
        desc = odesc.get(a, ".")
        ret += fstr % (i, a, desc)
        i += 1

    return ret


'''

command line args:
-s:<path>               -   path to recursively scan *.go files for existing descriptions
-o:<type>=<value>       -   add an output value type/description pair, example:  "-o:[]byte=raw JSON response."

'''

if __name__ == "__main__":

    path = None

    for arg in sys.argv[1:]:
        if arg[0:1] == "-" or arg[0:1] == "/":
            if arg[1:].lower().startswith("s:"):
                path = arg[3:]
            if arg[1:].lower().startswith("o:"):
                a = arg[3:].split("=")
                if len(a) == 2:
                    print("Adding '%s'->'%s'" % (a[0], a[1]))
                    odesc[a[0]] = a[1]

    n = scan_for_descriptions(path)
    print("Scanned %d files, %d input and %d output descriptions " % (n, len(idesc), len(odesc)))

    a = pyperclip.paste()
    all = do_header(a)
    if all is None:
        exit()
    p = print_nice(all[0], all[1], all[2])
    print(p)
    pyperclip.copy(p)
