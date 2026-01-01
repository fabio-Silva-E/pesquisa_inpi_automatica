import subprocess
import time
import os
import requests
import sys
import zipfile
import io
import random
OPENVPN_EXE = r"C:\Program Files\OpenVPN\bin\openvpn.exe"
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
VPN_DIR = os.path.join(BASE_DIR, "vpn")
class VPNManager:
    def __init__(self):
        self.process = None
        self.ovpns = [
            os.path.join(VPN_DIR, f)
            for f in os.listdir(VPN_DIR)
            if f.endswith(".ovpn")
        ]
        if not self.ovpns:
            raise RuntimeError("Nenhum arquivo .ovpn encontrado")

        random.shuffle(self.ovpns)  # ✅ AGORA SIM
        self.index = 0

    def conectar(self, status_callback=None):
        if status_callback:
            status_callback("🌐 IP: Aguardando VPN estabilizar...")

        print("INICIANDO VPN...")
        if self.process:
            self.desconectar()

        ovpn = self.ovpns[self.index]
        self.index = (self.index + 1) % len(self.ovpns)
        startupinfo = subprocess.STARTUPINFO()
        startupinfo.dwFlags |= subprocess.STARTF_USESHOWWINDOW
        startupinfo.wShowWindow = subprocess.SW_HIDE  # 🔥 ESCONDE DE VEZ
        self.process = subprocess.Popen(
            [OPENVPN_EXE, "--config", ovpn],
            cwd=VPN_DIR,
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
            creationflags=subprocess.CREATE_NO_WINDOW  # 🔥 OCULTA O CONSOLE
        
        )


        self._aguardar_rede_estavel()
        ip = self.ip_atual()
        if status_callback:
            status_callback(f"🌐 IP: {ip}")

        return ip

    def desconectar(self):
        if self.process:
            self.process.kill()
            self.process.wait()
            self.process = None
            time.sleep(8)


    def ip_atual(self):
        try:
            return requests.get("https://api.ipify.org", timeout=5).text
        except:
            return "Indisponível"

    def _aguardar_rede_estavel(self, timeout=40):
        print("⏳ Aguardando rede estabilizar...")
        inicio = time.time()

        while time.time() - inicio < timeout:
            try:
                r = requests.get("https://www.google.com", timeout=5)
                if r.status_code == 200:
                    print("✅ Rede estabilizada")
                    return
            except:
                pass
            time.sleep(2)

        raise RuntimeError("❌ Rede não estabilizou após VPN")





