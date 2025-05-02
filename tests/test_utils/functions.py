import socket

def get_free_port():
    """Encuentra y devuelve un puerto TCP disponible."""
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        s.bind(('0.0.0.0', 0))
        s.listen(1)
        port = s.getsockname()[1]
    return port

def service_work(client, requests_per_client):
    for i in range(requests_per_client):
        if i % 2 == 0:
            client.add_insult(f"insult{i}")
        else:
            client.get_all_insults()

def filter_work(client, requests_per_client):
    for i in range(requests_per_client):
        if i % 2 == 0:
            client.submit_text("insult idiot retardet")
        else:
            client.get_results()