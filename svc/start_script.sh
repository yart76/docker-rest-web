#!/bin/sh -e

git clone https://github.com/yart76/docker-rest-web.git
cd docker-rest-web/svc && vagrant up && cd ansible && ansible-playbook -vv -i inv_hosts main.yml --user vagrant -k -K