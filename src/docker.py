import subprocess
import json

def run_docker_ps():
    try:
        # Run the "docker ps --format json" command and capture the output
        output = subprocess.check_output(['docker', 'ps', '--format', 'json'], text=True)

        # Parse the JSON output
        container_info = json.loads(output)

        # Extract the desired fields from the container information
        extracted_info = []
        for container in container_info:
            info = {
                'Created At': container['CreatedAt'],
                'Image': container['Image'],
                'Names': container['Names'],
                'Networks': container['Networks'],
                'RunningFor': container['RunningFor'],
                'Size': container['Size'],
                'Status': container['Status']
            }
            extracted_info.append(info)

        return extracted_info

    except subprocess.CalledProcessError as e:
        return f"Error: {e}"