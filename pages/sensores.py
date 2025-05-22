import streamlit as st
import paho.mqtt.client as mqtt
import json
import time
from datetime import datetime

# Configuración MQTT
MQTT_BROKER = "broker.mqttdashboard.com"
MQTT_PORT = 1883
MQTT_TOPIC = "huerta/sofia/sensores"

# Variables de estado para los datos del sensor
if 'sensor_data' not in st.session_state:
    st.session_state.sensor_data = None
if 'messages' not in st.session_state:
    st.session_state.messages = []

def get_mqtt_message():
    """Función para obtener un único mensaje MQTT"""
    message_received = {"received": False, "payload": None}
    
    def on_message(client, userdata, message):
        try:
            # Intentar decodificar como JSON, si no funciona, usar texto plano
            try:
                payload = json.loads(message.payload.decode())
            except:
                payload = message.payload.decode()
            
            message_received["payload"] = payload
            message_received["received"] = True
        except Exception as e:
            st.error(f"Error al procesar mensaje: {e}")
    
    try:
        client = mqtt.Client()
        client.on_message = on_message
        client.connect(MQTT_BROKER, MQTT_PORT, 60)
        client.subscribe(MQTT_TOPIC)
        client.loop_start()
        
        # Esperar hasta 10 segundos por un mensaje
        timeout = time.time() + 10
        while not message_received["received"] and time.time() < timeout:
            time.sleep(0.1)
        
        client.loop_stop()
        client.disconnect()
        
        return message_received["payload"]
    
    except Exception as e:
        st.error(f"Error de conexión: {e}")
        return None

# Título de la aplicación
st.title('🌱 Monitor MQTT - Huerta Sofia')

with st.sidebar:
    st.subheader("Información de Conexión")
    st.write(f"**Broker:** {MQTT_BROKER}")
    st.write(f"**Puerto:** {MQTT_PORT}")
    st.write(f"**Tópico:** {MQTT_TOPIC}")

# Columna principal
st.subheader("📡 Datos del Sensor")

# Botón para obtener mensaje MQTT
if st.button("🔍 Escuchar Tópico", type="primary"):
    with st.spinner('Esperando mensaje del sensor...'):
        sensor_data = get_mqtt_message()
        
        if sensor_data:
            # Guardar en session state
            st.session_state.sensor_data = sensor_data
            
            # Añadir a la lista de mensajes con timestamp
            timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            new_message = {
                'timestamp': timestamp,
                'data': sensor_data
            }
            st.session_state.messages.append(new_message)
            
            # Mantener solo los últimos 20 mensajes
            if len(st.session_state.messages) > 20:
                st.session_state.messages = st.session_state.messages[-20:]
            
            st.success("✅ Mensaje recibido")
            
            # Mostrar el mensaje recibido
            st.subheader("📩 Último Mensaje Recibido:")
            
            if isinstance(sensor_data, dict):
                # Si es un diccionario (JSON), mostrarlo formateado
                st.json(sensor_data)
                
                # Si contiene datos de sensores típicos, mostrar métricas
                if 'Temp' in sensor_data or 'temperatura' in sensor_data:
                    temp = sensor_data.get('Temp') or sensor_data.get('temperatura')
                    st.metric("🌡️ Temperatura", f"{temp}°C")
                
                if 'Hum' in sensor_data or 'humedad' in sensor_data:
                    hum = sensor_data.get('Hum') or sensor_data.get('humedad')
                    st.metric("💧 Humedad", f"{hum}%")
                    
            else:
                # Si es texto plano, mostrarlo en un código block
                st.code(str(sensor_data))
            
        else:
            st.warning("⚠️ No se recibió ningún mensaje en 10 segundos")

if st.session_state.sensor_data:
    temp = st.session_state.sensor_data.get('Temp') or st.session_state.sensor_data.get('temperatura')
    try:
        if temp and float(temp) > 30:
            st.image("https://i.imgur.com/sZ5B4vM.png", caption="🌡️ ¡Alta temperatura detectada!", use_column_width=True)
    except ValueError:
        st.warning("⚠️ El valor de temperatura no es válido.")

# Mostrar historial de mensajes
if st.session_state.messages:
    st.markdown("---")
    st.subheader("📋 Historial de Mensajes")
    
    # Botón para limpiar historial
    if st.button("🗑️ Limpiar Historial"):
        st.session_state.messages = []
        st.session_state.sensor_data = None
        st.rerun()
    
    # Mostrar mensajes en orden inverso (más recientes primero)
    for i, msg in enumerate(reversed(st.session_state.messages)):
        with st.expander(f"📨 Mensaje {len(st.session_state.messages) - i} - {msg['timestamp']}", expanded=(i == 0)):
            if isinstance(msg['data'], dict):
                st.json(msg['data'])
            else:
                st.code(str(msg['data']))

# Información adicional en el pie
st.markdown("---")
st.info("💡 **Instrucciones:** Presiona el botón 'Escuchar Tópico' para recibir un mensaje del sensor. La aplicación esperará hasta 10 segundos por un mensaje nuevo.")
