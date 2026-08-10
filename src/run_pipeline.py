import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]

SCRIPTS = [
    "ingest.py",
    "load_warehouse.py",
    "build_silver.py",
    "build_marts.py",
    "build_rfm.py",
]

source = ROOT / "data" / "raw" / "online_retail_II.xlsx"

if not source.exists():
    print("Fichier source introuvable :", source)
    sys.exit(1)

for script in SCRIPTS:
    print(f"\n=== {script} ===")

    subprocess.run(
        [sys.executable, str(ROOT / "src" / script)],
        cwd=ROOT,
        check=True
    )

print("\nPipeline terminé avec succès.")