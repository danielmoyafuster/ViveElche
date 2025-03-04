import streamlit as st
import sqlite3
import pandas as pd
from datetime import datetime, timedelta
import streamlit.components.v1 as components

# --------------------------------------------------------------------------------------------
DB_PATH = "./ViveElche.db" 
# --------------------------------------------------------------------------------------------

# Traducción manual de los meses y días
traduccion_meses = {
    "January": "Enero", "February": "Febrero", "March": "Marzo", "April": "Abril",
    "May": "Mayo", "June": "Junio", "July": "Julio", "August": "Agosto",
    "September": "Septiembre", "October": "Octubre", "November": "Noviembre", "December": "Diciembre"
}

traduccion_dias = {
    "Monday": "Lunes", "Tuesday": "Martes", "Wednesday": "Miércoles",
    "Thursday": "Jueves", "Friday": "Viernes", "Saturday": "Sábado", "Sunday": "Domingo"
}

# Función para traducir fecha correctamente
def format_date(fecha):
    try:
        fecha_dt = datetime.strptime(fecha, '%Y-%m-%d')
        dia_semana = fecha_dt.strftime('%A')
        mes = fecha_dt.strftime('%B')
        return f"{traduccion_dias[dia_semana]}, {fecha_dt.day} de {traduccion_meses[mes]} de {fecha_dt.year}"
    except:
        return fecha

# Función para formatear precios con €
def format_price(precio):
    try:
        return f"{float(precio):.2f} €"
    except:
        return "-"

# Obtener la fecha de hoy y dentro de 15 días
today = datetime.today().date()  # 🔴 AHORA SOLO LA FECHA, SIN HORA
future_date = today + timedelta(days=15)

# Función para obtener eventos
def get_events():
    conn = sqlite3.connect(DB_PATH)
    query = """
    SELECT 
        r.RECIN_NOMBRE AS Recinto, 
        e.EVENT_FECHA AS Fecha, 
        e.EVENT_HORA AS Hora, 
        e.EVENT_ARTISTA AS Artista, 
        e.EVENT_TITULO AS Título, 
        e.EVENT_DURACION AS Duración, 
        e.EVENT_PRECIO AS Precio
    FROM tbl_eventos e
    LEFT JOIN tbl_recinto r ON e.RECIN_ID = r.RECIN_ID
    WHERE e.EVENT_FECHA BETWEEN ? AND ?
    ORDER BY e.EVENT_FECHA ASC
    """
    df = pd.read_sql_query(query, conn, params=(today.strftime('%Y-%m-%d'), future_date.strftime('%Y-%m-%d')))
    conn.close()

    df.fillna("", inplace=True)
    df["Precio"] = df["Precio"].apply(format_price)

    # Convertir Fecha a datetime para cálculos correctos
    df["Fecha_dt"] = pd.to_datetime(df["Fecha"], errors='coerce').dt.date  # 🔴 AHORA SOLO LA FECHA, SIN HORA
    df["Fecha"] = df["Fecha_dt"].apply(lambda x: format_date(x.strftime('%Y-%m-%d')))  # Traducir fecha a español

    return df

# Función para obtener color de fondo según urgencia
def get_row_color(fecha_evento):
    try:
        days_until_event = (fecha_evento - today).days  # 🔴 AHORA COMPARA FECHAS SIN HORA
        if days_until_event <= 3:
            return "background-color: rgba(255, 102, 102, 0.3);"  # Rojo pastel (urgencia alta)
        elif 4 <= days_until_event <= 7:
            return "background-color: rgba(255, 165, 0, 0.3);"  # Naranja pastel (urgencia media)
        elif 8 <= days_until_event <= 15:
            return "background-color: rgba(144, 238, 144, 0.3);"  # Verde pastel (urgencia baja)
        else:
            return "background-color: white;"
    except:
        return "background-color: white;"

# Streamlit UI
st.set_page_config(layout="wide")
st.title("Eventos en ViveElche 📅")
st.subheader(f"Eventos desde {format_date(today.strftime('%Y-%m-%d'))} hasta {format_date(future_date.strftime('%Y-%m-%d'))}")

# Obtener eventos y mostrar en tabla
eventos_df = get_events()

if not eventos_df.empty:
    eventos_df["Fecha_dt"] = pd.to_datetime(eventos_df["Fecha_dt"], errors='coerce').dt.date

    # Generar tabla en HTML con estilos de fondo según la fecha del evento
    html_table = """
    <style>
        .scrollable-table {
            max-height: 500px;
            overflow-y: auto;
            display: block;
        }
        table {
            width: 100%;
            border-collapse: collapse;
            font-size: 16px;
        }
        th, td {
            padding: 8px;
            border: 1px solid #ddd;
            text-align: left;
        }
        th {
            background-color: lightgray;
            position: sticky;
            top: 0;
            z-index: 2;
        }
    </style>
    <div class='scrollable-table'>
    <table>
    <tr>
        <th>Recinto</th>
        <th>Fecha</th>
        <th>Hora</th>
        <th>Artista</th>
        <th>Título</th>
        <th>Duración</th>
        <th>Precio</th>
    </tr>
    """
    
    for _, row in eventos_df.iterrows():
        color = get_row_color(row["Fecha_dt"])
        html_table += f"""
        <tr style='{color}'>
            <td><div style="font-size: 12px">{row["Recinto"]}</div></td>
            <td><div style="font-size: 12px">{row["Fecha"]}</div></td>
            <td><div style="font-size: 12px">{row["Hora"]}</div></td>
            <td><div style="font-size: 12px">{row["Artista"]}</div></td>
            <td><div style="font-size: 12px">{row["Título"]}</div></td>
            <td><div style="font-size: 12px">{row["Duración"]}</div></td>
            <td><div style="font-size: 12px">{row["Precio"]}</div></td>
        </tr>
        """

    html_table += "</table></div>"

    # Mostrar tabla en Streamlit usando `components.html()`
    components.html(html_table, height=500, scrolling=True)

    # Mostrar leyenda de colores debajo de la tabla
    st.markdown("""
    <div style="font-size: 12px; margin-top: 10px;">
        <b>Leyenda de colores (Urgencia para comprar entradas):</b><br>
        🟥 <span style="color: red;">Alta → Evento en 1-3 días (Rojo pastel)</span><br>
        🟧 <span style="color: orange;">Media → Evento en 4-7 días (Naranja pastel)</span><br>
        🟩 <span style="color: green;">Baja → Evento en 8-15 días (Verde pastel)</span>
    </div>
    """, unsafe_allow_html=True)

else:
    st.warning("No hay eventos programados en este rango de fechas.")