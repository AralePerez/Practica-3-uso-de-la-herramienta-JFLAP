from __future__ import annotations

import tkinter as tk
from tkinter import ttk, filedialog, messagebox
from pathlib import Path

from automaton import Automaton, EPSILON, prefixes, suffixes, substrings, kleene_closure
from io_formats import load_automaton, save_automaton


class TransitionTable(ttk.Frame):
    def __init__(self, master, on_change=None):
        super().__init__(master)
        self.on_change = on_change
        self.entries = {}
        self.states = []
        self.alphabet = []

    def rebuild(self, states, alphabet, include_lambda=False):
        for child in self.winfo_children():
            child.destroy()
        self.entries.clear()
        self.states = list(states)
        self.alphabet = list(alphabet)
        if include_lambda and EPSILON not in self.alphabet:
            self.alphabet.append(EPSILON)
        ttk.Label(self, text="Estado", width=16).grid(row=0, column=0, padx=2, pady=2)
        for j, sym in enumerate(self.alphabet, start=1):
            ttk.Label(self, text=sym, width=16).grid(row=0, column=j, padx=2, pady=2)
        for i, st in enumerate(self.states, start=1):
            ttk.Label(self, text=st, width=16).grid(row=i, column=0, padx=2, pady=2)
            for j, sym in enumerate(self.alphabet, start=1):
                e = ttk.Entry(self, width=18)
                e.grid(row=i, column=j, padx=2, pady=2)
                e.bind("<KeyRelease>", lambda _evt: self.on_change() if self.on_change else None)
                self.entries[(st, sym)] = e

    def fill_from_automaton(self, automaton: Automaton):
        for (st, sym), entry in self.entries.items():
            key = sym
            if sym == EPSILON and sym not in automaton.transitions.get(st, {}) and "" in automaton.transitions.get(st, {}):
                key = ""
            targets = automaton.transitions.get(st, {}).get(key, set())
            entry.delete(0, tk.END)
            entry.insert(0, ",".join(sorted(targets)))

    def get_values(self):
        result = {}
        for key, entry in self.entries.items():
            raw = entry.get().strip()
            result[key] = [x.strip() for x in raw.split(",") if x.strip()] if raw else []
        return result


class AFDSimulatorApp(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("Simulador de AFD / AFND / AFN-λ")
        self.geometry("1360x860")
        self.automaton = Automaton()
        self.current_trace = []
        self.current_step = 0
        self.current_sim_automaton = None
        self._build_ui()
        self.new_automaton()

    def _build_ui(self):
        toolbar = ttk.Frame(self)
        toolbar.pack(fill="x", padx=8, pady=6)
        ttk.Button(toolbar, text="Nuevo", command=self.new_automaton).pack(side="left", padx=2)
        ttk.Button(toolbar, text="Cargar", command=self.load_file).pack(side="left", padx=2)
        ttk.Button(toolbar, text="Guardar .jff", command=lambda: self.save_file(".jff")).pack(side="left", padx=2)
        ttk.Button(toolbar, text="Exportar .json", command=lambda: self.save_file(".json")).pack(side="left", padx=2)
        ttk.Button(toolbar, text="Exportar .xml", command=lambda: self.save_file(".xml")).pack(side="left", padx=2)
        ttk.Button(toolbar, text="AFND → AFD", command=self.determinize_current).pack(side="left", padx=10)
        ttk.Button(toolbar, text="AFN-λ → AFND", command=self.remove_lambda_current).pack(side="left", padx=2)
        ttk.Button(toolbar, text="Minimizar AFD", command=self.minimize_current).pack(side="left", padx=2)
        ttk.Button(toolbar, text="Completar AFD", command=self.complete_current_dfa).pack(side="left", padx=2)

        self.notebook = ttk.Notebook(self)
        self.notebook.pack(fill="both", expand=True, padx=8, pady=6)

        self.tab_definition = ttk.Frame(self.notebook)
        self.tab_simulation = ttk.Frame(self.notebook)
        self.tab_conversion = ttk.Frame(self.notebook)
        self.tab_batch = ttk.Frame(self.notebook)
        self.tab_utils = ttk.Frame(self.notebook)

        self.notebook.add(self.tab_definition, text="Definición")
        self.notebook.add(self.tab_simulation, text="Simulación")
        self.notebook.add(self.tab_conversion, text="Conversión / Minimización")
        self.notebook.add(self.tab_batch, text="Pruebas múltiples")
        self.notebook.add(self.tab_utils, text="Utilidades")

        self._build_definition_tab()
        self._build_simulation_tab()
        self._build_conversion_tab()
        self._build_batch_tab()
        self._build_utils_tab()

    def _build_definition_tab(self):
        left = ttk.Frame(self.tab_definition)
        left.pack(side="left", fill="y", padx=6, pady=6)
        right = ttk.Frame(self.tab_definition)
        right.pack(side="left", fill="both", expand=True, padx=6, pady=6)

        form = ttk.LabelFrame(left, text="Definición manual")
        form.pack(fill="x", pady=4)

        ttk.Label(form, text="Tipo:").grid(row=0, column=0, sticky="w", padx=4, pady=4)
        self.type_combo = ttk.Combobox(form, state="readonly", width=25, values=["dfa", "nfa", "nfae"])
        self.type_combo.grid(row=0, column=1, padx=4, pady=4)
        self.type_combo.bind("<<ComboboxSelected>>", lambda _e: self.refresh_transition_editor())

        ttk.Label(form, text="Alfabeto (coma):").grid(row=1, column=0, sticky="w", padx=4, pady=4)
        self.alphabet_entry = ttk.Entry(form, width=28)
        self.alphabet_entry.grid(row=1, column=1, padx=4, pady=4)

        ttk.Label(form, text="Estados (coma):").grid(row=2, column=0, sticky="w", padx=4, pady=4)
        self.states_entry = ttk.Entry(form, width=28)
        self.states_entry.grid(row=2, column=1, padx=4, pady=4)

        ttk.Label(form, text="Estado inicial:").grid(row=3, column=0, sticky="w", padx=4, pady=4)
        self.initial_combo = ttk.Combobox(form, state="readonly", width=25)
        self.initial_combo.grid(row=3, column=1, padx=4, pady=4)

        ttk.Label(form, text="Aceptación (coma):").grid(row=4, column=0, sticky="w", padx=4, pady=4)
        self.accept_entry = ttk.Entry(form, width=28)
        self.accept_entry.grid(row=4, column=1, padx=4, pady=4)

        ttk.Button(form, text="Construir tabla", command=self.refresh_transition_editor).grid(row=5, column=0, columnspan=2, pady=6)
        ttk.Button(form, text="Aplicar cambios", command=self.apply_manual_definition).grid(row=6, column=0, columnspan=2, pady=6)

        info = ttk.LabelFrame(left, text="Información")
        info.pack(fill="x", pady=4)
        self.info_text = tk.Text(info, width=46, height=24)
        self.info_text.pack(fill="both", expand=True, padx=4, pady=4)

        table_box = ttk.LabelFrame(right, text="Función de transición")
        table_box.pack(fill="x", pady=4)
        self.transition_table = TransitionTable(table_box)
        self.transition_table.pack(fill="x", padx=4, pady=4)

        view_box = ttk.LabelFrame(right, text="Visualización")
        view_box.pack(fill="both", expand=True, pady=4)
        self.canvas = tk.Canvas(view_box, bg="white")
        self.canvas.pack(fill="both", expand=True)

    def _build_simulation_tab(self):
        top = ttk.Frame(self.tab_simulation)
        top.pack(fill="x", padx=6, pady=6)
        ttk.Label(top, text="Cadena:").pack(side="left", padx=4)
        self.string_entry = ttk.Entry(top, width=32)
        self.string_entry.pack(side="left", padx=4)
        ttk.Button(top, text="Validar", command=self.run_validation).pack(side="left", padx=4)
        ttk.Button(top, text="Preparar paso a paso", command=self.prepare_step_simulation).pack(side="left", padx=4)
        ttk.Button(top, text="Siguiente paso", command=self.next_step).pack(side="left", padx=4)
        ttk.Button(top, text="Mostrar λ-clausura", command=self.show_selected_closure).pack(side="left", padx=12)

        self.result_var = tk.StringVar(value="Resultado: —")
        ttk.Label(self.tab_simulation, textvariable=self.result_var, font=("Arial", 12, "bold")).pack(anchor="w", padx=10)

        closure_row = ttk.Frame(self.tab_simulation)
        closure_row.pack(fill="x", padx=6, pady=4)
        ttk.Label(closure_row, text="Estado para λ-clausura:").pack(side="left")
        self.closure_state_combo = ttk.Combobox(closure_row, state="readonly", width=20)
        self.closure_state_combo.pack(side="left", padx=6)
        self.closure_var = tk.StringVar(value="λ-clausura: —")
        ttk.Label(closure_row, textvariable=self.closure_var).pack(side="left", padx=6)

        middle = ttk.Frame(self.tab_simulation)
        middle.pack(fill="both", expand=True, padx=6, pady=6)
        left = ttk.LabelFrame(middle, text="Traza")
        left.pack(side="left", fill="both", expand=True, padx=4)
        right = ttk.LabelFrame(middle, text="Diagrama")
        right.pack(side="left", fill="both", expand=True, padx=4)

        self.trace_text = tk.Text(left)
        self.trace_text.pack(fill="both", expand=True, padx=4, pady=4)
        self.sim_canvas = tk.Canvas(right, bg="white")
        self.sim_canvas.pack(fill="both", expand=True, padx=4, pady=4)

    def _build_conversion_tab(self):
        upper = ttk.Frame(self.tab_conversion)
        upper.pack(fill="both", expand=True, padx=8, pady=6)
        left = ttk.LabelFrame(upper, text="Proceso")
        left.pack(side="left", fill="both", expand=True, padx=4)
        right = ttk.LabelFrame(upper, text="Resumen / Comparación")
        right.pack(side="left", fill="both", expand=True, padx=4)
        self.conversion_text = tk.Text(left)
        self.conversion_text.pack(fill="both", expand=True, padx=4, pady=4)
        self.comparison_text = tk.Text(right)
        self.comparison_text.pack(fill="both", expand=True, padx=4, pady=4)

    def _build_batch_tab(self):
        top = ttk.Frame(self.tab_batch)
        top.pack(fill="x", padx=8, pady=6)
        ttk.Button(top, text="Cargar archivo TXT", command=self.load_batch_strings).pack(side="left", padx=4)
        ttk.Button(top, text="Validar archivo", command=self.run_batch_validation).pack(side="left", padx=4)
        ttk.Button(top, text="Guardar reporte", command=self.save_batch_report).pack(side="left", padx=4)
        self.batch_file_var = tk.StringVar(value="Archivo: —")
        ttk.Label(top, textvariable=self.batch_file_var).pack(side="left", padx=10)
        self.batch_strings = []
        self.batch_text = tk.Text(self.tab_batch)
        self.batch_text.pack(fill="both", expand=True, padx=8, pady=6)

    def _build_utils_tab(self):
        frame = ttk.Frame(self.tab_utils)
        frame.pack(fill="both", expand=True, padx=10, pady=10)

        sbox = ttk.LabelFrame(frame, text="Subcadenas, prefijos y sufijos")
        sbox.pack(fill="x", pady=6)
        ttk.Label(sbox, text="Cadena:").grid(row=0, column=0, padx=4, pady=4)
        self.utils_string_entry = ttk.Entry(sbox, width=30)
        self.utils_string_entry.grid(row=0, column=1, padx=4, pady=4)
        ttk.Button(sbox, text="Calcular", command=self.compute_string_utils).grid(row=0, column=2, padx=4, pady=4)
        ttk.Button(sbox, text="Guardar TXT", command=lambda: self.save_text(self.utils_output.get("1.0", tk.END))).grid(row=0, column=3, padx=4, pady=4)
        self.utils_output = tk.Text(sbox, height=12)
        self.utils_output.grid(row=1, column=0, columnspan=4, sticky="nsew", padx=4, pady=4)

        kbox = ttk.LabelFrame(frame, text="Cerradura de Kleene y positiva")
        kbox.pack(fill="both", expand=True, pady=6)
        ttk.Label(kbox, text="Alfabeto (coma):").grid(row=0, column=0, padx=4, pady=4)
        self.kleene_alpha_entry = ttk.Entry(kbox, width=30)
        self.kleene_alpha_entry.grid(row=0, column=1, padx=4, pady=4)
        ttk.Label(kbox, text="Longitud máxima:").grid(row=0, column=2, padx=4, pady=4)
        self.kleene_len = ttk.Entry(kbox, width=8)
        self.kleene_len.grid(row=0, column=3, padx=4, pady=4)
        ttk.Button(kbox, text="Generar Σ*", command=lambda: self.compute_closure(False)).grid(row=0, column=4, padx=4, pady=4)
        ttk.Button(kbox, text="Generar Σ+", command=lambda: self.compute_closure(True)).grid(row=0, column=5, padx=4, pady=4)
        ttk.Button(kbox, text="Guardar TXT", command=lambda: self.save_text(self.kleene_output.get("1.0", tk.END))).grid(row=0, column=6, padx=4, pady=4)
        self.kleene_output = tk.Text(kbox)
        self.kleene_output.grid(row=1, column=0, columnspan=7, sticky="nsew", padx=4, pady=4)

    def new_automaton(self):
        self.automaton = Automaton()
        self.automaton.add_state("q0", initial=True, x=200, y=160)
        self.automaton.add_state("q1", accept=True, x=460, y=160)
        self.automaton.alphabet = {"0", "1"}
        self.automaton.set_transition("q0", "0", "q0")
        self.automaton.set_transition("q0", "1", "q1")
        self.automaton.set_transition("q1", "0", "q0")
        self.automaton.set_transition("q1", "1", "q1")
        self.populate_form_from_automaton()
        self.refresh_views()

    def populate_form_from_automaton(self):
        self.type_combo.set(self.automaton.automaton_type)
        self.alphabet_entry.delete(0, tk.END)
        self.alphabet_entry.insert(0, ",".join(sorted(self.automaton.alphabet)))
        self.states_entry.delete(0, tk.END)
        self.states_entry.insert(0, ",".join(sorted(self.automaton.states)))
        self.initial_combo["values"] = sorted(self.automaton.states)
        self.initial_combo.set(self.automaton.initial_state or "")
        self.accept_entry.delete(0, tk.END)
        self.accept_entry.insert(0, ",".join(sorted(self.automaton.accept_states)))
        self.closure_state_combo["values"] = sorted(self.automaton.states)
        if self.automaton.states:
            self.closure_state_combo.set(sorted(self.automaton.states)[0])
        self.refresh_transition_editor()
        self.transition_table.fill_from_automaton(self.automaton)

    def refresh_transition_editor(self):
        states = [x.strip() for x in self.states_entry.get().split(",") if x.strip()]
        alphabet = [x.strip() for x in self.alphabet_entry.get().split(",") if x.strip()]
        self.initial_combo["values"] = states
        include_lambda = self.type_combo.get() == "nfae"
        self.transition_table.rebuild(states, alphabet, include_lambda=include_lambda)
        if states and self.automaton.states == set(states) and self.automaton.alphabet == set(alphabet):
            self.transition_table.fill_from_automaton(self.automaton)

    def apply_manual_definition(self):
        try:
            states = [x.strip() for x in self.states_entry.get().split(",") if x.strip()]
            alphabet = [x.strip() for x in self.alphabet_entry.get().split(",") if x.strip()]
            initial = self.initial_combo.get().strip()
            accepts = {x.strip() for x in self.accept_entry.get().split(",") if x.strip()}
            a = Automaton(alphabet=set(alphabet), automaton_type=self.type_combo.get() or "dfa")
            for st in states:
                a.add_state(st, initial=(st == initial), accept=(st in accepts))
            a.layout_states()
            values = self.transition_table.get_values()
            for (src, sym), targets in values.items():
                real_symbol = EPSILON if sym == EPSILON else sym
                for dst in targets:
                    a.add_transition(src, real_symbol, dst)
            a._update_type()
            self.automaton = a
            self.refresh_views()
            messagebox.showinfo("OK", "Definición aplicada correctamente.")
        except Exception as e:
            messagebox.showerror("Error", str(e))

    def refresh_views(self):
        self.draw_automaton(self.canvas, self.automaton)
        self.draw_automaton(self.sim_canvas, self.automaton)
        self.info_text.delete("1.0", tk.END)
        self.info_text.insert(tk.END, f"Tipo detectado: {self.automaton.automaton_type.upper()}\n")
        self.info_text.insert(tk.END, f"Alfabeto: {sorted(self.automaton.alphabet)}\n")
        self.info_text.insert(tk.END, f"Estados: {sorted(self.automaton.states)}\n")
        self.info_text.insert(tk.END, f"Inicial: {self.automaton.initial_state}\n")
        self.info_text.insert(tk.END, f"Aceptación: {sorted(self.automaton.accept_states)}\n\n")
        self.info_text.insert(tk.END, "Tabla de transición:\n")
        for row in self.automaton.transition_table():
            self.info_text.insert(tk.END, " | ".join(row) + "\n")
        errs = self.automaton.validate_nfa_structure()
        if errs:
            self.info_text.insert(tk.END, "\nErrores:\n- " + "\n- ".join(errs))
        if self.automaton.automaton_type == "nfae":
            self.show_selected_closure()

    def draw_automaton(self, canvas, automaton: Automaton, highlight_states=None, highlight_edge=None, highlight_lambda_edges=None):
        highlight_states = set(highlight_states or [])
        highlight_lambda_edges = set(highlight_lambda_edges or [])
        canvas.delete("all")
        width = max(canvas.winfo_width(), 800)
        height = max(canvas.winfo_height(), 420)
        if not automaton.visuals:
            automaton.layout_states(width, height)
        r = 28
        for src in sorted(automaton.states):
            for sym, targets in automaton.transitions.get(src, {}).items():
                for dst in sorted(targets):
                    x1, y1 = automaton.visuals[src].x, automaton.visuals[src].y
                    x2, y2 = automaton.visuals[dst].x, automaton.visuals[dst].y
                    is_lambda = sym in (EPSILON, "")
                    color = "red" if highlight_edge == (src, sym, dst) or (src, sym, dst) in highlight_lambda_edges else ("#3366cc" if is_lambda else "black")
                    dash = (4, 3) if is_lambda else None
                    label = EPSILON if is_lambda else sym
                    if src == dst:
                        canvas.create_oval(x1 + 12, y1 - 44, x1 + 52, y1 - 4, outline=color, dash=dash)
                        canvas.create_text(x1 + 32, y1 - 54, text=label, fill=color)
                    else:
                        canvas.create_line(x1, y1, x2, y2, arrow=tk.LAST, fill=color, width=2, dash=dash)
                        mx, my = (x1 + x2) / 2, (y1 + y2) / 2
                        canvas.create_text(mx, my - 10, text=label, fill=color)
        for st in sorted(automaton.states):
            x, y = automaton.visuals[st].x, automaton.visuals[st].y
            outline = "red" if st in highlight_states else "black"
            fill = "#fff3cd" if st in highlight_states else "white"
            canvas.create_oval(x - r, y - r, x + r, y + r, width=2, outline=outline, fill=fill)
            if st in automaton.accept_states:
                canvas.create_oval(x - r + 6, y - r + 6, x + r - 6, y + r - 6, width=2, outline=outline)
            canvas.create_text(x, y, text=st)
            if st == automaton.initial_state:
                canvas.create_line(x - 70, y, x - r, y, arrow=tk.LAST, width=2)

    def load_file(self):
        path = filedialog.askopenfilename(filetypes=[("Automatas", "*.jff *.json *.xml")])
        if not path:
            return
        try:
            self.automaton = load_automaton(path)
            if not self.automaton.visuals:
                self.automaton.layout_states()
            self.populate_form_from_automaton()
            self.refresh_views()
            messagebox.showinfo("Cargado", f"Archivo cargado: {path}")
        except Exception as e:
            messagebox.showerror("Error de carga", str(e))

    def save_file(self, ext):
        path = filedialog.asksaveasfilename(defaultextension=ext, filetypes=[(ext, f"*{ext}")])
        if not path:
            return
        try:
            save_automaton(self.automaton, path)
            messagebox.showinfo("Guardado", f"Archivo guardado: {path}")
        except Exception as e:
            messagebox.showerror("Error", str(e))

    def determinize_current(self):
        try:
            dfa, steps = self.automaton.determinize_with_steps()
            self.automaton = dfa
            self.populate_form_from_automaton()
            self.refresh_views()
            self.conversion_text.delete("1.0", tk.END)
            self.conversion_text.insert(tk.END, "Conversión AFND/AFN-λ → AFD (subconjuntos)\n\n")
            for i, step in enumerate(steps, start=1):
                self.conversion_text.insert(tk.END, f"Paso {i}: estado DFA {step['name']} = {step['subset']}\n")
                for tr in step["transitions"]:
                    self.conversion_text.insert(tk.END, f"  con '{tr['symbol']}' -> move={tr['move']} -> clausura={tr['closure']} -> {tr['target_name']}\n")
                self.conversion_text.insert(tk.END, "\n")
            messagebox.showinfo("Conversión", "AFND convertido a AFD correctamente.")
            self.notebook.select(self.tab_conversion)
        except Exception as e:
            messagebox.showerror("Error", str(e))

    def remove_lambda_current(self):
        try:
            nfa, steps = self.automaton.remove_epsilon_transitions()
            self.automaton = nfa
            self.populate_form_from_automaton()
            self.refresh_views()
            self.conversion_text.delete("1.0", tk.END)
            self.conversion_text.insert(tk.END, "Conversión AFN-λ → AFND\n\n")
            for step in steps:
                self.conversion_text.insert(tk.END, f"Estado {step['state']} | λ-clausura = {step['closure']}\n")
                for tr in step['transitions']:
                    self.conversion_text.insert(tk.END, f"  con '{tr['symbol']}' -> move={tr['move_from_closure']} -> expandido={tr['expanded']}\n")
                self.conversion_text.insert(tk.END, "\n")
            messagebox.showinfo("Conversión", "Transiciones λ eliminadas correctamente.")
            self.notebook.select(self.tab_conversion)
        except Exception as e:
            messagebox.showerror("Error", str(e))

    def minimize_current(self):
        try:
            minimized, info = self.automaton.minimize_dfa()
            original = self.automaton.clone()
            strings = original.representative_test_strings(limit=5, max_len=3)
            comparison_lines = [
                f"AFD original: {info['before_count']} estados",
                f"Alcanzables: {info['after_reachable_count']}",
                f"AFD mínimo: {info['after_count']} estados",
                f"Eliminados: {info['removed_total']}",
                f"Estados inaccesibles: {info['unreachable_states']}",
                f"Grupos equivalentes: {info['equivalent_groups']}",
                "",
                "Prueba de equivalencia con 5 cadenas:",
            ]
            for s in strings:
                a1, _ = original.simulate_dfa(s)
                a2, _ = minimized.simulate_dfa(s)
                comparison_lines.append(f"  {repr(s)} -> original={'A' if a1 else 'R'} | minimizado={'A' if a2 else 'R'}")
            self.conversion_text.delete("1.0", tk.END)
            self.conversion_text.insert(tk.END, "Proceso de minimización de AFD\n\n")
            self.conversion_text.insert(tk.END, f"Estados originales: {info['original_states']}\n")
            self.conversion_text.insert(tk.END, f"Estados inaccesibles eliminados: {info['unreachable_states']}\n\n")
            self.conversion_text.insert(tk.END, "Pares distinguibles:\n")
            for item in info['distinguishable_pairs']:
                self.conversion_text.insert(tk.END, f"  {item['pair']} -> {item['reason']}\n")
            self.conversion_text.insert(tk.END, "\nGrupos equivalentes fusionados:\n")
            for group in info['equivalent_groups']:
                self.conversion_text.insert(tk.END, f"  {group}\n")
            self.comparison_text.delete("1.0", tk.END)
            self.comparison_text.insert(tk.END, "\n".join(comparison_lines))
            self.automaton = minimized
            self.populate_form_from_automaton()
            self.refresh_views()
            messagebox.showinfo("Minimización", "AFD minimizado correctamente.")
            self.notebook.select(self.tab_conversion)
        except Exception as e:
            messagebox.showerror("Error", str(e))

    def complete_current_dfa(self):
        try:
            self.automaton.complete_with_sink()
            self.populate_form_from_automaton()
            self.refresh_views()
            messagebox.showinfo("AFD", "AFD completado con estado sumidero cuando fue necesario.")
        except Exception as e:
            messagebox.showerror("Error", str(e))

    def run_validation(self):
        s = self.string_entry.get()
        try:
            accepted, trace = self.automaton.simulate_dfa(s) if self.automaton.is_dfa() else self.automaton.simulate_nfa(s)
            self.result_var.set(f"Resultado: {'ACEPTADA' if accepted else 'RECHAZADA'}")
            self.trace_text.delete("1.0", tk.END)
            for item in trace:
                if 'from' in item:
                    self.trace_text.insert(tk.END, f"Paso {item['step']}: símbolo={item['symbol']} | {item.get('from')} -> {item.get('to')}\n")
                else:
                    self.trace_text.insert(tk.END, f"Paso {item['step']}: símbolo={item['symbol']} | activos={item.get('active_before')} | clausura={item.get('closure')} | resultado={item.get('active_after')}\n")
                    for branch in item.get('branches', []):
                        self.trace_text.insert(tk.END, f"    {branch['from']} --{branch['symbol']}--> {branch['to']}\n")
            last = trace[-1]
            highlight_states = [last.get('to')] if last.get('to') else last.get('active_after', [])
            self.draw_automaton(self.sim_canvas, self.automaton, highlight_states=highlight_states)
        except Exception as e:
            messagebox.showerror("Error", str(e))

    def prepare_step_simulation(self):
        s = self.string_entry.get()
        try:
            _accepted, trace = self.automaton.simulate_dfa(s) if self.automaton.is_dfa() else self.automaton.simulate_nfa(s)
            self.current_sim_automaton = self.automaton.clone()
            self.current_trace = trace
            self.current_step = 0
            self.trace_text.delete("1.0", tk.END)
            self.result_var.set("Resultado: simulación preparada")
            self.draw_automaton(self.sim_canvas, self.current_sim_automaton)
            self.next_step()
        except Exception as e:
            messagebox.showerror("Error", str(e))

    def next_step(self):
        if not self.current_trace:
            return
        if self.current_step >= len(self.current_trace):
            last = self.current_trace[-1]
            final_state = last.get("to")
            active = set(last.get("active_after", []))
            accepted = (final_state in self.current_sim_automaton.accept_states) if final_state else bool(active & self.current_sim_automaton.accept_states)
            self.result_var.set(f"Resultado final: {'ACEPTADA' if accepted else 'RECHAZADA'}")
            return
        item = self.current_trace[self.current_step]
        if 'from' in item:
            self.trace_text.insert(tk.END, f"Paso {item['step']}: símbolo={item['symbol']} | {item.get('from')} -> {item.get('to')}\n")
            edge = None
            if item.get('from') and item.get('to') and item.get('symbol') != 'ε':
                edge = (item['from'], item['symbol'], item['to'])
            self.draw_automaton(self.sim_canvas, self.current_sim_automaton, highlight_states=[item.get('to')] if item.get('to') else [], highlight_edge=edge)
        else:
            self.trace_text.insert(tk.END, f"Paso {item['step']}: símbolo={item['symbol']} | activos={item.get('active_before')} | clausura={item.get('closure')} | resultado={item.get('active_after')}\n")
            lambda_edges = set()
            if self.current_sim_automaton.automaton_type == 'nfae':
                for st in item.get('active_before', []):
                    for dst in self.current_sim_automaton.transitions.get(st, {}).get(EPSILON, set()):
                        if dst in item.get('closure', []):
                            lambda_edges.add((st, EPSILON, dst))
            self.draw_automaton(self.sim_canvas, self.current_sim_automaton, highlight_states=item.get('active_after', []), highlight_lambda_edges=lambda_edges)
        self.current_step += 1

    def show_selected_closure(self):
        st = self.closure_state_combo.get().strip()
        if not st:
            self.closure_var.set("λ-clausura: —")
            return
        closure = sorted(self.automaton.epsilon_closure({st}))
        self.closure_var.set(f"λ-clausura({st}) = {closure}")
        self.draw_automaton(self.sim_canvas, self.automaton, highlight_states=closure)

    def load_batch_strings(self):
        path = filedialog.askopenfilename(filetypes=[("Texto", "*.txt")])
        if not path:
            return
        lines = [line.rstrip("\n") for line in Path(path).read_text(encoding="utf-8").splitlines()]
        self.batch_strings = lines
        self.batch_file_var.set(f"Archivo: {path}")
        self.batch_text.delete("1.0", tk.END)
        self.batch_text.insert(tk.END, "Cadenas cargadas:\n")
        for line in lines:
            self.batch_text.insert(tk.END, repr(line) + "\n")

    def run_batch_validation(self):
        if not self.batch_strings:
            messagebox.showerror("Error", "Primero carga un archivo de cadenas.")
            return
        try:
            results = self.automaton.batch_validate_strings(self.batch_strings)
            self.batch_text.delete("1.0", tk.END)
            self.batch_text.insert(tk.END, "Reporte de validación múltiple\n\n")
            for item in results:
                self.batch_text.insert(tk.END, f"Cadena {repr(item['string'])}: {'ACEPTADA' if item['accepted'] else 'RECHAZADA'} | pasos={item['steps']}\n")
        except Exception as e:
            messagebox.showerror("Error", str(e))

    def save_batch_report(self):
        self.save_text(self.batch_text.get("1.0", tk.END))

    def compute_string_utils(self):
        s = self.utils_string_entry.get()
        self.utils_output.delete("1.0", tk.END)
        self.utils_output.insert(tk.END, f"Cadena: {s}\n\n")
        self.utils_output.insert(tk.END, "Prefijos:\n")
        self.utils_output.insert(tk.END, "\n".join(repr(x) for x in prefixes(s)) + "\n\n")
        self.utils_output.insert(tk.END, "Sufijos:\n")
        self.utils_output.insert(tk.END, "\n".join(repr(x) for x in suffixes(s)) + "\n\n")
        self.utils_output.insert(tk.END, "Subcadenas:\n")
        self.utils_output.insert(tk.END, "\n".join(repr(x) for x in substrings(s)) + "\n")

    def compute_closure(self, positive: bool):
        alphabet = [x.strip() for x in self.kleene_alpha_entry.get().split(",") if x.strip()]
        try:
            max_len = int(self.kleene_len.get().strip())
        except ValueError:
            messagebox.showerror("Error", "La longitud máxima debe ser un entero.")
            return
        results = kleene_closure(alphabet, max_len, positive=positive)
        self.kleene_output.delete("1.0", tk.END)
        title = "Σ+" if positive else "Σ*"
        self.kleene_output.insert(tk.END, f"{title} para Σ={alphabet} con longitud máxima {max_len}\n\n")
        self.kleene_output.insert(tk.END, "\n".join(repr(x) for x in results))

    def save_text(self, content: str):
        path = filedialog.asksaveasfilename(defaultextension=".txt", filetypes=[("Texto", "*.txt")])
        if path:
            Path(path).write_text(content, encoding="utf-8")
            messagebox.showinfo("Guardado", f"Archivo guardado: {path}")


if __name__ == "__main__":
    app = AFDSimulatorApp()
    app.mainloop()
