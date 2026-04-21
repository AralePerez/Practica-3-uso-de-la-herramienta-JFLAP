# Practica-3-uso-de-la-herramienta-JFLAP

Extensiones agregadas al simulador

1. Soporte mejorado para AFND y AFN-λ
- Simulación general para AFND y AFN-λ.
- Manejo de múltiples estados activos.
- Manejo de ramificaciones por símbolo.
- Aplicación de λ-clausura durante la simulación.
- Visualización textual paso a paso del conjunto activo de estados.

2. Conversión entre autómatas
- AFND / AFN-λ -> AFD con algoritmo de subconjuntos.
- AFN-λ -> AFND eliminando transiciones lambda.
- Registro textual del proceso de conversión.

3. Minimización de AFD
- Eliminación de estados inaccesibles.
- Detección de pares distinguibles.
- Fusión de estados equivalentes.
- Construcción del AFD mínimo.
- Comparación con 5 cadenas representativas.

4. Interfaz gráfica ampliada
- Selector de tipo: dfa, nfa, nfae.
- Tabla de transición con columna λ para AFN-λ.
- Botón para mostrar λ-clausura de un estado.
- Pestaña de Conversión / Minimización.
- Pestaña de Pruebas múltiples con carga de TXT.

5. Pruebas múltiples
- Carga de archivo TXT con cadenas.
- Validación de todas las cadenas.
- Reporte textual exportable.

6. Liga y archivo practica en LATEX
   https://es.overleaf.com/read/rhrrtznqvfdd#bb4d3b

   

Nota:
La visualización gráfica fue mejorada para resaltar estados activos y dibujar las transiciones lambda con estilo diferenciado.
