import subprocess
import json

def run_docker_ps():
    try:
        output = subprocess.check_output(['docker', 'ps', '--format', 'json'], text=True)
        lines = output.strip().split('\n')
        extracted_info = []
        for line in lines:
            container_info = json.loads(line)
            info = {
                'Created At': container_info['CreatedAt'],
                'Image': container_info['Image'],
                'Names': container_info['Names'],
                'Networks': container_info['Networks'],
                'RunningFor': container_info['RunningFor'],
                'Size': container_info['Size'],
                'Status': container_info['Status']
            }
            extracted_info.append(info)
        return extracted_info
    except subprocess.CalledProcessError as e:
        return f"Error: {e}"
