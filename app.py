from flask import Flask, request, render_template_string, jsonify
from datetime import datetime
import pytz
import requests
import os

app = Flask(__name__)

# Coordenadas y clave para el pronóstico
lat = 37.3382
lon = -121.8863
API_KEY = "9fbfb7854109d6c910f2d435052fb109"

# Variables actuales
datos = {
    "temperatura": "-",
    "humedad": "-",
    "presion": "-",
    "fecha": "-",
    "hora": "-"
}

# Historial de los últimos 36 datos (~3 horas si se envía cada 5 min)
historial = []

html_template = """
<html>
<head>
  <title>El tiempo en San Jose</title>
  <meta name='viewport' content='width=device-width, initial-scale=1'>
  <meta http-equiv='refresh' content='300'>
  <style>
    body { font-family: Arial; background: #FFB6C1; text-align: center; padding: 20px; }
    .header { display: flex; justify-content: center; gap: 10px; flex-wrap: wrap; }
    .mini-card { background: red; color: white; padding: 10px 20px; border-radius: 12px; font-weight: bold; font-size: 1.2em; }
    h1 { font-size: 2.2em; margin-bottom: 10px; }
    .card { background: linear-gradient(135deg, #00CED1, #c7ecee); margin: 10px auto; padding: 15px; max-width: 400px; border-radius: 20px; box-shadow: 0 4px 10px rgba(0,0,0,0.1); font-size: 1.5em; font-weight: bold; }
    canvas { max-width: 100%; margin: 20px auto; }
    .forecast-card { background: linear-gradient(135deg, #76e3e0, #c4f0f0); padding: 10px; margin: 5px auto; max-width: 400px; border-radius: 20px; font-size: 1.2em; box-shadow: 0 2px 8px rgba(0,0,0,0.1); }
  </style>
</head>
<body>
  <h1>El tiempo en San Jose</h1>
  <div class='header'>
    <div class='mini-card'>📅 {{ fecha }}</div>
    <div class='mini-card'>⏰ {{ hora }}</div>
  </div>
  <div class='card'>🌡️ Temperatura: {{ temperatura }} ℃</div>
  <div class='card'>💧 Humedad: {{ humedad }} %</div>
  <div class='card'>📈 Presión: {{ presion }} hPa</div>

  <h2>Gráfico de Temperatura</h2>
  <canvas id="graficoTemp"></canvas>
  <h2>Gráfico de Humedad</h2>
  <canvas id="graficoHum"></canvas>
  <h2>Gráfico de Presión</h2>
  <canvas id="graficoPres"></canvas>

  <h2>Pronóstico extendido</h2>
  {% if forecast %}
    {% for dia in forecast %}
      <div class='forecast-card'>
        <strong>{{ dia.dia }}</strong> - {{ dia.temp_max }}°C / {{ dia.temp_min }}°C - {{ dia.descripcion }}
      </div>
    {% endfor %}
  {% else %}
    <div class='forecast-card'>No se pudo obtener el pronóstico.</div>
  {% endif %}

<script src="https://cdn.jsdelivr.net/npm/chart.js@3.7.1/dist/chart.min.js"></script>
<script>
  let gTemp, gHum, gPres;
  function cargarGraficos() {
    fetch('/api/datos').then(r => r.json()).then(data => {
      const labels = data.labels;

      if (!gTemp) {
        gTemp = new Chart(document.getElementById('graficoTemp').getContext('2d'), {
          type: 'line', data: { labels: labels, datasets: [{ label: 'Temperatura (°C)', data: data.temperaturas, borderColor: 'red', tension: 0.4 }] },
          options: { responsive: true, scales: { x: {}, y: {} } }
        });
      } else {
        gTemp.data.labels = labels;
        gTemp.data.datasets[0].data = data.temperaturas;
        gTemp.update();
      }

      if (!gHum) {
        gHum = new Chart(document.getElementById('graficoHum').getContext('2d'), {
          type: 'line', data: { labels: labels, datasets: [{ label: 'Humedad (%)', data: data.humedades, borderColor: 'blue', tension: 0.4 }] },
          options: { responsive: true, scales: { x: {}, y: {} } }
        });
      } else {
        gHum.data.labels = labels;
        gHum.data.datasets[0].data = data.humedades;
        gHum.update();
      }

      if (!gPres) {
        gPres = new Chart(document.getElementById('graficoPres').getContext('2d'), {
          type: 'line', data: { labels: labels, datasets: [{ label: 'Presión (hPa)', data: data.presiones, borderColor: 'green', tension: 0.4 }] },
          options: { responsive: true, scales: { x: {}, y: {} } }
        });
      } else {
        gPres.data.labels = labels;
        gPres.data.datasets[0].data = data.presiones;
        gPres.update();
      }
    });
  }
  cargarGraficos();
  setInterval(cargarGraficos, 300000);
</script>
</body>
</html>
"""

@app.route("/", methods=["GET"])
def home():
    return render_template_string(
        html_template,
        temperatura=datos["temperatura"],
        humedad=datos["humedad"],
        presion=datos["presion"],
        fecha=datos["fecha"],
        hora=datos["hora"],
        forecast=obtener_forecast()
    )

@app.route("/update", methods=["POST"])
def update():
    zona = pytz.timezone('America/Los_Angeles')
    ahora = datetime.now(zona)
    datos["fecha"] = ahora.strftime("%d/%m/%Y")
    datos["hora"] = ahora.strftime("%H:%M:%S")

    try:
        temperatura = float(request.form.get("temperatura", "-"))
        humedad = float(request.form.get("humedad", "-"))
        presion = float(request.form.get("presion", "-"))

        datos["temperatura"] = f"{temperatura:.1f}"
        datos["humedad"] = f"{humedad:.1f}"
        datos["presion"] = f"{presion:.1f}"

        historial.append({
            "hora": ahora.strftime("%H:%M"),
            "temperatura": temperatura,
            "humedad": humedad,
            "presion": presion
        })
        if len(historial) > 36:
            historial.pop(0)
    except:
        datos["temperatura"] = datos["humedad"] = datos["presion"] = "-"

    return "OK"

@app.route("/api/datos")
def api_datos():
    return jsonify({
        "labels": [r["hora"] for r in historial],
        "temperaturas": [r["temperatura"] for r in historial],
        "humedades": [r["humedad"] for r in historial],
        "presiones": [r["presion"] for r in historial]
    })

def obtener_forecast():
    try:
        url = f"https://api.openweathermap.org/data/2.5/forecast?lat={lat}&lon={lon}&appid={API_KEY}&units=metric&lang=es"
        res = requests.get(url, timeout=10)
        dias = {}
        for f in res.json()["list"]:
            fecha = f["dt_txt"].split(" ")[0]
            dia = datetime.strptime(fecha, "%Y-%m-%d").strftime("%A")
            temp = f["main"]["temp"]
            desc = f["weather"][0]["description"]
            if fecha not in dias:
                dias[fecha] = {"dia": dia.capitalize(), "max": temp, "min": temp, "desc": desc}
            else:
                dias[fecha]["max"] = max(dias[fecha]["max"], temp)
                dias[fecha]["min"] = min(dias[fecha]["min"], temp)
        return [{"dia": v["dia"], "temp_max": round(v["max"]), "temp_min": round(v["min"]), "descripcion": v["desc"]} for k, v in list(dias.items())[:6]]
    except:
        return None

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT", 5000)))
