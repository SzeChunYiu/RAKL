import sys

# Read the script
with open("~/Desktop/RAKL-wt683gov/scripts/surface_six_family_governed_proposal.py") as f:
    lines = f.readlines()

# Find and fix the proposal_artifact section
# Look for the line with "$schema" and insert proposal_artifact = { before it
for i, line in enumerate(lines):
    if : paper2-governed-proposal-v1, in line:
        # Insert proposal_artifact = { before this line
        lines.insert(i, "    proposal_artifact = {\n")
        break

# Find the end of the dict and add the closing brace
for i in range(len(lines)-1, 0, -1):
    if i < len(lines) and "with open(proposal_path" in lines[i]:
        # Insert closing brace before this line
        lines.insert(i, "    }\n")
        break

# Write back
with open("~/Desktop/RAKL-wt683gov/scripts/surface_six_family_governed_proposal.py", "w") as f:
    f.writelines(lines)

print("Fixed proposal_artifact dict structure")
