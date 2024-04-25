import eel
import subprocess
import threading
import os
import requests
import zipfile
import io
import time
import shutil

eel.init('web')

server_process = None

@eel.expose
def download_repository():
    repo_url = 'https://github.com/Migrim/OTP-Manager/archive/refs/heads/main.zip'
    response = requests.get(repo_url)
    if response.status_code == 200:
        with zipfile.ZipFile(io.BytesIO(response.content)) as zip_ref:
            zip_ref.extractall('temp')
        extracted_folder = os.path.join('temp', 'OTP-Manager-main')
        target_folder = os.path.join('APP', 'Content')
        if os.path.exists(target_folder):
            shutil.rmtree(target_folder)
        os.makedirs('APP', exist_ok=True)
        os.rename(extracted_folder, target_folder)
        otp_db_path = os.path.join(target_folder, 'otp.db')
        if os.path.exists(otp_db_path):
            root_path = os.path.dirname(os.path.realpath(__file__))
            shutil.move(otp_db_path, os.path.join(root_path, 'otp.db'))
        shutil.rmtree('temp')
        eel.update_progress(100, "Download Complete")
        return True
    eel.update_progress(0, "Failed to download")
    return False

def read_output(process, output_func):
    while True:
        output = process.stdout.readline()
        if not output:
            break
        output_func(output.strip())
        time.sleep(0.5)

@eel.expose
def start_server():
    global server_process
    if server_process is None:
        if not os.path.exists('APP/Content'):  
            eel.start('install.html', size=(600, 700), mode='chrome')  
            return
        print("starting server")
        server_process = subprocess.Popen(['python', 'APP/Content/app.py'], stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True, bufsize=1)
        threading.Thread(target=read_output, args=(server_process, eel.update_output)).start()

@eel.expose
def get_server_port():
    if server_process:
        return server_process.port  
    return None

@eel.expose
def stop_server():
    global server_process
    if server_process is not None:
        server_process.terminate()
        server_process.wait()
        server_process = None
        
@eel.expose
def restart_server():
    stop_server()  
    start_server()  

start_page = 'install.html' if not os.path.exists('APP/Content') else 'main.html'
eel.start(start_page, size=(600, 700), mode='chrome')