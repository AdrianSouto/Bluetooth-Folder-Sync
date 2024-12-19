import tkinter as tk
from tkinter import filedialog
from tkinter import ttk
from main import start_sync, stop_sync
import threading

sync_thread = None

def browse_folder():
    folder_selected = filedialog.askdirectory()
    sync_folder_entry.delete(0, tk.END)
    sync_folder_entry.insert(0, folder_selected)

def on_start():
    global sync_thread
    if sync_thread is None or not sync_thread.is_alive():
        peer_addr = peer_addr_entry.get()
        local_addr = local_addr_entry.get()
        port = int(port_entry.get())
        sync_folder = sync_folder_entry.get()
        sync_thread = threading.Thread(target=start_sync, args=(peer_addr, local_addr, port, sync_folder))
        sync_thread.start()
        start_button.config(text="Stop Sync")
    else:
        # Detener el hilo
        stop_sync()
        sync_thread = None
        start_button.config(text="Start Sync")

# Crear la ventana principal
root = tk.Tk()
root.title("Sync Program")
root.configure(bg='#edf2f4')  # Cambiar el color de fondo

# Aplicar un tema
style = ttk.Style(root)
style.theme_use('clam')

# Estilo personalizado para botones redondeados
style.configure('RoundedButton.TButton',
                background='#4361ee',
                borderwidth=1,
                padding=2,
                anchor='center')
style.map('RoundedButton.TButton',
          background=[('active', '#6c84f5')],
          relief=[('pressed', 'sunken'), ('!pressed', 'flat')],)

# Crear y colocar los widgets
ttk.Label(root, text="Peer Address:", background='#edf2f4').grid(row=0, column=0, padx=10, pady=5, sticky='W')
peer_addr_entry = ttk.Entry(root)
peer_addr_entry.grid(row=0, column=1, padx=10, pady=5, sticky='EW')

ttk.Label(root, text="Local Address:", background='#edf2f4').grid(row=1, column=0, padx=10, pady=5, sticky='W')
local_addr_entry = ttk.Entry(root)
local_addr_entry.grid(row=1, column=1, padx=10, pady=5, sticky='EW')

ttk.Label(root, text="Port:", background='#edf2f4').grid(row=2, column=0, padx=10, pady=5, sticky='W')
port_entry = ttk.Entry(root)
port_entry.grid(row=2, column=1, padx=10, pady=5, sticky='EW')

ttk.Label(root, text="Sync Folder:", background='#edf2f4').grid(row=3, column=0, padx=10, pady=5, sticky='W')
sync_folder_entry = ttk.Entry(root)
sync_folder_entry.grid(row=3, column=1, padx=10, pady=5, sticky='EW')
ttk.Button(root, text="Browse", command=browse_folder, style='RoundedButton.TButton').grid(row=3, column=2, padx=10, pady=5)

start_button = ttk.Button(root, text="Start Sync", command=on_start, style='RoundedButton.TButton')
start_button.grid(row=4, column=1, padx=10, pady=10)

# Ajustar el tamaño de las columnas
root.columnconfigure(1, weight=1)

# Iniciar el bucle principal de la interfaz gráfica
root.mainloop()