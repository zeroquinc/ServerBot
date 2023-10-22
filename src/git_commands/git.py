import subprocess    

def run_git_pull():
    try:
        result = subprocess.run(['git', 'pull'], capture_output=True, text=True, check=True)
        return result.stdout
    except subprocess.CalledProcessError as e:
        return f'Error: {e.stderr}'
    
def run_git_status():
    try:
        status_result = subprocess.run(['git', 'status', '-uno'], stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
        if status_result.returncode == 0:
            return status_result.stdout
        else:
            return status_result.stderr
    except Exception as e:
        return str(e)

def run_git_fetch():
    try:
        fetch_result = subprocess.run(['git', 'fetch'], stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
        if fetch_result.returncode != 0:
            return fetch_result.stderr
        return 'Git fetch successful.'
    except Exception as e:
        return str(e)