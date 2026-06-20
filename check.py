import paramiko

def check():
    host = '45.148.29.33'
    username = 'nabiyev'
    password = 'CEO517984'
    
    client = paramiko.SSHClient()
    client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    client.connect(host, username=username, password=password)
    
    # Check docker
    stdin, stdout, stderr = client.exec_command("sudo -S docker ps | grep api")
    stdin.write(password + "\n")
    stdin.flush()
    print(stdout.read().decode('utf-8', 'ignore'))
    
    # Check curl
    stdin, stdout, stderr = client.exec_command("curl -s -I http://localhost:8001/docs")
    print(stdout.read().decode('utf-8', 'ignore'))

    client.close()

if __name__ == '__main__':
    check()
