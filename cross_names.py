import sys, os

'''

Goes though all go files in the tree and looks for copy-paste dirt : 
command line args:
-s:<path>               -   path to recursively scan *.go files 



Working example:

in the zabo-api-provider-gemini/
(and assuming there is a folder zabo-api-provider-bittrex/ 

func (c *Controller) GetTransactionsPage(context *zaboutils.ExtendedContext, account *zaboresources.Account, cursor *string) ([]*zaboresources.AccountTransactionRes, *string, bool, *echo.HTTPError) {
...
	c.logger.LogWithContextf(zaboutils.Severity.INFO, context, zaboutils.FuncName(c.GetBalance), "Next cursor is %v", "Bittrex")
...
}

-- this should issue a warning as the word bittrex is out of context

'''

prefix = "zabo-api-provider-"
providers = []


## scans go files in the path tree and gets existing descriptions, so we don't need to enter it manually again.
def scan_one_file(fname, provider_name):
    warns = 0
    line_number = 0

    # print("Scanning file %s for %s" % (fname, provider_name))
    with open(fname) as f:
        for line in f:
            line_number += 1
            pos = 0

            line = line.lower()
            for p in providers:
                if p == provider_name:
                    continue
                pos = line.find(p)
                if pos >= 0:
                    warns += 1
                    print("%s:%d:%d Warning: provider name: '%s' alien name: '%s'" % (
                        fname, line_number, pos, provider_name, p))

    return warns


def scan_for_functions(rootDir, provider):
    if rootDir is None: return 0, 0
    n = 0
    w = 0

    for lists in os.listdir(rootDir):
        if lists.startswith(prefix):
            provider = lists[len(prefix):]

        path = os.path.join(rootDir, lists)

        if path.endswith(".go") and provider is not None:
            w += scan_one_file(path, provider)
            n += 1

        if os.path.isdir(path):
            n1, w1 = scan_for_functions(path, provider)
            n += n1
            w += w1

    return n, w


###################################################

def get_providers(rootDir):
    if rootDir is None: return []
    res = []
    for lists in os.listdir(rootDir):
        path = os.path.join(rootDir, lists)
        if os.path.isdir(path):
            if lists.startswith(prefix):
                res.append(lists[len(prefix):].lower())

    return res


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

    providers = get_providers(path)
    print("Providers:", providers)

    n, w = scan_for_functions(path, None)
    print("Scanned %d files, %d warnings issued" % (n, w))
