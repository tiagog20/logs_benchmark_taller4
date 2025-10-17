import sys
import time
from pyspark.sql import SparkSession
from pyspark.sql.functions import col, count, when

if len(sys.argv) != 2:
    print("Usage: spark_benchmark_v2.py <s3_path>")
    sys.exit(1)

s3_path = sys.argv[1]

# --- Inicializar sesión Spark ---
spark = (
    SparkSession.builder
    .appName("Spark Benchmark Logs")
    .config("spark.hadoop.fs.s3a.impl", "org.apache.hadoop.fs.s3a.S3AFileSystem")
    .config("spark.hadoop.fs.s3a.aws.credentials.provider", "com.amazonaws.auth.InstanceProfileCredentialsProvider")
    .config("spark.hadoop.mapreduce.fileoutputcommitter.algorithm.version", "2")
    .config("spark.sql.shuffle.partitions", "8")
    .config("spark.driver.memory", "4g")
    .config("spark.executor.memory", "4g")
    .getOrCreate()
)

start_time = time.time()
print(f"\n🚀 Benchmark iniciado en: {s3_path}\n")

# --- Leer datos desde S3 ---
df = spark.read.json(s3_path)
total_rows = df.count()
print(f"✅ Archivos cargados desde {s3_path}")
print(f"Total de registros: {total_rows:,}\n")

# --- Simulación de checkpoints por volumen ---
# Suponemos 5 GB por lote
gb_step = 5
total_gb = 25  # ajusta según el tamaño total que estés probando

for i in range(1, total_gb // gb_step + 1):
    batch_start = time.time()
    
    # Simulamos un procesamiento de lote: conteo de códigos de respuesta
    batch_df = df.filter(col("size") > 0)
    stats = batch_df.groupBy().agg(
        count(when(col("status").startswith("2"), True)).alias("rate_2xx"),
        count(when(col("status").startswith("4"), True)).alias("rate_4xx"),
        count(when(col("status").startswith("5"), True)).alias("rate_5xx")
    ).collect()[0]
    
    batch_end = time.time()
    elapsed_batch = (batch_end - batch_start) / 60
    print(f"Checkpoint: ~{i * gb_step} GB procesados después de {elapsed_batch:.2f} min.")

# --- Benchmark final ---
end_time = time.time()
total_elapsed = (end_time - start_time) / 60

print("\n✅ Benchmark completado con éxito.")
print("\n📊 Resultados finales:")
print(f"  rate_2xx = {stats['rate_2xx']}")
print(f"  rate_4xx = {stats['rate_4xx']}")
print(f"  rate_5xx = {stats['rate_5xx']}")
print(f"\n🕒 Tiempo total transcurrido: {total_elapsed:.2f} minutos\n")

spark.stop()
