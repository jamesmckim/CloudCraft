import json
import ipaddress
from fabrictestbed_extensions.fablib.fablib import FablibManager

fablib = FablibManager()

def create_slice():
    # 1. Create a new slice (infrastructure request)
    slice_name = "k8s-game-cluster"
    slice = fablib.new_slice(name=slice_name)

    # 2. Add a Control Plane Node
    master = slice.add_node(
        name="control-plane",
        site="NCSA",
        image="default_ubuntu_22",
        cores=4,
        ram=16,
        disk=50
    )
    worker1 = slice.add_node(
        name="worker-1",
        site="NCSA",
        image="default_ubuntu_22"
        cores=4,
        ram=16,
        disk=100
    )
    worker2 = slice.add_node(
        name="worker-2",
        site="NCSA",
        image="default_ubuntu_22",
        cores=4,
        ram=16,
        disk=100
    )

    iface_m = master.add_component(model="NIC_Basic", name="nic1").get_interfaces()[0]
    iface_w1 = worker1.add_component(model="NIC_Basic", name="nic1").get_interfaces()[0]
    iface_w2 = worker2.add_component(model="NIC_Basic", name="nic1").get_interfaces()[0]

    # 3. Create a Local Area Network (LAN) connecting them
    net = slice.add_l2network(name="k8s-lan", interfaces=[iface_m, iface_w1, iface_w2])


    # 4. Submit the request and wait for the hardware to boot
    print("Submitting slice request to NSF FABRIC...")
    slice.submit()
    print("Slice is active! Waiting for SSH")
    slice.wait_ssh()
    
    master = slice.get_node("control-plane")
    worker1 = slice.get_node("worker-1")
    worker2 = slice.get_node("worker-2")
    
    iface_m = master.get_interface(network_name="k8s-lan")
    iface_w1 = worker1.get_interface(network_name="k8s-lan")
    iface_w2 = worker2.get_interface(network_name="k8s-lan")
    
    lan_subnet = ipaddress.IPv4Network("10.10.10.0/24") # This needs to be changed to dynamic ipv6 scaling
    
    print("Configuring Internal Network (10.10.10.x)...")
    iface_m.ip_addr_add(addr="10.10.10.10", subnet=lan_subnet)
    iface_m.ip_link_up()

    iface_w1.ip_addr_add(addr="10.10.10.11", subnet=lan_subnet)
    iface_w1.ip_link_up()

    iface_w2.ip_addr_add(addr="10.10.10.12", subnet=lan_subnet)
    iface_w2.ip_link_up()
    
    # 5. THE HANDOFF: Extract the IPs to pass to your SSH script
    # 5. THE HANDOFF: Generate Ansible Inventory
    print("Generating Ansible inventory.ini...")
    
    bastion_user = "jm1029804_0000480603" # From your old fabfile
    bastion_host = "bastion.fabric-testbed.net"
    
    # We write this as an INI formatted string
    inventory_content = f"""[master]
control-plane ansible_host={master.get_management_ip()} internal_ip=10.10.10.10

[workers]
worker-1 ansible_host={worker1.get_management_ip()} internal_ip=10.10.10.11
worker-2 ansible_host={worker2.get_management_ip()} internal_ip=10.10.10.12

[all:vars]
ansible_user=ubuntu
ansible_ssh_private_key_file=~/.ssh/slice_key
ansible_ssh_common_args='-o ProxyCommand="ssh -W [%h]:%p -o StrictHostKeyChecking=no -o UserKnownHostsFile=/dev/null {bastion_user}@{bastion_host}"'
"""
    
    # Save it to a file Ansible natively understands
    with open('ansible/inventory.ini', 'w') as f:
        f.write(inventory_content)
        
    print("✅ Saved IPs and SSH configs to inventory.ini")

if __name__ == "__main__":
    create_slice()