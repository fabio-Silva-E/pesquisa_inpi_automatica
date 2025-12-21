from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
import os
import time

BASE_DIR = os.path.dirname(os.path.abspath(__file__))

BUSTER_PATH = os.path.join(BASE_DIR, "ui", "buster", "3.1.0_0")
PROFILE_PATH = os.path.join(BASE_DIR, "ui", "chrome_profile")

options = Options()

# 🔐 PERFIL PERSISTENTE (OBRIGATÓRIO)
options.add_argument(f"--user-data-dir={PROFILE_PATH}")
options.add_argument("--profile-directory=Default")

# 🧩 EXTENSÃO BUSTER
options.add_argument(f"--load-extension={BUSTER_PATH}")

# ⚙️ ANTI-DETECÇÃO BÁSICA
options.add_argument("--disable-blink-features=AutomationControlled")
options.add_experimental_option("excludeSwitches", ["enable-automation"])
options.add_experimental_option("useAutomationExtension", False)

driver = webdriver.Chrome(options=options)
driver.maximize_window()

print("✅ Chrome iniciado com Buster e sessão salva")

# 1️⃣ ABRE O SITE
driver.get("https://www.google.com/recaptcha/api2/demo")

# 2️⃣ AGUARDA O IFRAME DO CHECKBOX
iframe = WebDriverWait(driver, 60).until(
    EC.presence_of_element_located(
        (By.CSS_SELECTOR, "iframe[src*='api2/anchor']")
    )
)

driver.switch_to.frame(iframe)

# 3️⃣ CLICA NO CHECKBOX
checkbox = WebDriverWait(driver, 20).until(
    EC.element_to_be_clickable((By.ID, "recaptcha-anchor"))
)
checkbox.click()
print("☑️ Checkbox clicado")

iframe2 = WebDriverWait(driver, 60).until(
    EC.presence_of_element_located(
        (By.CSS_SELECTOR, "iframe[src*='api2/rc-controls']")
    )
)

driver.switch_to.frame(iframe2)
#clica no antcaptcha
antcaptcha = WebDriverWait(driver, 20).until(
    EC.element_to_be_clickable((By.ID, "solver-button"))
)
#antcaptcha.click()
print("☑️ antcaptcha clicado")

driver.switch_to.default_content()

# 4️⃣ AGUARDA O DESAFIO (BUSTER TENTA AGIR)
print("⏳ Aguardando desafio / possível ação do Buster...")
time.sleep(20)

# 5️⃣ VERIFICA TOKEN (NO DEMO NORMALMENTE NÃO EXISTE)
try:
    token = driver.find_element(
        By.CSS_SELECTOR, "textarea#g-recaptcha-response"
    ).get_attribute("value")

    if token:
        print("✅ Token gerado:", token[:50], "...")
    else:
        print("❌ Token vazio")
except:
    print("❌ Nenhum token encontrado (esperado no site demo)")

# 6️⃣ MANTÉM O CHROME ABERTO PARA INSPEÇÃO
print("🧩 Chrome permanecerá aberto para análise manual")
time.sleep(300)
