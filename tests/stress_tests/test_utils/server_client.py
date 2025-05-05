from clients.pyro.insult_service_client import InsultServicePyroClient
from clients.redis.insult_service_client import InsultServiceRedisClient
from clients.xmlrpc.insult_service_client import InsultServiceXMLRPCClient
from clients.pyro.insult_filter_client import InsultFilterPyroClient
from clients.redis.insult_filter_client import InsultFilterRedisClient
from clients.xmlrpc.insult_filter_client import InsultFilterXMLRPClient
from clients.rabbitmq.insult_filter_client import InsultFilterRabbitMQClient
from clients.rabbitmq.insult_service_client import InsultServiceRabbitMQClient
from servers.xmlrpc.insult_service import run_server as serv_xmlrpc_run_server
from servers.redis.insult_service import run_server as serv_redis_run_server
from servers.pyro.insult_service import run_server as serv_pyro_run_server
from servers.rabbitmq.insult_service import run_server as serv_rabbitmq_run_server
from servers.xmlrpc.insult_filter import run_server as filt_xmlrpc_run_server
from servers.redis.insult_filter import run_server as filt_redis_run_server
from servers.pyro.insult_filter import run_server as filt_pyro_run_server
from servers.rabbitmq.insult_filter import run_server as filt_rabbitmq_run_server
from stress_tests.test_utils.functions import get_free_port

server_client = {
    "xmlrpc": {
        "targets": [serv_xmlrpc_run_server, filt_xmlrpc_run_server],
        "clients": [InsultServiceXMLRPCClient, InsultFilterXMLRPClient],
        "servers": [{'host': "127.0.0.1", 'port': get_free_port()},
                    {'host': "127.0.0.1", 'port': get_free_port()},
                    {'host': "127.0.0.1", 'port': get_free_port()}],
    },
    "redis": {
        "targets": [serv_redis_run_server, filt_redis_run_server],
        "clients": [InsultServiceRedisClient, InsultFilterRedisClient],
        "servers": [{'host': "127.0.0.1", 'port': 6379, 'container_name': 'redis'}],
    },
    "pyro": {
        "targets": [serv_pyro_run_server, filt_pyro_run_server],
        "clients": [InsultServicePyroClient, InsultFilterPyroClient],
        "servers": [{'host': "pyro.server.1", 'container_name': 'pyro'},
                    {'host': "pyro.server.2"},
                    {'host': "pyro.server.3"}]
    },
    "rabbitMQ": {
        "targets": [serv_rabbitmq_run_server, filt_rabbitmq_run_server],
        "clients": [InsultServiceRabbitMQClient, InsultFilterRabbitMQClient],
        "servers": [{'host': "127.0.0.1", 'port': 5672, 'container_name': 'rabbitmq'}],
    }
}