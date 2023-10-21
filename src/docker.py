import subprocess

def run_docker_ps():
    try:
        output = subprocess.check_output(['docker', 'ps', '-a'], text=True)
        return output
    except subprocess.CalledProcessError as e:
        return f"Error: {e}"