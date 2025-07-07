import ply.lex as lex
import sys
# 1) Palabras clave
errores_lexicos = []
reserved = {
    '"nombre"': 'NOMBRE',
    '"edad"': 'EDAD',
    '"cargo"': 'CARGO',
    '"foto"': 'FOTO',
    '"email"': 'EMAIL',
    '"habilidades"': 'HABILIDADES',
    '"salario"': 'SALARIO',
    '"activo"': 'ACTIVO',
    '"equipos"': 'EQUIPOS',
    '"nombre_equipo"': 'NOMBRE_EQUIPO',
    '"identidad_equipo"': 'IDENTIDAD_EQUIPO',
    '"link"': 'LINK',
    '"asignatura"': 'ASIGNATURA',
    '"carrera"': 'CARRERA',
    '"universidad_regional"': 'UNIVERSIDAD_REGIONAL',
    '"direccion"': 'DIRECCION',
    '"alianza_equipo"': 'ALIANZA_EQUIPO',
    '"integrantes"': 'INTEGRANTES',
    '"proyectos"': 'PROYECTOS',
    '"estado"': 'ESTADO',
    '"resumen"': 'RESUMEN',
    '"tareas"': 'TAREAS',
    '"fecha_inicio"': 'FECHA_INICIO',
    '"fecha_fin"': 'FECHA_FIN',
    '"video"': 'VIDEO',
    '"conclusion"': 'CONCLUSION',
    '"calle"': 'CALLE',
    '"ciudad"': 'CIUDAD',
    '"pais"': 'PAIS',
    '"firma"': 'FIRMA',
    '"firma_digital"': 'FIRMA_DIGITAL',
    '"version"': 'VERSION',
}

# Lista de tokens (añadimos CLAVE en caso de querer distinguirlo)
tokens = (
    'APERTURA_OBJETO', 'CLAUSURA_OBJETO',
    'APERTURA_LISTA', 'CLAUSURA_LISTA',
    'DOS_PUNTOS', 'COMA',
    'VALOR_NULL', 'VALOR_BOOL', 'VALOR_STRING', 'VALOR_FECHA',
    'VALOR_URL', 'VALOR_ENTERO', 'VALOR_REAL',
) + tuple(reserved.values())

t_ignore = ' \t'
t_APERTURA_OBJETO = r'\{'
t_CLAUSURA_OBJETO = r'\}'
t_APERTURA_LISTA = r'\['
t_CLAUSURA_LISTA = r'\]'
t_DOS_PUNTOS = r'\:'
t_COMA = r'\,'

# Regla para contar los números de línea
def t_newline(t):
    r'\n+'
    t.lexer.lineno += len(t.value)

def t_VALOR_NULL(t):
    r'null'
    t.value = None  # Representamos null como None en Python
    t.type = 'VALOR_NULL'
    return t

def t_VALOR_BOOL(t):
    r'true|false'
    t.value = (t.value == 'true')  # Convertimos a booleano
    t.type = 'VALOR_BOOL'
    return t

def t_VALOR_URL(t):
    r'"(https?|ftp)://[^\s/$.?#].[^\s]*"'
    t.value = t.value[1:-1]   # le quita las comillas
    t.type  = 'VALOR_URL'
    return t


def t_VALOR_FECHA(t):
    r'"(?:19[0-9]{2}|20[0-9]{2})-(?:0[1-9]|1[0-2])-(?:0[1-9]|[12][0-9]|3[01])"|"(?:0[1-9]|1[0-2])/(?:0[1-9]|[12][0-9]|3[01])/(?:19[0-9]{2}|20[0-9]{2})"'
    # quitamos las comillas
    texto = t.value[1:-1]
    if '-' in texto:
        y, m, d = map(int, texto.split('-'))
    else:
        m, d, y = map(int, texto.split('/'))
    t.value = {'year': y, 'month': m, 'day': d}
    t.type  = 'VALOR_FECHA'
    return t

def t_EMAIL(t):
    r'"[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+(\.[a-zA-Z0-9-]+)*\.[a-zA-Z]{2,4}"'
    t.value = t.value.strip('"')
    return t


def t_VALOR_REAL(t):
    r'\d+\.\d+'
    if float(t.value) < 0:
        print(f"Error: El valor real no puede ser negativo: {t.value}")
        t.lexer.skip(len(t.value))  # Saltamos el token inválido
    else:
        t.value = float(t.value)  # Convertimos a float
        t.type = 'VALOR_REAL'
        return t

def t_VALOR_ENTERO(t):
    r'-?\d+'
    if int(t.value) < 0:
        print(f"Error: El valor entero no puede ser negativo: {t.value}")
        t.lexer.skip(len(t.value))  # Saltamos el token inválido
    else:
        t.value = int(t.value)  # Convertimos a int
        t.type = 'VALOR_ENTERO'
        return t
    
def t_STRING(t):
    r'\"([^\\\n]|(\\.))*?\"'
    # Comprueba si el string es una de las claves reservadas
    if t.value in reserved:
        t.type = reserved.get(t.value)
    else:
        # Si no es una clave, es un valor de tipo string
        t.type = 'VALOR_STRING'
    return t

    


def t_error(t):
    """
    Reporta un error léxico para caracteres no reconocidos.
    Imprime el carácter ilegal y el número de línea, lo agrega a la
    lista de errores para la UI, y luego salta el carácter.
    """
    error_message = f"[ERROR LÉXICO] Carácter ilegal '{t.value[0]}' en la línea {t.lexer.lineno}"
    print(error_message) # Mantiene el mensaje en consola
    errores_lexicos.append(error_message) # Agrega el error a la lista global
    t.lexer.skip(1) # Avanza al siguiente carácter

lexer = lex.lex()

def analizar_entrada():
    print("Pegá el JSON (Ctrl+D o Ctrl+Z para terminar):")
    try:
        # Lee múltiples líneas hasta EOF (Ctrl+D en Linux/Mac, Ctrl+Z en Windows)
        datos = sys.stdin.read()
        lexer.input(datos)
        while True:
            tok = lexer.token()
            if not tok:
                break
            print(f'Token: {tok.type}, Valor: {tok.value}')
    except EOFError:
        pass


if __name__ == "__main__":
    analizar_entrada()
        