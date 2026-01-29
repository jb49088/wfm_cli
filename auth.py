import json

from config import APP_DIR, COOKIES_FILE, USER_AGENT

# ================================= COOKIE INPUT =================================


def prompt_for_cookies() -> dict[str, str]:
    """Prompt for and return cookies."""
    cookies = input("Cookies: ")

    cookies_dict = {
        cookie.strip().split("=", 1)[0]: cookie.strip().split("=", 1)[1]
        for cookie in cookies.split(";")
        if "=" in cookie.strip()
    }

    return cookies_dict


# =============================== FILE MANAGEMENT ================================


def ensure_app_dir() -> None:
    """Make sure the application data directory exists."""
    APP_DIR.mkdir(exist_ok=True)


def ensure_cookies_file(cookies: dict[str, str]) -> None:
    """Make sure the config file exists."""
    with COOKIES_FILE.open("w") as f:
        json.dump(cookies, f)


def load_cookies() -> dict[str, str]:
    """Load cookies from the config file."""
    with COOKIES_FILE.open() as f:
        return json.load(f)


# =============================== HEADER BUILDING ================================


def build_cookie_header(cookies: dict[str, str]) -> dict[str, str]:
    return {"Cookie": "; ".join(f"{k}={v}" for k, v in cookies.items())}


def build_authenticated_headers(cookie_header: dict[str, str]) -> dict[str, str]:
    """Build authenticated headers with cookies."""
    headers = {
        "Accept": "application/json, text/plain, */*",
        "Content-Type": "application/json",
        "Origin": "https://warframe.market",
        "Referer": "https://warframe.market/",
        "language": "en",
        "platform": "pc",
        "crossplay": "true",
        **USER_AGENT,
        **cookie_header,
    }

    return headers
