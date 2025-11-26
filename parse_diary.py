import json
import sys
import os
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
            y_str = year_part.split('-')[1]
            year = int(y_str)
            if year < 100: year += 1600 # Handle "61" -> 1661
        except ValueError:
            year = None
    else:
        try:
            year = int(year_part)
            if year < 100: year += 1600
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
    
    if not first_part:
        return False
    
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
                    # Just a number "1" or "29".
                    # Pepys usually has dot.
                    # Require punctuation OR specific context (like parens or month)
                    if len(parts) > 1:
                        # Case: "1 January"
                        if parts[1] in SHORT_MONTHS or parts[1].upper() in MONTHS:
                            return True
                        # Case: "1 (Sunday)"
                        if parts[1].startswith('('):
                            return True
                            
                    return False # "29th of May" -> remaining is "th", handled below. "1" -> False.
                
                # Check for suffix
                suffix_found = False
                suffix_len = 0
                for s in valid_suffixes:
                    if remaining.startswith(s):
                        # Special check for 'd' suffix: only allow 2d, 3d, 22d, 23d
                        if s == 'd' and val not in [2, 3, 22, 23]:
                            continue # Try other suffixes or fail
                            
                        suffix_found = True
                        suffix_len = len(s)
                        break
                
                after_suffix = remaining[suffix_len:] # e.g. ".(..." or "," or ""
                
                if suffix_found:
                    # Must be followed by punctuation or end of string (if split by space)
                    # e.g. "th." or "th," or "th" (if space followed)
                    # But "thstring" is invalid.
                    if not after_suffix:
                        # Suffix ended the word (e.g. "29th" in "29th of May")
                        # Require punctuation or special context
                        if len(parts) > 1:
                            if parts[1].startswith('('): return True
                            if parts[1] in SHORT_MONTHS or parts[1].upper() in MONTHS: return True
                        return False # "29th" followed by "of" -> False
                        
                    if not after_suffix[0].isalnum():
                        # Has punctuation, e.g. "th."
                        return True
                        
                # Check for simple dot after number
                if remaining.startswith('.'):
                    return True
                    
        return False
        
    # Case 2: Starts with Month (e.g. "Jan. 1st")
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

def is_footnote_start(line: str) -> bool:
    """Check if line is start of an indented footnote block."""
    # Check for indentation (start with space) and opening bracket
    if line.startswith(' ') or line.startswith('\t'):
        stripped = line.strip()
        if stripped.startswith('['):
            return True
    return False

def process_inline_footnotes(text: str, start_index: int, footnotes_list: List[str]) -> str:
    """
    Extract inline footnotes [text] to {N}, keep restorations [he].
    """
    result = ""
    i = 0
    n = len(text)
    while i < n:
        if text[i] == '[':
            # Find closing bracket
            j = text.find(']', i)
            if j != -1:
                content = text[i+1:j]
                
                # Heuristic: Keep if short (< 25 chars) or seems to be part of sentence flow
                # Most explanatory notes are long sentences or start with "Ed. note" or names/definitions
                
                is_restoration = False
                
                # Check for specific restoration patterns
                if len(content) < 25:
                    # Check if it looks like a definition?
                    # "i.e." is a definition/footnote usually
                    if content.strip().lower().startswith("i.e."):
                        is_restoration = False # Treat as footnote
                    elif "note" in content.lower():
                         is_restoration = False
                    else:
                        # Assume short things are restorations like [he], [she], [dirted]
                        is_restoration = True
                
                # Also check for "Ed. note" or similar explicit markers
                if "Ed." in content or "note:" in content:
                    is_restoration = False

                if is_restoration:
                    result += text[i:j+1] # Keep it including brackets
                else:
                    # Extract as footnote
                    footnotes_list.append(content)
                    marker = f"{{{start_index + len(footnotes_list) - 1}}}"
                    result += marker
                
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
    current_footnotes = []
    
    entries = []
    
    def flush_entry():
        nonlocal current_entry_lines, current_entry_date, current_footnotes
        if current_entry_date and current_entry_lines:
            # Join first
            full_text = " ".join(line.strip() for line in current_entry_lines)
            
            # Now process inline
            processed_text = process_inline_footnotes(full_text, len(current_footnotes), current_footnotes)
            
            entries.append({
                "date": current_entry_date,
                "entry": processed_text,
                "footnotes": list(current_footnotes) # Copy
            })
            
            current_entry_lines = []
            current_footnotes = []
    
    with open(file_path, 'r', encoding='utf-8') as f:
        lines = f.readlines()
        
    in_footnote_block = False
    in_bookmarks_block = False
    current_block_footnote_text = []
    
    for line in lines:
        stripped = line.strip()
        if not stripped:
            continue
            
        # Check for bookmarks block start
        if "ETEXT EDITOR’S BOOKMARKS" in stripped:
            in_bookmarks_block = True
            continue
            
        # If in bookmarks block, check if we should exit (Header or Entry Start)
        if in_bookmarks_block:
            if is_header(stripped) or is_entry_start(stripped):
                in_bookmarks_block = False
            else:
                continue

        # Check for block footnotes start
        if is_footnote_start(line):
            # Check if it's a single-line footnote
            if stripped.endswith(']'):
                # Single line footnote
                note_content = stripped.lstrip('[').rstrip(']').rstrip()
                current_footnotes.append(note_content)
                marker = f"{{{len(current_footnotes) - 1}}}"
                if current_entry_lines:
                    current_entry_lines[-1] += marker
            else:
                # Multi-line start
                in_footnote_block = True
                current_block_footnote_text = [stripped.lstrip('[').rstrip()] 
            continue
            
        if in_footnote_block:
            # Check end
            if stripped.endswith(']'):
                in_footnote_block = False
                current_block_footnote_text.append(stripped.rstrip(']').rstrip())
                
                # Finish block footnote
                note_content = " ".join(current_block_footnote_text)
                
                # Add to footnotes list
                current_footnotes.append(note_content)
                marker = f"{{{len(current_footnotes) - 1}}}"
                
                # Append marker to the last line of current entry
                if current_entry_lines:
                    current_entry_lines[-1] += marker
                else:
                    # If no entry yet (rare, maybe before first entry?), just ignore or print warning
                    pass
                
                current_block_footnote_text = []
            else:
                current_block_footnote_text.append(stripped)
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
    
    # Ensure output directory exists
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    
    with open(output_path, 'w', encoding='utf-8') as f:
        for entry in entries:
            f.write(json.dumps(entry) + '\n')
    
    print(f"Processed {len(entries)} entries.")

if __name__ == "__main__":
    process_diary("data/diary-trimmed.txt", "data/diary-parsed.ndjson")
