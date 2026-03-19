import geni.portal as portal
import geni.rspec.pg as rspec

request = portal.context.makeRequestRSpec()

NUM_WORKERS = 2
CLUSTER_TOKEN = "AgonesCloudLabSecureToken123" 

lan = request.LAN("k8s-lan")

# Define the commands that execute the scripts cloned to the nodes
# We pass the CLUSTER_TOKEN as the first argument ($1) to the bash scripts
CMD_MASTER = f"bash /local/repository/scripts/setup_control_plane.sh {CLUSTER_TOKEN}"
CMD_WORKER = f"bash /local/repository/scripts/setup_worker.sh {CLUSTER_TOKEN}"

# ==========================================
# HARDWARE ALLOCATION
# ==========================================

# 1. Provision Control Plane (node-0)
node_0 = request.RawPC("node-0")
node_0.disk_image = "urn:publicid:IDN+emulab.net+image+emulab-ops:UBUNTU22-64-STD"
lan.addInterface(node_0.addInterface("if1"))
node_0.addService(rspec.Execute(shell="bash", command=CMD_MASTER))

# 2. Provision Worker Nodes
for i in range(1, NUM_WORKERS + 1):
    node = request.RawPC(f"node-{i}")
    node.disk_image = "urn:publicid:IDN+emulab.net+image+emulab-ops:UBUNTU22-64-STD"
    lan.addInterface(node.addInterface("if1"))
    node.addService(rspec.Execute(shell="bash", command=CMD_WORKER))

portal.context.printRequestRSpec()