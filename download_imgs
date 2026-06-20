#!/usr/bin/env python3

import json
import sys
import urllib.error
import urllib.parse
import urllib.request


TOKEN_URL = "https://accounts.zoho.eu/oauth/v2/token"


def main():
    client_id = input("Enter client_id: ").strip()
    client_secret = input("Enter client_secret: ").strip()
    code = input("Enter code: ").strip()

    data = urllib.parse.urlencode(
        {
            "client_id": client_id,
            "client_secret": client_secret,
            "grant_type": "authorization_code",
            "code": code,
        }
    ).encode("utf-8")

    request = urllib.request.Request(TOKEN_URL, data=data, method="POST")

    try:
        with urllib.request.urlopen(request) as response:
            response_body = response.read().decode("utf-8")
    except urllib.error.HTTPError as exc:
        error_body = exc.read().decode("utf-8", errors="replace")
        print(f"Token request failed with HTTP {exc.code}")
        print(error_body)
        sys.exit(1)
    except urllib.error.URLError as exc:
        print(f"Token request failed: {exc}")
        sys.exit(1)

    try:
        token_data = json.loads(response_body)
    except json.JSONDecodeError:
        print("Token request succeeded but response was not valid JSON:")
        print(response_body)
        sys.exit(1)

    print("\nToken response:")
    print(json.dumps(token_data, indent=2, ensure_ascii=False))
    print(f"\naccess_token: {token_data.get('access_token', '')}")
    print(f"refresh_token: {token_data.get('refresh_token', '')}")


if __name__ == "__main__":
    main()
