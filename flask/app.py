from flask import Flask, render_template, request, redirect, url_for, flash, send_file
import requests
import json
import pandas as pd
from datetime import datetime, timedelta
import pytz
import sqlite3
import matplotlib
matplotlib.use('Agg')  # Usar el backend 'Agg' para evitar la apertura de ventanas gráficas
import matplotlib.pyplot as plt
import io
import base64
import csv
import numpy as np
from sklearn.linear_model import LinearRegression

# Crear la aplicación Flask
app = Flask(__name__)
app.secret_key = 'supersecretkey'  # Clave secreta necesaria para manejar mensajes flash

# --------------------------------------------------
# Diccionarios con datos adicionales de los activos
# --------------------------------------------------

# Diccionario con información adicional para cada activo (acciones y bonos)
informacion_adicional = {
    "ALUA": "ALUAR ALUMINIO ARGENTINO S.A.",
    "BBAR": "BANCO BBVA ARGENTINA S.A.",
    "BMA": "BANCO MACRO S.A.",
    "BYMA": "BOLSAS Y MERCADOS ARGENTINOS S.A.",
    "CEPU": "CENTRAL PUERTO S.A.",
    "COME": "SOCIEDAD COMERCIAL DEL PLATA S.A.",
    "CRES": "CRESUD S.A.C.I.F. Y A.",
    "EDN": "EMPRESA DISTRIBUIDORA Y COMERCIALIZADORA NORTE S.A. (EDENOR)",
    "GGAL": "GRUPO FINANCIERO GALICIA S.A.",
    "IRSA": "IRSA PROPIEDADES COMERCIALES S.A.",
    "LOMA": "LOMA NEGRA C.I.A.S.A.",
    "METR": "METROGAS S.A.",
    "MIRG": "MIRGOR S.A.C.I.F.I.A.",
    "PAMP": "PAMPA ENERGÍA S.A.",
    "SUPV": "BANCO SUPERVIELLE S.A.",
    "TECO2": "TELECOM ARGENTINA S.A.",
    "TGNO4": "TRANSPORTADORA DE GAS DEL NORTE S.A.",
    "TGSU2": "TRANSPORTADORA DE GAS DEL SUR S.A.",
    "TRAN": "TRANSENER S.A.",
    "TXAR": "TERNIUM ARGENTINA S.A.",
    "VALO": "GRUPO FINANCIERO VALORES S.A.",
    "YPFD": "YPF S.A.",
    "AL29": "BONOS DE LA REPÚBLICA ARGENTINA EN DÓLARES ESTADOUNIDENSES STEP UP 2029",
    "AL29D": "BONO REP. ARGENTINA USD STEP UP 2029",
    "AL30": "BONOS DE LA REPÚBLICA ARGENTINA EN DÓLARES ESTADOUNIDENSES STEP UP 2030",
    "AL30D": "BONO REP. ARGENTINA USD STEP UP 2030",
    "AL35": "BONOS DE LA REPÚBLICA ARGENTINA EN DÓLARES ESTADOUNIDENSES STEP UP 2035",
    "AL35D": "BONO REP. ARGENTINA USD STEP UP 2035",
    "AL41": "BONOS DE LA REPÚBLICA ARGENTINA EN DÓLARES ESTADOUNIDENSES STEP UP 2041",
    "AL41D": "BONO REP. ARGENTINA USD STEP UP 2041",
    "S11N4": "LETRA DEL TESORO NACIONAL CAPITALIZABLE EN PESOS CON VENCIMIENTO 11 DE NOVIEMBRE DE 2024",
    "S14O4": "LETRA DEL TESORO NACIONAL CAPITALIZABLE EN PESOS CON VENCIMIENTO 14 DE OCTUBRE DE 2024",
    "S16Y5": "LETRA DEL TESORO NACIONAL CAPITALIZABLE EN PESOS CON VENCIMIENTO 16 DE MAYO DE 2025",
    "S18J5": "LETRA DEL TESORO NACIONAL CAPITALIZABLE EN PESOS CON VENCIMIENTO 18 DE JUNIO DE 2025",
    "S28F5": "LETRA DEL TESORO NACIONAL CAPITALIZABLE EN PESOS CON VENCIMIENTO 28 DE FEBRERO DE 2025",
    "S29G5": "LETRA DEL TESORO NACIONAL CAPITALIZABLE EN PESOS CON VENCIMIENTO 29 DE JULIO DE 2025",
    "S30S5": "LETRA DEL TESORO NACIONAL CAPITALIZABLE EN PESOS CON VENCIMIENTO 30 DE SEPTIEMBRE DE 2025",
    "S31L5": "LETRA DEL TESORO NACIONAL CAPITALIZABLE EN PESOS CON VENCIMIENTO 31 DE DICIEMBRE DE 2025",
    "S31M5": "LETRA DEL TESORO NACIONAL CAPITALIZABLE EN PESOS CON VENCIMIENTO 31 DE MARZO DE 2025",
    "S31O4": "LETRA DEL TESORO NACIONAL CAPITALIZABLE EN PESOS CON VENCIMIENTO 31 DE OCTUBRE DE 2024"
}

# Diccionario que especifica la moneda de cada activo
monedas = {
    "ALUA": "Pesos Argentinos", "BBAR": "Pesos Argentinos", "BMA": "Pesos Argentinos", "BYMA": "Pesos Argentinos", 
    "CEPU": "Pesos Argentinos", "COME": "Pesos Argentinos", "CRES": "Pesos Argentinos", "EDN": "Pesos Argentinos", 
    "GGAL": "Pesos Argentinos", "IRSA": "Pesos Argentinos", "LOMA": "Pesos Argentinos", "METR": "Pesos Argentinos", 
    "MIRG": "Pesos Argentinos", "PAMP": "Pesos Argentinos", "SUPV": "Pesos Argentinos", "TECO2": "Pesos Argentinos", 
    "TGNO4": "Pesos Argentinos", "TGSU2": "Pesos Argentinos", "TRAN": "Pesos Argentinos", "TXAR": "Pesos Argentinos", 
    "VALO": "Pesos Argentinos", "YPFD": "Pesos Argentinos", "AL29": "Pesos Argentinos", "AL29D": "Dólares", 
    "AL30": "Pesos Argentinos", "AL30D": "Dólares", "AL35": "Pesos Argentinos", "AL35D": "Dólares", 
    "AL41": "Pesos Argentinos", "AL41D": "Dólares", "S11N4": "Pesos Argentinos", "S14O4": "Pesos Argentinos", 
    "S16Y5": "Pesos Argentinos", "S18J5": "Pesos Argentinos", "S28F5": "Pesos Argentinos", "S29G5": "Pesos Argentinos", 
    "S30S5": "Pesos Argentinos", "S31L5": "Pesos Argentinos", "S31M5": "Pesos Argentinos", "S31O4": "Pesos Argentinos"
}

# Diccionario con la fecha de vencimiento de cada activo
vencimientos = {
    "ALUA": "Inmediato", "BBAR": "Inmediato", "BMA": "Inmediato", "BYMA": "Inmediato", "CEPU": "Inmediato", 
    "COME": "Inmediato", "CRES": "Inmediato", "EDN": "Inmediato", "GGAL": "Inmediato", "IRSA": "Inmediato", 
    "LOMA": "Inmediato", "METR": "Inmediato", "MIRG": "Inmediato", "PAMP": "Inmediato", "SUPV": "Inmediato", 
    "TECO2": "Inmediato", "TGNO4": "Inmediato", "TGSU2": "Inmediato", "TRAN": "Inmediato", "TXAR": "Inmediato", 
    "VALO": "Inmediato", "YPFD": "Inmediato", "AL29": "Inmediato", "AL29D": "Inmediato", "AL30": "Inmediato", 
    "AL30D": "Inmediato", "AL35": "Inmediato", "AL35D": "Inmediato", "AL41": "Inmediato", "AL41D": "Inmediato", 
    "S11N4": "Inmediato", "S14O4": "Inmediato", "S16Y5": "Inmediato", "S18J5": "Inmediato", "S28F5": "Inmediato", 
    "S29G5": "Inmediato", "S30S5": "Inmediato", "S31L5": "Inmediato", "S31M5": "Inmediato", "S31O4": "Inmediato"
}

# --------------------------------------------------
# Funciones de Base de Datos y Obtención de Datos
# --------------------------------------------------

# Función para inicializar la base de datos de acciones
def init_db():
    # Conexión a la base de datos SQLite
    conn = sqlite3.connect('acciones.db')
    c = conn.cursor()

    # Crear la tabla de acciones si no existe
    c.execute('''
        CREATE TABLE IF NOT EXISTS acciones (
            ticker TEXT,
            timestamp TEXT,
            open REAL,
            close REAL,
            high REAL,
            low REAL,
            volume REAL
        )
    ''')
    conn.commit()  # Guardar cambios en la base de datos
    conn.close()   # Cerrar conexión

# Función para guardar los datos de las acciones en la base de datos
def save_to_db(ticker, data):
    # Conectar a la base de datos
    conn = sqlite3.connect('acciones.db')
    c = conn.cursor()

    # Insertar los datos de cada fila en la base de datos
    for row in data:
        timestamp_str = row['timestamp'].isoformat()  # Convertir la fecha a formato ISO
        c.execute('''
            INSERT INTO acciones (ticker, timestamp, open, close, high, low, volume)
            VALUES (?, ?, ?, ?, ?, ?, ?)
        ''', (ticker, timestamp_str, row['open'], row['close'], row['high'], row['low'], row['volume']))
    conn.commit()  # Guardar cambios
    conn.close()   # Cerrar conexión

# Función para obtener los datos de las acciones y guardarlos en la base de datos
def obtener_y_guardar_datos():
    init_db()  # Inicializar la base de datos si no existe
    s = requests.session()  # Crear una sesión de requests

    # Lista de tickers para los cuales se obtendrán los datos
    tickers = [
        "ALUA", "BBAR", "BMA", "BYMA", "CEPU", "COME", "CRES",
        "EDN", "GGAL", "IRSA", "LOMA", "METR", "MIRG", "PAMP",
        "SUPV", "TECO2", "TGNO4", "TGSU2", "TRAN", "TXAR",
        "VALO", "YPFD",
        "AL29", "AL29D", "AL30", "AL30D", "AL35", "AL35D",
        "AL41", "AL41D",
        "S11N4", "S14O4", "S16Y5", "S18J5", "S28F5", "S29G5",
        "S30S5", "S31L5", "S31M5", "S31O4"
    ]

    # Fechas de inicio y final para obtener los datos
    inicio = int(datetime(2020, 1, 1, 0, 0).timestamp())  # Convertir fecha a timestamp
    hoy = datetime.now(pytz.timezone('America/Argentina/Buenos_Aires')).timestamp()  # Obtener timestamp actual
    
    # Iterar sobre cada ticker para obtener sus datos
    for ticker in tickers:
        params = (
            ('symbol', f'{ticker} CDO'),  # Símbolo del activo
            ('resolution', 'D'),  # Resolución diaria
            ('from', str(inicio)),  # Desde la fecha de inicio
            ('to', str(int(hoy)))  # Hasta la fecha actual
        )

        # Hacer la solicitud a la API para obtener datos históricos
        response = requests.get(
            'https://open.bymadata.com.ar/vanoms-be-core/rest/api/bymadata/free/chart/historical-series/history',
            params=params, verify=False
        )

        # Si la respuesta es exitosa (status 200), procesar los datos
        if response.status_code == 200:
            data = json.loads(response.text)  # Convertir respuesta a formato JSON
            df = pd.DataFrame(data)  # Crear DataFrame a partir de los datos
            if not df.empty:
                df['t'] = pd.to_datetime(df['t'], unit='s').dt.normalize()  # Normalizar las fechas
                # Renombrar columnas para mayor claridad
                df.rename({'s': 'status', 't': 'timestamp', 'c': 'close', 'o': 'open', 'h': 'high', 'l': 'low', 'v': 'volume'}, axis=1, inplace=True)
                save_to_db(ticker, df.to_dict(orient='records'))  # Guardar datos en la base de datos
        else:
            print(f"No se pudo obtener datos para {ticker}")  # Imprimir error si falla
            
# --------------------------------------------------
# Página Análisis de Activos
# --------------------------------------------------            

# Ruta para la página principal (index)
@app.route('/')
def index():
    return render_template('index.html')  # Renderizar el template del index

# Ruta para la función de obtener y guardar los datos
@app.route('/obtener_guardar', methods=['POST'])
def obtener_guardar():
    try:
        obtener_y_guardar_datos()  # Llamar a la función que obtiene y guarda los datos
        flash('Los datos se han guardado correctamente en la base de datos.', 'success')  # Mensaje de éxito
    except Exception as e:
        flash(f'Error al guardar los datos: {str(e)}', 'danger')  # Mensaje de error
    return redirect(url_for('index'))  # Redirige al índice después de completar la acción

# Función para generar el contexto necesario para mostrar la información del activo seleccionado
def generar_contexto_activo(ticker):
    conn = sqlite3.connect('acciones.db')
    c = conn.cursor()

    # Obtener los datos más recientes del activo seleccionado
    c.execute('''
        SELECT timestamp, close, open, high, low, volume
        FROM acciones 
        WHERE ticker = ? 
        ORDER BY timestamp DESC 
        LIMIT 2
    ''', (ticker,))
    
    rows = c.fetchall()

    if len(rows) < 2:
        flash('No hay suficiente información para este activo.', 'danger')
        conn.close()
        return None

    # Obtener los precios actuales y el cierre anterior
    fecha, cotizacion_actual, apertura, maximo, minimo, volumen = rows[0]
    _, cierre_anterior = rows[1][:2]

    # Calcular la variación porcentual
    cotizacion_actual = float(cotizacion_actual)
    cierre_anterior = float(cierre_anterior)

    if cierre_anterior != 0:
        variacion_porcentual = round(((cotizacion_actual - cierre_anterior) / cierre_anterior) * 100, 2)
    else:
        variacion_porcentual = 0.0  # Evitar división por cero

    fecha = fecha.split("T")[0]  # Formatear la fecha para no mostrar la hora

    # Obtener información adicional del diccionario
    info_adicional = informacion_adicional.get(ticker, "Información no disponible")
    vencimiento_activo = vencimientos.get(ticker, "Desconocido")
    moneda = monedas.get(ticker, "Moneda no disponible")

    # Obtener todos los datos históricos del activo para el gráfico
    c.execute('''
        SELECT timestamp, close, volume
        FROM acciones 
        WHERE ticker = ?
        ORDER BY timestamp ASC
    ''', (ticker,))

    rows_graficos = c.fetchall()

    # Calcular las variaciones entre fechas (diaria, semanal, mensual, etc.)
    hoy = datetime.now()
    fechas_deltas = {
        'Diaria': timedelta(days=1),
        'Semanal': timedelta(weeks=1),
        'Mensual': timedelta(days=30),
        'Trimestral': timedelta(days=90),
        'Semestral': timedelta(days=180),
        'Anual': timedelta(days=365)
    }
    variaciones_fechas = {}

    for periodo, delta in fechas_deltas.items():
        fecha_anterior = (hoy - delta).strftime("%Y-%m-%d")
        c.execute('''
            SELECT close 
            FROM acciones 
            WHERE ticker = ? AND timestamp <= ?
            ORDER BY timestamp DESC 
            LIMIT 1
        ''', (ticker, fecha_anterior))

        row_anterior = c.fetchone()
        if row_anterior:
            cierre_anterior_periodo = float(row_anterior[0])
            variacion_periodo = round(((cotizacion_actual - cierre_anterior_periodo) / cierre_anterior_periodo) * 100, 2)
            variaciones_fechas[periodo] = f"{variacion_periodo}%"
        else:
            variaciones_fechas[periodo] = "No disponible"

    conn.close()

    # Convertir los resultados a un DataFrame para generar el gráfico
    df = pd.DataFrame(rows_graficos, columns=['timestamp', 'close', 'volume'])
    df['timestamp'] = pd.to_datetime(df['timestamp'])

    # Generar el gráfico de precio y volumen
    fig, ax1 = plt.subplots(figsize=(10, 5))

    # Graficar el precio
    ax1.plot(df['timestamp'], df['close'], color='b', label='Precio')
    ax1.set_xlabel('Fecha')
    ax1.set_ylabel('Precio', color='b')
    ax1.tick_params(axis='y', labelcolor='b')

    # Graficar el volumen
    ax2 = ax1.twinx()
    ax2.bar(df['timestamp'], df['volume'], alpha=0.3, color='g', label='Volumen')
    ax2.set_ylabel('Volumen', color='g')
    ax2.tick_params(axis='y', labelcolor='g')

    plt.title(f'Precio y Volumen histórico')

    # Convertir el gráfico a una imagen en base64 para mostrar en la página web
    img = io.BytesIO()
    plt.savefig(img, format='png')
    img.seek(0)
    graph_url = base64.b64encode(img.getvalue()).decode('utf8')
    plt.close()

    # Formatear valores según la moneda
    if moneda == "Pesos Argentinos":
        cotizacion_actual = f"${int(cotizacion_actual):,}".replace(",", ".")
        apertura = f"${int(apertura):,}".replace(",", ".")
        cierre_anterior = f"${int(cierre_anterior):,}".replace(",", ".")
        maximo = f"${int(maximo):,}".replace(",", ".")
        minimo = f"${int(minimo):,}".replace(",", ".")
        monto_negociado = f"${int(cotizacion_actual.replace('$', '').replace('.', '')) * int(volumen):,}".replace(",", ".")
    else:
        cotizacion_actual = f"U$S{cotizacion_actual:.2f}"
        apertura = f"U$S{apertura:.2f}"
        cierre_anterior = f"U$S{cierre_anterior:.2f}"
        maximo = f"U$S{maximo:.2f}"
        minimo = f"U$S{minimo:.2f}"
        monto_negociado = f"U$S{int(cotizacion_actual.replace('U$S', '').replace('.', '')) * int(volumen)}"

    variacion_porcentual = f"{variacion_porcentual}%"
    volumen = f"{int(volumen):,}".replace(",", ".")

    return {
        'ticker': ticker,
        'fecha': fecha,
        'precio': cotizacion_actual,
        'apertura': apertura,
        'cierre_anterior': cierre_anterior,
        'maximo': maximo,
        'minimo': minimo,
        'volumen': volumen,
        'monto_negociado': monto_negociado,
        'operaciones': "989",  # Número ficticio de operaciones para demo
        'variacion': variacion_porcentual,
        'info_adicional': info_adicional,
        'vencimiento': vencimiento_activo,
        'moneda': moneda,
        'variaciones_fechas': variaciones_fechas,
        'graph_url': graph_url
    }

# Ruta para manejar la selección del activo
@app.route('/analizar_activo', methods=['POST'])
def seleccionar_activo():
    ticker = request.form.get('ticker')  # Obtener el ticker seleccionado por el usuario
    contexto = generar_contexto_activo(ticker)  # Generar el contexto con los datos del activo

    if contexto is None:
        return redirect(url_for('index'))

    return render_template('index.html', **contexto)

# Ruta para buscar cotizaciones entre fechas seleccionadas
@app.route('/buscar_cotizaciones', methods=['POST'])
def buscar_cotizaciones():
    ticker = request.form.get('ticker')
    fecha_desde = request.form.get('fecha_desde')
    fecha_hasta = request.form.get('fecha_hasta')

    # Convertimos la fecha_hasta a formato datetime para incluir todo el día
    fecha_hasta_dt = datetime.strptime(fecha_hasta, '%Y-%m-%d') + timedelta(days=1)
    fecha_hasta_str = fecha_hasta_dt.strftime('%Y-%m-%d')

    # Conectar a la base de datos
    conn = sqlite3.connect('acciones.db')
    c = conn.cursor()

    # Consulta para obtener cotizaciones del rango de fechas seleccionado, usando DISTINCT para evitar duplicados
    c.execute('''
        SELECT DISTINCT timestamp, open, close, high, low, volume
        FROM acciones
        WHERE ticker = ? AND timestamp BETWEEN ? AND ?
        ORDER BY timestamp ASC
    ''', (ticker, fecha_desde, fecha_hasta_str))
    
    rows = c.fetchall()
    conn.close()

    # Si no hay filas, mostrar mensaje de error
    if not rows:
        flash('No hay datos disponibles para las fechas seleccionadas.', 'danger')
        contexto = generar_contexto_activo(ticker)
        return render_template('index.html', **contexto)

    # Crear DataFrame con los resultados de la consulta
    df = pd.DataFrame(rows, columns=['Fecha', 'Apertura', 'Cierre', 'Máximo', 'Mínimo', 'Volumen'])

    # Guardar el DataFrame en un archivo CSV
    df.to_csv('cotizaciones.csv', index=False)
    
    # Actualizar el contexto del activo seleccionado
    contexto = generar_contexto_activo(ticker)
    contexto.update({'df': df.to_html(index=False)})

    return render_template('index.html', **contexto)

# Ruta para exportar las cotizaciones a CSV
@app.route('/exportar_csv', methods=['GET'])
def exportar_csv():
    try:
        return send_file('cotizaciones.csv', as_attachment=True, download_name='cotizaciones.csv')
    except Exception as e:
        flash(f'Error al exportar el archivo CSV: {str(e)}', 'danger')
        return redirect(url_for('index'))

# --------------------------------------------------
# Página Calculadora de Activos
# --------------------------------------------------  

# Diccionario con fechas de vencimiento de cada lecap
fechas_vencimiento = {
    "S31O4": "2024-10-31",
    "S11N4": "2024-11-11",
    "S29N4": "2024-11-29",
    "S13D4": "2024-12-13",
    "S17E5": "2025-01-17",
    "S31E5": "2025-01-31",
    "S14F5": "2025-02-14",
    "S28F5": "2025-02-28",
    "S14M5": "2025-03-14",
    "S31M5": "2025-03-31",
    "S16A5": "2025-04-16",
    "S28A5": "2025-04-28",
    "S16Y5": "2025-05-16",
    "S30Y5": "2025-05-30",
    "S18J5": "2025-06-18",
    "S30J5": "2025-06-30",
    "S31L5": "2025-07-31",
    "S29G5": "2025-08-29",
    "S12S5": "2025-09-12",
    "S30S5": "2025-09-30"
}

# Diccionario con los pagos finales de cada lecap
pagos_finales = {
    "S31O4": 103.75,
    "S11N4": 109.10,
    "S29N4": 134.98,
    "S13D4": 126.83,
    "S17E5": 131.19,
    "S31E5": 172.65,
    "S14F5": 121.24,
    "S28F5": 158.29,
    "S14M5": 125.96,
    "S31M5": 155.58,
    "S16A5": 131.21,
    "S28A5": 130.81,
    "S16Y5": 136.86,
    "S30Y5": 136.33,
    "S18J5": 147.70,
    "S30J5": 146.61,
    "S31L5": 147.74,
    "S29G5": 157.70,
    "S12S5": 158.98,
    "S30S5": 159.73
}

# Ruta para la página de calculadora de carry trade
@app.route('/calculadora', methods=['GET', 'POST'])
def calculadora():
    if request.method == 'POST':
        # Obtener el activo seleccionado por el usuario
        activo = request.form.get('activo')
        
        # Obtener fecha de vencimiento del diccionario
        fecha_vencimiento = fechas_vencimiento.get(activo)
        
        # Obtener fecha de hoy (Liqui Secu)
        fecha_hoy = datetime.now().strftime("%Y-%m-%d")
        
        # Calcular Días y Meses
        fecha_venc = datetime.strptime(fecha_vencimiento, "%Y-%m-%d")
        fecha_actual = datetime.now()
        dias = (fecha_venc - fecha_actual).days
        
        # Calcular meses como (días / 30) para aproximar a meses
        meses = dias / 30

        # Obtener Px desde la base de datos (precio actual)
        conn = sqlite3.connect('acciones.db')
        c = conn.cursor()
        c.execute('SELECT close FROM acciones WHERE ticker = ? ORDER BY timestamp DESC LIMIT 1', (activo,))
        px = c.fetchone()[0]
        conn.close()

        # Obtener el pago final desde el diccionario
        pago_final = pagos_finales.get(activo)
        
        # Calcular TNA, TEM, TEA
        if px > 0 and dias > 0:
            tna = ((pago_final / px) - 1) * (365 / dias)  # Corrección en la fórmula TNA
            tem = (pago_final / px) ** (1 / meses) - 1  # Corrección en TEM
            tea = (pago_final / px) ** (365 / dias) - 1  # Corrección en TEA
        else:
            tna, tem, tea = 0, 0, 0  # Para evitar divisiones por 0 si hay errores de datos

        # Formatear los resultados con dos decimales
        tna = f"{tna:.2%}"
        tem = f"{tem:.2%}"
        tea = f"{tea:.2%}"

        # Generar gráfico de TEM vs Días para todas las Lecaps
        graph_url = generar_grafico_todas_lecaps()

        # Generar el segundo gráfico y tabla de ganancia en dólares
        grafico_ganancia_url, resultado_tabla = calcular_ganancia_y_tna(px, pago_final, dias)

        # Devolver los datos a la plantilla para mostrarlos
        return render_template('calculadora.html', activo=activo, 
                               fecha_vencimiento=fecha_vencimiento, fecha_hoy=fecha_hoy, 
                               dias=dias, meses=meses, px=px, pago_final=pago_final,
                               tna=tna, tem=tem, tea=tea, graph_url=graph_url,
                               resultado=resultado_tabla, grafico_ganancia_url=grafico_ganancia_url)
    
    # Si es GET, simplemente renderizar la página inicial del formulario
    return render_template('calculadora.html')

# Función para generar el gráfico de TEM vs Días para todas las Lecaps
def generar_grafico_todas_lecaps():
    # Datos de ejemplo de días a vencimiento y TEM para todas las lecaps
    dias_vencimiento = [18, 28, 46, 60, 95, 109, 123, 137, 151, 168, 184, 196, 214, 228, 247, 259, 290, 319, 333, 351]
    tem = [3.45, 3.67, 3.60, 3.67, 3.65, 3.77, 3.76, 3.71, 3.67, 3.73, 3.76, 3.78, 3.79, 3.79, 3.80, 3.84, 3.84, 3.78, 3.69, 3.68]

    # Ajustar una curva polinómica de grado 2 (parábola)
    coeficientes = np.polyfit(dias_vencimiento, tem, 2)
    polinomio = np.poly1d(coeficientes)

    # Generar puntos de la curva suave
    x_suave = np.linspace(min(dias_vencimiento), max(dias_vencimiento), 500)
    y_suave = polinomio(x_suave)

    # Crear la figura y el gráfico
    plt.figure(figsize=(8, 6))
    
    # Graficar los puntos de TEM vs Días a Vencimiento
    plt.scatter(dias_vencimiento, tem, color='b')

    # Añadir etiquetas a cada punto
    lecaps = ["S31O4", "S11N4", "S29N4", "S13D4", "S17E5", "S31E5", "S14F5", "S28F5", "S14M5", 
              "S31M5", "S16A5", "S28A5", "S16Y5", "S30Y5", "S18J5", "S30J5", "S31L5", "S29G5", 
              "S12S5", "S30S5"]
    
    for i, label in enumerate(lecaps):
        plt.text(dias_vencimiento[i], tem[i], label, fontsize=9, ha='right')

    # Graficar la curva ajustada
    plt.plot(x_suave, y_suave, color='lightblue', linewidth=2)

    # Configurar etiquetas y título
    plt.title('Tasa Efectiva Mensual (TEM) vs Días a Vencimiento')
    plt.xlabel('DÍAS A VENCIMIENTO')
    plt.ylabel('TEM')
    plt.grid(True)

    # Guardar la gráfica en un objeto BytesIO para enviarla como imagen en base64
    img = io.BytesIO()
    plt.savefig(img, format='png')
    img.seek(0)
    graph_url = base64.b64encode(img.getvalue()).decode('utf8')
    plt.close()

    return graph_url

# Función para calcular la ganancia y TNA en dólares
def calcular_ganancia_y_tna(px, pago_final, dias_hasta_pago):
    # Lista de precios del dólar en la fecha de pago de 1100 a 1520
    precios_dolar_pago = np.arange(1100, 1521, 20)

    # Cálculo de ganancia en dólares y TNA en dólares
    ganancias_usd = []
    tnas_usd = []

    for dolar_pago in precios_dolar_pago:
        # Calcular la ganancia en dólares basada en el precio de vencimiento y tasas
        ganancia_usd = ((pago_final / px) * (1100 / dolar_pago)) - 1
        ganancias_usd.append(ganancia_usd * 100)  # Convertimos a porcentaje

        # Calcular la TNA en dólares ajustada por la ganancia anual y días hasta el vencimiento
        tna_usd = (ganancia_usd / dias_hasta_pago) * 365 * 100  # Ajustamos la ganancia anual
        tnas_usd.append(tna_usd)

    # Crear el DataFrame para mostrar los resultados
    df = pd.DataFrame({
        'Precio Dólar al vencimiento': precios_dolar_pago,
        'Ganancia en dólares': ganancias_usd,
        'TNA en dólares': tnas_usd
    })

    # Formatear los resultados a dos decimales y añadir el símbolo de porcentaje
    df['Ganancia en dólares'] = df['Ganancia en dólares'].map(lambda x: f"{x:.2f}%")
    df['TNA en dólares'] = df['TNA en dólares'].map(lambda x: f"{x:.2f}%")

    # Graficar los resultados
    fig, ax = plt.subplots(figsize=(8, 6))
    ax.plot(precios_dolar_pago, ganancias_usd, label='Ganancia en dólares (%)', color='blue')
    ax.plot(precios_dolar_pago, tnas_usd, label='TNA en dólares (%)', color='red')
    ax.set_xlabel('Precio Dólar al vencimiento')
    ax.set_ylabel('Porcentaje (%)')
    ax.set_title('Ganancia y TNA en Dólares')
    ax.legend()

    # Convertir el gráfico en base64 para enviarlo al HTML
    img = io.BytesIO()
    plt.savefig(img, format='png', bbox_inches='tight')
    img.seek(0)
    grafico_ganancia_url = base64.b64encode(img.getvalue()).decode('utf8')
    plt.close()

    return grafico_ganancia_url, df.to_html(index=False)

# --------------------------------------------------
# Página para analizar el rendimiento de un activo
# --------------------------------------------------

# Función para calcular el rendimiento
def calcular_rendimiento(datos):
    datos['rendimiento'] = datos['close'].pct_change() * 100  # Cambio porcentual diario
    datos['clasificacion'] = datos['rendimiento'].apply(lambda x: 'Bueno' if x > 1 else 'Malo')
    return datos

@app.route('/analisis_activo', methods=['POST'])
def analizar_activo():
    ticker = request.form.get('ticker')
    
    # Cargar los datos del activo desde la base de datos
    conn = sqlite3.connect('acciones.db')
    query = f"SELECT timestamp, close, volume FROM acciones WHERE ticker = '{ticker}'"
    datos = pd.read_sql_query(query, conn)
    conn.close()
    
    # Calcular el rendimiento y la clasificación
    datos_clasificados = calcular_rendimiento(datos)
    
    # Retornar los datos clasificados al frontend
    return render_template('analisis_activo.html', datos=datos_clasificados.to_html(index=False))

# --------------------------------------------------
# Página para predecir el rendimiento de un activo
# --------------------------------------------------

# Función para entrenar un modelo de regresión y predecir rendimiento
def predecir_rendimiento(datos):
    # Usaremos el volumen y el precio de cierre como variables predictoras
    datos['rendimiento'] = datos['close'].pct_change() * 100  # Cambio porcentual diario
    datos = datos.dropna()

    X = datos[['close', 'volume']]
    y = datos['rendimiento']  # La variable objetivo es el rendimiento calculado
    
    # Crear y entrenar el modelo de regresión lineal
    modelo = LinearRegression()
    modelo.fit(X, y)
    
    # Realizar una predicción usando el último valor de cierre y volumen
    ultima_fila = datos.iloc[-1]
    prediccion = modelo.predict([[ultima_fila['close'], ultima_fila['volume']]])
    
    return prediccion[0]

@app.route('/predecir_rendimiento', methods=['POST'])
def predecir_rendimiento_activo():
    ticker = request.form.get('ticker')
    
    # Cargar los datos del activo desde la base de datos
    conn = sqlite3.connect('acciones.db')
    query = f"SELECT close, volume FROM acciones WHERE ticker = '{ticker}'"
    datos = pd.read_sql_query(query, conn)
    conn.close()
    
    # Calcular el rendimiento y hacer la predicción
    datos_clasificados = calcular_rendimiento(datos)
    prediccion = predecir_rendimiento(datos_clasificados)
    
    # Retornar los resultados al frontend
    return render_template('prediccion_rendimiento.html', prediccion=f"{prediccion:.2f}%", 
                           datos=datos_clasificados.to_html(index=False))

if __name__ == '__main__':
    app.run(debug=True)