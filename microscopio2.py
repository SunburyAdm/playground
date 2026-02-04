import socket
import threading
import time
import io
from PIL import Image, ImageTk
import tkinter as tk
from tkinter import ttk

MICROSCOPE_IP_DEFAULT = "192.168.29.1"

# Puertos típicos (tu captura mostró control en 20000/20001)
CTRL_PORT_DEFAULT = 20000
DATA_PORT_DEFAULT = 10900  # si ya te funciona, déjalo; si no, prueba 10800/10000/11000

# Comandos "JHCMD" observados en este tipo de dispositivos
CMD_10 = b"JHCMD" + bytes([0x10, 0x00])
CMD_20 = b"JHCMD" + bytes([0x20, 0x00, 0x00, 0x00, 0x00, 0x00])
CMD_D0_START = b"JHCMD" + bytes([0xD0, 0x01])  # start/keepalive (variante común)
CMD_D0_STOP  = b"JHCMD" + bytes([0xD0, 0x02])  # stop

START_SEQ = [CMD_10, CMD_20, CMD_D0_START, CMD_D0_START]

class WifiMicroscopeViewerRobust:
    def __init__(self, root):
        self.root = root
        self.root.title("Wi-Fi Microscope Viewer (Robust UDP/JPEG)")
        self.root.geometry("1100x700")

        self.running = False

        self.ctrl_sock = None
        self.data_sock = None

        # Threads
        self.recv_thread = None
        self.keepalive_thread = None

        # Watchdog
        self.last_rx_time = 0.0
        self.no_rx_restart_s = 2.5  # si no llega data en X segundos, reintenta start

        # JPEG reassembly (heurística más robusta)
        self.jpeg_buffer = bytearray()
        self.in_frame = False
        self.last_frame_render = 0.0

        self._build_ui()

    def _build_ui(self):
        top = ttk.Frame(self.root, padding=10)
        top.pack(side=tk.TOP, fill=tk.X)

        self.status_var = tk.StringVar(value="Listo. Presiona Start.")
        self.ip_var = tk.StringVar(value=MICROSCOPE_IP_DEFAULT)
        self.ctrl_var = tk.StringVar(value=str(CTRL_PORT_DEFAULT))
        self.data_var = tk.StringVar(value=str(DATA_PORT_DEFAULT))
        self.keepalive_ms_var = tk.StringVar(value="300")  # 200-500 suele ir bien

        ttk.Label(top, text="IP Microscopio:").grid(row=0, column=0, sticky="w")
        ttk.Entry(top, textvariable=self.ip_var, width=16).grid(row=0, column=1, padx=(6, 16), sticky="w")

        ttk.Label(top, text="CTRL Port:").grid(row=0, column=2, sticky="w")
        ttk.Entry(top, textvariable=self.ctrl_var, width=7).grid(row=0, column=3, padx=(6, 16), sticky="w")

        ttk.Label(top, text="DATA Port (local bind):").grid(row=0, column=4, sticky="w")
        ttk.Entry(top, textvariable=self.data_var, width=7).grid(row=0, column=5, padx=(6, 16), sticky="w")

        ttk.Label(top, text="Keepalive (ms):").grid(row=0, column=6, sticky="w")
        ttk.Entry(top, textvariable=self.keepalive_ms_var, width=7).grid(row=0, column=7, padx=(6, 16), sticky="w")

        self.start_btn = ttk.Button(top, text="Start", command=self.start)
        self.start_btn.grid(row=0, column=8, padx=(10, 6), sticky="w")

        self.stop_btn = ttk.Button(top, text="Stop", command=self.stop, state="disabled")
        self.stop_btn.grid(row=0, column=9, padx=(6, 0), sticky="w")

        ttk.Label(top, textvariable=self.status_var).grid(row=1, column=0, columnspan=10, sticky="w", pady=(8,0))

        self.video_label = ttk.Label(self.root)
        self.video_label.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)

    def _sock_set_buffers(self, s: socket.socket):
        # Aumenta buffers de recepción para reducir drop de UDP
        try:
            s.setsockopt(socket.SOL_SOCKET, socket.SO_RCVBUF, 4 * 1024 * 1024)
        except Exception:
            pass
        try:
            s.setsockopt(socket.SOL_SOCKET, socket.SO_SNDBUF, 512 * 1024)
        except Exception:
            pass

    def _open_sockets(self):
        ip = self.ip_var.get().strip()
        ctrl_port = int(self.ctrl_var.get().strip())
        data_port = int(self.data_var.get().strip())

        # Control socket (solo envío)
        self.ctrl_sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        self._sock_set_buffers(self.ctrl_sock)
        self.ctrl_sock.settimeout(1.0)

        # Data socket (recepción en puerto local)
        self.data_sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        self._sock_set_buffers(self.data_sock)
        self.data_sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        self.data_sock.bind(("", data_port))
        self.data_sock.settimeout(0.5)

        return ip, ctrl_port, data_port

    def _send_start_sequence(self, ip, ctrl_port):
        for cmd in START_SEQ:
            try:
                self.ctrl_sock.sendto(cmd, (ip, ctrl_port))
            except Exception:
                pass
            time.sleep(0.05)

    def _send_keepalive_once(self, ip, ctrl_port):
        try:
            self.ctrl_sock.sendto(CMD_D0_START, (ip, ctrl_port))
        except Exception:
            pass

    def _send_stop(self, ip, ctrl_port):
        try:
            self.ctrl_sock.sendto(CMD_D0_STOP, (ip, ctrl_port))
        except Exception:
            pass

    def start(self):
        if self.running:
            return

        self.running = True
        self.start_btn.configure(state="disabled")
        self.stop_btn.configure(state="normal")

        self.jpeg_buffer.clear()
        self.in_frame = False
        self.last_rx_time = time.time()

        ip, ctrl_port, data_port = self._open_sockets()

        self.status_var.set(f"Iniciando… esperando DATA en puerto local {data_port}")
        self._send_start_sequence(ip, ctrl_port)

        # Thread recepción
        self.recv_thread = threading.Thread(target=self._recv_loop, args=(ip, ctrl_port), daemon=True)
        self.recv_thread.start()

        # Thread keepalive
        self.keepalive_thread = threading.Thread(target=self._keepalive_loop, args=(ip, ctrl_port), daemon=True)
        self.keepalive_thread.start()

    def stop(self):
        if not self.running:
            return
        self.running = False

        ip = self.ip_var.get().strip()
        try:
            ctrl_port = int(self.ctrl_var.get().strip())
        except Exception:
            ctrl_port = CTRL_PORT_DEFAULT

        self._send_stop(ip, ctrl_port)

        # Cerrar sockets
        try:
            if self.data_sock:
                self.data_sock.close()
        except Exception:
            pass
        try:
            if self.ctrl_sock:
                self.ctrl_sock.close()
        except Exception:
            pass
        self.data_sock = None
        self.ctrl_sock = None

        self.start_btn.configure(state="normal")
        self.stop_btn.configure(state="disabled")
        self.status_var.set("Detenido.")

    # -------------------------
    # JPEG reassembly heurístico
    # -------------------------
    def _feed_payload(self, payload: bytes):
        """
        Muchos dispositivos envían: [8 bytes header] + [fragmento]
        pero el header varía. Para hacerlo robusto:
        - intentamos encontrar SOI/EOI dentro del stream recibido
        - mantenemos un buffer y cortamos frames por marcadores JPEG
        """
        if not payload:
            return

        # Añadir al buffer
        self.jpeg_buffer.extend(payload)

        # Buscar SOI
        if not self.in_frame:
            soi = self.jpeg_buffer.find(b"\xFF\xD8")
            if soi != -1:
                # descartar basura anterior
                if soi > 0:
                    del self.jpeg_buffer[:soi]
                self.in_frame = True

        # Si estamos en frame, buscar EOI
        if self.in_frame:
            eoi = self.jpeg_buffer.find(b"\xFF\xD9")
            if eoi != -1:
                jpg = bytes(self.jpeg_buffer[:eoi + 2])
                # remover frame del buffer
                del self.jpeg_buffer[:eoi + 2]
                self.in_frame = False
                self._render_jpeg(jpg)

                # Puede haber ya otro SOI en el buffer (frames pegados)
                self._feed_payload(b"")

        # Evitar crecimiento infinito si se pierde EOI
        if len(self.jpeg_buffer) > 5 * 1024 * 1024:
            # reset defensivo
            self.jpeg_buffer.clear()
            self.in_frame = False

    def _render_jpeg(self, jpg_bytes: bytes):
        try:
            img = Image.open(io.BytesIO(jpg_bytes))
            lw = max(1, self.video_label.winfo_width())
            lh = max(1, self.video_label.winfo_height())
            img.thumbnail((lw, lh))
            imgtk = ImageTk.PhotoImage(img)

            def update():
                self.video_label.imgtk = imgtk
                self.video_label.configure(image=imgtk)
                self.status_var.set("Recibiendo video (UDP/JPEG)…")

            self.root.after(0, update)
            self.last_frame_render = time.time()
        except Exception:
            # si hubo corrupción por fragmentos perdidos, simplemente ignora frame
            pass

    # -------------------------
    # Loops
    # -------------------------
    def _recv_loop(self, ip, ctrl_port):
        last_status = 0.0

        while self.running and self.data_sock:
            try:
                data, addr = self.data_sock.recvfrom(65535)
                # opcional: filtrar por IP del microscopio
                if addr and addr[0] != ip:
                    continue

                self.last_rx_time = time.time()

                # Heurística: muchos paquetes traen 8 bytes header
                # Probamos alimentar "data[8:]" si parece que hay header
                if len(data) > 12:
                    payload = data[8:]
                else:
                    payload = data

                self._feed_payload(payload)

            except socket.timeout:
                # watchdog de recepción
                now = time.time()
                if now - self.last_rx_time > self.no_rx_restart_s:
                    # Reintento: re-enviar start sequence para reactivar stream
                    self.status_var.set("Sin DATA… reintentando start/keepalive.")
                    self._send_start_sequence(ip, ctrl_port)
                    self.last_rx_time = now

                if now - last_status > 1.0:
                    last_status = now
                    # Mensaje útil si hay congelamiento
                    if self.last_frame_render and (now - self.last_frame_render > 2.0):
                        self.status_var.set("Conectado, pero frames no cierran (posible pérdida UDP). Ajusta keepalive/buffers o acércate al AP.")
            except OSError:
                break
            except Exception:
                pass

    def _keepalive_loop(self, ip, ctrl_port):
        # Keepalive periódico para que el microscopio no corte el stream
        try:
            interval_ms = int(self.keepalive_ms_var.get().strip())
        except Exception:
            interval_ms = 300

        interval_s = max(0.05, interval_ms / 1000.0)

        while self.running and self.ctrl_sock:
            self._send_keepalive_once(ip, ctrl_port)
            time.sleep(interval_s)


def main():
    root = tk.Tk()
    app = WifiMicroscopeViewerRobust(root)
    root.protocol("WM_DELETE_WINDOW", lambda: (app.stop(), root.destroy()))
    root.mainloop()

if __name__ == "__main__":
    main()
