import tkinter as tk # Para la interfaz
from tkinter import filedialog, messagebox, scrolledtext, ttk
import os
import webbrowser

import ply.yacc as yacc
# Se importa la lista de errores del lexer
from lexer import tokens, lexer as ply_lexer, reserved, errores_lexicos

html_output_parts = []
parsing_had_error = False
errores_lexico_sintactico = []
app_instance = None  

# ----- GRAMÁTICA -----

def p_json(p):
    'p_json : APERTURA_OBJETO contenido CLAUSURA_OBJETO'
    p[0] = dict(p[2])

def p_contenido(p):
    '''contenido : equipos COMA version COMA firma_digital
                 | equipos COMA firma_digital COMA version
                 | version COMA equipos COMA firma_digital
                 | version COMA firma_digital COMA equipos
                 | firma_digital COMA equipos COMA version
                 | firma_digital COMA version COMA equipos
                 | equipos COMA version
                 | version COMA equipos
                 | equipos COMA firma_digital
                 | firma_digital COMA equipos
                 | equipos'''
    p[0] = [g for g in p[1:] if g and g != ',']

def p_par_version(p):
    '''version : VERSION DOS_PUNTOS VALOR_STRING
               | VERSION DOS_PUNTOS VALOR_NULL'''
    p[0] = ('version', p[3])

def p_par_firma_digital(p):
    '''firma_digital : FIRMA_DIGITAL DOS_PUNTOS VALOR_STRING
                     | FIRMA_DIGITAL DOS_PUNTOS VALOR_NULL'''
    p[0] = ('firma_digital', p[3])

def p_par_equipos(p):
    'equipos : EQUIPOS DOS_PUNTOS APERTURA_LISTA lista_equipos CLAUSURA_LISTA'
    p[0] = ('equipos', p[4])

def p_lista_equipos(p):
    '''lista_equipos : APERTURA_OBJETO miembros_equipo CLAUSURA_OBJETO COMA lista_equipos
                     | APERTURA_OBJETO miembros_equipo CLAUSURA_OBJETO'''
    if len(p) == 6:
        p[0] = [dict(p[2])] + p[5]
    else:
        p[0] = [dict(p[2])]

def p_miembros_equipo(p):
    '''miembros_equipo : nombre_equipo COMA identidad_equipo COMA direccion COMA link COMA carrera COMA asignatura COMA universidad_regional COMA alianza_equipo COMA integrantes COMA proyectos
                       | nombre_equipo COMA identidad_equipo COMA direccion COMA carrera COMA asignatura COMA universidad_regional COMA alianza_equipo COMA integrantes COMA proyectos
                       | nombre_equipo COMA identidad_equipo COMA link COMA carrera COMA asignatura COMA universidad_regional COMA alianza_equipo COMA integrantes COMA proyectos
                       | nombre_equipo COMA identidad_equipo COMA carrera COMA asignatura COMA universidad_regional COMA alianza_equipo COMA integrantes COMA proyectos'''
    p[0] = [item for item in p[1:] if item and item != ',']

# --- Pares clave-valor de Equipo ---
def p_nombre_equipo(p):
    'nombre_equipo : NOMBRE_EQUIPO DOS_PUNTOS VALOR_STRING'
    p[0] = ('nombre_equipo', p[3])

def p_nombre_equipo_error(p):
    'nombre_equipo : NOMBRE_EQUIPO DOS_PUNTOS error'
    _reportar_error_tipo(p.lineno(1), "nombre_equipo", "una cadena de texto (ej: \"Equipo A\")")

def p_identidad_equipo(p):
    'identidad_equipo : IDENTIDAD_EQUIPO DOS_PUNTOS VALOR_URL'
    p[0] = ('identidad_equipo', p[3])

def p_identidad_equipo_error(p):
    'identidad_equipo : IDENTIDAD_EQUIPO DOS_PUNTOS error'
    _reportar_error_tipo(p.lineno(1), "identidad_equipo", "una URL válida (ej: \"http://example.com/logo.png\")")

# --- Reglas para Dirección ---
def p_direccion(p):
    '''direccion : DIRECCION DOS_PUNTOS valor_para_direccion'''
    p[0] = ('direccion', p[3])

def p_valor_para_direccion(p):
    '''valor_para_direccion : VALOR_NULL
                            | APERTURA_OBJETO CLAUSURA_OBJETO
                            | APERTURA_OBJETO miembros_direccion CLAUSURA_OBJETO'''
    if len(p) == 2:
        p[0] = p[1]
    elif len(p) == 3:
        p[0] = {}
    else:
        p[0] = dict(p[2])

def p_miembros_direccion(p):
    '''miembros_direccion : calle COMA ciudad COMA pais
                          | calle COMA pais COMA ciudad
                          | ciudad COMA calle COMA pais
                          | ciudad COMA pais COMA calle
                          | pais COMA calle COMA ciudad
                          | pais COMA ciudad COMA calle'''
    p[0] = [item for item in p[1:] if item and item != ',']

def p_par_calle(p):
    'calle : CALLE DOS_PUNTOS VALOR_STRING'
    p[0] = ('calle', p[3])

def p_par_calle_error(p):
    'calle : CALLE DOS_PUNTOS error'
    _reportar_error_tipo(p.lineno(1), "calle", "una cadena de texto (ej: \"Calle Falsa 123\")")

def p_par_ciudad(p):
    'ciudad : CIUDAD DOS_PUNTOS VALOR_STRING'
    p[0] = ('ciudad', p[3])

def p_par_ciudad_error(p):
    'ciudad : CIUDAD DOS_PUNTOS error'
    _reportar_error_tipo(p.lineno(1), "ciudad", "una cadena de texto (ej: \"Ciudad Ejemplo\")")

def p_par_pais(p):
    'pais : PAIS DOS_PUNTOS VALOR_STRING'
    p[0] = ('pais', p[3])

def p_par_pais_error(p):
    'pais : PAIS DOS_PUNTOS error'
    _reportar_error_tipo(p.lineno(1), "pais", "una cadena de texto (ej: \"Argentina\")")

# --- Seguimos con los pares clave-valor de Equipo ---
def p_link(p):
    '''link : LINK DOS_PUNTOS VALOR_URL
            | LINK DOS_PUNTOS VALOR_NULL'''
    p[0] = ('link', p[3])

def p_link_error(p):
    'link : LINK DOS_PUNTOS error'
    _reportar_error_tipo(p.lineno(1), "link", "una URL válida o null")

def p_carrera(p):
    'carrera : CARRERA DOS_PUNTOS VALOR_STRING'
    p[0] = ('carrera', p[3])

def p_carrera_error(p):
    'carrera : CARRERA DOS_PUNTOS error'
    _reportar_error_tipo(p.lineno(1), "carrera", "una cadena de texto (ej: \"Ingeniería en Sistemas\")")

def p_asignatura(p):
    'asignatura : ASIGNATURA DOS_PUNTOS VALOR_STRING'
    p[0] = ('asignatura', p[3])

def p_asignatura_error(p):
    'asignatura : ASIGNATURA DOS_PUNTOS error'
    _reportar_error_tipo(p.lineno(1), "asignatura", "una cadena de texto (ej: \"Programación Avanzada\")")

def p_universidad_regional(p):
    'universidad_regional : UNIVERSIDAD_REGIONAL DOS_PUNTOS VALOR_STRING'
    p[0] = ('universidad_regional', p[3])

def p_universidad_regional_error(p):
    'universidad_regional : UNIVERSIDAD_REGIONAL DOS_PUNTOS error'
    _reportar_error_tipo(p.lineno(1), "universidad_regional", "una cadena de texto (ej: \"UTN\")")

def p_alianza_equipo(p):
    'alianza_equipo : ALIANZA_EQUIPO DOS_PUNTOS VALOR_STRING'
    p[0] = ('alianza_equipo', p[3])

def p_alianza_equipo_error(p):
    'alianza_equipo : ALIANZA_EQUIPO DOS_PUNTOS error'
    _reportar_error_tipo(p.lineno(1), "alianza_equipo", "una cadena de texto (ej: \"Alianza X\")")

# --- Reglas para Integrantes ---
def p_integrantes(p):
    'integrantes : INTEGRANTES DOS_PUNTOS APERTURA_LISTA lista_integrantes CLAUSURA_LISTA'
    p[0] = ('integrantes', p[4])

def p_lista_integrantes(p):
    '''lista_integrantes : integrante_objeto COMA lista_integrantes
                         | integrante_objeto'''
    if len(p) == 4:
        p[0] = [p[1]] + p[3]
    else:
        p[0] = [p[1]]


def p_integrante_objeto(p):
    'integrante_objeto : APERTURA_OBJETO miembros_integrante CLAUSURA_OBJETO'
    p[0] = dict(p[2])

def p_miembros_integrante(p):
    '''miembros_integrante : nombre_par COMA edad_par COMA cargo_par COMA foto_par COMA email_par COMA habilidades_par COMA salario_par COMA activo_par
                           | nombre_par COMA cargo_par COMA foto_par COMA email_par COMA habilidades_par COMA salario_par COMA activo_par'''
    p[0] = [item for item in p[1:] if item and item != ',']

def p_par_nombre(p):
    'nombre_par : NOMBRE DOS_PUNTOS VALOR_STRING'
    p[0] = ('nombre', p[3])

def p_par_nombre_error(p):
    'nombre_par : NOMBRE DOS_PUNTOS error'
    _reportar_error_tipo(p.lineno(1), "nombre", "una cadena de texto (ej: \"Juan Pérez\")")

def p_par_edad(p):
    '''edad_par : EDAD DOS_PUNTOS VALOR_ENTERO
                | EDAD DOS_PUNTOS VALOR_NULL'''
    p[0] = ('edad', p[3])

def p_par_edad_error(p):
    'edad_par : EDAD DOS_PUNTOS error'
    _reportar_error_tipo(p.lineno(1), "edad", "un número entero (ej: 25) o null")

def p_par_cargo(p):
    'cargo_par : CARGO DOS_PUNTOS VALOR_STRING'
    cargos_validos = {
        "product analyst", "project manager", "ux designer", "marketing", "developer", "devops", "db admin"
    }

    valor_sin_comillas = p[3][1:-1].lower()
    if valor_sin_comillas in cargos_validos:
        p[0] = ('cargo', p[3])  # mantiene comillas
    else:
        errores_lexico_sintactico.append(f"Error sintáctico, cargo inválido: {p[3]}")
        global parsing_had_error
        parsing_had_error = True
        p[0] = ('cargo', p[3]) 
    
def p_par_cargo_error(p):
    'cargo_par : CARGO DOS_PUNTOS error'
    _reportar_error_tipo(p.lineno(1), "cargo", "una cadena de texto (ej: \"Desarrollador\")")

def p_par_foto(p):
    'foto_par : FOTO DOS_PUNTOS VALOR_URL'
    p[0] = ('foto', p[3])

def p_par_foto_error(p):
    'foto_par : FOTO DOS_PUNTOS error'
    _reportar_error_tipo(p.lineno(1), "foto", "una URL válida")

def p_par_email(p):
    'email_par : EMAIL DOS_PUNTOS EMAIL'
    p[0] = ('email', p[3])

def p_par_email_error(p):
    'email_par : EMAIL DOS_PUNTOS error'
    _reportar_error_tipo(p.lineno(1), "email", "un email válido (ej: \"user@example.com\")")

def p_par_habilidades(p):
    'habilidades_par : HABILIDADES DOS_PUNTOS VALOR_STRING'
    p[0] = ('habilidades', p[3])
    
def p_par_habilidades_error(p):
    'habilidades_par : HABILIDADES DOS_PUNTOS error'
    _reportar_error_tipo(p.lineno(1), "habilidades", "una cadena de texto ")

def p_par_salario(p):
    '''salario_par : SALARIO DOS_PUNTOS VALOR_REAL
                   | SALARIO DOS_PUNTOS VALOR_ENTERO'''
    p[0] = ('salario', p[3])

def p_par_salario_error(p):
    'salario_par : SALARIO DOS_PUNTOS error'
    _reportar_error_tipo(p.lineno(1), "salario", "un número entero o real (ej: 1500.50)")

def p_par_activo(p):
    'activo_par : ACTIVO DOS_PUNTOS VALOR_BOOL'
    p[0] = ('activo', p[3])

def p_par_activo_error(p):
    'activo_par : ACTIVO DOS_PUNTOS error'
    _reportar_error_tipo(p.lineno(1), "activo", "un valor booleano (true o false)")

def p_proyectos(p):
    'proyectos : PROYECTOS DOS_PUNTOS APERTURA_LISTA lista_proyectos CLAUSURA_LISTA'
    p[0] = ('proyectos', p[4])

def p_lista_proyectos(p):
    '''lista_proyectos : proyecto_objeto COMA lista_proyectos
                       | proyecto_objeto'''
    if len(p) == 4:
        p[0] = [p[1]] + p[3]
    else:
        p[0] = [p[1]]


def p_proyecto_objeto(p):
    'proyecto_objeto : APERTURA_OBJETO miembros_proyecto CLAUSURA_OBJETO'
    p[0] = dict(p[2])

def p_miembros_proyecto(p):
    '''miembros_proyecto : nombre_proyecto_par COMA estado_proyecto_par COMA resumen_proyecto_par COMA tareas_proyecto_par COMA fecha_inicio_proyecto_par COMA fecha_fin_proyecto_par COMA video_proyecto_par COMA conclusion_proyecto_par'''
    p[0] = [item for item in p[1:] if item and item != ',']

def p_par_nombre_proyecto(p):
    'nombre_proyecto_par : NOMBRE DOS_PUNTOS VALOR_STRING'
    p[0] = ('nombre', p[3])

def p_par_nombre_proyecto_error(p):
    'nombre_proyecto_par : NOMBRE DOS_PUNTOS error'
    _reportar_error_tipo(p.lineno(1), "nombre", "una cadena de texto (ej: \"Proyecto X\")")

def p_par_estado_proyecto(p):
    'estado_proyecto_par : ESTADO DOS_PUNTOS VALOR_STRING'
    estados_validos = {
        "to do", "in progress", "canceled", "done", "on hold"
    }

    valor_sin_comillas = p[3][1:-1].lower()
    if valor_sin_comillas in estados_validos:
        p[0] = ('estado', p[3])
    else:
        errores_lexico_sintactico.append(f"Error sintáctico, estado inválido: {p[3]}")
        global parsing_had_error
        parsing_had_error = True
        p[0] = ('estado', p[3]) 


def p_par_estado_proyecto_error(p):
    'estado_proyecto_par : ESTADO DOS_PUNTOS error'
    _reportar_error_tipo(p.lineno(1), "estado", "una cadena de texto (ej: \"En progreso\", \"Finalizado\")")

def p_par_resumen_proyecto(p):
    'resumen_proyecto_par : RESUMEN DOS_PUNTOS VALOR_STRING'
    p[0] = ('resumen', p[3])

def p_par_resumen_proyecto_error(p):
    'resumen_proyecto_par : RESUMEN DOS_PUNTOS error'
    _reportar_error_tipo(p.lineno(1), "resumen", "una cadena de texto (ej: \"Descripción del proyecto\")")

def p_tareas_proyecto_par(p):
    'tareas_proyecto_par : TAREAS DOS_PUNTOS APERTURA_LISTA lista_tareas CLAUSURA_LISTA'
    p[0] = ('tareas', p[4])

def p_lista_tareas(p):
    '''lista_tareas : tarea_objeto COMA lista_tareas
                     | tarea_objeto'''
    if len(p) == 4:
        p[0] = [p[1]] + p[3]
    else:
        p[0] = [p[1]]


def p_tarea_objeto(p):
    'tarea_objeto : APERTURA_OBJETO miembros_tarea CLAUSURA_OBJETO'
    p[0] = dict(p[2])

def p_miembros_tarea(p):
    '''miembros_tarea : miembros_obligatorios_tarea
                      | miembros_obligatorios_tarea COMA miembros_opcionales_tarea'''
    if len(p) == 2:
        p[0] = p[1]
    else:
        p[0] = p[1] + p[3]

def p_miembros_obligatorios_tarea(p):
    '''miembros_obligatorios_tarea : nombre_tarea_par COMA estado_tarea_par COMA resumen_tarea_par
                                   | nombre_tarea_par COMA resumen_tarea_par COMA estado_tarea_par
                                   | estado_tarea_par COMA nombre_tarea_par COMA resumen_tarea_par
                                   | estado_tarea_par COMA resumen_tarea_par COMA nombre_tarea_par
                                   | resumen_tarea_par COMA nombre_tarea_par COMA estado_tarea_par
                                   | resumen_tarea_par COMA estado_tarea_par COMA nombre_tarea_par'''
    p[0] = [p[1], p[3], p[5]]

def p_miembros_opcionales_tarea(p):
    '''miembros_opcionales_tarea : fecha_inicio_tarea_par COMA fecha_fin_tarea_par
                                 | fecha_fin_tarea_par COMA fecha_inicio_tarea_par
                                 | fecha_inicio_tarea_par
                                 | fecha_fin_tarea_par'''
    if len(p) == 2:
        p[0] = [p[1]]
    else:
        p[0] = [p[1], p[3]]

def p_nombre_tarea_par(p):
    'nombre_tarea_par : NOMBRE DOS_PUNTOS VALOR_STRING'
    p[0] = ('nombre', p[3])

def p_nombre_tarea_par_error(p):
    'nombre_tarea_par : NOMBRE DOS_PUNTOS error'
    _reportar_error_tipo(p.lineno(1), "nombre", "una cadena de texto (ej: \"Tarea 1\")")

def p_estado_tarea_par(p):
    'estado_tarea_par : ESTADO DOS_PUNTOS VALOR_STRING'
    p[0] = ('estado', p[3])

def p_estado_tarea_par_error(p):
    'estado_tarea_par : ESTADO DOS_PUNTOS error'
    _reportar_error_tipo(p.lineno(1), "estado", "una cadena de texto (ej: \"Pendiente\", \"En progreso\", \"Finalizada\")")

def p_resumen_tarea_par(p):
    'resumen_tarea_par : RESUMEN DOS_PUNTOS VALOR_STRING'
    p[0] = ('resumen', p[3])

def p_resumen_tarea_par_error(p):
    'resumen_tarea_par : RESUMEN DOS_PUNTOS error'
    _reportar_error_tipo(p.lineno(1), "resumen", "una cadena de texto (ej: \"Descripción de la tarea\")")

def p_fecha_inicio_tarea_par(p):
    '''fecha_inicio_tarea_par : FECHA_INICIO DOS_PUNTOS VALOR_FECHA
                              | FECHA_INICIO DOS_PUNTOS VALOR_NULL '''
    p[0] = ('fecha_inicio', p[3])

def p_fecha_inicio_tarea_par_error(p):
    'fecha_inicio_tarea_par : FECHA_INICIO DOS_PUNTOS error'
    _reportar_error_tipo(p.lineno(1), "fecha_inicio", "una fecha válida (ej: \"AAAA-MM-DD\") o null")

def p_fecha_fin_tarea_par(p):
    '''fecha_fin_tarea_par : FECHA_FIN DOS_PUNTOS VALOR_FECHA
                           | FECHA_FIN DOS_PUNTOS VALOR_NULL '''
    p[0] = ('fecha_fin', p[3])

def p_fecha_fin_tarea_par_error(p):
    'fecha_fin_tarea_par : FECHA_FIN DOS_PUNTOS error'
    _reportar_error_tipo(p.lineno(1), "fecha_fin", "una fecha válida (ej: \"AAAA-MM-DD\") o null")

def p_fecha_inicio_proyecto_par(p):
    'fecha_inicio_proyecto_par : FECHA_INICIO DOS_PUNTOS VALOR_FECHA'
    p[0] = ('fecha_inicio', p[3])

def p_fecha_inicio_proyecto_par_error(p):
    'fecha_inicio_proyecto_par : FECHA_INICIO DOS_PUNTOS error'
    _reportar_error_tipo(p.lineno(1), "fecha_inicio", "una fecha válida (ej: \"AAAA-MM-DD\")")

def p_fecha_fin_proyecto_par(p):
    'fecha_fin_proyecto_par : FECHA_FIN DOS_PUNTOS VALOR_FECHA'
    p[0] = ('fecha_fin', p[3])

def p_fecha_fin_proyecto_par_error(p):
    'fecha_fin_proyecto_par : FECHA_FIN DOS_PUNTOS error'
    _reportar_error_tipo(p.lineno(1), "fecha_fin", "una fecha válida (ej: \"AAAA-MM-DD\")")

def p_video_proyecto_par(p):
    'video_proyecto_par : VIDEO DOS_PUNTOS VALOR_URL'
    p[0] = ('video', p[3])

def p_video_proyecto_par_error(p):
    'video_proyecto_par : VIDEO DOS_PUNTOS error'
    _reportar_error_tipo(p.lineno(1), "video", "una URL válida")

def p_conclusion_proyecto_par(p):
    'conclusion_proyecto_par : CONCLUSION DOS_PUNTOS VALOR_STRING'
    p[0] = ('conclusion', p[3])

def p_conclusion_proyecto_par_error(p):
    'conclusion_proyecto_par : CONCLUSION DOS_PUNTOS error'
    _reportar_error_tipo(p.lineno(1), "conclusion", "una cadena de texto (ej: \"Lecciones aprendidas\")")

def quitar_comillas_extremos(texto):
    if isinstance(texto, str) and texto.startswith('"') and texto.endswith('"'):
        return texto[1:-1]
    return texto

def _reportar_error_tipo(linea, campo, esperado):
    """Función auxiliar para reportar errores de tipo de dato."""
    global parsing_had_error, errores_lexico_sintactico
    err = f"[ERROR DE TIPO] Línea {linea}: El valor para '{campo}' es incorrecto. Se esperaba {esperado}."
    if err not in errores_lexico_sintactico:
        errores_lexico_sintactico.append(err)
        print("\n" + err)
        
        if app_instance:
            app_instance.consola_msg(f"-> {err}")
            
    parsing_had_error = True

def p_error(p):
    """
    Maneja los errores de sintaxis generales.
    Esta versión reporta el primer error y detiene el análisis.
    Los errores de tipo de dato son manejados por reglas más específicas.
    """
    global parsing_had_error, errores_lexico_sintactico

    if parsing_had_error:
        return # Si un error de tipo ya fue reportado, no hacer nada.

    parsing_had_error = True

    if not p:
        err = "[ERROR DE SINTAXIS] Final inesperado del archivo. Puede que falten llaves '}' o corchetes ']'."
        if err not in errores_lexico_sintactico:
            errores_lexico_sintactico.append(err)
        print("\n" + err)
        return

    # Error de sintaxis general
    err = f"[ERROR DE SINTAXIS] Línea {p.lineno}: Error cerca del token '{p.type}' (valor: '{p.value}')."
    sugerencia = "    -> Sugerencia: Verifica la estructura del JSON. Puede faltar una coma, dos puntos, o haber llaves/corchetes desbalanceados."
    error_msg = err + "\n" + sugerencia

    if error_msg not in errores_lexico_sintactico:
        errores_lexico_sintactico.append(error_msg)
        print("\n" + error_msg)


# ----- GENERACIÓN DE HTML  -----
def generar_html_desde_datos(datos_json, modo_imprimir=False):
    global html_output_parts
    html_output_parts = []
    
    if not isinstance(datos_json, dict):
        print("Los datos parseados no son un diccionario válido.")
        return

    equipos = datos_json.get('equipos', [])
    if not equipos:
        print("No se encontraron equipos.")
        return

    for equipo in equipos:
        html = '<div style="border:1px solid gray; padding:20px; margin-bottom:20px;">'
        nombre = quitar_comillas_extremos(equipo.get('nombre_equipo', 'Equipo sin nombre'))
        html += f'<h1>{nombre}</h1>'
        for clave, valor in equipo.items():
            if clave in ('nombre_equipo', 'integrantes', 'proyectos'):
                continue
            if clave == 'identidad_equipo':
                url = quitar_comillas_extremos(valor)
                html += f'<p><strong>Identidad equipo:</strong><br><img src="{url}" ></p>'
            elif clave == 'link' and valor and valor != 'null':
                html += f'<p><strong>Link:</strong> <a href="{valor}" target="_blank">{valor}</a></p>'
            elif not isinstance(valor, (list, dict)) and valor not in (None, 'null'):
                etiqueta = clave.replace('_', ' ').capitalize()
                if isinstance(valor, str) and valor.startswith('"') and valor.endswith('"'):
                    valor = valor[1:-1]
                valor = quitar_comillas_extremos(valor)
                html += f'<p><strong>{etiqueta}:</strong> {valor}</p>'
        html += procesar_integrantes(equipo.get('integrantes', []))
        html += procesar_proyectos_generales(equipo.get('proyectos', []))
        html += '</div>'
        html_output_parts.append(html)

    if modo_imprimir:
        html_output_parts.append("""
        <script>
            window.onload = function() { setTimeout(function(){ window.print(); }, 200); }
        </script>
        """)

def procesar_integrantes(lista_integrantes):
    if not lista_integrantes:
        return ''
    html = '<div><h3>Integrantes</h3><ul>'
    for integrante in lista_integrantes:
        nombre = quitar_comillas_extremos(integrante.get('nombre', 'Sin Nombre'))
        html += f'<li><h2>{nombre}</h2><ul>'
        for k, v in integrante.items():
            if k == 'nombre':
                continue
            etiqueta = k.capitalize()
            if isinstance(v, str):
                v = quitar_comillas_extremos(v)
            if k == 'email':
                html += f'<li><strong>{etiqueta}:</strong> <a href="mailto:{v}">{v}</a></li>'
            elif k == 'foto':
                html += f'<li><strong>{etiqueta}:</strong><br><img src="{v}" style="max-width:200px; max-height:200px;"></li>'
            else:
                html += f'<li><strong>{etiqueta}:</strong> {v}</li>'
        html += '</ul></li>'
    html += '</ul></div>'
    return html

def procesar_proyectos_generales(lista_proyectos):
    if not lista_proyectos:
        return ''
    html = '<div><h3>Proyectos</h3><ul>'
    for proyecto in lista_proyectos:
        nombre = quitar_comillas_extremos(proyecto.get('nombre', 'Sin Nombre'))
        html += f'<li><h3>{nombre}</h3><ul>'
        for k, v in proyecto.items():
            if k in ('nombre', 'tareas'):
                continue
            etiqueta = k.replace('_', ' ').capitalize()
            if isinstance(v, str):
                v = quitar_comillas_extremos(v)
            if k == 'video':
                html += f'<li><strong>{etiqueta}:</strong> <a href="{v}" target="_blank">Ver video</a></li>'
            else:
                html += f'<li><strong>{etiqueta}:</strong> {v}</li>'
        html += '</ul>'
        tareas = proyecto.get('tareas', [])
        if tareas:
            html += (
                '<table border="1" style="width:100%; border-collapse:collapse; margin-top:10px;">'
                '<thead><tr>'
                '<th>Nombre</th><th>Estado</th><th>Resumen</th><th>Fecha inicio</th><th>Fecha fin</th>'
                '</tr></thead><tbody>'
            )
            for t in tareas:
                nombre_tarea = quitar_comillas_extremos(t.get("nombre", "N/A"))
                estado_tarea = quitar_comillas_extremos(t.get("estado", "N/A"))
                resumen_tarea = quitar_comillas_extremos(t.get("resumen", "N/A"))
                fecha_inicio = quitar_comillas_extremos(t.get("fecha_inicio", "N/A"))
                fecha_fin = quitar_comillas_extremos(t.get("fecha_fin", "N/A"))
                html += '<tr>'
                html += f'<td>{nombre_tarea}</td>'
                html += f'<td>{estado_tarea}</td>'
                html += f'<td>{resumen_tarea}</td>'
                html += f'<td>{fecha_inicio}</td>'
                html += f'<td>{fecha_fin}</td>'
                html += '</tr>'
            html += '</tbody></table>'
        html += '</li>'
    html += '</ul></div>'
    return html

parser = yacc.yacc()

# ----------- INTERFAZ -----------
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
ICON_PATH = os.path.join(BASE_DIR, "iconos", "icono.ico")

class ParserWin98App(tk.Tk):
    def __init__(self):
        import os
        from PIL import Image, ImageTk
        import tkinter as tk
        from tkinter import ttk, scrolledtext, messagebox
        global app_instance
        app_instance = self  


        super().__init__()
        ICON_PATH = os.path.join(os.path.dirname(__file__), "iconos", "icono.ico")
        try:
            self.iconbitmap(ICON_PATH)
        except Exception as e:
            print(f"No se pudo cargar el ícono .ico: {e}")

        self.title("ParserPoint")
        self.geometry("1160x730")
        self.resizable(False, False)
        self.config(bg="#C0C0C0")

        # Barra de iconos
        barraiconos = tk.Frame(self, bg="#E0E0E0", height=36, bd=2, relief="groove")
        barraiconos.pack(fill=tk.X)

        def mostrar_ayuda():
            mensaje = (
                "1. Pegue o cargué un archivo en formato JSON en el panel izquierdo.\n"
                "2. Presioné 'Enviar', Crtl+Z o Ctrl+D para ejecutar.\n"
                "3. Ahora puede abrir/exportar/imprimir el HTML generado en función a su JSON."
            )
            messagebox.showinfo("Ayuda - ¿Cómo usar el ParserPoint?", mensaje)

        # Cargar imágenes
        ruta_iconos = os.path.join(os.path.dirname(__file__), "iconos")
        self.img_abrir = ImageTk.PhotoImage(Image.open(os.path.join(ruta_iconos, "abrir.png")).resize((24, 24), Image.LANCZOS))
        self.img_exportar = ImageTk.PhotoImage(Image.open(os.path.join(ruta_iconos, "exportar.png")).resize((24,24), Image.LANCZOS))
        self.img_imprimir = ImageTk.PhotoImage(Image.open(os.path.join(ruta_iconos, "imprimir.png")).resize((24,24), Image.LANCZOS))
        self.img_ayuda = ImageTk.PhotoImage(Image.open(os.path.join(ruta_iconos, "ayuda.png")).resize((24,24), Image.LANCZOS))
        self.img_reiniciar = ImageTk.PhotoImage(Image.open(os.path.join(ruta_iconos, "papelera.png")).resize((24,24), Image.LANCZOS))

        # Botones con imagen
        def crear_btn_con_label(frame_padre, imagen, comando, texto):
            contenedor = tk.Frame(frame_padre, bg="#E0E0E0")
            contenedor.pack(side=tk.LEFT, padx=8, pady=3)
            btn = tk.Button(contenedor, image=imagen, relief="flat", bg="#E0E0E0", command=comando, width=30, height=30)
            btn.pack()
            lbl = tk.Label(contenedor, text=texto, font=("MS Sans Serif", 9), bg="#E0E0E0")
            lbl.pack()
            return btn
        
        self.btn_abrir = crear_btn_con_label(barraiconos, self.img_abrir, self.abrir_json, "Abrir JSON")
        self.btn_exportar = crear_btn_con_label(barraiconos, self.img_exportar, self.exportar_html, "Exportar")
        #self.btn_imprimir = crear_btn_con_label(barraiconos, self.img_imprimir, self.imprimir_html, "Imprimir")
        self.btn_ayuda = crear_btn_con_label(barraiconos, self.img_ayuda, mostrar_ayuda, "Ayuda")
        self.btn_reiniciar = crear_btn_con_label(barraiconos, self.img_reiniciar, self.reiniciar_todo, "Reiniciar")

        tk.Label(barraiconos, bg="#E0E0E0").pack(side=tk.LEFT, expand=True)

        # Panel principal
        panel = tk.PanedWindow(self, orient=tk.HORIZONTAL, bg="#C0C0C0", sashrelief="raised", bd=2, sashwidth=14)
        panel.pack(fill=tk.BOTH, expand=True, padx=6, pady=(2,0))

        left = tk.Frame(panel, bg="#C0C0C0", bd=2, relief="ridge")
        panel.add(left, stretch="always")
        tk.Label(left, text="Entrada", font=("MS Sans Serif", 11, "bold"), bg="#C0C0C0").pack(anchor="w", padx=4, pady=(4,0))
        self.entrada = scrolledtext.ScrolledText(left, width=56, height=20, font=("Consolas", 11), bg="#F3F3F3", relief="sunken", bd=2)
        self.entrada.pack(padx=2, pady=2, fill=tk.BOTH, expand=True)
        
        self.entrada.bind("<Control-d>", self.ejecutar_parser)
        self.entrada.bind("<Control-D>", self.ejecutar_parser)

        
        btn_enviar = tk.Button(left, text="Enviar", font=("MS Sans Serif", 11), command=self.ejecutar_parser, state=tk.NORMAL, width=20, relief="raised", bg="#E6E6E6", bd=3)
        btn_enviar.pack(pady=(3,5))
        
        right = tk.Frame(panel, bg="#C0C0C0", bd=2, relief="ridge")
        panel.add(right, stretch="always")

        tk.Label(right, text="Salida", font=("MS Sans Serif", 11, "bold"), bg="#C0C0C0").pack(anchor="w", padx=4, pady=(4, 0))
        self.msg_mini_consola = tk.Label(right, text="", bg="#202020", fg="#ffffff", font=("Consolas", 10), anchor="w", justify="left", relief="sunken", bd=2, height=2)
        self.msg_mini_consola.pack(fill=tk.X, padx=2, pady=(2, 4))
        self.salida = scrolledtext.ScrolledText(right, width=56, height=18, font=("Consolas", 11), bg="#F3F3F3", relief="sunken", bd=2)
        self.salida.pack(padx=2, pady=(0, 4), fill=tk.BOTH, expand=True)
        self.salida.config(state=tk.DISABLED)
        self.btn_ver_html = tk.Button(right, text="Ver HTML generado", font=("MS Sans Serif", 11), command=self.ver_html, state=tk.DISABLED, width=20, relief="raised", bg="#E6E6E6", bd=3)
        self.btn_ver_html.pack(pady=(3, 5))
        
        consola_frame = tk.LabelFrame(self, text="Consola", font=("MS Sans Serif", 10, "bold"), bg="#C0C0C0", fg="#000080")
        consola_frame.pack(fill=tk.X, padx=6, pady=(2, 5))
        self.consola = scrolledtext.ScrolledText(consola_frame, height=6, font=("Consolas", 10), bg="#1D1D1D", fg="#F0F0F0", relief="sunken", bd=2)
        self.consola.pack(fill=tk.BOTH, expand=True)
        self.consola.insert(tk.END, "Listo para analizar un JSON\n")
        self.consola.config(state=tk.DISABLED)

        self.cadena_json = ""
        self.resultado_html = ""
        self.output_file_path = ""
        self.parsing_had_error = False

    def reiniciar_todo(self):
            self.entrada.config(state=tk.NORMAL)
            self.entrada.delete(1.0, tk.END)
            self.salida.config(state=tk.NORMAL)
            self.salida.delete(1.0, tk.END)
            self.salida.insert(tk.END, "Salida")
            self.salida.config(state=tk.DISABLED)
            self.consola.config(state=tk.NORMAL)
            self.consola.delete(1.0, tk.END)
            self.consola.insert(tk.END, "Listo para analizar un JSON\n")
            self.consola.config(state=tk.DISABLED)
            self.msg_mini_consola.config(text="")
            self.btn_ver_html.config(state=tk.DISABLED)
            self.cadena_json = ""
            self.resultado_html = ""
            self.output_file_path = ""
            
    def abrir_json(self):
        archivo = filedialog.askopenfilename(title="Abrir archivo JSON", filetypes=[("Archivos JSON", "*.json")])
        self.json_file_path = archivo
        if archivo:
            with open(archivo, "r") as f:
                contenido = f.read()
            self.entrada.delete(1.0, tk.END)
            self.entrada.insert(tk.END, contenido)
            self.consola_msg(f"Archivo cargado: {archivo}")
            self.output_file_path = os.path.splitext(archivo)[0] + ".html"
            self.btn_ver_html.config(state=tk.DISABLED)
        else:
            self.consola_msg("No se seleccionó archivo.")

    def consola_msg(self, txt):
        self.consola.config(state=tk.NORMAL)
        self.consola.insert(tk.END, txt + "\n")
        self.consola.see(tk.END)
        self.consola.config(state=tk.DISABLED)

    def ejecutar_parser(self, *_):
        self.msg_mini_consola.config(text="")
        self.salida.config(state=tk.NORMAL)
        self.salida.delete(1.0, tk.END)
        self.salida.insert(tk.END, "Salida")
        self.salida.config(state=tk.DISABLED)
        self.btn_ver_html.config(state=tk.DISABLED)

        # Reiniciar todas las listas de errores antes de cada ejecución
        global parsing_had_error, html_output_parts, errores_lexico_sintactico
        parsing_had_error = False
        html_output_parts = []
        errores_lexico_sintactico = []
        errores_lexicos.clear() 

        self.cadena_json = self.entrada.get(1.0, tk.END)
        if not self.cadena_json.strip():
            self.consola_msg("No hay JSON para analizar.")
            return
        self.consola_msg("\nEjecutando análisis...")
        self.update()

        try:
            ply_lexer.lineno = 1
            datos_parseados_lista = parser.parse(self.cadena_json, lexer=ply_lexer)
            
            todos_los_errores = errores_lexicos + errores_lexico_sintactico

            if todos_los_errores:
                errores_unicos = sorted(list(set(todos_los_errores)), key=todos_los_errores.index)
                self.msg_mini_consola.config(text=f"Se encontraron {len(errores_unicos)} errores en el JSON")
                
                # 1. Limpia el panel de salida y muestra un mensaje de referencia
                self.salida.config(state=tk.NORMAL)
                self.salida.delete(1.0, tk.END)
                self.salida.insert(tk.END, "El análisis falló.\n\nRevisa la consola de abajo para ver los detalles de los errores.")
                self.salida.config(state=tk.DISABLED)
                
                # 2. Envía cada error a la consola de abajo
                self.consola_msg("Errores léxicos/sintácticos detectados:")
                for err in errores_unicos:
                    self.consola_msg(f"-> {err}")
                
                self.btn_ver_html.config(state=tk.DISABLED)
            
            elif datos_parseados_lista and not parsing_had_error:
                self.consola_msg("[ÉXITO] El análisis se completó correctamente.")
                datos_parseados_dict = {}
                if isinstance(datos_parseados_lista, dict):
                    datos_parseados_dict = datos_parseados_lista
                elif isinstance(datos_parseados_lista, list):
                    for item in datos_parseados_lista:
                        if isinstance(item, tuple):
                            datos_parseados_dict[item[0]] = item[1]

                generar_html_desde_datos(datos_parseados_dict)
                final_html_body = "".join(html_output_parts)
                self.resultado_html = f'''
                <html>
                    <head><title>Reporte de Equipos</title>
                    <style>
                        body {{ background-color: lightgray; font-family: sans-serif; }}
                        table, th, td {{ border: 1px solid black; border-collapse: collapse; padding: 5px; text-align: left;}}
                    </style>
                    </head>
                    <body>{final_html_body}</body>
                </html>'''
                self.msg_mini_consola.config(text="¡HTML generado correctamente!")
                self.salida.config(state=tk.NORMAL)
                self.salida.delete(1.0, tk.END)
                self.salida.insert(tk.END, self.resultado_html[:2000] + ("\n...(truncado)" if len(self.resultado_html)>2000 else ""))
                self.salida.config(state=tk.DISABLED)
                self.output_file_path = "salida_json.html"
                with open(self.output_file_path, "w", encoding="utf-8") as file:
                    file.write(self.resultado_html)
                self.btn_ver_html.config(state=tk.NORMAL)
                self.consola_msg(f"HTML generado: {self.output_file_path}")
            
            else:
                self.salida.config(state=tk.NORMAL)
                self.salida.delete(1.0, tk.END)
                if not todos_los_errores:
                    self.salida.insert(tk.END, "No se pudo analizar correctamente el JSON.\nVerifique la estructura general.")
                    self.consola_msg("[ERROR] El análisis falló. Verifique la estructura del JSON.")
                else:
                    self.salida.insert(tk.END, "No se pudo analizar correctamente el JSON.\n")
                    self.consola_msg("[ERROR] El análisis falló o hubo errores graves en el JSON.")
                self.salida.config(state=tk.DISABLED)

        except Exception as e:
            self.salida.config(state=tk.NORMAL)
            self.salida.delete(1.0, tk.END)
            self.salida.insert(tk.END, f"[ERROR] Ocurrió un error inesperado:\n{e}")
            self.salida.config(state=tk.DISABLED)
            self.btn_ver_html.config(state=tk.DISABLED)
            self.consola_msg(f"[ERROR] {e}")

    def ver_html(self):
        if not self.resultado_html.strip():
            messagebox.showinfo("Sin HTML", "Primero ejecuta el parser.")
            return
        abs_path = os.path.abspath(self.output_file_path)
        url = 'file://' + abs_path
        webbrowser.open_new_tab(url)
        self.consola_msg(f"Abriendo en navegador: {self.output_file_path}")


    def exportar_html(self):
        import os
        import datetime
        from tkinter import filedialog, messagebox

        if not self.resultado_html.strip():
            messagebox.showerror("Error", "No hay HTML generado para exportar.")
            return

        try:
            if hasattr(self, "json_file_path") and self.json_file_path:
                base = os.path.basename(self.json_file_path)
                nombre_sugerido = os.path.splitext(base)[0] + ".html"
            else:
                nombre_sugerido = "resultado_" + datetime.datetime.now().strftime("%Y%m%d_%H%M%S") + ".html"

            ruta_guardado = filedialog.asksaveasfilename(
                defaultextension=".html",
                filetypes=[("Archivos HTML", "*.html"), ("Todos los archivos", "*.*")],
                initialfile=nombre_sugerido
            )

            if ruta_guardado:
                with open(ruta_guardado, "w") as f:
                    f.write(self.resultado_html)
                messagebox.showinfo("Éxito", f"Archivo guardado:\n{ruta_guardado}")
        except Exception as e:
            messagebox.showerror("Error al guardar", str(e))

    def imprimir_html(self):
        if not self.resultado_html.strip():
            messagebox.showinfo("Sin HTML", "Primero ejecuta el parser.")
            return
        
        ply_lexer.lineno = 1
        errores_lexicos.clear()
        errores_lexico_sintactico.clear()
        
        datos = self.obtener_dict_html()

        if not parsing_had_error and datos:
            generar_html_desde_datos(datos, modo_imprimir=True)
            html_print = f'''
            <html>
                <head><title>Imprimir Reporte de Equipos</title>
                <style>
                    body {{ background-color: lightgray; font-family: sans-serif; }}
                    table, th, td {{ border: 1px solid black; border-collapse: collapse; padding: 5px; text-align: left;}}
                </style>
                </head>
                <body>{''.join(html_output_parts)}</body>
            </html>'''
            archivo_tmp = "salida_json_imprimir.html"
            with open(archivo_tmp, "w") as file:
                file.write(html_print)
            abs_path = os.path.abspath(archivo_tmp)
            url = 'file://' + abs_path
            webbrowser.open_new_tab(url)
            self.consola_msg("Abriendo para imprimir (Ctrl+P en caso de no aparecer automático)")
        else:
            messagebox.showerror("Error", "No se puede imprimir porque el JSON contiene errores.")


    def obtener_dict_html(self):
        global parsing_had_error
        ply_lexer.lineno = 1
        
        errores_lexicos.clear()
        errores_lexico_sintactico.clear()
        parsing_had_error = False
        
        datos_parseados_lista = parser.parse(self.entrada.get(1.0, tk.END), lexer=ply_lexer)
        
        if parsing_had_error:
            return {}

        if isinstance(datos_parseados_lista, dict):
            return datos_parseados_lista
        elif isinstance(datos_parseados_lista, list):
            datos_parseados_dict = {}
            for item in datos_parseados_lista:
                if isinstance(item, tuple):
                    datos_parseados_dict[item[0]] = item[1]
            return datos_parseados_dict
        return {}

if __name__ == "__main__":
    app = ParserWin98App()
    app.mainloop()