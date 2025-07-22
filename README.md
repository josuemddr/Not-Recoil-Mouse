# FocusRecoil

Herramienta avanzada para controlar el recoil automático en juegos de disparos. Implementada en Python con una interfaz gráfica amigable y funcionalidades integradas para una experiencia eficiente y personalizable.

---

## Características principales

- **Simulación realista de recoil:**  
  Algoritmo no lineal que calcula la fuerza del recoil basada en un slider ajustable para simular el retroceso natural de las armas.

- **Control preciso del mouse a nivel sistema:**  
  Usa llamadas nativas de Windows para mover el cursor con alta precisión y compatibilidad con juegos.

- **Escucha global de mouse y teclado:**  
  Detecta pulsaciones del botón izquierdo del mouse y tecla activadora configurada para activar/desactivar el recoil.

- **Restricción a ventana específica:**  
  Solo activa recoil cuando la ventana objetivo está en primer plano, evitando interferencias en otras apps.

- **Interfaz gráfica funcional y amigable:**  
  - Slider para ajustar fuerza del recoil.  
  - Botón para asignar tecla activadora personalizada.  
  - Selector de ventana objetivo.  
  - Indicador flotante movible que muestra el estado ON/OFF.  
  - Minimización a la bandeja con icono dinámico que refleja estado.

- **Multihilos para mejor rendimiento:**  
  Ejecuta escuchas y GUI en paralelo para mantener la app responsiva.

---

## Requisitos

- Python 3.11
- Windows (por el uso de API Win32)  
- Paquetes Python:  
  - `pynput`  
  - `pystray`  
  - `Pillow`  
  - `pywin32`  

