import sys
filename = "projects/neblina_1/config/monte_carlo.yaml"
with open(filename, "r") as f:
    lines = f.readlines()

with open(filename, "w") as f:
    for line in lines:
        if line.startswith("     "): # 5 spaces
            line = line[1:]
        elif line.startswith("       "): # 7 spaces -> wait, if it was 7, removing 1 makes it 6. But originally if 5 spaces -> 4 spaces, 7 spaces -> 6 spaces.
            pass
        f.write(line)
