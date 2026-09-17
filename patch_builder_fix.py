import re
with open('source/antares_fd/reporting/builder.py', 'r', encoding='utf-8') as f:
    text = f.read()

text = text.replace("create_standard_table(", "tables.create_standard_table(")

with open('source/antares_fd/reporting/builder.py', 'w', encoding='utf-8') as f:
    f.write(text)
