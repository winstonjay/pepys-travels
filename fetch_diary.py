import urllib.request
import sys
import os
import ssl

# Bypass SSL verification
ssl._create_default_https_context = ssl._create_unverified_context

URL = "https://www.gutenberg.org/cache/epub/4200/pg4200.txt"
OUTPUT_FILE = "data/diary-trimmed.txt"

START_MARKER = "JANUARY 1659-1660"
END_MARKER = "END OF THE DIARY."

def fetch_and_clean():
    print(f"Downloading from {URL}...")
    try:
        with urllib.request.urlopen(URL) as response:
            content = response.read().decode('utf-8')
    except Exception as e:
        print(f"Error downloading file: {e}")
        sys.exit(1)

    print(f"Download complete. Total size: {len(content)} characters.")

    # Find start
    start_index = content.find(START_MARKER)
    if start_index == -1:
        print(f"Error: Start marker '{START_MARKER}' not found.")
        sys.exit(1)

    # Find end
    # We look for the end marker starting from the start index
    end_index = content.find(END_MARKER, start_index)
    if end_index == -1:
        print(f"Error: End marker '{END_MARKER}' not found.")
        sys.exit(1)

    # Adjust end index to include the marker length
    end_index += len(END_MARKER)

    # Slice the content
    trimmed_content = content[start_index:end_index]
    
    # Write to file
    print(f"Writing trimmed content to {OUTPUT_FILE}...")
    with open(OUTPUT_FILE, "w", encoding="utf-8") as f:
        f.write(trimmed_content)

    print(f"Success! Trimmed file size: {len(trimmed_content)} characters.")

if __name__ == "__main__":
    fetch_and_clean()

