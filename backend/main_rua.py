import os
import json
from RUA_extractor import extract_rua

# Input PDF path
pdf_path = input("Enter PDF path: ")

# Extract RUA data
rua_data = extract_rua(pdf_path)

# Create output filename
pdf_name = os.path.splitext(os.path.basename(pdf_path))[0]

output_path = f"outputs/{pdf_name}_rua.json"

# Save JSON
with open(output_path, "w") as outfile:

    json.dump(rua_data, outfile, indent=4)

print("\nRUA JSON saved successfully!")
print("Saved at:", output_path)