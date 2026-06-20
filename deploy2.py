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

def deploy2():
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

    print("\nUpdating requirements.txt remotely...")
    sftp = client.open_sftp()
    
    # Read local requirements.txt
    with open('d:/mentor/requirements.txt', 'r') as f:
        local_reqs = f.read()

    # Write to remote
    remote_path = f"{project_dir}/requirements.txt"
    try:
        with sftp.file(remote_path, 'w') as f:
            f.write(local_reqs)
    except Exception as e:
        print(f"Error writing reqs: {e}")
    sftp.close()

    print("\nRebuilding and restarting API...")
    status, out, err = execute_sudo_cmd(client, f"cd {project_dir} && docker compose build --no-cache api && docker compose up -d", password)
    print(out)
    if err: print("ERR:", err)

    print("\nChecking if it's up...")
    status, out, err = execute_sudo_cmd(client, "docker ps | grep api", password)
    print(out)
    
    client.close()
    print("Done fixing requirements!")

if __name__ == '__main__':
    deploy2()
