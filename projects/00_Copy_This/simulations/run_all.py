import os
import subprocess
from pathlib import Path

def main():
    current_dir = Path(__file__).resolve().parent
    # Project root is Flight_Dynamics_Antares
    project_root = current_dir.parents[2]
    
    env = os.environ.copy()
    # Add 'source' directory to PYTHONPATH
    source_dir = project_root / "source"
    current_pythonpath = env.get("PYTHONPATH", "")
    env["PYTHONPATH"] = f"{source_dir}:{current_pythonpath}" if current_pythonpath else str(source_dir)
    
    for file in sorted(current_dir.glob("*.py")):
        if file.name != "run_all.py" and file.name != "__init__.py":
            print(f"========================================")
            print(f"Running simulation: {file.name}")
            print(f"========================================")
            
            result = subprocess.run(
                [os.sys.executable, str(file)], 
                cwd=str(project_root),
                env=env
            )
            if result.returncode != 0:
                print(f"WARNING: Simulation {file.name} failed with code {result.returncode}")
                
if __name__ == "__main__":
    main()
