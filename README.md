# docker-rest-web

Technologies and tools that are used in this task.

Web is Flask with Flask Restful library support for having API support

Web app is started with Gunicorn WSGI server

Docker for container platform

Vagrant for managing environment

VirtualBox as hypervisor provider

Ansible for automated provisioning

Redis as in-memory data storage


Deployment

cd svc
vagrant up
cd ansible
ansible-playbook -vv -i inv_hosts main.yml --user vagrant -k -K

ssh and sudo passwords is vagrant
