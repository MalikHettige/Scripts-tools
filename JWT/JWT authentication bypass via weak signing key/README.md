# Script for JWT authentication bypass via weak signing key

So the process of the server allowing any authenticated user to travel to any path in the application is vary when the session cookie is JWT-based. When a user requests a certain path the server checks the payload segment of the token and verifies with the signature (instructed by `alg` value) and used against the private key. The bug in this specific lab/application is that the private key is crackable cause it is guessable.

### How to get triggered by this bug?
Always make sure to check if the token of JWT-based cookie's `alg` value is **HS256**, it is the opportunity. **any time you see HS256 in a JWT header, attempt a secret brute-force by default**

### How to brute force? 
Well there are several ways, main ones I know are via **Hashcat** or or by using a python script. I chose python script. Either of them is fine. 

**Note:** This can also be used for Horizontal access if you replace `administrator` with the victim's username in `sub` parameter of the script

1. Requires **Python + pip** so install them if you haven't by running ```pip install pyjwt``` in your **GIT BASH**.
2. Make sure you have **JWT editor** burp extension installed and enabled (use a standalone command-line tool, or are switching to alternative intercepting proxies if JWT editor does not suit)
3. Download the wordlist if you haven't: ```curl -O https://raw.githubusercontent.com/wallarm/jwt-secrets/master/jwt.secrets.list```
4. Paste [this script](https://github.com/MalikHettige/Scripts-tools/blob/main/JWT/JWT%20authentication%20bypass%20via%20weak%20signing%20key/cracking_script.py) but make sure to replace **"PASTE_YOUR_FULL_JWT_HERE"** with your entire JWT-based cookie.
5. Run the script ```python crack_jwt.py```
6. After the results appeared, the secret code will be shown as ``[+] FOUND SECRET: secret1``
7. Copy the value, run [this script](https://github.com/MalikHettige/Scripts-tools/blob/main/JWT/JWT%20authentication%20bypass%20via%20weak%20signing%20key/forge_the_admin_token.py) to forge the admin token. Make sure to replace `APPLICATION_ISSUER` with the application's issuer, it can be found when you locate the `iss` section in **JWT web token/JWT editor**
8. And at the bottom of the results (likely below `return self._jws.encode(`) the session cookie of administrator is shown. 

