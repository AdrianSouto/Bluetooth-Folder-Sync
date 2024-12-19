import os
import socket
import threading
from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler

server_socket = None
server_running = True
receiving_files = set()

class SyncHandler(FileSystemEventHandler):
    def __init__(self, peer_addr, port):
        self.peer_addr = peer_addr
        self.port = port

    def on_modified(self, event):
        if not event.is_directory and event.src_path not in receiving_files:
            self.sync_file(event.src_path)

    def on_created(self, event):
        if not event.is_directory and event.src_path not in receiving_files:
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
    global server_socket, server_running, receiving_files
    server_socket = socket.socket(socket.AF_BLUETOOTH, socket.SOCK_STREAM, socket.BTPROTO_RFCOMM)
    server_socket.bind((local_addr, port))
    server_socket.listen(1)

    while server_running:
        client_sock, address = server_socket.accept()
        command = client_sock.recv(1024).decode('utf-8').strip()
        if command.startswith("SYNC::"):
            file_name = command.split("::")[1]
            file_name = os.path.basename(file_name)  # Ensure only the file name is used
            file_path = sync_folder+'/'+file_name
            receiving_files.add(file_path)
            with open(file_path, 'wb') as f:
                while True:
                    data = client_sock.recv(1024)
                    if not data:
                        break
                    f.write(data)
            receiving_files.remove(file_path)
            print(f"File {file_name} received successfully.")
        elif command.startswith("DELETE::"):
            file_name = command.split("::")[1]
            file_name = os.path.basename(file_name)  # Ensure only the file name is used
            file_path = sync_folder+'/'+file_name
            if os.path.exists(file_path):
                os.remove(file_path)
            print(f"File {file_name} deleted successfully.")
        client_sock.close()
    server_socket.close()

def sync_all_files(sync_folder, peer_addr, port):
    for root, _, files in os.walk(sync_folder):
        for file in files:
            file_path = root+'/'+file
            if file_path not in receiving_files:
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
    global server_running
    server_running = True
    server_thread = threading.Thread(target=start_server, args=(local_addr, port, sync_folder))
    server_thread.daemon = True
    server_thread.start()

    sync_all_files(sync_folder, peer_addr, port)

    event_handler = SyncHandler(peer_addr, port)
    observer = Observer()
    observer.schedule(event_handler, sync_folder, recursive=True)
    observer.start()

    try:
        while server_running:
            pass
    except KeyboardInterrupt:
        observer.stop()
    observer.join()

def stop_sync():
    global server_running
    server_running = False
    if server_socket:
        server_socket.close()