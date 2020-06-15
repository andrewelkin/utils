import sys, os

'''

Goes though all go files in the tree and looks for usage cases for go maps: - gives warning
when the map is accessed an unprotected way, for instance:

var a map[string][]int

(this is 'before map' code situation) 
temp: = a['foobar'][1]    // will panic as nil[1] is a memory violation

the correct way would be:

var temp int

el,ok := a['foobar']
if ok && len(el)>=1 {
    temp = el[1]
}


(after map code is suspicious):
a['foobar'][0] = 5  // will panic if there is no entry for 'foobar' 


command line args:
-s:<path>               -   path to recursively scan *.go files 


'''


def get_word(s):
    s = s.lstrip()
    ndx = s.find(" ")
    if ndx < 0:
        return s
    return s[:ndx]


def get_last_word(s):
    s = s.rstrip()
    ndx = s.rfind(" ")
    if ndx < 0:
        return s
    return s[ndx + 1:]


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


# gets go func definition and finds three pieces: func name,arg string and params string
def do_header(func):
    ndx = func.find("func")
    if ndx < 0:
        return None, None, None
    func = func[ndx + 4:].lstrip().rstrip()
    ndx = func.find("{")
    if ndx > 0:
        func = func[:ndx - 1]

    if func[0] == '(':
        ndx = find_matching(func, "(", ")")
        func = func[ndx + 1:].lstrip()

    ndx = func.find("(")
    if ndx < 0:
        return None, None, None

    fname = func[:ndx].rstrip()
    args = func[ndx:].lstrip()

    ndx = find_matching(args)
    if ndx < 0:
        return None, None, None

    retr = args[ndx + 1:].lstrip()
    args = args[1:ndx]

    if len(args) > 0:
        args = [f.lstrip().rstrip() for f in args.split(',')]
    else:
        args = []

    if len(retr) > 0:
        if retr[0] == '(':
            ndx = find_matching(retr)
            retr = retr[1:]
            if ndx > 0:
                retr = retr[:ndx - 1].rstrip()
        retr = [f.lstrip().rstrip() for f in retr.split(',')]
    else:
        retr = []

    return fname, args, retr


def find_map_definition(s):
    while True:
        ndx = s.find(" map")
        if ndx < 0:
            ndx = s.find("=map")
        if ndx < 0:
            ndx = s.find("(map")
        if ndx < 0:
            return -1

        s = s[ndx + 4:]
        if len(s) == 0:
            return -1
        if s[0] == ' ' or s[0] == '[':
            return ndx


## scans go files in the path tree
def scan_one_file(fname):
    warns = 0

    maps = set()

    with open(fname) as f:

        func_name = None
        count = 0
        line_number = 0
        for s in f:
            s = s.rstrip("\n")
            s1 = s.lstrip()
            line_number += 1
            com = s1.find("//")
            if com >= 0:
                s1 = s1[:com].rstrip()
            if len(s1) == 0:
                continue

            if s1.startswith("var"):
                ndx = s1.find("map")
                if ndx >= 0:
                    mapname = get_word(s1[3:])
                    # print("%s:%d:Warning: global map: %s" % (fname, line_number, mapname))
                    maps.add(mapname)

            if s1.startswith("func"):
                _, args, _ = do_header(s1)
                if args is not None:
                    for a in args:
                        ndx = find_map_definition(a)
                        if ndx > 0:
                            mapname = get_last_word(a[:ndx].strip())
                            # print("%s:%d:Warning: param map: %s" % (fname, line_number, mapname))
                            maps.add(mapname)

                continue

            ndx = find_map_definition(s1)
            if ndx >= 0:
                n1 = s1.find("=")
                if n1 < 0:
                    # parameter line
                    ##   a map[string]int
                    # TODO: ignore returns in interface functions, now it's just garbage
                    mapname = s1[:ndx].rstrip()
                    mapname = get_last_word(mapname)
                    maps.add(mapname)
                    # print("%s:%d:Warning: struct map: %s" % (fname, line_number, mapname))
                else:
                    ##   a := make(map[string]int)
                    mapname = s1[:n1]
                    if mapname.endswith(":"):
                        mapname = mapname[:-1]

                    mapname = get_last_word(mapname)
                    # print("%s:%d:Warning: local map: %s" % (fname, line_number, mapname))
                    maps.add(mapname)
                continue

            # look for map usage

            for mapname in list(maps):
                ndx1 = s1.find(mapname)
                if ndx1 < 0:
                    continue

                after = s1[ndx1 + len(mapname):].lstrip()
                before = s1[:ndx1].strip()
                if after.startswith("["):
                    ndx2 = after.find("=")
                    if ndx2 > 0:
                        after = after[:ndx2 - 1].strip()
                        sq1 = after.find("]")
                        if sq1 > 0:
                            sq2 = after[sq1:].find("]")
                            if sq2 > 0:
                                print("%s:%d:Warning: possibly assignment to non-exisitng map %s value used: (code after map):'%s':" % (fname, line_number, mapname, after))

                    ndx2 = before.rfind("=")
                    if ndx2 > 0:
                        before = before[:ndx2]
                        if before.endswith(":"):
                            before = before[:-1]

                        before = before.rstrip()
                        if before.find(",") < 0:
                            print("%s:%d:Warning: possibly unchecked assignment to map %s value (code before map) :'%s' :" % (fname, line_number, mapname, before))

    return warns


#######################################################################################################################
def scan_(rootDir):
    if rootDir is None: return 0, 0
    n = 0
    w = 0
    for lists in os.listdir(rootDir):
        path = os.path.join(rootDir, lists)

        if path.endswith(".go"):
            w += scan_one_file(path)
            n += 1

        if os.path.isdir(path):
            n1, w1 = scan_(path)
            n += n1
            w += w1
    return n, w


###################################################


if __name__ == "__main__":

    path = None

    for arg in sys.argv[1:]:
        if arg[0:1] == "-" or arg[0:1] == "/":
            if arg[1:].lower().startswith("s:"):
                path = arg[3:]

    n, w = scan_(path)
    print("Scanned %d files, %d warnings issued" % (n, w))
