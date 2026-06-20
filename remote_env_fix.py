import os
import sys
import subprocess

# Ensure paramiko is installed
try:
    import paramiko
except ImportError:
    subprocess.check_call([sys.executable, "-m", "pip", "install", "paramiko"])
    import paramiko

def fix_remote_env():
    host = '45.148.29.33'
    username = 'nabiyev'
    password = 'CEO517984'
    project_dir = '/home/nabiyev/mentor'

    client = paramiko.SSHClient()
    client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    
    print(f"Connecting to {host}...")
    try:
        client.connect(host, username=username, password=password, timeout=10)
    except Exception as e:
        print(f"Failed to connect: {e}")
        return

    # Check if .env exists
    print("Checking for .env file...")
    stdin, stdout, stderr = client.exec_command(f'cat {project_dir}/.env')
    env_content = stdout.read().decode('utf-8')
    
    if not env_content:
        print(".env not found. Trying .env.example...")
        stdin, stdout, stderr = client.exec_command(f'cat {project_dir}/.env.example')
        env_content = stdout.read().decode('utf-8')

    if not env_content:
        print("Neither .env nor .env.example was found in the remote directory!")
        client.close()
        return

    # Update env_content
    lines = env_content.split('\n')
    
    # Remove existing GEMINI lines if they exist
    new_lines = [line for line in lines if not line.startswith('GEMINI_API_KEY') and not line.startswith('GEMINI_MODEL_NAME')]
    
    # Add our gemini lines
    # Using gemini-1.5-flash as requested (free tier model)
    new_lines.append("")
    new_lines.append("# Gemini AI (1.5 Flash / Pro)")
    new_lines.append("GEMINI_API_KEY=ILTIMOS_SHU_YERGA_O'Z_API_KALITINGIZNI_YOZING")
    new_lines.append("GEMINI_MODEL_NAME=gemini-1.5-flash")
    
    new_env_content = '\n'.join(new_lines)
    
    # Write back to .env
    print("Writing updated .env to server...")
    # Escape quotes and special chars for bash echo
    # A safer way to write is using SFTP
    sftp = client.open_sftp()
    remote_env_path = f"{project_dir}/.env"
    with sftp.file(remote_env_path, 'w') as f:
        f.write(new_env_content)
    sftp.close()

    print("Success! The .env file has been updated.")
    
    # Check what is inside
    stdin, stdout, stderr = client.exec_command(f'tail -n 5 {project_dir}/.env')
    print("Last lines of new .env:")
    print(stdout.read().decode('utf-8'))

    client.close()

if __name__ == "__main__":
    fix_remote_env()
