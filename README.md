# Synology Photos Album Downloader

Downloads all photos from a password-protected Synology Photos shared album.

## Requirements

```bash
pip install requests
```

## Usage

```bash
python3 download_synology_album.py <album_url> [--password <password>] [--output <directory>]
```

### Arguments

| Argument | Description |
|----------|-------------|
| `album_url` | Full URL of the shared album (required) |
| `--password` | Album password — prompted interactively if omitted |
| `--output` | Directory where photos are saved (default: `synology_photos`) |

## Examples

Prompt for password:
```bash
python3 download_synology_album.py https://nas.example.com:5001/mo/sharing/rCAjWXAMW
```

Pass password directly:
```bash
python3 download_synology_album.py https://nas.example.com:5001/mo/sharing/rCAjWXAMW --password MySecret
```

Custom output directory:
```bash
python3 download_synology_album.py https://nas.example.com:5001/mo/sharing/rCAjWXAMW --password MySecret --output ~/Pictures/vacation
```

## Notes

- Photos are saved as JPEG regardless of the original format (HEIC, PNG, etc.), as the NAS serves high-quality JPEG previews for shared albums configured in view-only mode.
- Already downloaded files are skipped, so the script can be re-run safely to resume an interrupted download.
