docker exec -it namenode hdfs dfs -test -e /data
if [ $? -eq 1 ] #ako ne postoji
then
  docker exec -it namenode hdfs dfs -mkdir /data
fi

docker exec -it namenode hdfs dfs -test -e /data/feds.csv
if [ $? -eq 1 ]
then
  docker exec -it namenode hdfs dfs -copyFromLocal /data/feds.csv /data/feds.csv
fi
