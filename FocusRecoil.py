import tkinter as tk
from tkinter import ttk
import threading
import time
import pystray
from PIL import Image, ImageDraw
from pynput.keyboard import Listener as KeyboardListener, KeyCode
import ctypes
import win32gui
import win32con

recoil_strength = 10
activation_key = None
recoil_enabled = False
mouse_pressed = False
running = True
tray_icon = None
ventana_objetivo_hwnd = None
icono_texto = None
pos_texto = [50, 50]
mover_texto = False
movimiento_bloqueado = False  # Nuevo para bloqueo de movimiento texto

# === Movimiento Real Compatible con Juegos ===
def mover_mouse(dx, dy):
    ctypes.windll.user32.mouse_event(0x0001, dx, dy, 0, 0)

# === Recoil Real ===
def calcular_fuerza_real(valor_slider):
    exponente = 1.5
    max_slider = 100
    max_fuerza = 20
    fuerza = (valor_slider ** exponente) / (max_slider ** exponente) * max_fuerza
    if valor_slider > 80:
        fuerza *= 2
    return max(1, int(fuerza))

def disparo_continuo():
    delay = 0.005
    while mouse_pressed and recoil_enabled and ventana_activa_es_valida():
        fuerza_real = calcular_fuerza_real(recoil_strength)
        mover_mouse(0, fuerza_real)
        time.sleep(delay)

def recoil_loop():
    import pynput.mouse
    def on_click(x, y, button, pressed):
        global mouse_pressed
        if not running: return False
        if button == pynput.mouse.Button.left:
            mouse_pressed = pressed
            if pressed and recoil_enabled:
                threading.Thread(target=disparo_continuo, daemon=True).start()
    with pynput.mouse.Listener(on_click=on_click) as listener:
        listener.join()

# === Estado Visual ===
def mostrar_texto_flotante():
    global icono_texto

    if icono_texto and icono_texto.winfo_exists():
        if icono_texto.state() == 'withdrawn':
            icono_texto.deiconify()
        else:
            icono_texto.withdraw()
        return

    icono_texto = tk.Toplevel()
    icono_texto.overrideredirect(True)
    icono_texto.attributes('-topmost', True)
    icono_texto.geometry(f"100x30+{pos_texto[0]}+{pos_texto[1]}")
    icono_texto.config(bg='pink')  # color transparente
    icono_texto.wm_attributes('-transparentcolor', 'pink')  # hacer 'pink' invisible

    fondo = tk.Label(icono_texto, text="OFF", bg="pink", fg="red", font=("Segoe UI", 14, "bold"))
    fondo.pack(expand=True, fill="both")

    def mover_inicio(event):
        global mover_texto
        if not movimiento_bloqueado:
            mover_texto = True

    def mover(event):
        if mover_texto and not movimiento_bloqueado:
            x = icono_texto.winfo_pointerx() - 50
            y = icono_texto.winfo_pointery() - 15
            icono_texto.geometry(f"+{x}+{y}")
            pos_texto[0], pos_texto[1] = x, y

    def mover_fin(event):
        global mover_texto
        mover_texto = False

    fondo.bind("<Button-1>", mover_inicio)
    fondo.bind("<B1-Motion>", mover)
    fondo.bind("<ButtonRelease-1>", mover_fin)

def actualizar_texto_flotante():
    if icono_texto:
        label = icono_texto.winfo_children()[0]
        if recoil_enabled:
            label.config(text="ON", fg="green")
        else:
            label.config(text="OFF", fg="red")

# === Tray Icon ===
def generar_icono(color):
    size = 64
    img = Image.new('RGB', (size, size), 'black')
    d = ImageDraw.Draw(img)
    c = size // 2
    d.line((c-10, c, c+10, c), fill=color, width=3)
    d.line((c, c-10, c, c+10), fill=color, width=3)
    return img

def toggle_recoil(icon=None, item=None):
    global recoil_enabled
    recoil_enabled = not recoil_enabled
    actualizar_estado_gui()
    actualizar_texto_flotante()
    actualizar_icono_tray()

def on_restore(icon, item):
    ventana.after(0, ventana.deiconify)

def on_exit(icon, item):
    global running
    running = False
    if tray_icon: tray_icon.stop()
    if icono_texto: icono_texto.destroy()
    ventana.destroy()

def create_tray_icon():
    global tray_icon
    icon_img = generar_icono('green' if recoil_enabled else 'red')
    menu = pystray.Menu(
        pystray.MenuItem("Restaurar ventana", on_restore),
        pystray.MenuItem("Salir", on_exit)
    )
    tray_icon = pystray.Icon("RecoilScript", icon_img, "Control de Recoil", menu)
    threading.Thread(target=tray_icon.run, daemon=True).start()

def actualizar_icono_tray():
    if tray_icon:
        color = 'green' if recoil_enabled else 'red'
        tray_icon.icon = generar_icono(color)

# === Selección de Ventana ===
def ventana_activa_es_valida():
    if ventana_objetivo_hwnd is None:
        return True
    fg = win32gui.GetForegroundWindow()
    return fg == ventana_objetivo_hwnd

def seleccionar_ventana():
    def listar_ventanas(hwnd, extra):
        if win32gui.IsWindowVisible(hwnd) and win32gui.GetWindowText(hwnd):
            lista.insert(tk.END, (win32gui.GetWindowText(hwnd), hwnd))
    def confirmar():
        global ventana_objetivo_hwnd
        seleccion = lista.curselection()
        if seleccion:
            ventana_objetivo_hwnd = lista.get(seleccion[0])[1]
            seleccionar.destroy()

    seleccionar = tk.Toplevel()
    seleccionar.title("Seleccionar ventana")
    lista = tk.Listbox(seleccionar, width=60)
    lista.pack(padx=10, pady=10)
    win32gui.EnumWindows(listar_ventanas, None)
    ttk.Button(seleccionar, text="Aceptar", command=confirmar).pack(pady=5)

# === GUI ===
def asignar_tecla():
    def on_press(key):
        global activation_key
        try:
            if isinstance(key, KeyCode) and key.char is not None:
                activation_key = key.char
                tecla_label.config(text=f"Tecla asignada: {activation_key.upper()}")
                keyboard_listener.stop()
            else:
                tecla_label.config(text="⛔ Tecla no válida. Intenta otra.")
        except Exception:
            tecla_label.config(text="⛔ Error al asignar tecla.")
    tecla_label.config(text="Presiona una tecla...")
    keyboard_listener = KeyboardListener(on_press=on_press)
    keyboard_listener.start()

def actualizar_estado_gui():
    if recoil_enabled:
        estado_btn.config(text="🟢 Activado", style="Green.TButton")
    else:
        estado_btn.config(text="🔴 Desactivado", style="Red.TButton")

def set_recoil(value):
    global recoil_strength
    recoil_strength = int(float(value))
    valor_label.config(text=f"Fuerza actual: {recoil_strength}")

def keyboard_watcher():
    def on_press(key):
        if activation_key is None:
            return
        try:
            if isinstance(key, KeyCode) and key.char is not None:
                key_str = key.char.lower()
            else:
                key_str = str(key).replace("Key.", "").lower()
            if key_str == activation_key.lower():
                toggle_recoil()
        except AttributeError:
            pass  # Ignorar teclas sin .char
    with KeyboardListener(on_press=on_press) as listener:
        listener.join()

def minimizar_a_bandeja():
    ventana.withdraw()
    create_tray_icon()

def toggle_bloqueo_movimiento():
    global movimiento_bloqueado
    movimiento_bloqueado = not movimiento_bloqueado
    if movimiento_bloqueado:
        btn_bloquear.config(text="🔓 Desbloquear movimiento")
    else:
        btn_bloquear.config(text="🔒 Bloquear movimiento")

def iniciar_listeners():
    threading.Thread(target=recoil_loop, daemon=True).start()
    threading.Thread(target=keyboard_watcher, daemon=True).start()

# === INTERFAZ ===
ventana = tk.Tk()
ventana.title("Recoil Pro Controller")
ventana.geometry("360x400")
ventana.resizable(False, False)

style = ttk.Style()
style.configure("Green.TButton", foreground="green", font=("Segoe UI", 12, "bold"))
style.configure("Red.TButton", foreground="red", font=("Segoe UI", 12, "bold"))

ttk.Label(ventana, text="Fuerza del recoil (1-100):").pack(pady=10)
valor_label = ttk.Label(ventana, text=f"Fuerza actual: {recoil_strength}")
valor_label.pack()
recoil_slider = ttk.Scale(ventana, from_=1, to=100, orient='horizontal', command=set_recoil)
recoil_slider.set(recoil_strength)
recoil_slider.pack(pady=5)

ttk.Button(ventana, text="Asignar tecla", command=asignar_tecla).pack(pady=5)
tecla_label = ttk.Label(ventana, text="Tecla asignada: Ninguna")
tecla_label.pack()

estado_btn = ttk.Button(ventana, text="🔴 Desactivado", style="Red.TButton", command=toggle_recoil)
estado_btn.pack(pady=10)
ttk.Button(ventana, text="Seleccionar ventana", command=seleccionar_ventana).pack(pady=5)
ttk.Button(ventana, text="Mover texto ON/OFF", command=mostrar_texto_flotante).pack(pady=5)

btn_bloquear = ttk.Button(ventana, text="🔒 Bloquear movimiento", command=toggle_bloqueo_movimiento)
btn_bloquear.pack(pady=5)

ttk.Button(ventana, text="Minimizar a bandeja", command=minimizar_a_bandeja).pack(pady=15)

actualizar_estado_gui()
mostrar_texto_flotante()
iniciar_listeners()

ventana.mainloop()
