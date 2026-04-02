import urllib.request, urllib.parse, json, time, os, sys, subprocess

def print_out(msg):
    print(msg, flush=True)
    with open("push_log.txt", "a") as f:
        f.write(msg + "\n")

client_id = '178c6fc778ccc68e1d6a' # Reusing user's client ID from Ayurvedic-bot
repo_url_base = "https://github.com/kathiravan-gte/sales_crm_main.git"
user_email = "kathiravan-gte@users.noreply.github.com"
user_name = "kathiravan-gte"

print_out("--- Starting GitHub Push Process ---")

# 1. Request Device Code
req = urllib.request.Request('https://github.com/login/device/code', 
    data=urllib.parse.urlencode({'client_id': client_id, 'scope': 'repo'}).encode('utf-8'), 
    headers={'Accept': 'application/json'})

try:
    with urllib.request.urlopen(req) as res:
        data = json.loads(res.read())
except Exception as e:
    print_out(f"Error requesting device code: {e}")
    sys.exit(1)

print_out("\n" + "="*40)
print_out(f"1. Open your browser: {data['verification_uri']}")
print_out(f"2. Enter this code: {data['user_code']}")
print_out("="*40 + "\n")

device_code = data['device_code']
interval = data['interval']

print_out("Waiting for authentication...")

# 2. Poll for Access Token
while True:
    time.sleep(interval)
    token_req = urllib.request.Request('https://github.com/login/oauth/access_token',
        data=urllib.parse.urlencode({
            'client_id': client_id,
            'device_code': device_code,
            'grant_type': 'urn:ietf:params:oauth:grant-type:device_code'
        }).encode('utf-8'),
        headers={'Accept': 'application/json'})
    
    try:
        with urllib.request.urlopen(token_req) as res:
            token_data = json.loads(res.read())
            
        if 'access_token' in token_data:
            token = token_data['access_token']
            print_out("\nAuthentication Successful!")
            
            # 3. Setup Authenticated URL
            auth_repo_url = f"https://{token}@github.com/kathiravan-gte/sales_crm_main.git"
            
            # 4. Git Configuration & Push
            git_path = "C:\\Program Files\\Git\\cmd\\git.exe"
            
            print_out("Running git commands...")
            subprocess.run([git_path, "config", "user.email", user_email])
            subprocess.run([git_path, "config", "user.name", user_name])
            
            # Set remote URL
            subprocess.run([git_path, "remote", "add", "origin", repo_url_base], stderr=subprocess.DEVNULL)
            subprocess.run([git_path, "remote", "set-url", "origin", auth_repo_url])
            
            # Initial Commit
            subprocess.run([git_path, "add", "."])
            subprocess.run([git_path, "commit", "-m", "Initial commit from Sales CRM AI integration"])
            subprocess.run([git_path, "branch", "-M", "main"])

            print_out("Pushing to GitHub...")
            result = subprocess.run(
                [git_path, "push", "-u", "origin", "main", "--force"],
                capture_output=True, text=True
            )
            
            print_out("EXIT CODE: " + str(result.returncode))
            if result.returncode == 0:
                print_out("Push Successful!")
            else:
                print_out("Push Failed.")
                print_out("STDOUT: " + result.stdout)
                print_out("STDERR: " + result.stderr)
            
            # Reset remote to public URL (cleanup)
            subprocess.run([git_path, "remote", "set-url", "origin", repo_url_base])
            break
            
        elif token_data.get('error') not in ('authorization_pending', 'slow_down'):
            print_out("Error/Expired: " + str(token_data))
            break
    except Exception as e:
        print_out("Error checking token: " + str(e))
        break

print_out("\n--- Process Finished ---")
