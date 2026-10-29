# Soccer Edge System

**Proyecto experimental en Python para integrar fuentes de datos deportivos, organizar un recorrido de análisis y conservar resultados en SQLite.** Su valor de portafolio está en la adquisición de datos, la separación de componentes, la interfaz y el seguimiento del resultado; no acredita rentabilidad ni precisión predictiva.

[Lectura de portafolio y evidencia](PORTFOLIO.md) · [Perfil del autor](https://github.com/eslay07)

## Alcance actual

El repositorio contiene una entrada de consola, una interfaz Tkinter y un paquete `cg0p` con configuración, módulos y funciones de cálculo. También conserva archivos de compatibilidad de versiones anteriores.

La presencia de fórmulas, modelos y parámetros no demuestra que el sistema produzca decisiones correctas. La validación estadística, la calidad de la fuente y la evaluación fuera de muestra deben estudiarse por separado. No se presentan ganancias ni tasas de acierto como resultados verificados.

## Componentes que se pueden revisar

| Componente | Evidencia |
| --- | --- |
| Entrada de consola | [main.py](main.py) |
| Interfaz local | [gui_tkinter.py](gui_tkinter.py) |
| Configuración centralizada | [cg0p/config/settings.py](cg0p/config/settings.py) |
| Recorrido de análisis | [cg0p/core/pipeline.py](cg0p/core/pipeline.py) |
| Persistencia | [database.py](database.py) |
| Datos y variables de análisis | [features.py](features.py) |
| Dependencias | [requirements.txt](requirements.txt) |

## Preparar el entorno

Use un entorno virtual independiente e instale las dependencias del repositorio:

```powershell
py -3.12 -m venv .venv
.\.venv\Scripts\python.exe -m pip install -r requirements.txt
```

La configuración actual está en `cg0p/config/settings.py`; `config.py` reexporta valores por compatibilidad. La clave de la fuente configurada se lee desde la variable de entorno `SHARP_API_KEY`. No debe pegarse una clave real en el código ni publicarse un archivo de entorno con credenciales.

La configuración y disponibilidad de una API externa deben comprobarse con su proveedor. Esta documentación no garantiza el acceso a un plan o endpoint concreto.

## Recorridos disponibles

```powershell
.\.venv\Scripts\python.exe gui_tkinter.py
.\.venv\Scripts\python.exe main.py
```

La entrada de consola puede consultar servicios y escribir resultados locales; revise la configuración antes de ejecutarla. La revisión documental no ejecutó consultas, apuestas ni transacciones reales.

## Qué demuestra como proyecto técnico

- Separación entre configuración, adquisición, cálculo, interfaz y persistencia.
- Manejo de resultados y estados en una base local.
- Necesidad de distinguir el cálculo implementado de su validación estadística.
- Evolución de una entrada simple hacia una estructura por paquetes y componentes.

## Límites y siguientes pasos

- Verificar los contratos y la disponibilidad de las fuentes de datos.
- Incorporar conjuntos de datos sintéticos y pruebas deterministas para cada componente.
- Medir rendimiento y errores antes de atribuir mejoras al modelo.
- Documentar las versiones de compatibilidad y retirar rutas obsoletas cuando exista cobertura de pruebas.
- Mantener fuera de GitHub claves, bases locales, reportes personales y registros de uso.

## Autor

**Jimmy Toapanta** · [LinkedIn](https://www.linkedin.com/in/jimmy-toapanta-950a441b8/) · [Portafolio](https://github.com/eslay07)
