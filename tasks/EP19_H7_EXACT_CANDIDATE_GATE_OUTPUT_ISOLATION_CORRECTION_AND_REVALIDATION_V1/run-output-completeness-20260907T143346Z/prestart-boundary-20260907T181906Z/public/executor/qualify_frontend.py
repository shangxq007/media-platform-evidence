"""Run focused external-validator qualifications; never a product frontend build."""
from pathlib import Path
import subprocess,sys
if __name__=="__main__":
 raise SystemExit(subprocess.call([sys.executable,"-B",str(Path(__file__).resolve().parents[1]/"qualification/run.py"),*sys.argv[1:]]))
