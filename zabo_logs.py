import requests
import json
import time
import random
import os.path
import sys

'''

zabo_logs retrieves all log entries for a request id

usage:

python zabo_logs.py [-r] [-s:<severity level>]  <request id>

-r reverses log entries to the natural order (older first)
-s:<int>  minimal severity level: 1 - all including DEBUG(default), 2 - INFO and higher, 3 - WARNING and ERROR, 4 - ERROR and CRITICALs  
-b:<token>  - set bearer token directly.  

Example:what the fruit fruit 9
python zabo_logs.py -r -s:2  63052069-a61d-4bda-b756-2f6c81367607  > "63052069-a61d-4bda-b756-2f6c81367607.log"


if the bearer token is not set in the command line,
it uses login/password and those are need to be placed in a file ~/.config/zabo_credentials:

sample contents, two lines of text:
myusername
mypassword 


access token will be saved in "/tmp/zabo_bearer.txt"
you can change this location in the global section below (if you feel it's not secure)


'''

#
limit = 50  # Max number of log entries to get. it's a zabo.com limitation

scene = "prod"  # Realm, i.e: 'stage'  or 'dev' or 'prod'
env = "live"  # Environment: i.e. 'live' or 'sandbox'

# credenitals file, default  ~/.config/zabo_credentials
credf = os.path.join(os.path.expanduser("~/.config"), "zabo_credentials")

# where token is saved. must have write access
tokenf = "/tmp/zabo_bearer.txt"

# url path to logs
logs_url = "https://" + ((scene + "-") if scene != "prod" else "") + "api.zabo.com/admin-v0/" + env + "/logs"

# Zabo login urls

authenticate_urls = {

    "dev": "https://zabo-api-dev.auth0.com/co/authenticate",
    "dev1": "https://login.zabo.com/co/authenticate",
    "stage": "https://login.zabo.com/co/authenticate",
    "prod": "https://login.zabo.com/co/authenticate"
}

authorization_urls = {

    "dev": "https://zabo-api-dev.auth0.com/authorize",
    "stage": "https://login.zabo.com/authorize",
    "prod": "https://login.zabo.com/authorize"

}

authenticate_url = authenticate_urls[scene]
authorization_url = authorization_urls[scene]

## These are zabo Auth0 ids. They are not secret and they are visible when attempting to log in
auth0_client = "eyJuYW1lIjoiYXV0aDAuanMiLCJ2ZXJzaW9uIjoiOS4xMi4yIn0="

auth0_client_ids = {
    "stage": "otCKt0GXtITJJKpr191RlSiQ3bi4kJsB",
    "dev": "kYZX21csufu44b8x9MIOES0Hvk6QbH1Y",
    "prod": "otCKt0GXtITJJKpr191RlSiQ3bi4kJsB",
}

auth0_client_id = auth0_client_ids[scene]

#########################################################################


log_severity = {"DEBUG": 1,
                "INFO": 2,
                "WARNING": 3,
                "ERROR": 4,
                }


def do_authenticate(url, login, password):

    if scene != "prod":
        scene_ = scene + "-"
    else:
        scene_ = ""
    headers = {
        "Accept": "*/*",
        "Accept-Encoding": "gzip, deflate, br",
        "Accept-Language": "en-US,en;q=0.9,ru;q=0.8",
        "Access-Control-Request-Headers": "auth0-client,content-type",
        "Access-Control-Request-Method": "POST",
        "Cache-Control": "no-cache",
        "Connection": "keep-alive",
        "Host": "login.zabo.com",
        "Origin": "https://" + scene_ + "admin.zabo.com",
        "Pragma": "no-cache",
        "Referer": "https://" + scene_ + "admin.zabo.com/login",
        "Sec-Fetch-Dest": "empty",
        "Sec-Fetch-Mode": "cors",
        "Sec-Fetch-Site": "cross-site",
        "User-Agent": "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/83.0.4103.97"
    }

    resp = requests.options(url, headers=headers)
    print("Pre-authentication: %d" % resp.status_code)

    if resp.status_code != 200:
        return False, None, None

    headers = {
        "accept": "*/*",
        "accept-encoding": "gzip,deflate,br",
        "accept-language": "en-US,en",
        "Auth0-Client": auth0_client,
        "Origin": "https://" + scene_ + "admin.zabo.com",
        "Referer": "https://" + scene_ + "admin.zabo.com/login",
        "cache-control": "no-cache",
        "content-type": "application/json",

        "sec-fetch-dest": "empty",
        "sec-fetch-mode": "cors",
        "sec-fetch-site": "cross-site",

    }

    payload = {
        "client_id": auth0_client_id,
        "username": login,
        "password": password,
        "realm": "Username-Password-Authentication",
        "credential_type": "http://auth0.com/oauth/grant-type/password-realm"

    }

    resp = requests.post(url, headers=headers, data=json.dumps(payload), cookies=resp.cookies)
    print("Authentication: %d" % resp.status_code)

    if resp.status_code != 200:
        return False, None, None

    resp_json = json.loads(resp.text)
    ticket = resp_json['login_ticket']
    # '{"login_ticket":"OUJYjZmS-tqrmUxdc9biCDr4jz4oENtj","co_verifier":"3OAndqz93_LpVgjlHj3o9Jej5Fj9LceZ","co_id":"n0NwifoMeome"}'
    return True, resp.cookies, ticket


def do_authorization(url, ticket, cookies):

    if scene != "prod":
        scene_ = scene + "-"
    else:
        scene_ = ""

    headers = {
        "accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.9",
        "accept-encoding": "gzip,deflate,br",
        "accept-language": "en-US,en",
        "Referer": "https://" + scene_ + "admin.zabo.com/login",
        "cache-control": "no-cache",
        "content-type": "application/json",
        "DNT": "1",
        "Host": "login.zabo.com",
        "Pragma": "no-cache",
        "Sec-Fetch-Dest": "document",
        "Sec-Fetch-Mode": "navigate",
        "Sec-Fetch-Site": "cross-site",
        "Sec-Fetch-User": "?1",
        #        "upgrade-insecure-requests": "1",
        "user-agent": "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/83.0.4103.97 Safari/537.36"

    }

    qparams = {
        "client_id": auth0_client_id,
        "response_type": "token id_token",
        "redirect_uri": "https://" + scene_ + "admin.zabo.com/callback",
        "scope": "openid profile",
        "realm": "Username-Password-Authentication",
        "audience": "https://zabo-api.auth0.com/api/v2/",
        "state": ''.join([str(random.randint(0, 9)) for i in range(24)]),
        "nonce": ''.join([str(random.randint(0, 9)) for i in range(24)]),
        "login_ticket": ticket,
        "auth0Client": auth0_client
    }

    resp = requests.get(url, headers=headers, params=qparams, cookies=cookies)
    # print("%d" % resp.status_code)

    tok = None

    for h in resp.history:
        if h.status_code == 302:
            # print(h.headers)
            loc = h.headers.get("Location")
            if loc is not None:
                ndx = loc.find("id_token=")
                if ndx > 0:
                    tok = loc[ndx + len("id_token="):]
                    toks = tok.split("&")
                    tok = toks[0]

    return tok


#########################################################################


def get_session_token(forced=False):
    bearer = None
    if not forced:
        try:
            with open(tokenf) as f:
                bearer = f.read()
        except:
            print("There is no bearer token in %s, getting new one" % tokenf, file=sys.stderr)

    if bearer is None:
        try:
            with open(credf) as f:
                creds = f.read().split("\n")
                adm_username = creds[0]
                adm_password = creds[1].strip()
        except:
            print(
                "Please create file " + credf + "\n. It must have two lines: first line - username and second - password",
                file=sys.stderr)

        st, co, ticket = do_authenticate(authenticate_url, adm_username, adm_password)
        if not st:
            return None

        bearer = do_authorization(authorization_url, ticket, co)
        if bearer is None:
            print("Could not get access token", file=sys.stderr)
            return None

        print("Saving new bearer token to " + tokenf, file=sys.stderr)
        with open(tokenf, 'w') as f:
            f.write(bearer)

        print("Authenticated OK")

    else:
        print("Using saved bearer token from ", tokenf, file=sys.stderr)

    return bearer


#########################################################################

def request_log_entries(log_id, bearer, min_severitiy=1, cursor=None):
    if bearer is None:
        return [], 0, None, True

    headers = {

        "accept": "application/json, text/plain, */*",
        "accept-encoding": "gzip,deflate,br",
        "accept-language": "en-US,en",
        "cache-control": "no-cache",
        "Authorization": "Bearer " + bearer,
        "content-type": "application/json",
        "origin": "https://stage-admin.zabo.com"
    }

    qparams = {
        "env": "live",
        "limit": limit,
        "request_id": log_id
    }

    if cursor is not None:
        qparams['cursor'] = cursor

    resp = requests.get(logs_url, headers=headers, params=qparams)

    tx = json.loads(resp.text)

    if resp.status_code != 200:
        print("Error: Status code %d" % resp.status_code)
        message = tx.get("message")
        if message is not None and message.startswith("Unauthorized"):
            return [], 0, None, True
        else:
            return [], 0, None, False

    res = []
    total = tx["total"]
    list_cursor = tx['list_cursor']
    has_more = list_cursor['has_more']
    log = tx['data']
    next_request_id = None

    for l in log:
        l1 = l.get("logs")
        if l1 is None:
            continue
        for l2 in l1:

            if has_more:
                next_request_id = l2['id']

            t = l2['created_at']

            ls = log_severity.get(l2['severity'], 5)
            if ls < min_severitiy:
                continue
            tstamp = time.strftime("%H:%M:%S", time.localtime(t // 1000))
            msecs = t % 1000

            message = l2['message']
            message = message.replace("\n", "\n%-53.53s" % " ")

            res.append("%s.%03d %-7.7s %-20.20s %-35.35s %s" % (
                tstamp, msecs, l2['severity'], l2['package'], l2['function'], message))

    return res, total, next_request_id, False


#####################################################################################################################


if __name__ == "__main__":

    res_reversed = False
    min_severity = 1
    bearer = None
    for g in sys.argv[1:]:
        if g.lower().startswith('/r') or g.lower().startswith('-r'):
            res_reversed = True
        elif g.lower().startswith('/s:') or g.lower().startswith('-s:'):
            min_severity = int(g[3:])
        elif g.lower().startswith('/b:') or g.lower().startswith('-b:'):
            bearer = int(g[3:])
        else:
            log_id = g

    if bearer is None:
        bearer = get_session_token(False)
    else:
        print("Using bearer token from the command line")

    print("Retrieving log for request id ", log_id, file=sys.stderr)
    print("Min log severity level %d" % min_severity, file=sys.stderr)
    cursor = None

    res = []
    attempts_to_auhorize = 2
    while True:

        r, t, cursor, need_authorize = request_log_entries(log_id, bearer, min_severity, cursor)
        if need_authorize:
            print("Requiring new authorization.. ", file=sys.stderr)
            attempts_to_auhorize -= 1
            if attempts_to_auhorize < 0:
                print("No more attempts for authorization.. ", file=sys.stderr)
                exit()

            bearer = get_session_token(True)
            continue

        res += r

        print("Total records retrieved: %d, left to retrieve: %d, has more: %s" % (
            len(res), t, "yes" if cursor is not None else "no"), file=sys.stderr)

        if cursor is None:
            break

    if res_reversed:
        res.reverse()

    print("\n--- Request id %s\n" % log_id)
    for l in res:
        print(l)
