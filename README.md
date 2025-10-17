# 🏁 Data Processing Benchmark – Python, Pandas, Polars, DuckDB & Spark

**Autor:** Santiago González Granada  
**Curso:** Minería de Grandes Volúmenes de Datos – Taller III  
**Institución:** Universidad EAFIT  

---

## 📘 Descripción General

Este proyecto presenta una **comparativa de rendimiento** entre cinco enfoques de procesamiento de datos a gran escala:

1. **Pure Python (boto3 + json)**
2. **Pandas**
3. **Polars**
4. **DuckDB**
5. **Apache Spark**

El objetivo fue evaluar **tiempo de ejecución**, **uso de CPU** y **consumo de memoria** al procesar volúmenes crecientes de datos almacenados en AWS S3, manteniendo un entorno controlado y homogéneo.

---

## ⚙️ Entorno Experimental

- **Infraestructura:** AWS EC2 `m5.2xlarge` (8 vCPU, 32 GiB RAM)
- **Sistema Operativo:** Ubuntu 22.04 LTS
- **Dataset:** 25 GB (~50M JSON lines) almacenados en S3
- **Procesamiento:** Lectura y transformación de registros JSON
- **Checkpoints:** mediciones a 5, 10, 15, 20 y 25 GB

---

## ⏱️ Resultados Globales

| **Implementación** | **Tiempo total (25 GB)** | **CPU Utilization** | **Memoria Máx.** | **Descripción y Trade-off** |
|:-------------------:|:-------------------------:|:--------------------:|:----------------:|:-----------------------------|
| 🥇 **DuckDB** | 8.12 min | Alta | Moderado | 🏎️ **El Coche Deportivo:** velocidad pura con excelente eficiencia de recursos. El ganador claro. |
| 🥈 **Polars** | 8.77 min | Alta | Baja | 🚗 **El Coche de Rally:** casi tan rápido como DuckDB, pero con mejor eficiencia de memoria. |
| 🥉 **Spark** | 19.6 min | Muy Alta | Muy Alta | 🚚 **El Camión Pesado:** más lento en esta prueba, usa la mayor potencia y memoria. Ideal para escalar más allá de 25 GB. |
| 4️⃣ **Pure Python** | 26.33 min | Baja | Muy baja | 🛵 **El Scooter Eléctrico:** el más lento, pero con la huella de recursos más pequeña. |
| 5️⃣ **Pandas** | 35.75 min | Media | Alta | 🚙 **El Sedán Familiar:** cómodo y conocido, pero no apto para grandes volúmenes. |

---

## 🔍 Análisis Resumido

DuckDB logró el mejor tiempo de procesamiento total, aprovechando un motor vectorizado en memoria con un paralelismo eficiente.
Polars le siguió muy de cerca, mostrando un rendimiento casi idéntico, con una excelente eficiencia de memoria y ejecución columnar.
Spark proporcionó un buen rendimiento relativo y una gran escalabilidad distribuida, aunque con una mayor sobrecarga y consumo de recursos.
Pure Python fue significativamente más lento, procesando los datos línea por línea sin vectorización ni concurrencia.
Pandas fue el más lento, limitado por la ejecución de un solo subproceso y el alto uso de memoria.

---

## 🧠 Conclusiones

- 🥇 **DuckDB y Polars** son las opciones más eficientes para procesar grandes volúmenes de datos en un solo nodo, combinando **velocidad** y **uso moderado de memoria**.  
- ⚙️ **Spark** es más adecuado para **escalabilidad horizontal**, aunque no el más rápido en una máquina individual.  
- 🐍 **Pandas y Pure Python** sirven como línea base o para tareas pequeñas, pero **no son óptimos** para big data.  

---
