#!/usr/bin/env python3
"""
Download all photos from a password-protected Synology Photos shared album.

Usage:
    python3 download_synology_album.py <album_url> [--password <password>] [--output <directory>]

Arguments:
    album_url               Full URL of the shared album
                            Example: https://nas.example.com:5001/mo/sharing/rCAjWXAMW

Options:
    --password <password>   Album password (prompted interactively if omitted)
    --output <directory>    Directory where photos will be saved (default: synology_photos)

Examples:
    python3 download_synology_album.py https://nas.example.com:5001/mo/sharing/rCAjWXAMW
    python3 download_synology_album.py https://nas.example.com:5001/mo/sharing/rCAjWXAMW --password MySecret
    python3 download_synology_album.py https://nas.example.com:5001/mo/sharing/rCAjWXAMW --output ~/Pictures/vacation
"""
import argparse
import getpass
import os
import sys
from urllib.parse import urlparse
import requests


def parse_sharing_token(album_url: str) -> tuple[str, str]:
    """Extract the base URL and sharing token from the album URL."""
    parsed = urlparse(album_url)
    base_url = f"{parsed.scheme}://{parsed.netloc}"
    path_parts = parsed.path.rstrip("/").split("/")
    sharing_token = path_parts[-1]
    if not sharing_token:
        print(f"Error: could not extract sharing token from URL '{album_url}'")
        print("Expected format: https://nas.example.com:5001/mo/sharing/<TOKEN>")
        sys.exit(1)
    return base_url, sharing_token


def authenticate(session: requests.Session, api_url: str, sharing_url: str, sharing_token: str, password: str) -> None:
    session.get(sharing_url)
    response = session.post(api_url, data={
        "api": "SYNO.Core.Sharing.Login",
        "method": "login",
        "version": "1",
        "sharing_id": sharing_token,
        "password": password,
    })
    result = response.json()
    if not result.get("success"):
        print(f"Error: authentication failed (wrong password?): {result}")
        sys.exit(1)
    print("Authenticated.")


def list_all_photos(session: requests.Session, api_url: str, sharing_token: str) -> list:
    photos = []
    offset = 0
    limit = 100
    while True:
        response = session.get(api_url, params={
            "api": "SYNO.Foto.Browse.Item",
            "method": "list",
            "version": "1",
            "offset": offset,
            "limit": limit,
            "_sharing_id": sharing_token,
            "additional": '["thumbnail"]',
        })
        items = response.json()["data"]["list"]
        photos.extend(items)
        offset += len(items)
        if len(items) < limit:
            break
    return photos


def download_photo(session: requests.Session, api_url: str, sharing_token: str, photo: dict, index: int, total: int, output_dir: str) -> None:
    photo_id = photo["id"]
    cache_key = photo["additional"]["thumbnail"]["cache_key"]
    original_name = os.path.splitext(photo["filename"])[0]
    filename = f"{original_name}.jpg"
    output_path = os.path.join(output_dir, filename)
    if os.path.exists(output_path):
        print(f"[{index}/{total}] Skip (exists): {filename}")
        return
    response = session.get(api_url, params={
        "api": "SYNO.Foto.Thumbnail",
        "method": "get",
        "version": "2",
        "id": photo_id,
        "cache_key": cache_key,
        "size": "xl",
        "type": "unit",
        "_sharing_id": sharing_token,
    })
    if "image" not in response.headers.get("content-type", ""):
        print(f"[{index}/{total}] Failed: {filename} ({response.text[:100]})")
        return
    with open(output_path, "wb") as file:
        file.write(response.content)
    size_kb = len(response.content) // 1024
    print(f"[{index}/{total}] {filename} ({size_kb} KB)")


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Download all photos from a Synology Photos shared album.",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="Example:\n  python3 download_synology_album.py https://nas.example.com:5001/mo/sharing/TOKEN --password MySecret",
    )
    parser.add_argument("album_url", help="Full URL of the shared album (e.g. https://nas.example.com:5001/mo/sharing/TOKEN)")
    parser.add_argument("--password", help="Album password (prompted interactively if omitted)")
    parser.add_argument("--output", default="synology_photos", help="Output directory (default: synology_photos)")
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    base_url, sharing_token = parse_sharing_token(args.album_url)
    sharing_url = f"{base_url}/mo/sharing/{sharing_token}"
    api_url = f"{base_url}/mo/sharing/webapi/entry.cgi"
    password = args.password or getpass.getpass("Album password: ")
    session = requests.Session()
    authenticate(session, api_url, sharing_url, sharing_token, password)
    print("Listing photos...")
    photos = list_all_photos(session, api_url, sharing_token)
    print(f"Found {len(photos)} photos. Saving to {args.output}/")
    os.makedirs(args.output, exist_ok=True)
    for index, photo in enumerate(photos, start=1):
        download_photo(session, api_url, sharing_token, photo, index, len(photos), args.output)
    print("Done.")


if __name__ == "__main__":
    main()
