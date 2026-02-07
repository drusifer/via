"""Debug UAT test issue."""
import subprocess
import sys
import tempfile
from pathlib import Path

# Simple test
with tempfile.TemporaryDirectory() as tmpdir:
    project_dir = Path(tmpdir)
    
    # Create simple test files
    (project_dir / "base.py").write_text('''
class BaseClass:
    pass

class ChildClass(BaseClass):
    pass

class GrandChildClass(ChildClass):
    pass
''')
    
    print(f"Project dir: {project_dir}")
    
    # Index it
    print("\nIndexing...")
    result = subprocess.run(
        [sys.executable, "-m", "via", "index", str(project_dir)],
        capture_output=True,
        text=True
    )
    print(f"Index return: {result.returncode}")
    
    # Test 1: Simple query
    print("\nTest 1: -mg BaseClass -tc -Vinh -mg *")
    result1 = subprocess.run(
        [sys.executable, "-m", "via", "-mg", "BaseClass", "-tc", "-Vinh", "-mg", "*"],
        cwd=str(project_dir),
        capture_output=True,
        text=True
    )
    print(f"  Return: {result1.returncode}")
    print(f"  Stdout: '{result1.stdout}'")
    print(f"  Stderr: '{result1.stderr}'")
    
    # Test 2: With type flag
    print("\nTest 2: -mg BaseClass -tc -Vinh -mg * -tc")
    result2 = subprocess.run(
        [sys.executable, "-m", "via", "-mg", "BaseClass", "-tc", "-Vinh", "-mg", "*", "-tc"],
        cwd=str(project_dir),
        capture_output=True,
        text=True
    )
    print(f"  Return: {result2.returncode}")
    print(f"  Stdout: '{result2.stdout}'")
    print(f"  Stderr: '{result2.stderr}'")
    
    # Test 3: ChildClass query
    print("\nTest 3: -mg ChildClass -tc -Vinh -mg * -tc")
    result3 = subprocess.run(
        [sys.executable, "-m", "via", "-mg", "ChildClass", "-tc", "-Vinh", "-mg", "*", "-tc"],
        cwd=str(project_dir),
        capture_output=True,
        text=True
    )
    print(f"  Return: {result3.returncode}")
    print(f"  Stdout: '{result3.stdout}'")
    print(f"  Stderr: '{result3.stderr}'")
    
    # Test 4: With -oL
    print("\nTest 4: -mg ChildClass -tc -Vinh -mg * -tc -oL")
    result4 = subprocess.run(
        [sys.executable, "-m", "via", "-mg", "ChildClass", "-tc", "-Vinh", "-mg", "*", "-tc", "-oL"],
        cwd=str(project_dir),
        capture_output=True,
        text=True
    )
    print(f"  Return: {result4.returncode}")
    print(f"  Stdout: '{result4.stdout}'")
    print(f"  Stderr: '{result4.stderr}'")
