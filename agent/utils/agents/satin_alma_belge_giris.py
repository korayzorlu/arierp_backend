from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.common.exceptions import NoSuchElementException,NoAlertPresentException,NoSuchWindowException,WebDriverException
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.common.action_chains import ActionChains
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import Select
from selenium.webdriver.common.alert import Alert

import time
import pandas as pd
import getpass
import traceback
import os
import requests
import argparse

DJANGO_BASE = os.getenv("DJANGO_BASE", "http://localhost:8000/api")
AGENT_TOKEN = "__AGENT_TOKEN__"

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

def get_menu_index(username):
    if username == "koray.zorlu":
        return {
                "satin_alma": "13",
                "musteriler_ve_satislar": "13_1",
                "e_arsiv": "13_1_9",
                "e_fatura": "13_1_10"
            }
    elif username == "burcu.akgul":
        return {
                "cari_islemler": "12",
                "musteriler_ve_satislar": "12_1",
                "e_arsiv": "12_1_2",
                "e_fatura": "12_1_3"
            }
    else:
        return "300"

def run_bot(username, password, file_name, task_id):
    update(str(task_id), "in_progress")

    error_list = []

    if username == "koray.zorlu" or username == "korayzorlu":
        url = "https://testleaseflex.arileasing.com.tr/Ari_Leasing/Logon.aspx"
    else:
        url = "https://leaseflex.arileasing.com.tr/Ari_Leasing/Logon.aspx"

    options = Options()

    driver = webdriver.Chrome(options=options)
    driver.set_window_size(1920, 1080)
    wait = WebDriverWait(driver, 10)

    error_list = []

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

        #go to satın alma
        satin_alma = wait.until(EC.element_to_be_clickable((By.XPATH, "//*[@id='M_ApplicationMenuWebTree']//div[@igtag='4000']//span[contains(@class, 'igtr_Root')]")))
        # cari_islemler = wait.until(EC.element_to_be_clickable((By.XPATH, f"//*[@id='ApplicationMenuWebTree_{get_menu_index(username)['cari_islemler']}']//span[contains(@class, 'igtr_Root')]")))

        satin_alma.click()

        #go to satın alma belgeleri
        satin_alma_belgeleri = wait.until(EC.element_to_be_clickable((By.XPATH, "//*[@id='M_ApplicationMenuWebTree']//div[@igtag='4040']//span[contains(@class, 'igtr_Parent')]")))
        # musteriler_ve_satislar = wait.until(EC.element_to_be_clickable((By.XPATH, f"//div[@id='ApplicationMenuWebTree_{get_menu_index(username)['musteriler_ve_satislar']}']//span[contains(@class, 'igtr_Parent')]")))
        satin_alma_belgeleri.click()

        #go to tümü
        tumu = wait.until(EC.element_to_be_clickable((By.XPATH, "//*[@id='M_ApplicationMenuWebTree']//div[@igtag='4041']//span[contains(@class, 'igtr_Leaf')]")))
        tumu.click()

        #import file
        excel_file = pd.ExcelFile(file_name)
        sheet_name = excel_file.sheet_names[0]

        file_data = pd.read_excel(file_name, sheet_name)
        df = pd.DataFrame(file_data)

        driver.switch_to.default_content()
        driver.switch_to.frame("main")

        
        main_window = driver.current_window_handle

        # if username == "koray.zorlu" or username == "korayzorlu":
        #     uyari_kapat_button = wait.until(EC.presence_of_element_located((By.CLASS_NAME, "messageDialogOKButton")))
        #     uyari_kapat_button.click()

        for index,row in df.iterrows():
            try:
                yeni_kayit_button = wait.until(EC.presence_of_element_located((By.ID, "ListGrid_btnMenuAddNew")))
                yeni_kayit_button.click()

                sozlesme_input = wait.until(EC.element_to_be_clickable((By.ID, "cmbQuotationProjectIdTextBoxMain")))
                sozlesme_input.click()
                sozlesme_input.send_keys(str(row["Sözleşme"]))
                sozlesme_option = wait.until(EC.element_to_be_clickable((By.ID, "Tr0")))
                sozlesme_option.click()

                belge_seri_no_input = wait.until(EC.element_to_be_clickable((By.ID, "txtDocumentSerial")))
                belge_seri_no_input.click()
                belge_seri_no_input.send_keys(str(row["Fatura-1"]))

                belge_sira_no_input = wait.until(EC.element_to_be_clickable((By.ID, "txtDocumentSequence")))
                belge_sira_no_input.click()
                belge_sira_no_input.send_keys(str(row["Fatura-2"]))

                belge_tarihi_input = wait.until(EC.element_to_be_clickable((By.ID, "dtDocumentDate_input")))
                belge_tarihi_input.click()
                belge_tarihi_input.send_keys(str(row["Tarih"]))


                time.sleep(1)

                
            except Exception as e:
                update(str(task_id), "rejected", log=traceback.format_exc())

                
                print(traceback.format_exc())
                error_list.append(row["Sözleşme"])

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

    excel_dosyasi_adi = f"işlenmeyenler.xlsx"
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



