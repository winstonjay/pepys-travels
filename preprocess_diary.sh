#!/bin/bash
set -e

echo "Starting Pepys Diary Preprocessing..."

# Create directories
echo "Creating directories..."
mkdir -p data data

# 1. Fetch
echo "Running fetch_diary.py..."
python3 fetch_diary.py

# 2. Parse
echo "Running parse_diary.py..."
python3 parse_diary.py

# 3. Check Dates
echo "Running check_dates.py..."
python3 check_dates.py

# 4. Generate Stats
echo "Running generate_stats.py..."
python3 generate_stats.py

echo "Preprocessing complete!"

