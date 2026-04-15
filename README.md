# Wistia Video Extractor

A Python script to extract and download videos from Wistia embeds.

## Features

- Extracts video ID from HTML containing Wistia embed code
- Downloads videos with resume support for large files
- Automatic filename extraction from HTML input
- Retry logic for failed downloads
- Avoids overwriting existing files

## Usage

1. Run the script:
   ```bash
   python3 video_extractor.py
   ```

2. Paste the HTML content containing the Wistia embed (e.g., from a course page).

3. Press Enter twice to finish input.

4. Enter "go" to finish prompting for embeds and start the download.

5. The script will extract the video ID, find the download URL, and download the video.

Alternatively, use the shell script:
```bash
./run_video_extractor.sh
```

## Requirements

- Python 3
- `requests` library (`pip install requests`)

## Testing

Run the test suite:
```bash
python3 test_video_extractor.py
```

## License

[Add your license here]