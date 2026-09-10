with open("source/antares_fd/builders/environment.py", "r") as f:
    lines = f.readlines()
    
new_lines = []
for line in lines:
    if "print(f\"[MAGI] Loaded {len(envs)} ensemble members successfully." in line:
        new_lines.append("    print(f\"[MAGI] Loaded {len(envs)} ensemble members successfully.\")\n")
    elif '")' in line and "print" not in line:
        pass
    else:
        new_lines.append(line)
        
with open("source/antares_fd/builders/environment.py", "w") as f:
    f.writelines(new_lines)
