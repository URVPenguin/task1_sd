import docker
import time
from typing import Optional

from test_utils.functions import get_free_port


class DockerContainerManager:
    def __init__(self):
        self.client = docker.from_env()

    def run_rabbitmq(
            self,
            container_name: str = "rabbitmq",
            port: Optional[int] = 5672,
            host: str = "127.0.0.1",
            restart_existing: bool = True
    ) -> bool:

        return self.run_container(
            image="rabbitmq:management",
            container_name=container_name,
            ports={"5672/tcp": (host, port), "15672/tcp": (host, get_free_port())},
            environment={},
            restart_existing=restart_existing
        )

    def run_redis(
            self,
            container_name: str = "redis",
            port: Optional[int] = 6379,
            host: str = "127.0.0.1",
            restart_existing: bool = True
    ) -> bool:

        return self.run_container(
            image="redis:latest",
            container_name=container_name,
            ports={"6379/tcp": (host, port)},
            environment={},
            restart_existing=restart_existing
        )

    def run_pyro_nameserver(
            self,
            container_name: str = "pyro-ns",
            port: Optional[int] = 9090,
            host: str = "127.0.0.1",
            restart_existing: bool = True
    ) -> bool:

        return self.run_container(
            image="python:3-slim",
            container_name=container_name,
            ports={"9090/tcp": (host, port)},
            environment={},
            restart_existing=restart_existing,
            command=["sh", "-c", "pip install pyro4 && python -m Pyro4.naming --host 0.0.0.0 --port 9090"],
            tty=True
        )

    def run_container(
            self,
            image: str,
            container_name: str,
            ports: dict,
            environment: dict,
            restart_existing: bool,
            command: Optional[str] = None,
            tty: bool = False
    ) -> bool:
        try:
            try:
                container = self.client.containers.get(container_name)

                if container.status == "running":
                    print(f"El contenedor {container_name} ya está en ejecución.")
                    return True

                if restart_existing:
                    print(f"Reiniciando contenedor existente: {container_name}")
                    container.start()
                    time.sleep(2)  # Esperar un poco para que el servicio esté listo
                    return True
                else:
                    print(f"El contenedor {container_name} existe pero no está en ejecución.")
                    return False

            except docker.errors.NotFound:
                pass  # El contenedor no existe, continuar con la creación

            # Mapear puertos en el formato correcto para Docker SDK
            port_bindings = {
                container_port: (host_ip, host_port)
                for container_port, (host_ip, host_port) in ports.items()
            }

            print(f"Iniciando nuevo contenedor {container_name} con imagen {image}...")
            self.client.containers.run(
                image=image,
                name=container_name,
                ports=port_bindings,
                environment=environment,
                command=command,
                detach=True,
                remove=True,
                tty=tty,
                stdin_open=tty
            )

            time.sleep(2)  # Esperar un poco para que el servicio esté listo
            return True

        except docker.errors.DockerException as e:
            print(f"Error al manejar el contenedor {container_name}: {str(e)}")
            return False

    def stop_container(self, container_name: str) -> bool:
        """Detiene un contenedor por nombre"""
        try:
            container = self.client.containers.get(container_name)
            container.stop()
            print(f"Contenedor {container_name} detenido.")
            return True
        except docker.errors.NotFound:
            print(f"Contenedor {container_name} no encontrado.")
            return False
        except docker.errors.DockerException as e:
            print(f"Error al detener el contenedor {container_name}: {str(e)}")
            return False

    def remove_container(self, container_name: str) -> bool:
        """Elimina un contenedor por nombre"""
        try:
            container = self.client.containers.get(container_name)
            container.remove(force=True)
            print(f"Contenedor {container_name} eliminado.")
            return True
        except docker.errors.NotFound:
            print(f"Contenedor {container_name} no encontrado.")
            return False
        except docker.errors.DockerException as e:
            print(f"Error al eliminar el contenedor {container_name}: {str(e)}")
            return False

    def is_container_running(self, container_name: str) -> bool:
        """Verifica si un contenedor está en ejecución"""
        try:
            container = self.client.containers.get(container_name)
            return container.status == "running"
        except docker.errors.NotFound:
            return False