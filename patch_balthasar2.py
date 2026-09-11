import sys
import os

with open("MAGI/balthasar.py", "r") as f:
    content = f.read()

# I will add relative_humidity_pct and cloud_cover_pct to df_member
new_metadata = """            df_member['w_up_mps'] = 0.0
            df_member['relative_humidity_pct'] = 50.0
            df_member['cloud_cover_pct'] = 50.0
"""
content = content.replace("            df_member['w_up_mps'] = 0.0\n", new_metadata)

with open("MAGI/balthasar.py", "w") as f:
    f.write(content)
