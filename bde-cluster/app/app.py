import json
from os import *

from pyspark import SparkFiles
from pyspark.sql import SparkSession

import pyspark

from pyspark.sql.types import *
from pyspark.sql.functions import col
import pyspark.sql.functions as func
from decimal import Decimal


def main():
   
    spark = SparkSession.builder.appName('app').getOrCreate()

    print('Analysis started...')

    root = getenv('HDFS_ROOT')
    dataset_location = getenv('HDFS_DATASET_PATH')
    
    schema = StructType() \
      .add("adshex",StringType(),True) \
      .add("flight_id",StringType(),True) \
      .add("latitude",DoubleType(),True) \
      .add("longitude",DoubleType(),True) \
      .add("altitude",IntegerType(),True) \
      .add("speed",IntegerType(),True) \
      .add("track",IntegerType(),True) \
      .add("squawk",IntegerType(),True) \
      .add("type",StringType(),True) \
      .add("timestamp",TimestampType(),True) \
      .add("name",StringType(),True) \
      .add("other_names1",StringType(),True) \
      .add("other_names2",StringType(),True) \
      .add("n_number",StringType(),True) \
      .add("serial_number",StringType(),True) \
      .add("mfr_mdl_code",IntegerType(),True) \
      .add("mfr",StringType(),True) \
      .add("model",StringType(),True) \
      .add("year_mfr",IntegerType(),True) \
      .add("type_aircraft",IntegerType(),True) \
      .add("agency",StringType(),True)
      
    df = spark.read.format("csv") \
      .option("header", True) \
      .option("delimiter", ";") \
      .schema(schema) \
      .option("timestampFormat", "yyyy-MM-dd'T'HH:mm:ss'Z'") \
      .load(root + dataset_location + "feds.csv")      
    
    date_from = func.to_timestamp(func.lit(getenv('SPARK_APP_ARG_DATE_FROM')),"yyyy-MM-dd'T'HH:mm:ss'Z'")
    date_to = func.to_timestamp(func.lit(getenv('SPARK_APP_ARG_DATE_TO')),"yyyy-MM-dd'T'HH:mm:ss'Z'")
    lat = Decimal(getenv('SPARK_APP_ARG_LAT'))
    lon = Decimal(getenv('SPARK_APP_ARG_LON'))
    latPrecision = Decimal(getenv('SPARK_APP_ARG_LAT_PRECISION'))
    lonPrecision = Decimal(getenv('SPARK_APP_ARG_LON_PRECISION'))  
    attributeName = getenv('SPARK_APP_ARG_ATTR_NAME')
    attributeValue = getenv('SPARK_APP_ARG_ATTR_VALUE')
    attributeToShow = getenv('SPARK_APP_ARG_ATTR_TO_SHOW')
       
    sf = df.filter(df.timestamp > date_from).filter(df.timestamp < date_to).filter(df.latitude > lat-latPrecision).filter(df.latitude < lat+latPrecision).filter(df.longitude > lon-lonPrecision).filter(df.longitude < lon+lonPrecision).filter(col(attributeName) == attributeValue)
   
    sf.groupBy(col(attributeToShow)).count().show()
    max_value=sf.select(func.max(func.col(attributeToShow)).alias("MAX")).first().MAX
    print("Maximum of given column:");
    print(max_value);

    min_value=sf.select(func.min(func.col(attributeToShow)).alias("MIN")).first().MIN
    print("Minimum of given column:");
    print(min_value);
    
    df_stats = df.select(func.mean(col(attributeToShow)).alias('mean'), func.stddev(col(attributeToShow)).alias('std')).collect()

    mean = df_stats[0]['mean']
    std = df_stats[0]['std']

    print("Mean of given column:");
    print(mean);
    
    print("Standard deviation of given column:");
    print(std);
    
    spark.stop()

    return None
    
if __name__ == '__main__':
    main()
