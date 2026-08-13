# ============================================================
#  SOCCER EDGE SYSTEM — modelo.py
#  XGBoost multinomial para predecir H / D / A
#  Con calibración Platt + re-entrenamiento incremental
# ============================================================

import os
import pickle
import sqlite3
import numpy as np
import pandas as pd
from datetime import datetime

try:
    import xgboost as xgb
    from sklearn.calibration import CalibratedClassifierCV
    from sklearn.preprocessing import LabelEncoder
    from sklearn.model_selection import cross_val_score
    from sklearn.metrics import log_loss, brier_score_loss
    XGB_DISPONIBLE = True
except ImportError:
    XGB_DISPONIBLE = False

from config import DB_PATH
from features import construir_feature_vector

# ─────────────────────────────────────────────
#  PATHS
# ─────────────────────────────────────────────
MODEL_PATH  = "modelo_xgb.pkl"
SCALER_PATH = "scaler.pkl"
DATOS_PATH  = "datos_entrenamiento.csv"

# ─────────────────────────────────────────────
#  PARÁMETROS XGBOOST
# ─────────────────────────────────────────────
XGB_PARAMS = {
    "objective":       "multi:softprob",
    "num_class":       3,
    "n_estimators":    300,
    "max_depth":       4,
    "learning_rate":   0.05,
    "subsample":       0.8,
    "colsample_bytree": 0.8,
    "min_child_weight": 3,
    "gamma":           0.1,
    "reg_alpha":       0.1,
    "reg_lambda":      1.0,
    "eval_metric":     "mlogloss",
    "random_state":    42,
    "n_jobs":          1,   # -1 crashea en Windows con Python 3.13 (joblib bug)
}

# Mapeo de clases: 0=H, 1=D, 2=A
CLASES = {0: "HOME", 1: "DRAW", 2: "AWAY"}
CLASES_INV = {"HOME": 0, "DRAW": 1, "AWAY": 2}


# ─────────────────────────────────────────────
#  CLASE PRINCIPAL DEL MODELO
# ─────────────────────────────────────────────
class SoccerModel:

    def __init__(self):
        self.modelo     = None
        self.calibrado  = None
        self.entrenado  = False
        self.features_names = None
        self.metricas   = {}
        self._cargar_si_existe()

    # ── CARGAR MODELO GUARDADO ───────────────
    def _cargar_si_existe(self):
        if os.path.exists(MODEL_PATH):
            try:
                with open(MODEL_PATH, "rb") as f:
                    estado = pickle.load(f)
                self.modelo         = estado["modelo"]
                self.calibrado      = estado["calibrado"]
                self.features_names = estado["features_names"]
                self.metricas       = estado.get("metricas", {})
                self.entrenado      = True
                print(f"✅ Modelo cargado desde {MODEL_PATH}")
                if self.metricas:
                    print(f"   LogLoss CV: {self.metricas.get('logloss_cv', 'N/A'):.4f}  "
                          f"|  Partidos entrenados: {self.metricas.get('n_samples', '?')}")
            except Exception as e:
                print(f"⚠️  No se pudo cargar el modelo: {e}")

    # ── GUARDAR MODELO ───────────────────────
    def _guardar(self):
        with open(MODEL_PATH, "wb") as f:
            pickle.dump({
                "modelo":         self.modelo,
                "calibrado":      self.calibrado,
                "features_names": self.features_names,
                "metricas":       self.metricas,
            }, f)
        print(f"💾 Modelo guardado: {MODEL_PATH}")

    # ── CARGAR DATOS DE ENTRENAMIENTO ────────
    def cargar_datos(self, csv_path: str = DATOS_PATH) -> pd.DataFrame:
        """
        El CSV debe tener las columnas de features + columna 'resultado'
        donde resultado ∈ {HOME, DRAW, AWAY}
        """
        if not os.path.exists(csv_path):
            print(f"⚠️  No se encontró {csv_path}. Generando datos sintéticos de demostración...")
            return self._generar_datos_demo()
        df = pd.read_csv(csv_path)
        print(f"📂 Datos cargados: {len(df)} partidos desde {csv_path}")
        return df

    # ── DATOS SINTÉTICOS PARA DEMO ───────────
    def _generar_datos_demo(self, n: int = 2000) -> pd.DataFrame:
        """
        Genera datos de entrenamiento simulados realistas.
        En producción esto se reemplaza con datos históricos reales
        (Football-Data.co.uk, StatsBomb, API-Football, etc.)
        """
        np.random.seed(42)
        rows = []
        for _ in range(n):
            fh = np.random.dirichlet([3, 1, 1])   # home tiene ventaja
            fa = np.random.dirichlet([1, 1, 3])

            home_pts = fh[0] * 0.6 + np.random.normal(0, 0.05)
            away_pts = fa[0] * 0.6 + np.random.normal(0, 0.05)

            # Probabilidad real del partido
            logit_h = 0.5 + 1.5 * (home_pts - away_pts) + np.random.normal(0, 0.3)
            logit_d = -0.2 + np.random.normal(0, 0.2)
            logit_a = -0.5 - 1.5 * (home_pts - away_pts) + np.random.normal(0, 0.3)
            softmax = np.exp([logit_h, logit_d, logit_a])
            softmax /= softmax.sum()
            resultado = np.random.choice(["HOME", "DRAW", "AWAY"], p=softmax)

            fv = construir_feature_vector(
                home="TeamA", away="TeamB",
                forma_home={"wins": fh[0], "draws": fh[1], "losses": fh[2],
                            "gf_avg": 1.5*fh[0]+0.5, "gc_avg": 0.8*fh[2]+0.5, "puntos": home_pts},
                forma_away={"wins": fa[0], "draws": fa[1], "losses": fa[2],
                            "gf_avg": 1.5*fa[0]+0.5, "gc_avg": 0.8*fa[2]+0.5, "puntos": away_pts},
                h2h={"h2h_win_rate": softmax[0], "h2h_goles_avg": 2.4, "h2h_partidos": 5},
                prob_implicita_home=softmax[0] * (1 + np.random.uniform(0.03, 0.08)),
                prob_implicita_away=softmax[2] * (1 + np.random.uniform(0.03, 0.08)),
                prob_implicita_draw=softmax[1] * (1 + np.random.uniform(0.03, 0.08)),
                mov_linea_home=np.random.normal(0, 0.02),
                dias_descanso_home=np.random.randint(4, 14),
                dias_descanso_away=np.random.randint(4, 14),
            )
            fv["resultado"] = resultado
            rows.append(fv)

        df = pd.DataFrame(rows)
        df.to_csv(DATOS_PATH, index=False)
        print(f"✅ {n} partidos de demo generados y guardados en {DATOS_PATH}")
        return df

    # ── ENTRENAR ─────────────────────────────
    def entrenar(self, df: pd.DataFrame = None, forzar: bool = False):
        if not XGB_DISPONIBLE:
            print("❌ XGBoost no instalado. Ejecuta: pip install xgboost scikit-learn")
            return

        if self.entrenado and not forzar:
            print("ℹ️  Modelo ya entrenado. Usa entrenar(forzar=True) para re-entrenar.")
            return

        if df is None:
            df = self.cargar_datos()

        if len(df) < 100:
            print(f"⚠️  Solo {len(df)} muestras. Se recomienda mínimo 500 para resultados confiables.")

        feature_cols = [c for c in df.columns if c != "resultado"]
        self.features_names = feature_cols

        X = df[feature_cols].values
        y = np.array([CLASES_INV[r] for r in df["resultado"]])

        print(f"\n🤖 Entrenando XGBoost con {len(df)} partidos...")
        print(f"   Distribución: HOME={sum(y==0)} | DRAW={sum(y==1)} | AWAY={sum(y==2)}")

        self.modelo = xgb.XGBClassifier(**XGB_PARAMS)

        # Cross-validation para estimar rendimiento real
        scores = cross_val_score(self.modelo, X, y, cv=5, scoring="neg_log_loss", n_jobs=1)
        logloss_cv = -scores.mean()
        print(f"   LogLoss CV (5-fold): {logloss_cv:.4f}  ±{scores.std():.4f}")
        print(f"   (Referencia: modelo sin info = {np.log(3):.4f} | Buen modelo < 0.90)")

        # Entrenar en todo el dataset
        self.modelo.fit(X, y)

        # Calibración Platt para que las probabilidades sean realistas
        self.calibrado = CalibratedClassifierCV(self.modelo, method="isotonic", cv=3)
        self.calibrado.fit(X, y)
        print("   ✅ Calibración isotónica aplicada")

        self.metricas = {
            "logloss_cv":    round(logloss_cv, 4),
            "n_samples":     len(df),
            "fecha_entreno": datetime.now().isoformat(),
        }

        self.entrenado = True
        self._guardar()
        self._mostrar_importancia()

    # ── RE-ENTRENAR CON NUEVOS DATOS ─────────
    def actualizar_con_nuevo_partido(self, features: dict, resultado: str):
        """
        Añade un partido resuelto al CSV y re-entrena el modelo.
        Llamar después de cada jornada o lote de resultados.
        """
        nueva_fila = {**features, "resultado": resultado}

        if os.path.exists(DATOS_PATH):
            df = pd.read_csv(DATOS_PATH)
            df = pd.concat([df, pd.DataFrame([nueva_fila])], ignore_index=True)
        else:
            df = pd.DataFrame([nueva_fila])

        df.to_csv(DATOS_PATH, index=False)
        print(f"📥 Partido añadido al dataset ({len(df)} total). Re-entrenando...")
        self.entrenar(df=df, forzar=True)

    # ── PREDECIR ─────────────────────────────
    def predecir(self, features: dict) -> dict:
        """
        Recibe un dict de features y retorna probabilidades.
        → {"HOME": 0.48, "DRAW": 0.27, "AWAY": 0.25}
        """
        if not self.entrenado:
            print("⚠️  Modelo no entrenado. Usando fallback de mercado.")
            return None

        try:
            X = pd.DataFrame([features])[self.features_names].values
            probs = self.calibrado.predict_proba(X)[0]
            return {
                "HOME": round(probs[0], 4),
                "DRAW": round(probs[1], 4),
                "AWAY": round(probs[2], 4),
            }
        except Exception as e:
            print(f"⚠️  Error en predicción: {e}")
            return None

    # ── IMPORTANCIA DE FEATURES ──────────────
    def _mostrar_importancia(self, top_n: int = 10):
        if not self.modelo or not self.features_names:
            return
        importancias = self.modelo.feature_importances_
        ranking = sorted(zip(self.features_names, importancias),
                        key=lambda x: x[1], reverse=True)
        print(f"\n📊 Top {top_n} features más importantes:")
        for i, (feat, imp) in enumerate(ranking[:top_n], 1):
            bar = "█" * int(imp * 100)
            print(f"   {i:2}. {feat:<25} {imp:.4f}  {bar}")

    # ── EVALUAR CALIBRACIÓN ──────────────────
    def evaluar_calibracion(self, df: pd.DataFrame = None):
        """
        Compara probabilidades del modelo vs frecuencias reales.
        Un modelo bien calibrado tiene Brier Score < 0.20.
        """
        if df is None:
            df = self.cargar_datos()

        feature_cols = [c for c in df.columns if c != "resultado"]
        X = df[feature_cols].values
        y = np.array([CLASES_INV[r] for r in df["resultado"]])
        probs = self.calibrado.predict_proba(X)

        print("\n📐 Calibración del modelo:")
        for i, clase in enumerate(["HOME", "DRAW", "AWAY"]):
            y_bin  = (y == i).astype(int)
            p_clase = probs[:, i]
            bs = brier_score_loss(y_bin, p_clase)
            print(f"   {clase}: Brier Score = {bs:.4f}  "
                  f"({'✅ Bien calibrado' if bs < 0.22 else '⚠️ Mejorable'})")


# ─────────────────────────────────────────────
#  INSTANCIA GLOBAL (importar desde otros módulos)
# ─────────────────────────────────────────────
modelo_global = SoccerModel()


def entrenar_modelo(forzar: bool = False):
    modelo_global.entrenar(forzar=forzar)


def predecir_partido(features: dict) -> dict:
    return modelo_global.predecir(features)


def actualizar_modelo(features: dict, resultado: str):
    modelo_global.actualizar_con_nuevo_partido(features, resultado)
