# local_agent.py — Bu tek seferlik kurulur, güncellenmez
import urllib3
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)
import sys
import os
import time
import uuid
import base64
import subprocess
import tempfile
import requests
import win32serviceutil
import win32service
import win32event
import win32ts
import servicemanager
import traceback
import shutil
import logging



def get_active_username():
    try:
        sessions = win32ts.WTSEnumerateSessions(win32ts.WTS_CURRENT_SERVER_HANDLE)
        for session in sessions:
            if session["State"] == win32ts.WTSActive:
                username = win32ts.WTSQuerySessionInformation(
                    win32ts.WTS_CURRENT_SERVER_HANDLE,
                    session["SessionId"],
                    win32ts.WTSUserName,
                )
                if username:
                    return username
    except Exception:
        pass

    return os.getenv("USERNAME", "SYSTEM")

if getattr(sys, 'frozen', False):
    BASE_DIR = os.path.dirname(sys.executable)
else:
    BASE_DIR = os.path.dirname(os.path.abspath(__file__))

PYTHON_EXE = os.path.join(BASE_DIR, "python_embed", "python.exe")
LOG_PATH = os.path.join(BASE_DIR, "agent.log")

# DJANGO_BASE = "http://localhost:8000/api"
DJANGO_BASE = "https://arinet.arileasing.com.tr/api"
AGENT_TOKEN = "11c168a6bcb394698304244c9873c3bddbfd68970a242783b1d6ac3bf004fe7a"
AGENT_ID = str(uuid.uuid4())

logging.basicConfig(
    filename=LOG_PATH,
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s",
    encoding="utf-8",
)

logger = logging.getLogger("local_agent")

# ─── Task Çalıştırma ──────────────────────────────────────────────────────────

# Yakalanmamış (uncaught) hataları da log dosyasına yazdır
def log_uncaught_exceptions(exc_type, exc_value, exc_traceback):
    if issubclass(exc_type, KeyboardInterrupt):
        sys.__excepthook__(exc_type, exc_value, exc_traceback)
        return
    logger.error("Yakalanmamış hata:", exc_info=(exc_type, exc_value, exc_traceback))


def update(task_id, status, log=None):
    try:
        requests.post(
            f"{DJANGO_BASE}/agent/update_agent_task/",
            json={"task_id": task_id, "status": status, "log": log},
            headers={"X-Agent-Token": AGENT_TOKEN},
            timeout=5,
        )
    except Exception as e:
        logger.error(f"Hata: {e}", exc_info=True)
        pass

def poll_and_run():
    try:
        resp = requests.post(
            f"{DJANGO_BASE}/agent/get_agent_task/",
            json={"agent_id": AGENT_ID,"username": get_active_username()},
            headers={"X-Agent-Token": AGENT_TOKEN},
            timeout=10,
            verify=False
        )

        task_data = resp.json()

    except Exception as e:
        #print(traceback.format_exc())
        logger.error(f"Hata: {e}", exc_info=True)
        return

    if not task_data.get("task_id"):
        return
    
    
    task_id = task_data["task_id"]
    agent_code = task_data["agent_code"]
    excel_b64 = task_data["excel_b64"]
    username = task_data["username"]
    password = task_data["password"]

    agent_code = agent_code.replace("__AGENT_TOKEN__", AGENT_TOKEN)

    tmp_dir = tempfile.mkdtemp(prefix=f"aritask_{task_id}_")
    excel_path = os.path.join(tmp_dir, "input.xlsx")
    bot_path = os.path.join(tmp_dir, "bot.py")

    try:
        with open(excel_path, "wb") as f:
            f.write(base64.b64decode(excel_b64))

        with open(bot_path, "w", encoding="utf-8") as f:
            f.write(agent_code)

        result  = subprocess.run(
            [
                PYTHON_EXE,
                bot_path,
                "--username", username,
                "--password", password,
                "--file", excel_path,
                "--task-id", str(task_id),
            ],
            timeout=3600,
            capture_output=True,
            text=True,
            encoding="utf-8",
            errors="replace",
        )

        if result.stdout:
            logger.info(f"[bot.py stdout - task {task_id}]\n{result.stdout}")
        if result.stderr:
            logger.error(f"[bot.py stderr - task {task_id}]\n{result.stderr}")

        if result.returncode != 0:
            logger.error(f"bot.py hata koduyla sonlandı: {result.returncode} (task {task_id})")
            update(task_id, "rejected")
        else:
            logger.info(f"Task tamamlandı: {task_id}")

    except subprocess.TimeoutExpired as e:
        # requests.post(
        #     f"{DJANGO_BASE}/bot/agent/task-hata/",
        #     json={"task_id": task_id, "hata": "Zaman aşımı (1 saat)"},
        #     headers={"X-Agent-Token": AGENT_TOKEN},
        #     timeout=5,
        # )
        logger.error(f"Hata: {e}", exc_info=True)
        update(str(task_id), "rejected", log=traceback.format_exc())
    except Exception as e:
        # requests.post(
        #     f"{DJANGO_BASE}/bot/agent/task-hata/",
        #     json={"task_id": task_id, "hata": str(e)},
        #     headers={"X-Agent-Token": AGENT_TOKEN},
        #     timeout=5,
        # )
        logger.error(f"Hata: {e}", exc_info=True)
        update(str(task_id), "rejected", log=traceback.format_exc())
    finally:
        try:
            os.remove(excel_path)
            os.remove(bot_path)
            os.rmdir(tmp_dir)
        except Exception as e:
            logger.error(f"Hata: {e}", exc_info=True)
            update(str(task_id), "rejected", log=traceback.format_exc())


# ─── Windows Service ──────────────────────────────────────────────────────────

class AriLeasingBotService(win32serviceutil.ServiceFramework):
    _svc_name_ = "AriLeasingBotAgent"
    _svc_display_name_ = "Arı Leasing Bot Agent"
    _svc_description_ = "Arı Leasing ERP otomasyon servisi"

    def __init__(self, args):
        win32serviceutil.ServiceFramework.__init__(self, args)
        self.stop_event = win32event.CreateEvent(None, 0, 0, None)
        self.running = True

    def SvcStop(self):
        self.ReportServiceStatus(win32service.SERVICE_STOP_PENDING)
        win32event.SetEvent(self.stop_event)
        self.running = False

    def SvcDoRun(self):
        servicemanager.LogMsg(
            servicemanager.EVENTLOG_INFORMATION_TYPE,
            servicemanager.PYS_SERVICE_STARTED,
            (self._svc_name_, ""),
        )
        while self.running:
            try:
                poll_and_run()
            except Exception:
                pass
            time.sleep(5)

sys.excepthook = log_uncaught_exceptions
# ─── Giriş Noktası ────────────────────────────────────────────────────────────

if __name__ == "__main__":
    # if len(sys.argv) == 1:
    #     servicemanager.Initialize()
    #     servicemanager.PrepareToHostSingle(AriLeasingBotService)
    #     servicemanager.StartServiceCtrlDispatcher()
    # else:
    #     win32serviceutil.HandleCommandLine(AriLeasingBotService)

    if len(sys.argv) == 1:
        # Direkt çalıştırılıyor, test modu
        while True:
            poll_and_run()
            time.sleep(5)
    else:
        # install / start / stop / remove — SCM tarafından çalıştırılıyor
        win32serviceutil.HandleCommandLine(AriLeasingBotService)