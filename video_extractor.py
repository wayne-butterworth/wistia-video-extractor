#!/usr/bin/env python3
"""
Extract Wistia video IDs from HTML and download the video file.
Process:
1. Extract video ID from HTML (wvideo parameter)
2. Build Wistia embed URL
3. Download embed URL content (with retries)
4. Find .bin URL and replace with .mp4
5. Download final video file with user-specified filename (with resume and retries)
6. Validate download

Features:
- Automatic filename extraction from HTML
- Resume interrupted downloads
- Retry failed requests
- Avoid overwriting existing files
"""

import re
import requests
import os
from pathlib import Path
from urllib.parse import urlparse
import time


def extract_video_id(html):
    """Extract Wistia video ID from HTML using regex"""
    match = re.search(r'wvideo=([a-z0-9]+)', html)
    if match:
        return match.group(1)
    raise ValueError("Could not find video ID in HTML (looking for wvideo=xxx)")


def get_embed_url(video_id):
    """Construct the Wistia embed URL"""
    return f"https://fast.wistia.net/embed/iframe/{video_id}?videoFoam=true"


def find_bin_url(content):
    """Find the first URL with .bin extension and replace .bin with .mp4"""
    # Find all URLs with .bin extension (handles quoted and unquoted URLs)
    bin_urls = re.findall(r'https?://[^\s"\'<>]+\.bin', content)
    if bin_urls:
        mp4_url = bin_urls[0].replace('.bin', '.mp4')
        return mp4_url
    raise ValueError("Could not find .bin URL in downloaded content")


def extract_filename(html):
    """Extract a suggested filename from HTML input if present."""
    # Prefer anchor text that looks like a filename
    match = re.search(r'<a[^>]*>\s*([^<]*\.mp4)\s*</a>', html, re.IGNORECASE)
    if match:
        filename = match.group(1).strip()
        return Path(filename).stem

    # Fallback: find any text that looks like a sensible mp4 filename
    match = re.search(r'([\w \-_.]+\.mp4)', html, re.IGNORECASE)
    if match:
        filename = match.group(1).strip()
        return Path(filename).stem

    return None


def get_unique_filename(filename):
    """Return a non-overwriting filename stem by appending a counter if needed."""
    base = Path(filename).stem
    candidate = Path(f"{base}.mp4")
    count = 1
    while candidate.exists():
        candidate = Path(f"{base}-{count}.mp4")
        count += 1
    return candidate.stem


def download_file(url, filename, max_retries=3):
    """Download a file from URL and save with .mp4 extension, with retry and resume support"""
    filepath = f"{filename}.mp4"
    
    # Check if file already exists and get its size for resume
    existing_size = 0
    if Path(filepath).exists():
        existing_size = Path(filepath).stat().st_size
        print(f"   Resuming download from byte {existing_size}")
    
    print(f"   Downloading from: {url}")
    
    headers = {}
    if existing_size > 0:
        headers['Range'] = f'bytes={existing_size}-'
    
    for attempt in range(max_retries):
        try:
            response = requests.get(url, stream=True, timeout=30, headers=headers)
            response.raise_for_status()
        except requests.exceptions.RequestException as e:
            if attempt < max_retries - 1:
                print(f"   Download attempt {attempt + 1} failed: {e}. Retrying in 5 seconds...")
                time.sleep(5)
                continue
            else:
                raise Exception(f"Failed to download file after {max_retries} attempts: {e}")
    
    # Get total file size (may be partial if resuming)
    total_size = int(response.headers.get('content-length', 0)) + existing_size
    mode = 'ab' if existing_size > 0 else 'wb'
    
    # Download with progress indicator
    downloaded = existing_size
    with open(filepath, mode) as f:
        for chunk in response.iter_content(chunk_size=8192):
            if chunk:
                f.write(chunk)
                downloaded += len(chunk)
                if total_size:
                    percent = (downloaded / total_size) * 100
                    print(f"   Progress: {percent:.1f}% ({downloaded}/{total_size} bytes)", end='\r')
    
    print(f"\n   ✓ Downloaded successfully to: {filepath}")
    
    # Basic validation: check if file size matches expected
    if total_size and downloaded != total_size:
        raise Exception(f"Downloaded file size mismatch: expected {total_size}, got {downloaded}")
    
    return filepath


def get_multiline_input():
    """Get HTML content from user (paste and press Enter twice)"""
    print("Paste the HTML content (press Enter twice when done):")
    lines = []
    empty_count = 0
    
    while True:
        try:
            line = input()
            if line == "":
                empty_count += 1
                if empty_count >= 2:
                    break
            else:
                empty_count = 0
                lines.append(line)
        except EOFError:
            break
    
    return "\n".join(lines)


def main():
    print("\n" + "="*60)
    print("Wistia Video Downloader")
    print("="*60 + "\n")
    
    try:
        # Step 1: Get HTML input
        html = get_multiline_input()
        if not html.strip():
            print("Error: No HTML content provided")
            return
        
        # Step 2: Extract video ID
        print("\n[1/6] Extracting video ID from HTML...")
        video_id = extract_video_id(html)
        print(f"   ✓ Found video ID: {video_id}")
        
        # Step 3: Build Wistia embed URL
        print("\n[2/6] Building Wistia embed URL...")
        embed_url = get_embed_url(video_id)
        print(f"   URL: {embed_url}")
        
        # Step 4: Download from embed URL
        print("\n[3/6] Downloading Wistia embed page...")
        for attempt in range(3):
            try:
                response = requests.get(embed_url, timeout=15)
                response.raise_for_status()
                break
            except requests.exceptions.RequestException as e:
                if attempt < 2:
                    print(f"   Embed download attempt {attempt + 1} failed: {e}. Retrying...")
                    time.sleep(2)
                else:
                    raise Exception(f"Failed to download embed URL after 3 attempts: {e}")
        
        embed_content = response.text
        print("   ✓ Embed page downloaded")
        
        # Step 5: Find .bin URL and convert to .mp4
        print("\n[4/6] Searching for .bin URL in embed content...")
        mp4_url = find_bin_url(embed_content)
        print(f"   ✓ Found video URL")
        print(f"   Original: {mp4_url.replace('.mp4', '.bin')}")
        print(f"   Modified: {mp4_url}")
        
        # Step 6: Derive filename from original HTML input if possible
        print("\n[5/6] Determining filename from input...")
        filename = extract_filename(html)
        if filename:
            print(f"   ✓ Derived filename: {filename}.mp4")
        else:
            filename = "video"
            print(f"   ✓ No filename found in input, defaulting to: {filename}.mp4")

        original_filename = filename
        filename = get_unique_filename(filename)
        if filename != original_filename:
            print(f"   ✓ Adjusted to avoid overwrite: {filename}.mp4")
        else:
            print(f"   ✓ Final filename: {filename}.mp4")

        # Step 7: Download final file
        print("\n[6/6] Downloading video file...")
        download_file(mp4_url, filename)
        
        print("\n" + "="*60)
        print("✓ All steps completed successfully!")
        print("="*60 + "\n")
        
    except ValueError as e:
        print(f"\n✗ Error: {e}")
        return 1
    except Exception as e:
        print(f"\n✗ Error: {e}")
        return 1
    
    return 0


if __name__ == "__main__":
    exit(main())
