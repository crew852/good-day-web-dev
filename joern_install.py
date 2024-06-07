import os
import subprocess
import pexpect

def install_joern(install_dir):
    # 절대 경로로 변환
    install_dir = os.path.abspath(install_dir)
    
    # Joern 설치 디렉토리 생성
    if not os.path.exists(install_dir):
        try:
            os.makedirs(install_dir)
            print(f"Directory {install_dir} created.")
        except OSError as e:
            print(f"Error creating directory {install_dir}: {e}")
            return
    
    os.chdir(install_dir)
    print(f"Changed working directory to {install_dir}")

    # Joern 설치 스크립트 다운로드
    joern_install_script_url = "https://github.com/joernio/joern/releases/latest/download/joern-install.sh"
    install_script_path = os.path.join(install_dir, "joern-install.sh")

    curl_command = f'curl -L "{joern_install_script_url}" -o {install_script_path}'
    chmod_command = f'chmod u+x {install_script_path}'

    try:
        print("Downloading Joern install script...")
        subprocess.run(curl_command, shell=True, check=True)
        
        print("Setting execute permission on install script...")
        subprocess.run(chmod_command, shell=True, check=True)

        print("Running Joern install script...")
        child = pexpect.spawn(f'./joern-install.sh --interactive', timeout=120)
        child.expect('This*')
        child.sendline("y")
        child.expect('Enter*')
        child.sendline(install_dir)
        child.expect('Would*')
        child.sendline("y")
        child.expect('Where*')
        child.sendline("")
        child.expect('Please*')
        child.sendline("")
        child.interact()

        print("Joern installation completed successfully.")
    except subprocess.CalledProcessError as e:
        print(f"An error occurred: {e}")
    except pexpect.exceptions.ExceptionPexpect as e:
        print(f"An error occurred with pexpect: {e}")

if __name__ == "__main__":
    install_dir = "./"
    install_joern(install_dir)
