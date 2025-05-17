
import tkinter as tk

from pyo import Server, Sine, LFO, Adsr, Biquad, Delay, Mixer


class PianoSynthesizer:
    def __init__(self, root):
        self.root = root
        self.root.title("NATH SYNTH")
        self.root.geometry("1200x550")
        self.root.resizable(True, True) # la pantalla se acomoda al mouse
        self.root.configure(bg='#172a4a')

        self.server = Server().boot() #inicia pyo
        self.server.start()

        self.notes = {                      #diccionario
            'q': 261.63, '2': 277.18, 'w': 293.66, '3': 311.13, 'e': 329.63,
            'r': 349.23, '5': 369.99, 't': 392.00, '6': 415.30, 'y': 440.00,
            '7': 466.16, 'u': 493.88, 'i': 523.25, '9': 554.37, 'o': 587.33,
            '0': 622.25, 'p': 659.26
        }

        self.oscillators = {}  #limpia nota repetida

        # Octava actual (para los botones de octava)
        self.octave = 4

        # Parámetros del sintetizador
        self.synth_params = {
            'attack': 0.01,
            'decay': 0.1,
            'sustain': 0.7,
            'release': 0.3,
            'volume': 0.4,
            'filter_freq': 1000,
            'filter_res': 1,
            'lfo_rate': 0,
            'lfo_spd': 0,
            'lfo_depth': 0,
            'filter_type': 0,  # 0: lowpass, 1: highpass, 2: bandpass
            'echo_time': 0.2,
            'echo_feedback': 0,
            'echo_mix': 0
        }

        self.waveforms = [
            lambda freq, mul=1: Sine(freq, mul=mul),  # Onda senoidal
            lambda freq, mul=1: Sine(freq, mul=mul),  # Onda senoidal
            lambda freq, mul=1: LFO(freq=freq, type=1, mul=mul),  # Onda cuadrada
            lambda freq, mul=1: LFO(freq=freq, type=3, mul=mul),  # Onda triangular
            lambda freq, mul=1: LFO(freq=freq, type=2, mul=mul)  # Onda diente de sierra
        ]
        self.current_waveform = 1

        # Crear marco principal
        self.main_frame = tk.Frame(root, bg='#351440')
        self.main_frame.pack(fill=tk.BOTH, expand=True, padx=20, pady=20)

        # Crear sección de controles de octava en la parte superior
        self.create_octave_controls()

        # Crear el teclado del piano
        self.create_piano_keyboard()

        # Crear los paneles de control
        self.create_control_panels()

        self.root.bind("<KeyPress>", self.key_press)  # estás diciendo: "Cuando ocurra este tipo de evento en la ventana principal (root), llama a esta función específica".
        self.root.bind("<KeyRelease>", self.key_release) #libera tecla

    def create_octave_controls(self):#define metodo
        octave_frame = tk.Frame(self.main_frame, bg='black', bd=2, relief=tk.RAISED)# raisen estilo de borde
        octave_frame.pack(fill=tk.X, pady=(0, 20))

        # Dividir en dos mitades
        left_frame = tk.Frame(octave_frame, bg='dark green')
        left_frame.pack(side=tk.LEFT, expand=True, fill=tk.BOTH, padx=10)

        right_frame = tk.Frame(octave_frame, bg="purple")  # Otro color para diferenciar
        right_frame.pack(side=tk.LEFT, expand=True, fill=tk.BOTH, padx=10)

        # Controles de octava en la parte izquierda
        self.octave_label = tk.Label(left_frame, text="OCT RANGE", bg='black', fg="white", width=12,
                                     font=('Imprint MT Shadow', 10))
        self.octave_label.pack(side=tk.LEFT, pady=10)

        oct_frame = tk.Frame(left_frame, bg='black')
        oct_frame.pack(side=tk.LEFT, padx=5)

        btn_minus = self.create_button(oct_frame, "-", command=lambda: self.change_octave(-1), width=2) #ejecuta el comando
        btn_minus.pack(side=tk.LEFT, padx=5)

        self.octave_label = tk.Label(oct_frame, text=str(self.octave), bg='#2d0875', fg='white', width=2)
        self.octave_label.pack(side=tk.LEFT)

        btn_plus = self.create_button(oct_frame, "+", command=lambda: self.change_octave(+1), width=2)
        btn_plus.pack(side=tk.LEFT, padx=5)#boton plus es la funcion que crea el sumador izq

        # Agregar otra sección en la mitad derecha (Ejemplo: otro control similar)
        self.another_label = tk.Label(right_frame, text="WAVEFORM", bg='#444444', fg="white", width=15,
                                      font=('Garamond', 10))
        self.another_label.pack(side=tk.LEFT, pady=10)

        waveform_buttons_frame = tk.Frame(right_frame, bg='#444444')
        waveform_buttons_frame.pack(side=tk.LEFT)

        # Botones para formas de onda
        waveforms = ["SINE", "SQUARE", "TRIANGLE", "SAW"]
        self.waveform_buttons = []

        for i, wf in enumerate(waveforms, start=1): #itera sobre la lsita
            btn = self.create_button(  #
                waveform_buttons_frame,
                wf,
                width=10,
                height=1,
                command=lambda idx=i: self.set_waveform(idx)
            )
            btn.grid(row=0, column=i - 1, padx=5, pady=5)
            self.waveform_buttons.append(btn)

        self.waveform_buttons[0].config(bg="#0D47A1", fg="white")

    def create_piano_keyboard(self):
        # Marco para el teclado del piano
        keyboard_frame = tk.Frame(self.main_frame, bg='#e0e0e0', height=200)
        keyboard_frame.pack(fill=tk.X, pady=(0, 20))




        # Canvas para el teclado
        self.canvas = tk.Canvas(keyboard_frame, height=200, bg='#82ff69', highlightthickness=0)
        self.canvas.pack(fill=tk.X)

        # Dibujar las teclas
        self.draw_piano_keys()

    def draw_piano_keys(self):
        white_key_width, white_key_height = 50, 180
        black_key_width, black_key_height = 30, 110
        start_x = 100

        self.white_keys = {}
        self.black_keys = {}
        self.key_rects = {}

        white_notes = ['q', 'w', 'e', 'r', 't', 'y', 'u', 'i', 'o', 'p']
        for i, note in enumerate(white_notes): #Inicia un bucle for que itera sobre la lista white_notes. La función enumerate() proporciona tanto el índice (i) como el valor (note) de cada elemento en la lista.
            x = start_x + i * white_key_width #Calcula la coordenada x de la esquina superior izquierda de cada tecl
            key = self.canvas.create_rectangle(x, 10, x + white_key_width, 10 + white_key_height, fill='white',
                                               outline='black', width=1)
            self.canvas.create_text(x + white_key_width / 2, white_key_height - 10, text=note.upper(), fill='#aaaaaa',
                                    font=('Ravie', 14))

            self.white_keys[note] = key
            self.key_rects[key] = note

            self.canvas.tag_bind(key, "<ButtonPress-1>", self.mouse_press)
            self.canvas.tag_bind(key, "<ButtonRelease-1>", self.mouse_release)

        black_notes = [('2', 0), ('3', 1), ('5', 3), ('6', 4), ('7', 5), ('9', 7), ('0', 8)]
        for note, i in black_notes:
            x = start_x + i * white_key_width + white_key_width - black_key_width / 2
            key = self.canvas.create_rectangle(x, 10, x + black_key_width, 10 + black_key_height, fill='black',
                                               outline='black', width=1)
            self.canvas.create_text(x + black_key_width / 2, 10 + black_key_height - 20, text=note, fill='#888888',
                                    font=('Ravie', 12))

            self.black_keys[note] = key
            self.key_rects[key] = note

            self.canvas.tag_bind(key, "<ButtonPress-1>", self.mouse_press)
            self.canvas.tag_bind(key, "<ButtonRelease-1>", self.mouse_release)

    def create_control_panels(self):
        # Marco para los paneles de control
        controls_frame = tk.Frame(self.main_frame, bg='#333333')
        controls_frame.pack(fill=tk.X)

        # Panel de Envolvente y Volumen (rosa)
        envelope_frame = self.create_panel(controls_frame, "ENVELOPES / VOLUME", "#141be0")
        envelope_frame.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=5)

        envelope_params = [
            ("ATTK", "attack", 0, 1),
            ("DCV", "decay", 0, 1),
            ("STN", "sustain", 0, 1),
            ("REL", "release", 0, 1),
            ("VOL", "volume", 0, 1)
        ]

        self.create_sliders(envelope_frame, envelope_params)

        # Panel de Filtro (amarillo)
        filter_frame = self.create_panel(controls_frame, "F I L T E R", "#2cd4bb")
        filter_frame.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=5)

        filter_params = [
            ("FREQ", "filter_freq", 50, 5000),
            ("RES", "filter_res", 0.1, 10),
            ("LFO", "lfo_rate", 0, 10),
            ("SPD", "lfo_spd", 0, 1),
            ("DPTH", "lfo_depth", 0, 1)
        ]

        self.create_sliders(filter_frame, filter_params)

        # Panel de Eco (verde)
        echo_frame = self.create_panel(controls_frame, "E C H O", "#571694")
        echo_frame.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=5)

        echo_params = [
            ("TIME", "echo_time", 0, 1),
            ("FBCK", "echo_feedback", 0, 0.9),
            ("FREQ", "echo_freq", 50, 5000),
            ("MIX", "echo_mix", 0, 1)
        ]

        self.create_sliders(echo_frame, echo_params)

    def create_panel(self, parent, title, bg_color):
        frame = tk.Frame(parent, bg=bg_color, bd=2, relief=tk.RAISED, padx=10, pady=15)

        title_label = tk.Label(frame, text=title, bg='black', fg='white', font=('Nepomuk SC', 12, 'bold'), width=20, pady=5)
        title_label.pack(pady=(0, 15))

        return frame

    def create_sliders(self, parent, params):
        # Crear marco para las etiquetas
        labels_frame = tk.Frame(parent, bg=parent['bg'])
        labels_frame.pack(fill=tk.X, pady=(0, 5))

        # Mostrar etiquetas
        for i, (label, param, min_val, max_val) in enumerate(params):
            lbl = tk.Label(labels_frame, text=label, bg=parent['bg'], fg='black', font=('Arial', 10, 'bold'))
            lbl.grid(row=0, column=i, padx=17)

        # Crear marco para los deslizadores
        sliders_frame = tk.Frame(parent, bg=parent['bg'])
        sliders_frame.pack(fill=tk.X)

        # Crear deslizadores verticales
        for i, (label, param, min_val, max_val) in enumerate(params):
            slider_frame = tk.Frame(sliders_frame, bg='black', bd=1, relief=tk.SUNKEN,
                                    width=50, height=100)
            slider_frame.grid(row=0, column=i, padx=10, pady=5)
            slider_frame.grid_propagate(False)

            # Crear el control deslizante
            knob = tk.Frame(slider_frame, width=30, height=30, bg='black', bd=1, relief=tk.RAISED)
            knob.place(relx=0.5, rely=0.7, anchor=tk.CENTER)

            # Crear un círculo negro dentro del knob
            circle = tk.Canvas(knob, width=20, height=20, bg='black', highlightthickness=0)
            circle.place(relx=0.5, rely=0.5, anchor=tk.CENTER)
            circle.create_oval(2, 2, 18, 18, fill='black', outline='white')

            slider_frame.bind("<Button-1>",
                              lambda event, p=param, min_v=min_val, max_v=max_val:
                              self.start_dragging(event, p, min_v, max_v))

            # Guardar referencia al knob
            setattr(self, f"{param}_knob", knob)

    def create_button(self, parent, text, command=None, bg="#b08ad4", fg="white", width=None, height=None):
        btn = tk.Button(parent, text=text, bg=bg, fg=fg, relief=tk.RAISED,
                        bd=2, command=command, font=('Baskerville Old Face', 11, 'bold'),
                        width=width, height=height)
        return btn

    def change_octave(self, delta):
        self.octave = max(0, min(8, self.octave + delta))
        self.octave_label.config(text=str(self.octave))

        if self.oscillators:
            self.update_active_oscillators()

    def start_dragging(self, event, param, min_val, max_val):
        frame = event.widget
        knob = getattr(self, f"{param}_knob")

        def on_drag(e):
            # Calcular posición relativa del deslizador (0-1)
            frame_height = frame.winfo_height()
            y = max(0, min(frame_height, e.y))
            rel_y = 1 - (y / frame_height)  # Invertir para que abajo sea 0 y arriba sea 1

            # Posicionar el knob
            knob.place(relx=0.5, rely=1 - rel_y, anchor=tk.CENTER)
            value = (max_val - min_val) * rel_y + min_val
            self.synth_params[param] = value

            self.update_active_oscillators()

        frame.bind("<B1-Motion>", on_drag)

        def stop_dragging(e):
            frame.unbind("<B1-Motion>")
            frame.unbind("<ButtonRelease-1>")

        frame.bind("<ButtonRelease-1>", stop_dragging)

    def set_waveform(self, waveform_idx):
        self.waveform_buttons[self.current_waveform - 1].config(bg='#0077A0', fg='white')

        self.current_waveform = waveform_idx
        self.waveform_buttons[waveform_idx - 1].config(bg='#0D47A1', fg='white')

        self.update_active_oscillators()

    def update_active_oscillators(self):
        for note in list(self.oscillators.keys()):
            self.stop_note(note)
            self.play_note(note)

    def key_press(self, event):
        note = event.char.lower()
        if note in self.notes and note not in self.oscillators:
            self.play_note(note)

    def key_release(self, event):
        note = event.char.lower()
        if note in self.oscillators:
            self.stop_note(note)

    def mouse_press(self, event):
        key_id = self.canvas.find_closest(event.x, event.y)[0]
        note = self.key_rects.get(key_id, None)
        if note in self.notes and note not in self.oscillators:
            self.play_note(note)

    def mouse_release(self, event):
        key_id = self.canvas.find_closest(event.x, event.y)[0]
        note = self.key_rects.get(key_id, None)
        if note in self.oscillators:
            self.stop_note(note)

    def play_note(self, note):#uni pyo
        if note in self.white_keys:
            self.canvas.itemconfig(self.white_keys[note], fill="#ccccff")
        elif note in self.black_keys:
            self.canvas.itemconfig(self.black_keys[note], fill="#333399")

        base_freq = self.notes[note]
        octave_diff = self.octave - 4
        adjusted_freq = base_freq * (2 ** octave_diff)

        waveform_class = self.waveforms[self.current_waveform]

        env = Adsr(
            attack=self.synth_params["attack"],
            decay=self.synth_params["decay"],
            sustain=self.synth_params["sustain"],
            release=self.synth_params["release"],
            mul=self.synth_params["volume"],
        ).play()

        osc = waveform_class(freq=adjusted_freq, mul=env)

        if self.synth_params["filter_freq"] > 0:
            filt = Biquad(
                input=osc,
                freq=self.synth_params["filter_freq"],
                q=self.synth_params["filter_res"],
                type=self.synth_params["filter_type"],
            )

            if self.synth_params["lfo_rate"] > 0:   #si modifica lleva la varia bla a a la seañal actual, volumen
                lfo_actual_freq = self.synth_params["lfo_spd"] * 10
                lfo = Sine(
                    freq=lfo_actual_freq,
                    mul=self.synth_params["lfo_depth"] * 1000
                )
                filt.freq = self.synth_params["filter_freq"] + lfo

            signal = filt
        else:# llevo la nota
            signal = osc

        if self.synth_params["echo_feedback"] > 0:
           #si echo es mayor que cero

            echo = Delay(
                input=signal,
                delay=self.synth_params["echo_time"],
                feedback=self.synth_params["echo_feedback"],
            )

            mixer = Mixer(outs=2, chnls=2)
            mixer.addInput(0, signal) # signal original
            mixer.addInput(1, echo) # signal echo
            mixer.setAmp(0,0, 1 - self.synth_params["echo_mix"]) # nivel original
            mixer.setAmp(1,0, self.synth_params["echo_mix"]) # nivel echo
            final_signal = mixer
        else:
            final_signal = signal

        final_signal.out()

        self.oscillators[note] = (osc, env, final_signal)

    def stop_note(self, note):
        if note in self.oscillators:
            osc, env, final_signal = self.oscillators[note]

            env.stop()
            del self.oscillators[note]

            if note in self.white_keys:
                self.canvas.itemconfig(self.white_keys[note], fill="white")
            elif note in self.black_keys:
                self.canvas.itemconfig(self.black_keys[note], fill="black")

    def on_close(self):
        self.root.destroy()
        self.server.stop()


if __name__ == "__main__": # El código dentro de este bloque solo se ejecutará cuando el script se ejecute directamente (no cuando se importe como un módulo en otro script
    root = tk.Tk() #inicia biblioteca tk
    app = PianoSynthesizer(root) #la clase pasa al root
    root.protocol("WM_DELETE_WINDOW", app.on_close) #cierra la venta  app funcio on class ue maneje cualquier limpieza necesaria antes de que la aplicación se cierre por completo
    root.mainloop()
