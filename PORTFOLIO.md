# Soccer Edge System · lectura de portafolio

Proyecto experimental de adquisición, análisis y reporte de datos deportivos con persistencia local.

**Autor:** Jimmy Toapanta · [Perfil profesional](https://www.linkedin.com/in/jimmy-toapanta-950a441b8/) · [Portafolio](https://github.com/eslay07)

**Tecnologías:** Python · SQLite · pandas · NumPy · interfaz Tkinter

## Problema y solución

Integrar fuentes y conservar resultados de un análisis exige separar configuración, cálculo, persistencia e interfaz.

Contiene clientes de datos, funciones de análisis, módulos de cálculo y registro de resultados. La configuración actual se centraliza en cg0p/config/settings.py.

## Evidencia para revisar el trabajo

| Archivo o componente | Qué permite revisar |
| --- | --- |
| [main.py](main.py) | Entrada de consola. |
| [gui_tkinter.py](gui_tkinter.py) | Interfaz local. |
| [cg0p/config/settings.py](cg0p/config/settings.py) | Configuración y lectura de variables de entorno. |
| [cg0p/core/pipeline.py](cg0p/core/pipeline.py) | Recorrido de análisis. |
| [database.py](database.py) | Persistencia de resultados. |

## Estado y límites

Experimental. La presencia de modelos o cálculos no demuestra precisión predictiva, mejora continua ni resultados económicos. No se evaluó rendimiento estadístico ni un servicio en producción.

## Cómo evaluar el proyecto

Leer la configuración y usar datos de prueba antes de consultar servicios. Esta revisión no realizó apuestas ni validó predicciones.

Esta actualización documental se basa en la revisión del código y de la documentación disponibles. No añade métricas de ahorro, clientes, usuarios ni resultados de producción que no estén respaldados.

## Capacidad que demuestra

Organizar un sistema de análisis y distinguir una implementación técnica de una validación de resultados.

[Volver al README](README.md).
