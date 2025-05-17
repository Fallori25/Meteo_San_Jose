from flask import Flask, request, render_template_string, jsonify
from datetime import datetime
import pytz

app = Flask(__name__)

# Variables actuales
datos = {
    "temperatura": "-",
    "humedad": "-",
    "presion": "-",
    "fecha": "-"
}

# Historial (últimos 10)
historial = []

# HTML con 3 gráficos separados
html_template = """
<html>
<head>
<title>Monitor Climatico de Fer 9D</title>
<meta name='viewport' content='width=device-width, initial-scale=1'>
<meta http-equiv='refresh' content='300'>
<style>
body { font-family: Arial, sans-serif; background-color: #FFB6C1; text-align: center; padding: 20px; margin: 0; }
.header { display: flex; justify-content: center; align-items: center; gap: 10px; flex-wrap: wrap; margin-bottom: 30px; }
.mini-card { background-color: red; color: white; padding: 10px 15px; border-radius: 10px; font-size: 1em; font-weight: bold; }
h1 { color: #2c3e50; font-size: 2em; margin: 0; }
.card { background: linear-gradient(135deg, #00CED1, #c7ecee); padding: 15px; margin: 15px auto; border-radius: 20px; max-width: 400px; box-shadow: 0px 4px 20px rgba(0,0,0,0.1); }
.dato { font-size: 2em; font-weight: bold; }
canvas { max-width: 100%; margin: 20px auto; }
</style>
</head>
<body>
  <div class='header'>
    <div class='mini-card'>San Miguel de Tucumán</div>
    <div class='mini-card'>{{ fecha }}</div>
  </div>

  <h1>Monitor Climatico de Fer 9D</h1>

  <div class='card'><div class='dato'>Temperatura: {{ temperatura }} &#8451;</div></div>
  <div class='card'><div class='dato'>Humedad: {{ humedad }} %</div></div>
  <div class='card'><div class='dato'>Presión: {{ presion }} hPa</div></div>

  <h2>Gráfico de Temperatura</h2>
  <canvas id="graficoTemp"></canvas>

  <h2>Gráfico de Humedad</h2>
  <canvas id="graficoHum"></canvas>

  <h2>Gráfico de Presión</h2>
  <canvas id="graficoPres"></canvas>

 <script src="https://cdn.jsdelivr.net/npm/chart.js@3.7.1/dist/chart.min.js"></script>

 <script src="https://cdn.jsdelivr.net/npm/chart.js@3.7.1/dist/chart.min.js"></script>

<script>
  let gTemp, gHum, gPres;

  function cargarGraficos() {
    fetch('/api/datos')
      .then(r => r.json())
      .then(data => {

        // Temperatura
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
            options: {
              responsive: true,
              scales: {
                x: { display: true },
                y: { display: true }
              }
            }
          });
        } else {
          gTemp.data.labels = data.labels;
          gTemp.data.datasets[0].data = data.temperaturas;
          gTemp.update();
        }

        // Humedad
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
            options: {
              responsive: true,
              scales: {
                x: { display: true },
                y: { display: true }
              }
            }
          });
        } else {
          gHum.data.labels = data.labels;
          gHum.data.datasets[0].data = data.humedades;
          gHum.update();
        }

        // Presión
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
            options: {
              responsive: true,
              scales: {
                x: { display: true },
                y: { display: true }
              }
            }
          });
        } else {
          gPres.data.labels = data.labels;
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
    return render_template_string(html_template,
                                  temperatura=datos["temperatura"],
                                  humedad=datos["humedad"],
                                  presion=datos["presion"],
                                  fecha=datos["fecha"])

@app.route("/update", methods=["POST"])
def update():
    argentina = pytz.timezone('America/Argentina/Buenos_Aires')
    datos["fecha"] = datetime.now(argentina).strftime("%d/%m/%Y %H:%M")

    try:
        temperatura = float(request.form.get("temperatura", "-"))
        humedad = float(request.form.get("humedad", "-"))
        presion = float(request.form.get("presion", "-"))

        datos["temperatura"] = f"{temperatura:.1f}"
        datos["humedad"] = f"{humedad:.1f}"
        datos["presion"] = f"{presion:.1f}"

        registro = {
            "hora": datetime.now(argentina).strftime("%H:%M"),
            "temperatura": temperatura,
            "humedad": humedad,
            "presion": presion
        }
        historial.append(registro)
        if len(historial) > 36:
            historial.pop(0)

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
    app.run(host="0.0.0.0", port=10000)







