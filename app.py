from flask import Flask, request, render_template_string, jsonify
from datetime import datetime
import pytz
import requests
import os

app = Flask(__name__)

# Coordenadas de San José, California
lat = 37.3382
lon = -121.8863

# Variables actuales
datos = {
    "temperatura": "-",
    "humedad": "-",
    "presion": "-",
    "fecha": "-",
    "hora": "-",
    "pronostico_html": "No se pudo obtener el pronóstico."
}

# Historial (últimos 36 para 3 horas cada 5 minutos)
historial = []

def obtener_pronostico():
    try:
        api_key = "9fbfb7854109d6c910f2d435052fb109"
        url = f"https://api.openweathermap.org/data/2.5/onecall?lat={lat}&lon={lon}&exclude=current,minutely,hourly,alerts&units=metric&lang=es&appid={api_key}"
        r = requests.get(url)
        data = r.json()
        dias = []
        iconos = {
            "Clear": "☀️", "Clouds": "☁️", "Rain": "🌧️", "Drizzle": "🌦️",
            "Thunderstorm": "⛈️", "Snow": "❄️", "Mist": "🌫️"
        }
        for i in range(1, 7):
            d = data["daily"][i]
            dt = datetime.fromtimestamp(d["dt"])
            dia = dt.strftime("%A")
            descripcion = d["weather"][0]["main"]
            icono = iconos.get(descripcion, "🌡️")
            max_temp = d["temp"]["max"]
            min_temp = d["temp"]["min"]
            dias.append(f"{icono} {dia}: {max_temp:.0f}°C / {min_temp:.0f}°C - {d['weather'][0]['description'].capitalize()}")
        return "<br>".join(dias)
    except:
        return "No se pudo obtener el pronóstico."

html_template = """
<html>
<head>
<title>El tiempo en San Jose</title>
<meta name='viewport' content='width=device-width, initial-scale=1'>
<style>
body {
  font-family: Arial, sans-serif;
  background-color: #FFB6C1;
  text-align: center;
  padding: 20px;
  margin: 0;
}
.header {
  display: flex;
  justify-content: center;
  align-items: center;
  gap: 10px;
  flex-wrap: wrap;
  margin-bottom: 30px;
}
.mini-card {
  background-color: red;
  color: white;
  padding: 10px 15px;
  border-radius: 10px;
  font-size: 1em;
  font-weight: bold;
}
h1 {
  color: #2c3e50;
  font-size: 2em;
  margin: 0 0 10px;
}
.card {
  background: linear-gradient(135deg, #00CED1, #c7ecee);
  padding: 15px;
  margin: 10px auto;
  border-radius: 20px;
  max-width: 400px;
  box-shadow: 0px 4px 20px rgba(0,0,0,0.1);
}
.dato {
  font-size: 2em;
  font-weight: bold;
}
canvas {
  max-width: 100%;
  margin: 20px auto;
}
#pronostico {
  margin-top: 40px;
  background: linear-gradient(135deg, #00CED1, #7fffd4);
  border-radius: 20px;
  padding: 15px;
  font-size: 1.2em;
  font-weight: bold;
}
</style>
<script>
  setInterval(() => window.location.reload(), 600000);  // Refresca cada 10 min
</script>
</head>
<body>
  <h1>El tiempo en San Jose</h1>
  <div class='header'>
    <div class='mini-card'>📅 {{ fecha }}</div>
    <div class='mini-card'>🕒 {{ hora }}</div>
  </div>

  <div class='card'><div class='dato'>🌡️ Temperatura: {{ temperatura }} &#8451;</div></div>
  <div class='card'><div class='dato'>💧 Humedad: {{ humedad }} %</div></div>
  <div class='card'><div class='dato'>📈 Presión: {{ presion }} hPa</div></div>

  <h2>Gráfico de Temperatura</h2>
  <canvas id="graficoTemp"></canvas>

  <h2>Gráfico de Humedad</h2>
  <canvas id="graficoHum"></canvas>

  <h2>Gráfico de Presión</h2>
  <canvas id="graficoPres"></canvas>

  <h2>Pronóstico extendido</h2>
  <div id="pronostico">{{ pronostico|safe }}</div>

<script src="https://cdn.jsdelivr.net/npm/chart.js@3.7.1/dist/chart.min.js"></script>
<script>
let gTemp, gHum, gPres;
function cargarGraficos() {
  fetch('/api/datos')
    .then(r => r.json())
    .then(data => {
      if (!gTemp) {
        gTemp = new Chart(document.getElementById('graficoTemp').getContext('2d'), {
          type: 'line',
          data: {
            labels: data.labels,
            datasets: [{
              label: 'Temperatura (°C)',
              data: data.temperaturas,
              borderColor: 'red',
              backgroundColor: 'transparent',
              tension: 0.4
            }]
          },
          options: { responsive: true, scales: { x: { display: true }, y: { display: true } } }
        });
      } else {
        gTemp.data.labels = data.labels;
        gTemp.data.datasets[0].data = data.temperaturas;
        gTemp.update();
      }

      if (!gHum) {
        gHum = new Chart(document.getElementById('graficoHum').getContext('2d'), {
          type: 'line',
          data: {
            labels: data.labels,
            datasets: [{
              label: 'Humedad (%)',
              data: data.humedades,
              borderColor: 'blue',
              backgroundColor: 'transparent',
              tension: 0.4
            }]
          },
          options: { responsive: true, scales: { x: { display: true }, y: { display: true } } }
        });
      } else {
        gHum.data.labels = data.labels;
        gHum.data.datasets[0].data = data.humedades;
        gHum.update();
      }

      if (!gPres) {
        gPres = new Chart(document.getElementById('graficoPres').getContext('2d'), {
          type: 'line',
          data: {
            labels: data.labels,
            datasets: [{
              label: 'Presión (hPa)',
              data: data.presiones,
              borderColor: 'green',
              backgroundColor: 'transparent',
              tension: 0.4
            }]
          },
          options: { responsive: true, scales: { x: { display: true }, y: { display: true } } }
        });
      } else {
        gPres.data.labels = data.labels;
        gPres.data.datasets[0].data = data.presiones;
        gPres.update();
      }
    });
}
cargarGraficos();
</script>
</body>
</html>
"""

@app.route("/", methods=["GET"])
def home():
    return render_template_string(html_template,
                                  temperatura=datos["temperatura"],
                                  humedad=datos["humedad"],
                                  presion=datos["presion"],
                                  fecha=datos["fecha"],
                                  hora=datos["hora"],
                                  pronostico=datos["pronostico_html"])

@app.route("/update", methods=["POST"])
def update():
    usa = pytz.timezone('America/Los_Angeles')
    ahora = datetime.now(usa)
    datos["fecha"] = ahora.strftime("%d/%m/%Y")
    datos["hora"] = ahora.strftime("%H:%M:%S")
    try:
        temperatura = float(request.form.get("temperatura", "-"))
        humedad = float(request.form.get("humedad", "-"))
        presion = float(request.form.get("presion", "-"))

        datos["temperatura"] = f"{temperatura:.1f}"
        datos["humedad"] = f"{humedad:.1f}"
        datos["presion"] = f"{presion:.1f}"

        registro = {
            "hora": ahora.strftime("%H:%M"),
            "temperatura": temperatura,
            "humedad": humedad,
            "presion": presion
        }
        historial.append(registro)
        if len(historial) > 36:
            historial.pop(0)

        datos["pronostico_html"] = obtener_pronostico()

    except:
        datos["temperatura"] = datos["humedad"] = datos["presion"] = "-"

    return "OK"

@app.route("/api/datos", methods=["GET"])
def api_datos():
    etiquetas = [r["hora"] for r in historial]
    temperaturas = [r["temperatura"] for r in historial]
    humedades = [r["humedad"] for r in historial]
    presiones = [r["presion"] for r in historial]
    return jsonify({
        "labels": etiquetas,
        "temperaturas": temperaturas,
        "humedades": humedades,
        "presiones": presiones
    })

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port)

