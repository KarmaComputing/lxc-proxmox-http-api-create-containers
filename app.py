from pydantic import BaseModel
from pydantic.error_wrappers import ValidationError
from typing import Optional

from time import sleep
import subprocess
import tempfile
from flask import Flask, request, render_template, jsonify
from flask_cors import CORS
import os


def create_app():
    app = Flask(__name__)
    CORS(app)

    @app.route("/")
    def index():
        return render_template("index.html")

    @app.route("/container", methods=["POST"])
    def create_container():
        """
        Create a container with the default template and auto public ipv6 address asignment
        See class Container and class Network for defaults.
        Usage:
        curl http://127.0.0.1:5000/container -d '{"hostname":123, "memory": 1024, "network": {}}'

        Or, with public ssh key injected for root user login
        curl http://127.0.0.1:5000/container -d '{"hostname":123, "memory": 1024, "network": {}, "ssh_public_keys": "<your id.rsa.pub>"}'

        """
        try:
            container = Container(**request.get_json(force=True))
            container.status = "creating"
            new_container(container)

            def get_ip():
                public_ip = subprocess.getoutput(
                    f"pct exec {get_vmid()} -- ip -6 addr show eth0 | grep -oP '(?<=inet6\s)[\da-f:]+' | head -n 1"
                )
                return public_ip

            attempts = 0
            max_attempts = 10
            while attempts < max_attempts:
                if len(get_ip()) < 5 and "fe80" not in get_ip():
                    sleep(3)
                    print("Waiting for ip address...")
                    max_attempts += 1
                else:
                    public_ip = get_ip()
                    print(f"Got ip address: {public_ip}")
                    attempts = max_attempts

            return (
                jsonify(
                    {
                        "msg": f"""Container created! Probably.\n
                  ssh into it with: `ssh root@{public_ip}` using your public key\n
                  You might need to wait a minute or two before the public address is
                  reachable. Not 100% sure why.\n
                  You can expediate it by traceroute6{public_ip} will add your route to
                  routing tables along the way."""
                    }
                ),
                201,
            )

        except ValidationError as e:
            return e.json()
        return container.json()

    @app.route("/health")
    def health():
        return "OK"

    @app.route("/redoc")
    @app.route("/openapi")
    def redoc():
        return """<body>
  <div id="redoc-container"></div>
  <script src="//cdn.jsdelivr.net/npm/redoc@2.0.0-rc.48/bundles/redoc.standalone.min.js"> </script>
  <script src="//cdn.jsdelivr.net/gh/wll8/redoc-try@1.3.4/dist/try.js"></script>
  <script>
    initTry(`https://raw.githubusercontent.com/karmacomputing/lxc-proxmox-http-api-create-containers/main/openapi.yaml`)
  </script>
</body>"""

    # Return fask wsgi app
    return app


class Network(BaseModel):
    name: Optional[str] = "eth0"
    bridge: Optional[str] = "vmbr0"
    ipv6: Optional[str] = "dhcp"


class Container(BaseModel):
    id: Optional[int] = ""
    hostname: str
    memory: int
    network: Network = None
    template: Optional[str] = "local:vztmpl/debian-10-standard_10.7-1_amd64.tar.gz"
    ssh_public_keys: Optional[str] = ""
    status: Optional[str] = ""


# Get id of container
def get_vmid():
    max = 0
    for root, dirs, files in os.walk("/etc/pve/lxc/"):
        for file in files:
            vmid = int(file.replace(".conf", ""))
            if vmid > max:
                max = vmid
        return max


def new_container(container: Container):
    # Container ssh keys (optional, but needed if you want to login)
    fp = tempfile.NamedTemporaryFile(mode="wt")
    fp.write(container.ssh_public_keys)
    fp.seek(0)
    next_id = get_vmid() + 1
    command = f"pct create {next_id} --start --hostname {container.hostname} --net0 name={container.network.name},bridge={container.network.bridge},ip6={container.network.ipv6} --memory {container.memory} --ssh-public-keys {fp.name} {container.template}"
    subprocess.run(command, shell=True)
    fp.close()


"""
Example:
pct create 999 --start --hostname 999 --net0 name=eth0,bridge=vmbr0,ip6=dhcp,gw6=2a01:4f8:160:2333:0:1:0:2 --memory 10240 local:vztmpl/debian-10-standard_10.7-1_amd64.tar.gz

"""
