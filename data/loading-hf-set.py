from datasets import load_dataset
import os

# check dir
script_dir = os.path.dirname(os.path.abspath(__file__))
output_file = os.path.join(script_dir, "QA_data.jsonl")

# create file if doens't exist
if not os.path.exists(output_file):
    ds = load_dataset("rsilveira79/soprano_dpo_pairs")
    ds["train"] = ds["train"].remove_columns(["rejected"])
    ds["train"] = ds["train"].rename_columns({"question": "instruction", "chosen": "response"})
    ds["train"].to_json(output_file)
    print(f"file created at {output_file}")
