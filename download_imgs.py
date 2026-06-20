#!/usr/bin/env python3

import configparser
import json
import sys
import urllib.error
import urllib.parse
import urllib.request
from pathlib import Path


TOKEN_URL = "https://accounts.zoho.eu/oauth/v2/token"
TICKETS_URL = "https://desk.zoho.eu/api/v1/tickets"
CONFIG_FILENAME = "zoho_exporter.ini"
CONFIG_SECTION = "zoho"
TOKENS_FILENAME = "tokens.txt"
TICKETS_FILENAME = "tickets.json"
ORG_ID = "20067925477"


def load_config() -> configparser.SectionProxy | None:
    """Load config from ./zoho_exporter.ini or ~/.zoho_exporter.ini.

    Returns the [zoho] section proxy, or None if no valid config is found.
    """
    candidates = [
        Path(CONFIG_FILENAME),
        Path.home() / CONFIG_FILENAME,
    ]
    config = configparser.ConfigParser()
    for path in candidates:
        if path.is_file():
            try:
                config.read(path, encoding="utf-8")
                if config.has_section(CONFIG_SECTION):
                    return config[CONFIG_SECTION]
            except configparser.Error:
                pass
    return None


def prompt_with_default(prompt: str, default: str) -> str:
    """Prompt the user, showing *default* in brackets; return default on empty input."""
    if default:
        value = input(f"{prompt} [{default}]: ").strip()
        return value if value else default
    return input(f"{prompt}: ").strip()


def save_tokens(token_data: dict) -> None:
    """Save access and refresh tokens to tokens.txt."""
    access_token = token_data.get("access_token", "")
    refresh_token = token_data.get("refresh_token", "")
    token_file = Path(TOKENS_FILENAME)
    token_file.write_text(
        f"access_token={access_token}\nrefresh_token={refresh_token}\n",
        encoding="utf-8",
    )


def fetch_tickets(access_token: str) -> dict | list:
    """Fetch all tickets from Zoho Desk."""
    request = urllib.request.Request(
        TICKETS_URL,
        headers={
            "orgId": ORG_ID,
            "Authorization": f"Zoho-oauthtoken {access_token}",
        },
        method="GET",
    )

    try:
        with urllib.request.urlopen(request) as response:
            response_body = response.read().decode("utf-8")
    except urllib.error.HTTPError as exc:
        error_body = exc.read().decode("utf-8", errors="replace")
        print(f"Tickets request failed with HTTP {exc.code}")
        print(error_body)
        sys.exit(1)
    except urllib.error.URLError as exc:
        print(f"Tickets request failed: {exc}")
        sys.exit(1)

    try:
        return json.loads(response_body)
    except json.JSONDecodeError:
        print("Tickets request succeeded but response was not valid JSON:")
        print(response_body)
        sys.exit(1)


def save_tickets(tickets_data: dict | list) -> None:
    """Save tickets response to pretty-printed JSON file."""
    tickets_file = Path(TICKETS_FILENAME)
    tickets_file.write_text(
        json.dumps(tickets_data, indent=2, ensure_ascii=False),
        encoding="utf-8",
    )


def main():
    cfg = load_config()
    default_id = cfg.get("client_id", "") if cfg else ""
    default_secret = cfg.get("client_secret", "") if cfg else ""

    client_id = prompt_with_default("Enter client_id", default_id)
    client_secret = prompt_with_default("Enter client_secret", default_secret)
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

    save_tokens(token_data)
    print(f"\nSaved tokens to {TOKENS_FILENAME}")

    access_token = token_data.get("access_token", "")
    if not access_token:
        print("Cannot fetch tickets because access_token is missing from the token response.")
        sys.exit(1)

    tickets_data = fetch_tickets(access_token)
    save_tickets(tickets_data)
    print(f"Saved tickets to {TICKETS_FILENAME}")


if __name__ == "__main__":
    main()
