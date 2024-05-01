import eel
import subprocess
import threading
import os
import requests
import zipfile
import io
import time
import shutil
import configparser
import sys

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
        shutil.rmtree('temp')
        eel.update_progress(100, "Download Complete")
        return True
    eel.update_progress(0, "Failed to download")
    return False

def read_output(process, output_func):
    try:
        for line in iter(process.stdout.readline, ''):
            output_func(line.strip())
            time.sleep(0.1) 
    except Exception as e:
        output_func("Error reading output: " + str(e))

@eel.expose
def start_server():
    global server_process
    if server_process is None:
        port = read_config_port()
        app_script_path = os.path.join('APP', 'Content', 'app.py')
        if not os.path.exists(app_script_path):
            eel.update_progress(0, "Server script not found.")
            print("Server script not found:", app_script_path)
            return  
        if not os.path.exists('APP/Content'):
            eel.start('install.html', size=(600, 700), mode='chrome')
            return
        print("Starting server on port", port)
        try:
            server_process = subprocess.Popen(
                [sys.executable, app_script_path, '--port', port],
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT, 
                text=True,
                bufsize=1
            )
            thread = threading.Thread(target=read_output, args=(server_process, eel.update_output))
            thread.daemon = True  
            thread.start()
        except Exception as e:
            eel.update_progress(0, "Failed to start server: " + str(e))
            print("Failed to start server:", e)

@eel.expose
def read_config_port():
    config_path = os.path.join('APP', 'Content', 'config.ini')
    if not os.path.exists(config_path):
        print("Config file not found:", config_path)
        return '8000'  
    config = configparser.ConfigParser()
    config.read(config_path)
    if 'server' in config and 'port' in config['server']:
        return config['server']['port']
    else:
        print("Failed to read 'port' from 'server' in config file")
        return '8000'  

@eel.expose
def change_port(new_port):
    config_path = os.path.join('APP', 'Content', 'config.ini')
    config = configparser.ConfigParser()
    config.read(config_path)
    if 'server' not in config:
        config['server'] = {}
    config['server']['port'] = new_port
    with open(config_path, 'w') as configfile:
        config.write(configfile)
    print(f"Port changed to {new_port}")
    return f"Port updated to {new_port}"

@eel.expose
def get_server_port():
    return read_config_port()

@eel.expose
def stop_server():
    global server_process
    if server_process is not None:
        server_process.terminate()
        server_process.wait()
        server_process = None
        return f"Server Stopped"
        
@eel.expose
def restart_server():
    stop_server()  
    start_server()  

start_page = 'install.html' if not os.path.exists('APP/Content') else 'main.html'
eel.start(start_page, size=(550, 700), mode='chrome', resizable=False)