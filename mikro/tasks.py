from celery import shared_task
from core.celery import app
from django.shortcuts import render, HttpResponse, redirect, get_object_or_404
from django.http import JsonResponse
from django.contrib import messages
from django.conf import settings
from django.core.mail import EmailMessage, send_mail

import os
import sys
import subprocess

@shared_task
def setVpn(aa):
    try:
        command = [sys.executable,"sudo", "openvpn", "/vpn/dentanetbilisim.ovpn"]
        command2 = "sudo openvpn /vpn/dentanetbilisim.ovpn"
        result = subprocess.run(command,shell=True,stdout=subprocess.PIPE,stderr=subprocess.STDOUT,text=True)
        print(result)
        if result.returncode == 0:
            return {"status": "success", "message": "VPN çalıştırıldı."}
        else:
            return {"status": "error", "message": result.stderr}
    except Exception as e:
        return {"status": "error", "message": str(e)}
    