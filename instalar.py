import subprocess
import sys

print("Instalando o customtkinter... Por favor, aguarde.")
try:
    subprocess.check_call([sys.executable, "-m", "pip", "install", "customtkinter"])
    print("\n[OK] Instalado com sucesso!")
except Exception as e:
    print(f"\n[ERRO] Ocorreu uma falha: {e}")
