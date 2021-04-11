Create containers via http api

The type of containers are lxc containers

# lxc-proxmox-http-api-create-containers


gunicorn -w 4 -b 0.0.0.0:4000 -b 0.0.0.0:80 "app:create_app()" --daemon

To kill / stop
killall gunicorn

