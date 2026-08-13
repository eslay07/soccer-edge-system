# ⚽ SOCCER EDGE SYSTEM

Sistema de análisis de apuestas con detección de edge, aprendizaje continuo y exportación de reportes.

---

## 📦 INSTALACIÓN

```bash
pip install -r requirements.txt
```

---

## ⚙️ CONFIGURACIÓN (3 pasos)

### 1. Obtener API Key gratuita
→ Regístrate en: https://the-odds-api.com
→ Plan gratuito: 500 requests/mes (suficiente para probar)

### 2. Pegar tu API Key en config.py
```python
API_KEY = "aquí_tu_api_key"
```

### 3. Ajustar parámetros (opcional)
En `config.py`:
- `EDGE_MINIMO = 3.5`      # % mínimo para que sea PICK (no PASS)
- `KELLY_FRACCION = 0.25`  # conservador: 25% del Kelly
- `BANKROLL = 1000`        # tu bankroll en la moneda que uses
- `VALUE_BET_MAXIMO = 4.0` # filtra longshots sin base estadística

---

## 🚀 USO

### Correr análisis completo
```bash
python main.py
```
→ Descarga odds de todas las ligas configuradas
→ Calcula edge para cada partido/selección
→ Imprime PICK 🟢 o PASS 🔴 con justificación
→ Genera imagen PNG del reporte en /reportes/
→ Guarda todo en la base de datos

### Resolver picks pasados (actualizar resultado)
```bash
python main.py resolver
```
→ Muestra picks pendientes
→ Ingresas resultado (W/L/P)
→ El sistema calcula P&L y actualiza la calibración

---

## 📊 ESTRUCTURA DE ARCHIVOS

```
soccer_edge_system/
│
├── config.py         # ← Parámetros del sistema (empieza aquí)
├── scraper.py        # Motor de odds + detección de edge
├── database.py       # SQLite: picks, resultados, aprendizaje
├── reportes.py       # Generador de imágenes PNG
├── main.py           # Punto de entrada
├── requirements.txt
│
├── soccer_edge.db    # Base de datos (se crea automáticamente)
└── reportes/         # Imágenes generadas (se crea automáticamente)
```

---

## 🧠 APRENDIZAJE CONTINUO

Cada vez que resuelves un pick con `python main.py resolver`, el sistema:
1. Registra el resultado real vs el edge calculado
2. Acumula datos de calibración por liga y mercado
3. Las estadísticas globales mejoran su precisión con el tiempo

Próximas versiones incluirán re-entrenamiento automático con `scikit-learn`.

---

## 📈 LÓGICA DE PICK / PASS

```
Cuota < 1.05          → PASS (sin valor)
Cuota > 4.00          → PASS (longshot sin base)
Edge < 3.5%           → PASS ("No hay apuesta con edge suficiente. Se pasa.")
Prob. real < 20%      → PASS (demasiada incertidumbre)
Todo lo anterior OK   → ✅ PICK con stake Kelly fraccionado
```

---

## 🔧 PRÓXIMOS MÓDULOS

- [ ] Dashboard Streamlit con curva de bankroll
- [ ] Modelo ML propio (XGBoost) para probabilidades
- [ ] Detección de steam moves (movimiento de línea)
- [ ] Alertas por Telegram cuando aparece un pick
- [ ] Scheduler automático cada 2h
