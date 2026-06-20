import os
import sys
import time
import subprocess

try:
    import paramiko
except ImportError:
    subprocess.check_call([sys.executable, "-m", "pip", "install", "paramiko"])
    import paramiko

def execute_sudo_cmd(client, cmd, password):
    print(f"Executing: {cmd}")
    # Run with sudo -S to read password from stdin
    stdin, stdout, stderr = client.exec_command(f"sudo -S bash -c \"{cmd}\"")
    stdin.write(password + "\n")
    stdin.flush()
    
    exit_status = stdout.channel.recv_exit_status()
    out = stdout.read().decode('utf-8')
    err = stderr.read().decode('utf-8')
    return exit_status, out, err

def deploy():
    host = '45.148.29.33'
    username = 'nabiyev'
    password = 'CEO517984'
    project_dir = '/home/nabiyev/mentor/mentor_ai'

    client = paramiko.SSHClient()
    client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    
    print(f"Connecting to {host}...")
    try:
        client.connect(host, username=username, password=password, timeout=10)
        print("Connected successfully!")
    except Exception as e:
        print(f"Connection failed: {e}")
        return

    # 1. Stop current containers
    print("\nStopping containers...")
    execute_sudo_cmd(client, f"cd {project_dir} && docker compose down", password)

    # 2. Fix docker-compose.yml (Change to port 8001)
    print("\nFixing docker-compose.yml...")
    compose_content = """version: "3.9"

services:
  db:
    image: postgres:16-alpine
    container_name: men_mentor_db
    restart: unless-stopped
    environment:
      POSTGRES_USER: postgres
      POSTGRES_PASSWORD: password
      POSTGRES_DB: men_mentor_db
    volumes:
      - postgres_data:/var/lib/postgresql/data
    healthcheck:
      test: ["CMD-SHELL", "pg_isready -U postgres"]
      interval: 10s
      timeout: 5s
      retries: 5

  api:
    build: .
    container_name: men_mentor_api
    restart: unless-stopped
    env_file:
      - .env
    ports:
      - "8001:8000"
    depends_on:
      db:
        condition: service_healthy
    volumes:
      - .:/app
    command: uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload

volumes:
  postgres_data:
"""
    sftp = client.open_sftp()
    compose_path = f"{project_dir}/docker-compose.yml"
    try:
        with sftp.file(compose_path, 'w') as f:
            f.write(compose_content)
    except Exception as e:
        print(f"Error modifying docker-compose: {e}")

    # 3. Fix .env file
    print("\nFixing .env file...")
    env_path = f"{project_dir}/.env"
    try:
        with sftp.file(env_path, 'r') as f:
            env_content = f.read().decode('utf-8')
            
        lines = env_content.split('\n')
        new_env = []
        for line in lines:
            if line.startswith("DATABASE_URL="):
                new_env.append("DATABASE_URL=postgresql+asyncpg://postgres:password@db:5432/men_mentor_db")
            elif line.startswith("GEMINI_API_KEY="):
                pass # remove old
            elif line.startswith("GEMINI_MODEL_NAME="):
                pass # remove old
            else:
                new_env.append(line)
                
        new_env.append("GEMINI_API_KEY=your_gemini_api_key_here")
        new_env.append("GEMINI_MODEL_NAME=gemini-1.5-flash")
        
        with sftp.file(env_path, 'w') as f:
            f.write('\n'.join(new_env))
    except Exception as e:
        print(f"Error modifying .env: {e}")

    sftp.close()

    # 4. Start containers
    print("\nStarting containers...")
    status, out, err = execute_sudo_cmd(client, f"cd {project_dir} && docker compose up -d --build", password)
    print(out)
    if err: print("Stderr:", err)

    # 5. Wait a few seconds for DB to be ready
    print("Waiting 10 seconds for DB to initialize...")
    time.sleep(10)

    # 6. Run Migrations
    print("\nRunning database migrations...")
    status, out, err = execute_sudo_cmd(client, f"cd {project_dir} && docker compose exec -T api alembic upgrade head", password)
    print(out)
    if err: print("Stderr:", err)

    # 7. Check if API is answering
    print("\nChecking local API response...")
    stdin, stdout, stderr = client.exec_command("curl -I http://localhost:8001/docs")
    print(stdout.read().decode('utf-8'))

    # 8. Open firewall port 8001 just in case
    print("\nOpening firewall port 8001...")
    execute_sudo_cmd(client, "ufw allow 8001/tcp", password)

    client.close()
    print("Deployment script finished.")

if __name__ == '__main__':
    deploy()
