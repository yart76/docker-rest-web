# docker-rest-web

Start VM, preferably on Ubuntu, sample is using Ubuntu 16.04 LTS
Ssh to the machine

cd <src_folder>/functions/ping

docker build -t python-ping .

sudo apt-get update

sudo apt-get install -y virtualenv

sudo apt-get install -y python3-venv

#[stackoverflow.com/questions/14547631/python-locale-error-unsupported-locale-setting]

export LC_ALL="en_US.UTF-8"

export LC_CTYPE="en_US.UTF-8"

mkdir python_venvs

cd python_venvs

python3 -m venv controller

source controller/bin/activate

pip install --upgrade pip

cd <src_folder>/web

pip3 install -r requirements.txt

python3 flask_rest.py

open browser on http://<VM_IP>:5002:/ping and you should get {"status": "successfull", "msg": "This is returned ping"}
