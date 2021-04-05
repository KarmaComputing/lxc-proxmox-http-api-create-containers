from pydantic import BaseModel
from typing import Optional

class Network(BaseModel):
    name: Optional[str] = 'eth0'
    bridge: Optional[str] = 'vmbr0'
    ipv6: Optional[str] = 'dhcp'
    gw6: Optional[str] = '2a01:4f8:160:2333:0:1:0:2'


class Container(BaseModel):
    id: int
    hostname: str
    memory: int
    network: Optional[Network] = Network
    template: Optional[str] = 'local:vztmpl/debian-10-standard_10.7-1_amd64.tar.gz'
 
data = {
  'id': 1234,
  'hostname': '1234',
  'memory': 1024,
  'template': 'local:vztmpl/debian-10-standard_10.7-1_amd64.tar.gz'
}

container = Container(**data)

"""
pct create 999 --start --hostname 999 --net0 name=eth0,bridge=vmbr0,ip6=dhcp,gw6=2a01:4f8:160:2333:0:1:0:2 --memory 10240 local:vztmpl/debian-10-standard_10.7-1_amd64.tar.gz

"""
