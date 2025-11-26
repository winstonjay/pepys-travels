import json
import csv
import sys
import os
import re
from typing import Dict, List

# Keywords to track in entries (case-insensitive)
KEYWORDS = [
    "wife", 
    "lord", 
    "king", 
    "duke", 
    "money", 
    "dinner", 
    "supper", 
    "bed", 
    "office", 
    "plague", 
    "fire",
    "music",
    "play",
    "church"
]

def count_words(text: str) -> int:
    return len(text.split())

def count_occurrences(text: str, word: str) -> int:
    # Simple regex to match whole words
    return len(re.findall(r'\b' + re.escape(word) + r'\b', text, re.IGNORECASE))

def generate_stats(input_file: str, output_file: str):
    print(f"Analyzing {input_file}...")
    
    stats_list = []
    
    try:
        with open(input_file, 'r', encoding='utf-8') as f:
            for i, line in enumerate(f, 1):
                try:
                    entry_data = json.loads(line)
                    entry_text = entry_data.get('entry', '')
                    footnotes = entry_data.get('footnotes', [])
                    date = entry_data.get('date', '')
                    
                    row = {
                        "date": date,
                        "entry_length_chars": len(entry_text),
                        "entry_word_count": count_words(entry_text),
                        "footnote_count": len(footnotes),
                        "footnote_word_count": sum(count_words(fn) for fn in footnotes)
                    }
                    
                    # Calculate keyword counts
                    for keyword in KEYWORDS:
                        row[f"mentions_{keyword}"] = count_occurrences(entry_text, keyword)
                    
                    stats_list.append(row)
                    
                except json.JSONDecodeError:
                    print(f"Warning: Invalid JSON on line {i}")

        if not stats_list:
            print("No valid entries found.")
            return

        # Write to CSV
        fieldnames = list(stats_list[0].keys())
        
        # Ensure output directory exists
        os.makedirs(os.path.dirname(output_file), exist_ok=True)
        
        with open(output_file, 'w', newline='', encoding='utf-8') as csvfile:
            writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
            writer.writeheader()
            writer.writerows(stats_list)
            
        print(f"Stats generated for {len(stats_list)} entries.")
        print(f"Output saved to {output_file}")
        
        # Print some summary stats
        total_words = sum(s['entry_word_count'] for s in stats_list)
        avg_words = total_words / len(stats_list)
        max_words = max(stats_list, key=lambda x: x['entry_word_count'])
        
        print("\nSummary:")
        print(f"Total Words: {total_words:,}")
        print(f"Average Words per Entry: {avg_words:.0f}")
        print(f"Longest Entry: {max_words['date']} ({max_words['entry_word_count']:,} words)")

    except FileNotFoundError:
        print(f"Error: File {input_file} not found.")

if __name__ == "__main__":
    generate_stats("output/diary-parsed.ndjson", "output/diary-stats.csv")

