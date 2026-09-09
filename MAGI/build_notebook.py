import nbformat as nbf
import re
import os

app_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "MAGI_App.py")

with open(app_path, "r", encoding="utf-8") as f:
    lines = f.readlines()

nb = nbf.v4.new_notebook()

current_type = None
current_lines = []

def add_cell():
    if not current_lines:
        return
    text = "".join(current_lines).strip()
    if not text:
        return
    if current_type == "markdown":
        md_lines = []
        for line in current_lines:
            if line.startswith("# "):
                md_lines.append(line[2:])
            elif line.startswith("#"):
                md_lines.append(line[1:])
            else:
                md_lines.append(line)
        nb.cells.append(nbf.v4.new_markdown_cell("".join(md_lines).strip()))
    elif current_type == "code":
        nb.cells.append(nbf.v4.new_code_cell(text))

for line in lines:
    if line.startswith("#!") or line.startswith("# coding:"):
        continue
    if re.match(r"^# In\[.*\]:", line):
        add_cell()
        current_type = "code"
        current_lines = []
    elif line.startswith("# #"):
        add_cell()
        current_type = "markdown"
        current_lines = [line]
    else:
        if current_type is None:
            if line.startswith("#"):
                current_type = "markdown"
            else:
                current_type = "code"
        current_lines.append(line)

add_cell()

nb_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "MAGI_App.ipynb")
with open(nb_path, "w", encoding="utf-8") as f:
    nbf.write(nb, f)

print(f"Notebook MAGI_App.ipynb successfully rebuilt from MAGI_App.py with {len(nb.cells)} cells.")
