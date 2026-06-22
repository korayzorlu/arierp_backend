from selenium.common.exceptions import NoSuchElementException,NoAlertPresentException,NoSuchWindowException,WebDriverException

import requests

DJANGO_BASE = "http://localhost:8000/api"
# DJANGO_BASE = "https://arinet.arileasing.com.tr/api"
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

