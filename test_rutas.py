import os

base_dir = os.path.dirname(os.path.abspath(__file__))
print(f"Base dir: {base_dir}")

scripts = ["inicializar_bd_fernet.py", "check_db.py", "scripts/generar_manual_pdf.py"]

for script in scripts:
    path = os.path.join(base_dir, script)
    print(f"{script}: {'✅' if os.path.exists(path) else '❌'} {path}")
