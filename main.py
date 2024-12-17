import os
import socket
import threading
from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler

class SyncHandler(FileSystemEventHandler):
    def __init__(self, peer_addr, port):
        self.peer_addr = peer_addr
        self.port = port

    def on_modified(self, event):
        if not event.is_directory:
            self.sync_file(event.src_path)

    def on_created(self, event):
        if not event.is_directory:
            self.sync_file(event.src_path)

    def on_deleted(self, event):
        if not event.is_directory:
            self.delete_file(event.src_path)

    def sync_file(self, file_path):
        try:
            with socket.socket(socket.AF_BLUETOOTH, socket.SOCK_STREAM, socket.BTPROTO_RFCOMM) as sock:
                sock.connect((self.peer_addr, self.port))
                with open(file_path, 'rb') as f:
                    file_name = os.path.basename(file_path)
                    sock.sendall(f"SYNC::{file_name}".encode('utf-8'))
                    sock.sendall(f.read())
        except OSError as e:
            print(f"Error syncing file {file_path}: {e}")

    def delete_file(self, file_path):
        try:
            with socket.socket(socket.AF_BLUETOOTH, socket.SOCK_STREAM, socket.BTPROTO_RFCOMM) as sock:
                sock.connect((self.peer_addr, self.port))
                file_name = os.path.basename(file_path)
                sock.sendall(f"DELETE::{file_name}".encode('utf-8'))
        except OSError as e:
            print(f"Error deleting file {file_path}: {e}")

def start_server(local_addr, port, sync_folder):
    sock = socket.socket(socket.AF_BLUETOOTH, socket.SOCK_STREAM, socket.BTPROTO_RFCOMM)
    sock.bind((local_addr, port))
    sock.listen(1)

    while True:
        client_sock, address = sock.accept()
        command = client_sock.recv(1024).decode('utf-8').strip()
        if command.startswith("SYNC::"):
            file_name = command.split("::")[1]
            file_path = os.path.join(sync_folder, os.path.basename(file_name))
            with open(file_path, 'wb') as f:
                while True:
                    data = client_sock.recv(1024)
                    if not data:
                        break
                    f.write(data)
        elif command.startswith("DELETE::"):
            file_name = command.split("::")[1]
            file_path = os.path.join(sync_folder, os.path.basename(file_name))
            if os.path.exists(file_path):
                os.remove(file_path)
        client_sock.close()

def sync_all_files(sync_folder, peer_addr, port):
    for root, _, files in os.walk(sync_folder):
        for file in files:
            file_path = os.path.join(root, file)
            try:
                with socket.socket(socket.AF_BLUETOOTH, socket.SOCK_STREAM, socket.BTPROTO_RFCOMM) as sock:
                    sock.connect((peer_addr, port))
                    with open(file_path, 'rb') as f:
                        file_name = os.path.basename(file_path)
                        sock.sendall(f"SYNC::{file_name}".encode('utf-8'))
                        sock.sendall(f.read())
            except OSError as e:
                print(f"Error syncing file {file_path}: {e}")

def start_sync(peer_addr, local_addr, port, sync_folder):
    # Iniciar el servidor en un hilo separado
    server_thread = threading.Thread(target=start_server, args=(local_addr, port, sync_folder))
    server_thread.daemon = True
    server_thread.start()

    # Sincronizar todos los archivos al iniciar
    sync_all_files(sync_folder, peer_addr, port)

    # Configurar el observador para monitorear la carpeta de sincronización
    event_handler = SyncHandler(peer_addr, port)
    observer = Observer()
    observer.schedule(event_handler, sync_folder, recursive=True)
    observer.start()

    try:
        while True:
            pass
    except KeyboardInterrupt:
        observer.stop()
    observer.join()