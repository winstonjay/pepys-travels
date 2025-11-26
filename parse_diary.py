import json
import sys
from typing import List, Dict, Optional

# Constants
MONTHS = {
    "JANUARY": 1, "FEBRUARY": 2, "MARCH": 3, "APRIL": 4, "MAY": 5, "JUNE": 6,
    "JULY": 7, "AUGUST": 8, "SEPTEMBER": 9, "OCTOBER": 10, "NOVEMBER": 11, "DECEMBER": 12
}

SHORT_MONTHS = {
    "Jan": 1, "Feb": 2, "Mar": 3, "Apr": 4, "May": 5, "Jun": 6,
    "Jul": 7, "Aug": 8, "Sep": 9, "Oct": 10, "Nov": 11, "Dec": 12
}

def is_header(line: str) -> bool:
    """Check if line is a Month Year header (e.g. JANUARY 1659-1660)."""
    clean_line = line.strip()
    if not clean_line:
        return False
    
    # Header must be uppercase (ignoring numbers and separators)
    # and contain a year-like structure
    parts = clean_line.split()
    if not parts:
        return False
        
    first_word = parts[0].replace(',', '').replace('.', '')
    if first_word not in MONTHS:
        return False
        
    # Check if the line contains digits (for the year)
    has_digits = any(c.isdigit() for c in clean_line)
    
    # Check if mostly uppercase
    is_upper = clean_line.replace('-', ' ').replace('0', '').replace('1', '').replace('2', '').replace('3', '').replace('4', '').replace('5', '').replace('6', '').replace('7', '').replace('8', '').replace('9', '').strip().isupper()
    
    return has_digits and is_upper

def parse_header(line: str) -> tuple[Optional[int], Optional[int]]:
    """Extract month and year from header."""
    parts = line.strip().split()
    if not parts:
        return None, None
        
    month_str = parts[0]
    month = MONTHS.get(month_str)
    
    year_part = parts[-1] # Usually at the end
    
    # Handle "1659-1660" -> 1660 (modern year)
    if '-' in year_part:
        try:
            year = int(year_part.split('-')[1])
        except ValueError:
            year = None
    else:
        try:
            year = int(year_part)
        except ValueError:
            year = None
            
    return month, year

def is_entry_start(line: str) -> bool:
    """Check if line starts a new entry (e.g. '1st.', 'Jan. 1st')."""
    clean_line = line.strip()
    if not clean_line:
        return False
        
    # Must start with a number or a month name
    parts = clean_line.split()
    if not parts:
        return False
        
    first_part = parts[0].rstrip('.,')
    
    # Case 1: Starts with number (e.g. "1st.", "2nd.")
    if first_part[0].isdigit():
        # Extract the numeric part
        num_str = ""
        for char in first_part:
            if char.isdigit():
                num_str += char
            else:
                break
        
        if num_str:
            val = int(num_str)
            # Day of month constraint (1-31)
            if 1 <= val <= 31:
                # Check for valid suffix or dot
                # We check the original part (without rstrip, but split by space)
                # parts[0] is like "5th,(Lord's"
                
                raw_first = parts[0]
                remaining = raw_first[len(num_str):] # e.g. "th,(Lord's" or "." or ""
                
                valid_suffixes = ['st', 'nd', 'rd', 'th', 'd']
                
                # 1. Exact match suffix + dot/comma/end
                # e.g. "1st." "1st," "1."
                
                if not remaining: 
                    # Just a number. Pepys usually has dot. But maybe "1 Jan"
                    if len(parts) > 1:
                        return True
                    return False # Just "1" on a line? Unlikely entry start.
                
                # Check for suffix
                suffix_found = False
                suffix_len = 0
                for s in valid_suffixes:
                    if remaining.startswith(s):
                        suffix_found = True
                        suffix_len = len(s)
                        break
                
                after_suffix = remaining[suffix_len:] # e.g. ".(..." or "," or ""
                
                if suffix_found:
                    # Must be followed by punctuation or end of string (if split by space)
                    # e.g. "th." or "th," or "th" (if space followed)
                    # But "thstring" is invalid.
                    if not after_suffix:
                        return True
                    if not after_suffix[0].isalnum():
                        return True
                        
                # Check for simple dot after number
                if remaining.startswith('.'):
                    return True
                    
        return False
        
    # Case 2: Starts with Month (e.g. "Jan. 1st")
    # Check against short months or full months (capitalized title case usually)
    first_part_clean = first_part.replace('.', '')
    if first_part_clean in SHORT_MONTHS or first_part_clean.upper() in MONTHS:
        # Check if second part exists and is a number/ordinal
        if len(parts) > 1 and parts[1][0].isdigit():
            return True
            
    return False

def parse_entry_date(line: str, current_year: int, current_month: int) -> tuple[int, int, int, str]:
    """Parse the date from an entry line. Returns (year, month, day, cleaned_line)."""
    clean_line = line.strip()
    parts = clean_line.split()
    
    day = 1
    month = current_month
    year = current_year
    
    first_part = parts[0].rstrip('.,')
    
    # Detect if it starts with month
    first_part_clean = first_part.replace('.', '')
    start_idx = 0
    
    if first_part_clean in SHORT_MONTHS:
        month = SHORT_MONTHS[first_part_clean]
        start_idx = 1
    elif first_part_clean.upper() in MONTHS:
        month = MONTHS[first_part_clean.upper()]
        start_idx = 1
        
    # Parse day part (e.g. "1st", "2nd", "1")
    day_part = parts[start_idx].rstrip('.,:()')
    # Remove suffix like st, nd, rd, th
    day_str = ""
    for char in day_part:
        if char.isdigit():
            day_str += char
        else:
            break
            
    if day_str:
        day = int(day_str)
        
    return year, month, day, line

def is_footnote(line: str) -> bool:
    """Check if line is an indented footnote block."""
    # Check for indentation (start with space) and opening bracket
    if line.startswith(' ') or line.startswith('\t'):
        stripped = line.strip()
        if stripped.startswith('['):
            return True
    return False

def clean_inline_footnotes(text: str) -> str:
    """
    Remove explanatory footnotes [text] but keep restorations like [he].
    Strategy: 
    1. Find brackets [ ]
    2. If text inside is short (e.g. < 15 chars) or looks like a restoration (starts with lowercase or specific words), keep it.
    3. Otherwise remove.
    """
    # Simple bracket removal for now as requested: "remove all the footnotes but keep references in place"
    # User clarified: "Remove only explanatory notes (long text/definitions) and keep restorations like [he]"
    
    result = ""
    i = 0
    n = len(text)
    while i < n:
        if text[i] == '[':
            # Find closing bracket
            j = text.find(']', i)
            if j != -1:
                content = text[i+1:j]
                # Heuristic: Keep if short (< 20 chars) or seems to be part of sentence flow
                # Most explanatory notes are long sentences or start with "Ed. note" or names/definitions
                
                is_restoration = False
                if len(content) < 25:
                    is_restoration = True
                elif content.strip().lower().startswith("i.e."):
                    is_restoration = True
                
                if is_restoration:
                    result += text[i:j+1] # Keep it including brackets
                else:
                    pass # Skip it
                i = j + 1
                continue
        result += text[i]
        i += 1
    return result

def process_diary(file_path: str, output_path: str):
    current_year = 1660
    current_month = 1
    current_entry_date = None
    current_entry_lines = []
    
    entries = []
    
    def flush_entry():
        nonlocal current_entry_lines, current_entry_date
        if current_entry_date and current_entry_lines:
            full_text = " ".join(line.strip() for line in current_entry_lines)
            cleaned_text = clean_inline_footnotes(full_text)
            entries.append({
                "date": current_entry_date,
                "entry": cleaned_text
            })
            current_entry_lines = []
    
    with open(file_path, 'r', encoding='utf-8') as f:
        lines = f.readlines()
        
    # Skip file header (first few lines usually file metadata in some text files, but here seems to start with HEADER)
    
    in_footnote_block = False
    
    for line in lines:
        stripped = line.strip()
        if not stripped:
            continue
            
        # Check for block footnotes
        if is_footnote(line):
            in_footnote_block = True
            continue
            
        if in_footnote_block:
            # Check if we are still in footnote block (indentation continues)
            # Or if it ended (end bracket usually)
            if line.strip().endswith(']'):
                in_footnote_block = False
            # Also if indentation stops, it might be end of footnote
            if not (line.startswith(' ') or line.startswith('\t')):
                in_footnote_block = False
                # Reprocess this line as it is not a footnote
            else:
                continue

        if is_header(stripped):
            m, y = parse_header(stripped)
            if m and y:
                current_month = m
                current_year = y
            continue
            
        if is_entry_start(stripped):
            flush_entry()
            year, month, day, _ = parse_entry_date(stripped, current_year, current_month)
            current_entry_date = f"{year:04d}-{month:02d}-{day:02d}"
            current_entry_lines.append(stripped)
        else:
            if current_entry_date:
                current_entry_lines.append(stripped)
                
    flush_entry()
    
    with open(output_path, 'w', encoding='utf-8') as f:
        for entry in entries:
            f.write(json.dumps(entry) + '\n')
    
    print(f"Processed {len(entries)} entries.")

if __name__ == "__main__":
    process_diary("diary-sample.txt", "diary-parsed.jsonl")

