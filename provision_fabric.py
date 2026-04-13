from fabrictestbed_extensions.fablib.fablib import FablibManager

fablib = FablibManager()

def create_slice():
    # 1. Create a new slice (infrastructure request)
    slice_name = "k8s-game-cluster"
    slice = fablib.new_slice(name=slice_name)

    # 2. Add a Control Plane Node
    master = slice.add_node(name="control-plane", site="TACC", image="default_ubuntu_22")
    
    # 3. Add Worker Nodes
    worker1 = slice.add_node(name="worker-1", site="TACC", image="default_ubuntu_22")
    worker2 = slice.add_node(name="worker-2", site="TACC", image="default_ubuntu_22")

    # 4. Submit the request and wait for the hardware to boot
    print("Submitting slice request to NSF FABRIC...")
    slice.submit()
    print("Slice is active!")
    
    slice.wait_ssh()
    print("All nodes are accessible via SSH!")

    # 5. THE HANDOFF: Extract the IPs to pass to your SSH script
    cluster_ips = {
        "master": slice.get_node("control-plane").get_management_ip(),
        "workers": [
            slice.get_node("worker-1").get_management_ip(),
            slice.get_node("worker-2").get_management_ip()
        ]
    }
    
    # Save these IPs to a file so fabfile.py can read them
    import json
    with open('cluster_ips.json', 'w') as f:
        json.dump(cluster_ips, f)
    print("Saved IPs to cluster_ips.json")

if __name__ == "__main__":
    create_slice()