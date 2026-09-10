with open("projects/neblina_1/motors/Yaripo_teste_est_2_2.eng", "r") as f:
    lines = f.readlines()
with open("projects/neblina_1/motors/Yaripo_teste_est_2_2.eng", "w") as f:
    for line in lines:
        parts = line.strip().split()
        if len(parts) == 2 and not line.startswith(';'):
            try:
                f.write(f"{float(parts[0]):.3f} {float(parts[1]):.2f}\n")
            except:
                f.write(line)
        else:
            f.write(line.strip() + "\n")
