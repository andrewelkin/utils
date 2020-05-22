import sys, os

'''

Goes though all go files in the tree and looks for inconsistent usage of zaboutils.FuncName : - argument of it must be
the same as the surrounding func name 

command line args:
-s:<path>               -   path to recursively scan *.go files 



Working example:

func (c *Controller) GetTransactionsPage(context *zaboutils.ExtendedContext, account *zaboresources.Account, cursor *string) ([]*zaboresources.AccountTransactionRes, *string, bool, *echo.HTTPError) {

...
	c.logger.LogWithContextf(zaboutils.Severity.INFO, context, zaboutils.FuncName(c.GetBalance), "Next cursor is %v", sMarker)
...
}


-- this should issue a warning as GetTransactionsPage != GetBalance


Note: RateLimits() is excluded from checks

'''


## scans go files in the path tree and gets existing descriptions, so we don't need to enter it manually again.
def scan_one_file(fname):
    warns = 0
    with open(fname) as f:

        func_name = None
        count = 0
        line_number = 0
        for s in f:
            s = s.rstrip("\n")
            s1 = s.lstrip()
            line_number += 1
            if s1.startswith("//"):
                continue

            if s1.startswith("func"):

                if count != 0:
                    print("File %s line %d Warning: count=%d" % (fname, line_number, count))

                count = 0

                func = s1[4:].lstrip().rstrip()
                ndx = func.find("{")
                if ndx > 0:
                    func = func[:ndx - 1]

                if func[0] == '(':
                    ndx = find_matching(func, "(", ")")
                    func = func[ndx + 1:].lstrip()

                ndx = func.find("(")
                if ndx < 0:
                    print("DEBUG: no '(' in the line", func, fname)
                    return 0

                func_name = func[:ndx].rstrip()

                # print("File %s line %d Function: '%s' " % (fname, line_number, func_name))

            for a in s:
                if a == '{':
                    count += 1
                elif a == '}':
                    count -= 1

            if count != 0:
                ndx = s.find("zaboutils.FuncName")

                if ndx >= 0:
                    pos = ndx
                    s = s[ndx:]
                    ndx = s.find("(")

                    pos += ndx + 1
                    zname = s[ndx + 1:].lstrip().rstrip()
                    ndx = zname.find(")")
                    if ndx >= 0:
                        zname = zname[:ndx]

                    ndx = zname.find(".")
                    if ndx >= 0:
                        pos += ndx + 2
                        zname = zname[ndx + 1:]

                    # print("\t\tZname '%s'" % zname)

                    if zname != func_name and func_name != "RateLimits":
                        warns += 1
                        print("%s:%d:%d Warning: function name: '%s' zaboutils.FuncName: '%s'" % (
                            fname, line_number, pos, func_name, zname))

    return warns


def scan_for_functions(rootDir):
    if rootDir is None: return 0, 0
    n = 0
    w = 0
    for lists in os.listdir(rootDir):
        path = os.path.join(rootDir, lists)

        if path.endswith(".go"):
            w += scan_one_file(path)
            n += 1

        if os.path.isdir(path):
            n1, w1 = scan_for_functions(path)
            n += n1
            w += w1

    return n, w


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


if __name__ == "__main__":

    path = None

    for arg in sys.argv[1:]:
        if arg[0:1] == "-" or arg[0:1] == "/":
            if arg[1:].lower().startswith("s:"):
                path = arg[3:]

    n, w = scan_for_functions(path)
    print("Scanned %d files, %d warnings issued" % (n, w))
