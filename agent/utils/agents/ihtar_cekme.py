from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.common.exceptions import NoSuchElementException,NoAlertPresentException,NoSuchWindowException,WebDriverException
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.common.action_chains import ActionChains
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import Select
from selenium.webdriver.common.alert import Alert
import requests, time, base64, uuid, os

import time
import pandas as pd
import getpass
import traceback
import argparse

# DJANGO_BASE = "http://localhost:8000/api"
DJANGO_BASE = "https://arinet.arileasing.com.tr/api"
AGENT_TOKEN = "__AGENT_TOKEN__"

def get_menu_index(username):
    if username == "koray.zorlu":
        return {
                "musteri_risk_yonetimi": "14",
                "ihtar_hazirlama": "14_2",
            }
    elif username == "gozde.ergan":
        return {
                "musteri_risk_yonetimi": "12",
                "ihtar_hazirlama": "12_2",
            }
    else:
        return "300"
    
def update(task_id, status, log=None):
    try:
        requests.post(
            f"{DJANGO_BASE}/agent/update_agent_task/",
            json={"task_id": task_id, "status": status, "log": log},
            headers={"X-Agent-Token": AGENT_TOKEN},
            timeout=5,
        )
    except Exception:
        pass

def is_browser_closed_error(exception):
    """Kullanıcının tarayıcı penceresini manuel kapatıp kapatmadığını tespit eder."""
    if isinstance(exception, NoSuchWindowException):
        return True
    if isinstance(exception, WebDriverException):
        mesaj = str(exception).lower()
        kapatma_isaretleri = [
            "no such window",
            "target window already closed",
            "web view not found",
            "chrome not reachable",
            "disconnected: not connected to devtools",
        ]
        return any(isaret in mesaj for isaret in kapatma_isaretleri)
    return False

def run_bot(username, password, file_name, task_id):
    update(str(task_id), "in_progress")

    if not username == "koray.zorlu":
        url = "https://leaseflex.arileasing.com.tr/Ari_Leasing/Logon.aspx"
    else:
        url = "https://testleaseflex.arileasing.com.tr/Ari_Leasing/Logon.aspx"

    options = Options()

    driver = webdriver.Chrome(options=options)
    driver.set_window_size(1920, 1080)
    wait = WebDriverWait(driver, 10)

    try:
        driver.get(url)

        #login
        #username_input = driver.find_element(By.ID, "txtUserName")
        username_input = wait.until(EC.element_to_be_clickable((By.ID, "txtUserName")))
        #password_input = driver.find_element(By.ID, "txtPassword")
        password_input = wait.until(EC.element_to_be_clickable((By.ID, "txtPassword")))
        #login_button = driver.find_element(By.ID, "btnLogonEx")
        login_button = wait.until(EC.element_to_be_clickable((By.ID, "btnLogonEx")))

        username_input.click()
        username_input.send_keys(username)

        password_input.click()
        password_input.send_keys(password)

        login_button.click()

        #time.sleep(2)

        #go to contents frame
        #driver.switch_to.frame("contents")
        WebDriverWait(driver, 5).until(EC.frame_to_be_available_and_switch_to_it((By.NAME, "contents")))

        #risk izleme
        risk_izleme = wait.until(EC.element_to_be_clickable((By.XPATH, f"//*[@id='ApplicationMenuWebTree_{get_menu_index(username)['musteri_risk_yonetimi']}']//span[contains(@class, 'igtr_Root')]")))
        risk_izleme.click()

        #go to kira planı detaylı
        ihtar_hazirlama = wait.until(EC.element_to_be_clickable((By.XPATH, f"//div[@id='ApplicationMenuWebTree_{get_menu_index(username)['ihtar_hazirlama']}']//span[contains(@class, 'igtr_Leaf')]")))
        ihtar_hazirlama.click()

        #import file
        excel_file = pd.ExcelFile(file_name)
        sheet_name = excel_file.sheet_names[0]

        file_data = pd.read_excel(file_name, sheet_name)
        df = pd.DataFrame(file_data)

        driver.switch_to.default_content()
        driver.switch_to.frame("main")

        error_list = []
        main_window = driver.current_window_handle

        for index,row in df.iterrows():
            try:
                musteri_ara_input = wait.until(EC.presence_of_element_located((By.ID, "cmbContractHeaderIdTextBoxMain")))
                musteri_ara_input.click()
                musteri_ara_input.send_keys(str(row["Sözleşme"]))
                # Tüm satırları bul
                rows = driver.find_elements(By.CLASS_NAME, "utopiaComboAlternateRow")
                
                if len(rows) > 1:
                    ####
                    musteri_sil_button = wait.until(EC.presence_of_element_located((By.ID, "cmbContractHeaderIdDeleteImageBtn")))
                    musteri_sil_button.click()
                    ####
                    continue
                musteri_option = wait.until(EC.element_to_be_clickable((By.ID, "Tr0")))
                musteri_option.click()

                listele_button = wait.until(EC.presence_of_element_located((By.ID, "btnList")))
                listele_button.click()

                #loading gitmesini bekle
                wait.until(EC.invisibility_of_element_located((By.CLASS_NAME, "blockUI")))

                # ihtar çekilecek sözleşmeyi bul
                sozlesme_td = wait.until(EC.presence_of_element_located((By.XPATH, f"//td[nobr[text()='{str(row['Sözleşme'])}']]")))
                
                if not sozlesme_td.is_displayed():
                    ####
                    musteri_sil_button = wait.until(EC.presence_of_element_located((By.ID, "cmbContractHeaderIdDeleteImageBtn")))
                    musteri_sil_button.click()
                    ####
                    continue

                # ihtar çek
                ihtar_button = wait.until(EC.presence_of_element_located((By.XPATH, f"//td[@id='grdLegalWarningListxGrid_rc_0_5']//input[@type='button']")))
                ihtar_button.click()
                
                #loading gitmesini bekle
                wait.until(EC.invisibility_of_element_located((By.CLASS_NAME, "blockUI")))

                ####
                musteri_sil_button = wait.until(EC.element_to_be_clickable((By.ID, "cmbContractHeaderIdDeleteImageBtn")))
                musteri_sil_button.click()
                ####
                
            except Exception as e:
                update(str(task_id), "rejected", log=traceback.format_exc())
                ####
                musteri_sil_button = wait.until(EC.element_to_be_clickable((By.ID, "cmbContractHeaderIdDeleteImageBtn")))
                musteri_sil_button.click()
                ####
                print(traceback.format_exc())
                error_list.append(str(row["Sözleşme"]))

        update(str(task_id), "completed")
    except Exception as e:
        if is_browser_closed_error(e):
            update(str(task_id), "rejected", log="Kullanıcı tarayıcıyı kapattı.")
        else:
            update(str(task_id), "rejected", log=traceback.format_exc())
    finally:
        try:
            driver.quit()
        except Exception:
            pass

    data = {
        "Sözleşme": [],
    }

    for error in error_list:
        data["Sözleşme"].append(error)

    df = pd.DataFrame(data)
    df = df.drop_duplicates()

    excel_dosyasi_adi = f"ihtar-çekilmeyenler.xlsx"
    with pd.ExcelWriter(excel_dosyasi_adi, engine='openpyxl') as writer:
        df.to_excel(writer, sheet_name='Sayfa', index=False)

    print("------------")

    return error_list





if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--username", required=True)
    parser.add_argument("--password", required=True)
    parser.add_argument("--file", required=True)
    parser.add_argument("--task-id", required=True)
    args = parser.parse_args()

    error_list = run_bot(args.username, args.password, args.file, args.task_id)

    update(args.task_id, "completed")
