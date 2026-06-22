from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.common.exceptions import NoSuchElementException,NoAlertPresentException,NoSuchWindowException,WebDriverException
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.common.action_chains import ActionChains
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import Select
from selenium.webdriver.common.alert import Alert

import os
import time
import pandas as pd
import getpass
import traceback
import argparse
import requests

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
                "cari_islemler": "13",
                "tahsil_tediye_fatura": "13_4",
                "e_arsiv": "13_4_5"
            }
    elif username == "cemil.baritci":
        return {
                "cari_islemler": "10",
                "tahsil_tediye_fatura": "10_3",
                "e_arsiv": "10_3_5"
            }
    elif username == "gokmen.duman":
        return {
                "cari_islemler": "10",
                "tahsil_tediye_fatura": "10_4",
                "e_arsiv": "10_4_5"
            }
    else:
        return "300"
    
def run_bot(username, password, file_name, task_id):
    update(str(task_id), "in_progress")

    if username == "koray.zorlu" or username == "korayzorlu":
        url = "https://testleaseflex.arileasing.com.tr/Ari_Leasing/Logon.aspx"
    else:
        url = "https://leaseflex.arileasing.com.tr/Ari_Leasing/Logon.aspx"

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

        #go to cari işlemler
        cari_islemler = wait.until(EC.element_to_be_clickable((By.XPATH, f"//*[@id='ApplicationMenuWebTree_{get_menu_index(username)['cari_islemler']}']//span[contains(@class, 'igtr_Root')]")))
        cari_islemler.click()

        #go to tahsil tdiye fatura
        tahsil_tediye_fatura = wait.until(EC.element_to_be_clickable((By.XPATH, f"//div[@id='ApplicationMenuWebTree_{get_menu_index(username)['tahsil_tediye_fatura']}']//span[contains(@class, 'igtr_Parent')]")))
        tahsil_tediye_fatura.click()

        #import file
        excel_file = pd.ExcelFile(file_name)
        sheet_name = excel_file.sheet_names[0]

        file_data = pd.read_excel(file_name, sheet_name)
        df = pd.DataFrame(file_data)

        ####e-arsiv####
        e_arsiv = wait.until(EC.element_to_be_clickable((By.XPATH, f"//div[@id='ApplicationMenuWebTree_{get_menu_index(username)['e_arsiv']}']//span[contains(@class, 'igtr_Leaf')]")))
        e_arsiv.click()

        driver.switch_to.default_content()
        driver.switch_to.frame("main")

        error_list = []
        main_window = driver.current_window_handle

        yeni_fatura_button = wait.until(EC.presence_of_element_located((By.ID, "btnNewInvoice")))
        yeni_fatura_button.click()

        for index,row in df.iterrows():
            try:
                fatura_tipi_input = wait.until(EC.presence_of_element_located((By.ID, "cmbInvoiceTypeTextBoxMain")))
                fatura_tipi_input.click()
                fatura_tipi_input.send_keys(row["Fatura Tipi"])
                fatura_tipi_option = wait.until(EC.element_to_be_clickable((By.ID, "Tr0")))
                fatura_tipi_option.click()

                kira_plani_input = wait.until(EC.presence_of_element_located((By.ID, "CPO_cmbUCLeasingOperationProjectIdTextBoxMain")))
                kira_plani_input.click()
                kira_plani_input.send_keys(str(row["Sözleşme"]).replace(".0",""))
                kira_plani_option = wait.until(EC.element_to_be_clickable((By.ID, "Tr0")))
                kira_plani_option.click()

                gib_calisma_sekli_input = wait.until(EC.presence_of_element_located((By.ID, "cmbteiWorkTypeTextBoxMain")))
                gib_calisma_sekli_input.click()
                gib_calisma_sekli_input.clear()
                gib_calisma_sekli_input.send_keys(row["GIB Çalışma Şekli"])
                gib_calisma_sekli_option = wait.until(EC.element_to_be_clickable((By.ID, "Tr0")))
                gib_calisma_sekli_option.click()

                gib_posta_kutusu_input = wait.until(EC.presence_of_element_located((By.ID, "cmbteiPostBoxTextBoxMain")))
                gib_posta_kutusu_input.click()
                gib_posta_kutusu_input.send_keys(" ")
                gib_posta_kutusu_input.clear()
                gib_posta_kutusu_option = wait.until(EC.element_to_be_clickable((By.ID, "Tr0")))
                gib_posta_kutusu_option.click()

                gib_aciklama_input = wait.until(EC.presence_of_element_located((By.ID, "txtteiDecsription")))
                gib_aciklama_input.click()
                gib_aciklama_input.send_keys(row["GIB Açıklaması"])

                aciklama_input = wait.until(EC.presence_of_element_located((By.ID, "txtTrnReturnDocumentDescription")))
                aciklama_input.click()
                aciklama_input.send_keys(row["GIB Açıklaması"])

                tarih_input = wait.until(EC.presence_of_element_located((By.ID, "dtInvoiceDate_input")))
                tarih_input.click()
                tarih_input.send_keys(row["Fatura Tarihi"].strftime("%d.%m.%Y"))

                vade_input = wait.until(EC.presence_of_element_located((By.ID, "dtDueDate_input")))
                vade_input.click()

                fis_tipi_input = wait.until(EC.presence_of_element_located((By.ID, "cmbVoucherTypeTextBoxMain")))
                fis_tipi_input.click()
                fis_tipi_input.send_keys(row["Fiş Tipi"])
                fis_tipi_option = wait.until(EC.element_to_be_clickable((By.ID, "Tr0")))
                fis_tipi_option.click()

                kdv_input = wait.until(EC.presence_of_element_located((By.ID, "igtxtnmVATRate")))
                kdv_input.click()
                kdv_input.clear()
                kdv_input.send_keys(row["KDV Oranı (%)"])

                tutar_input = wait.until(EC.presence_of_element_located((By.ID, "igtxtnmInvoiceAmount")))
                tutar_input.click()
                tutar_input.clear()
                tutar_input.send_keys(str(row["Fatura Tutarı"]).replace(".",","))

                kur_input = wait.until(EC.presence_of_element_located((By.ID, "igtxtnmExchangeRateLocal")))
                kur_input.click()

                time.sleep(1)

                muhasebelestir_button = wait.until(EC.presence_of_element_located((By.ID, "btnPostLedger")))
                muhasebelestir_button.click()

                time.sleep(0.5)
                
                # try:
                #     wait.until(EC.alert_is_present())
                #     alert = Alert(driver)
                #     alert.accept()
                # except NoAlertPresentException:
                #     pass
                

                yeni_fatura_button = wait.until(EC.presence_of_element_located((By.ID, "btnNewInvoice")))
                yeni_fatura_button.click()

                # kira_plani_sil_button = wait.until(EC.presence_of_element_located((By.ID, "CPO_cmbUCLeasingOperationProjectIdDeleteImageBtn")))
                # kira_plani_sil_button.click()
                # proje_sil_button = wait.until(EC.presence_of_element_located((By.ID, "CPO_cmbUCProjectIdDeleteImageBtn")))
                # proje_sil_button.click()
                # sozlesme_sil_button = wait.until(EC.presence_of_element_located((By.ID, "CPO_cmbUCContractIdDeleteImageBtn")))
                # sozlesme_sil_button.click()
                # cari_sil_button = wait.until(EC.presence_of_element_located((By.ID, "CPO_cmbUCAccountIdDeleteImageBtn")))
                # cari_sil_button.click()
                # fatura_tipi_sil_button = wait.until(EC.presence_of_element_located((By.ID, "cmbInvoiceTypeDeleteImageBtn")))
                # fatura_tipi_sil_button.click()
          
            except Exception as e:
                update(str(task_id), "rejected", log=traceback.format_exc())

                driver.switch_to.default_content()
                driver.switch_to.frame("contents")

                e_arsiv = wait.until(EC.element_to_be_clickable((By.XPATH, f"//div[@id='ApplicationMenuWebTree_{get_menu_index(username)['e_arsiv']}']//span[contains(@class, 'igtr_Leaf')]")))
                e_arsiv.click()

                driver.switch_to.default_content()
                driver.switch_to.frame("main")

                error_list = []
                main_window = driver.current_window_handle

                yeni_fatura_button = wait.until(EC.presence_of_element_located((By.ID, "btnNewInvoice")))
                yeni_fatura_button.click()

                # kira_plani_sil_button = wait.until(EC.presence_of_element_located((By.ID, "CPO_cmbUCLeasingOperationProjectIdDeleteImageBtn")))
                # kira_plani_sil_button.click()
                # proje_sil_button = wait.until(EC.presence_of_element_located((By.ID, "CPO_cmbUCProjectIdDeleteImageBtn")))
                # proje_sil_button.click()
                # sozlesme_sil_button = wait.until(EC.presence_of_element_located((By.ID, "CPO_cmbUCContractIdDeleteImageBtn")))
                # sozlesme_sil_button.click()
                # cari_sil_button = wait.until(EC.presence_of_element_located((By.ID, "CPO_cmbUCAccountIdDeleteImageBtn")))
                # cari_sil_button.click()
                # fatura_tipi_sil_button = wait.until(EC.presence_of_element_located((By.ID, "cmbInvoiceTypeDeleteImageBtn")))
                # fatura_tipi_sil_button.click()

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



