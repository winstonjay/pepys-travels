import json
import sys
from datetime import datetime

def check_dates(file_path: str):
    previous_date = None
    previous_line_num = 0
    
    issues = []
    
    print(f"Checking {file_path}...")
    
    with open(file_path, 'r', encoding='utf-8') as f:
        for i, line in enumerate(f, 1):
            try:
                entry = json.loads(line)
                date_str = entry.get('date')
                if not date_str:
                    print(f"Line {i}: Missing date")
                    continue
                
                current_date = datetime.strptime(date_str, "%Y-%m-%d")
                
                if previous_date:
                    if current_date < previous_date:
                        issues.append({
                            "line": i,
                            "current_date": date_str,
                            "previous_date": previous_date.strftime("%Y-%m-%d"),
                            "previous_line": previous_line_num,
                            "diff_days": (previous_date - current_date).days
                        })
                        
                previous_date = current_date
                previous_line_num = i
                
            except json.JSONDecodeError:
                print(f"Line {i}: Invalid JSON")
            except ValueError as e:
                print(f"Line {i}: Invalid date format: {e}")

    if issues:
        print(f"Found {len(issues)} out-of-order entries:")
        for issue in issues:
            print(f"Line {issue['line']} ({issue['current_date']}) is BEFORE Line {issue['previous_line']} ({issue['previous_date']}) by {issue['diff_days']} days.")
    else:
        print("All entries are in chronological order.")

if __name__ == "__main__":
    check_dates("diary-parsed.ndjson")

