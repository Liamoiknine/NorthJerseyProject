#!/usr/bin/env python3
"""
Script to combine multiple JSONL dataset files into a single master dataset.
Only keeps 'instruction' and 'response' fields from each file.
"""

import json
import os
from pathlib import Path

# Define the files to combine in order
FILES_TO_COMBINE = [
    "question_answer_data.jsonl",
    "multi_turn_data.jsonl",
    "emotional_data.jsonl",
    "everyday_topics_data.jsonl",
    "guardrails_data.jsonl",
    "environmental_grounding_data.jsonl"
]

OUTPUT_FILE = "master_dataset.jsonl"

def extract_instruction_response(obj):
    """
    Extract only 'instruction' and 'response' fields from a JSON object.
    Returns None if either field is missing.
    """
    if "instruction" not in obj or "response" not in obj:
        return None
    
    return {
        "instruction": obj["instruction"],
        "response": obj["response"]
    }

def process_jsonl_file(filepath):
    """
    Process a single JSONL file and yield (instruction, response) objects.
    Handles cases where multiple JSON objects might be on the same line.
    """
    if not os.path.exists(filepath):
        print(f"Warning: File not found: {filepath}")
        return
    
    with open(filepath, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # Parse JSON objects by tracking brace counts (handles multiple objects per line)
    brace_count = 0
    start_pos = 0
    
    for i, char in enumerate(content):
        if char == '{':
            if brace_count == 0:
                start_pos = i
            brace_count += 1
        elif char == '}':
            brace_count -= 1
            if brace_count == 0:
                # We have a complete JSON object
                json_str = content[start_pos:i+1].strip()
                if json_str:
                    try:
                        obj = json.loads(json_str)
                        extracted = extract_instruction_response(obj)
                        if extracted:
                            yield extracted
                    except json.JSONDecodeError as e:
                        print(f"Warning: Failed to parse JSON in {filepath} at position {start_pos}: {e}")
                        continue

def main():
    # Get the directory where this script is located
    script_dir = Path(__file__).parent
    
    output_path = script_dir / OUTPUT_FILE
    
    total_count = 0
    file_counts = {}
    
    print("Combining datasets...")
    print("-" * 50)
    
    with open(output_path, 'w', encoding='utf-8') as outfile:
        for filename in FILES_TO_COMBINE:
            filepath = script_dir / filename
            file_count = 0
            
            print(f"Processing {filename}...", end=" ")
            
            for obj in process_jsonl_file(filepath):
                outfile.write(json.dumps(obj, ensure_ascii=False) + '\n')
                file_count += 1
                total_count += 1
            
            file_counts[filename] = file_count
            print(f"{file_count} entries")
    
    print("-" * 50)
    print(f"Total entries written: {total_count}")
    print(f"Output file: {output_path}")
    
    # Print summary
    print("\nSummary by file:")
    for filename, count in file_counts.items():
        print(f"  {filename}: {count} entries")

if __name__ == "__main__":
    main()

