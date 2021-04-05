from pydantic import BaseModel
from pydantic.error_wrappers import ValidationError
from typing import Optional

import subprocess
from random import randrange
from flask import Flask, request

def create_app():
  app = Flask(__name__)

  @app.route('/container', methods=["POST"])
  def create_container():
    """Usage
    curl http://127.0.0.1:5000/container -d '{"id":"123", "hostname":123, "memory": 1024, "network": {}}'
    Will create a container with the default template and auto public ipv6 address asignment
    See class Container and class Network for defaults
    """
    try:
      container = Container(**request.get_json(force=True))
      container.status = 'creating'
      command = f"pct create {container.id} --start --hostname {container.hostname} --net0 name={container.network.name},bridge={container.network.bridge},ip6={container.network.ipv6},gw6={container.network.gw6} --memory {container.memory} {container.template}"
      subprocess.run(command, shell=True)
      return f"Container created, probably. With container_id: {container_id}"

    except ValidationError as e:
      return e.json()
    return container.json()

  @app.route('/')
  def create_random_container():
      container_id = randrange(1000,9000)
      command = f"pct create {container_id} --start --hostname {container_id} --net0 name=eth0,bridge=vmbr0,ip6=dhcp,gw6=2a01:4f8:160:2333:0:1:0:2 --memory 10240 local:vztmpl/debian-10-standard_10.7-1_amd64.tar.gz"

      subprocess.run(command, shell=True)
      return f"Container created, probably. With container_id: {container_id}"

  return app


class Network(BaseModel):
    name: Optional[str] = 'eth0'
    bridge: Optional[str] = 'vmbr0'
    ipv6: Optional[str] = 'dhcp'
    gw6: Optional[str] = '2a01:4f8:160:2333:0:1:0:2'


class Container(BaseModel):
    id: int
    hostname: str
    memory: int
    network: Network = None
    template: Optional[str] = 'local:vztmpl/debian-10-standard_10.7-1_amd64.tar.gz'
    status: Optional[str] = ''
 

"""
Example:
pct create 999 --start --hostname 999 --net0 name=eth0,bridge=vmbr0,ip6=dhcp,gw6=2a01:4f8:160:2333:0:1:0:2 --memory 10240 local:vztmpl/debian-10-standard_10.7-1_amd64.tar.gz

"""
