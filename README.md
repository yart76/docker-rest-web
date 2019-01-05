# docker-rest-web

1. Technologies and tools that are used in this task.
2. Web is Flask with Flask Restful library support for having API support
3. Web app is started with Gunicorn WSGI server
4. Docker for container platform
5. Vagrant for managing environment
6. VirtualBox as hypervisor provider
7. Ansible for automated provisioning
8. Redis as in-memory data storage


Deployment

1. cd svc
2. vagrant up
3. cd ansible
4. ansible-playbook -vv -i inv_hosts main.yml --user vagrant -k -K

ssh and sudo passwords is vagrant

Access

Open web browser on controller on http://192.168.33.50:8000/ page, you should see reply from main page showing that application is running and accessible

Open web browser on http://192.168.33.50:8000/ping page, you should have reply from forwarded request to instance of functions running on one of the node

Open web browser on http://192.168.33.50:8000/stats page, you should have reply from forwarded request to instance of functions running on one of the node
