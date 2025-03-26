import xmlrpc.client

proxy = xmlrpc.client.ServerProxy("http://localhost:8000")

def send_text_to_queue(text):
    proxy.add_task(text)

send_text_to_queue("Eres un estúpido genio")

print(proxy.process_next_task())
print(proxy.get_results())