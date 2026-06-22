from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.common.exceptions import NoSuchElementException,NoSuchWindowException,WebDriverException
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.common.action_chains import ActionChains
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import Select

import time
import pandas as pd
from utils import *
import getpass
import os
import requests
import argparse
import traceback

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

def run_bot(username, password, file_name, task_id):
    update(str(task_id), "in_progress")

    if username == "koray.zorlu" or username == "korayzorlu":
        url = "https://testleaseflex.arileasing.com.tr/Ari_Leasing/Logon.aspx"
    else:
        url = "https://leaseflex.arileasing.com.tr/Ari_Leasing/Logon.aspx"

    options = Options()

    driver = webdriver.Chrome(options=options)
    driver.set_window_size(1920, 1080)
    wait = WebDriverWait(driver, 30)

    import_type = '2'

    try:
        driver.get(url)

        #login
        username_input = driver.find_element(By.ID, "txtUserName")
        password_input = driver.find_element(By.ID, "txtPassword")
        login_button = driver.find_element(By.ID, "btnLogonEx")

        username_input.click()
        username_input.send_keys(username)

        password_input.click()
        password_input.send_keys(password)

        login_button.click()

        #time.sleep(2)

        #go to contents frame
        #driver.switch_to.frame("contents")
        #WebDriverWait(driver, 30).until(EC.frame_to_be_available_and_switch_to_it("contents"))
        WebDriverWait(driver, 5).until(EC.frame_to_be_available_and_switch_to_it((By.NAME, "contents")))

        #go to cari fiş
        if username == "gokmen.duman":
            menu_sira_1 = "11"
            menu_sira_2 = "11_6"
            menu_sira_3 = "11_6_3"
        elif username == "cemil.baritci":
            menu_sira_1 = "11"
            menu_sira_2 = "11_4"
            menu_sira_3 = "11_4_3"
        else:
            if not username == "koray.zorlu" or username == "korayzorlu":
                menu_sira_1 = "14"
                menu_sira_2 = "14_6"
                menu_sira_3 = "14_6_3"
            else:
                menu_sira_1 = "16"
                menu_sira_2 = "16_6"
                menu_sira_3 = "16_6_3"

        genel_muhasebe_button = wait.until(EC.element_to_be_clickable((By.XPATH, f"//*[@id='ApplicationMenuWebTree_{menu_sira_1}']//span[contains(@class, 'igtr_Root')]")))
        #genel_muhasebe_button = driver.find_element(By.ID, f"ApplicationMenuWebTree_{menu_sira_1}").find_element(By.CLASS_NAME, "igtr_Root")
        genel_muhasebe_button.click()

        muhasebe_fisleri_button = wait.until(EC.element_to_be_clickable((By.XPATH, f"//div[@id='ApplicationMenuWebTree_{menu_sira_2}']//span[contains(@class, 'igtr_Parent')]")))
        #muhasebe_fisleri_button = driver.find_element(By.ID, f"ApplicationMenuWebTree_{menu_sira_2}").find_element(By.CLASS_NAME, "igtr_Parent")
        muhasebe_fisleri_button.click()

        cari_fisleri_button = wait.until(EC.element_to_be_clickable((By.XPATH, f"//div[@id='ApplicationMenuWebTree_{menu_sira_3}']//span[contains(@class, 'igtr_Leaf')]")))
        #cari_fisleri_button = driver.find_element(By.ID, f"ApplicationMenuWebTree_{menu_sira_3}").find_element(By.CLASS_NAME, "igtr_Leaf")
        cari_fisleri_button.click()

        driver.switch_to.default_content()
        #driver.switch_to.frame("main")
        WebDriverWait(driver, 30).until(EC.frame_to_be_available_and_switch_to_it("main"))
        #time.sleep(0.5)

        if import_type == "2":
            #type_select_element = driver.find_element(By.ID, "ddlAccountType")
            type_select_element = wait.until(EC.element_to_be_clickable((By.ID, "ddlAccountType")))
            type_select = Select(type_select_element)
            type_select.select_by_visible_text("Banka")

        #go to yeni fiş
        # driver.switch_to.default_content()
        # driver.switch_to.frame("main")
        # time.sleep(0.5)

        #yeni_fis_button = driver.find_element(By.ID, "btnNewVoucher")
        yeni_fis_button = wait.until(EC.element_to_be_clickable((By.ID, "btnNewVoucher")))
        yeni_fis_button.click()
        #time.sleep(2)

        tarih_input = wait.until(EC.element_to_be_clickable((By.ID, "dtDate_input")))
        tarih_input.click()
        tarih_input.send_keys(date)

        #fis_grubu_input = driver.find_element(By.ID, "cmbVoucherGroupTextBoxMain")
        fis_grubu_input = wait.until(EC.element_to_be_clickable((By.ID, "cmbVoucherGroupTextBoxMain")))
        fis_grubu_input.click()
        fis_grubu_input.send_keys("mahsup")
        #time.sleep(1.5)
        #fis_grubu_option = driver.find_element(By.ID, "Tr0")
        fis_grubu_option = wait.until(EC.element_to_be_clickable((By.ID, "Tr0")))
        fis_grubu_option.click()

        #fis_tipi_input = driver.find_element(By.ID, "cmbVoucherTypeTextBoxMain")
        fis_tipi_input = wait.until(EC.element_to_be_clickable((By.ID, "cmbVoucherTypeTextBoxMain")))
        fis_tipi_input.click()
        fis_tipi_input.send_keys("mahsup")
        #time.sleep(1.5)
        #fis_tipi_option = driver.find_element(By.ID, "Tr0")
        fis_tipi_option = wait.until(EC.element_to_be_clickable((By.ID, "Tr0")))
        fis_tipi_option.click()

        noBakiyeCheck = driver.find_element(By.ID, "chkAccountWithouBalance")
        noBakiyeCheck.click()

        # add row
        # add_row_button = driver.find_element(By.ID, "grdLedgerVoucherxGrid_an_0")
        # add_row_button.click()

        # # add kira
        # islem_grubu_block = driver.find_element(By.ID, "grdLedgerVoucherxGrid_rc_0_2").find_element(By.CSS_SELECTOR, "nobr")
        # islem_grubu_block.click()
        # islem_grubu_input = driver.find_element(By.ID, "grdLedgerVoucherxGrid_tb")
        # islem_grubu_input.send_keys("kira")
        # time.sleep(3)
        # islem_grubu_option = driver.find_element(By.ID, "Tr0")
        # islem_grubu_option.click()

        #import file
        page = 3 if import_type == "1" else 4
        excel_file = pd.ExcelFile("mizan.xlsx")
        sheet_name = excel_file.sheet_names[page]

        file_data = pd.read_excel("mizan.xlsx", sheet_name)
        df_ham = pd.DataFrame(file_data)

        #df = df_ham[df_ham["Grup"] == int(group)].reset_index(drop=True)
        df = df_ham[:int(group)]

        if import_type == "1":
            musteri_yontemi(df,driver,By,wait,EC,ActionChains)
        elif import_type == "2":
            banka_yontemi(df,driver,By,wait,EC,ActionChains)
        else:
            driver.quit()
            print("Yöntem hatalı!")

        bos_block = driver.find_element(By.ID, f"grdLedgerVoucherxGrid_div")
        bos_block.click()

        bakiye_block = driver.find_element(By.ID, "igtxtnmVoucherBalance")
        bakiye = bakiye_block.get_attribute("value")
        bakiye = bakiye.replace(".","")

        bakiye_type_block = driver.find_element(By.ID, "txtAmountType")
        bakiye_type = bakiye_type_block.get_attribute("value")

        if bakiye != 0 or bakiye != str(0):
            row_count = len(df) if import_type == "1" else len(df) + 2
            add_row_button = driver.find_element(By.ID, "grdLedgerVoucherxGrid_an_0")
            add_row_button.click()

            select_input = driver.find_element(By.ID, f"grdLedgerVoucherxGrid_rc_{row_count}_0")
            select_input.click()

            pb_block_no = "11" if import_type == "1" else "8"
            pb_block = driver.find_element(By.ID, f"grdLedgerVoucherxGrid_rc_{row_count}_{pb_block_no}").find_element(By.CSS_SELECTOR, "nobr")
            pb_block.click()
            pb_input = driver.find_element(By.ID, "grdLedgerVoucherxGrid_tb")
            pb_input.send_keys("tl")
            #pb_option = driver.find_element(By.ID, "Tr0")
            pb_option = wait.until(EC.element_to_be_clickable((By.ID, "Tr0")))
            pb_option.click()

            musteri_block_no = "7" if import_type == "1" else "13"
            musteri_block = driver.find_element(By.ID, f"grdLedgerVoucherxGrid_rc_{row_count}_{musteri_block_no}")
            main_window = driver.current_window_handle
            musteri_block.click()

            # go to menu window
            wait.until(EC.number_of_windows_to_be(2))
            for window_handle in driver.window_handles:
                if window_handle != main_window:
                    driver.switch_to.window(window_handle)
                    break

            musteri_karti_block = driver.find_element(By.ID, "WebGridSearch_rc_0_1").find_element(By.CSS_SELECTOR, "nobr")
            actions = ActionChains(driver)
            actions.double_click(musteri_karti_block).perform()

            musteri_karti_input = driver.find_element(By.ID, "WebGridSearch_tb")
            musteri_karti_input.send_keys("392.99.7.00.003")

            search_button = driver.find_element(By.CLASS_NAME, "ig_38e2bc54_r1")
            search_button.click()
            #time.sleep(1)

            try:
                #searched_row = driver.find_element(By.ID, "WebGrid_l_0")
                searched_row = wait.until(EC.element_to_be_clickable((By.ID, "WebGrid_l_0")))
                searched_row.click()
            except:
                pass
            
            ok_button = driver.find_element(By.ID, "btnOk")
            ok_button.click()
            
            # back to main window
            if len(driver.window_handles) > 1:
                driver.close()

            wait.until(EC.number_of_windows_to_be(1))
            for window_handle in driver.window_handles:
                if window_handle == main_window:
                    driver.switch_to.window(window_handle)
                    break
            
            driver.switch_to.default_content()
            driver.switch_to.frame("main")

            if bakiye_type == "A":
                eklenecek_bakiye_type = "B"
            elif bakiye_type == "B":
                eklenecek_bakiye_type = "A"

            aciklama_block_no = "17" if import_type == "1" else "16"
            aciklama_block = driver.find_element(By.ID, f"grdLedgerVoucherxGrid_rc_{row_count}_{aciklama_block_no}").find_element(By.CSS_SELECTOR, "nobr")
            aciklama_block.click()
            aciklama_input = driver.find_element(By.ID, "grdLedgerVoucherxGrid_tb")
            aciklama_input.send_keys("Tapu Devri Nedeniyle Cari Virmanı")

            b_a_block_no = "18" if import_type == "1" else "15"
            b_a_block = driver.find_element(By.ID, f"grdLedgerVoucherxGrid_rc_{row_count}_{b_a_block_no}").find_element(By.CSS_SELECTOR, "nobr")
            b_a_block.click()
            b_a_input = driver.find_element(By.ID, "grdLedgerVoucherxGrid_tb")
            b_a_input.send_keys(eklenecek_bakiye_type)

            tutar_block_no = "19" if import_type == "1" else "17"
            tutar_block = driver.find_element(By.ID, f"grdLedgerVoucherxGrid_rc_{row_count}_{tutar_block_no}").find_element(By.CSS_SELECTOR, "nobr")
            tutar_block.click()
            tutar_input = driver.find_element(By.ID, "igtxtgrdLedgerVoucher_DoubleColumn")
            tutar_input.send_keys(bakiye)

        bos_block = driver.find_element(By.ID, f"grdLedgerVoucherxGrid_div")
        bos_block.click()
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


    print(f"Bakiye: {bakiye}")

    #final
    print("İşlem tamamlandı. Tarayıcıyı kapatmak için pencereyi kendiniz kapatın.")
    print("Tarayıcı kapanana kadar bekleniyor...")

    try:
        while True:
            # Tarayıcı hala açık mı kontrol et
            driver.title  # bir etkileşim olsun ki hata fırlatsın kapanırsa
    except:
        print("Tarayıcı kapatıldı. Program sonlandırılıyor.")

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--username", required=True)
    parser.add_argument("--password", required=True)
    parser.add_argument("--file", required=True)
    parser.add_argument("--task-id", required=True)
    args = parser.parse_args()

    error_list = run_bot(args.username, args.password, args.file, args.task_id)

    update(args.task_id, "completed")