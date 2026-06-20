import os
import sys
import subprocess

try:
    import paramiko
except ImportError:
    subprocess.check_call([sys.executable, "-m", "pip", "install", "paramiko"])
    import paramiko

def execute_sudo_cmd(client, cmd, password):
    print(f"Executing: {cmd}")
    stdin, stdout, stderr = client.exec_command(f"sudo -S bash -c \"{cmd}\"")
    stdin.write(password + "\n")
    stdin.flush()
    exit_status = stdout.channel.recv_exit_status()
    out = stdout.read().decode('utf-8')
    err = stderr.read().decode('utf-8')
    return exit_status, out, err

def diagnose():
    host = '45.148.29.33'
    username = 'nabiyev'
    password = 'CEO517984'
    project_dir = '/home/nabiyev/mentor/mentor_ai'

    client = paramiko.SSHClient()
    client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    
    print(f"Connecting to {host}...")
    try:
        client.connect(host, username=username, password=password, timeout=10)
    except Exception as e:
        print(f"Connection failed: {e}")
        return

    print("\n--- DOCKER PS ---")
    st, out, err = execute_sudo_cmd(client, "docker ps -a", password)
    print(out)

    print("\n--- DOCKER LOGS API ---")
    st, out, err = execute_sudo_cmd(client, "docker logs men_mentor_api --tail 50", password)
    print(out)
    if err: print("ERR:", err)

    print("\n--- LOCAL CURL ---")
    st, out, err = execute_sudo_cmd(client, "curl -v http://localhost:8001/docs", password)
    print(out)
    if err: print("ERR:", err)
    
    print("\n--- UFW STATUS ---")
    st, out, err = execute_sudo_cmd(client, "ufw status", password)
    print(out)
    if err: print("ERR:", err)

    client.close()

if __name__ == '__main__':
    diagnose()
