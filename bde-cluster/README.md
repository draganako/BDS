## Struktura projekta

Projekat predstavlja aplikaciju napisanu u programskom jeziku Python, koja analizira podatke o letovima širom Amerike. Aplikacija se izvršava na klasteru Docker kontejnera koji se pokreću na osnovu [image-a datih od strane BDE Europe](https://github.com/big-data-europe/docker-spark).
Struktura projekta se može videti u nastavku. U folderu `app` nalazi se aplikacija sa svojim docker fajlom, potrebnim komponentama za instalaciju i shell skriptom za njeno pokretanje.
Folder `infrastructure` definiše infrastrukturu klastera i u njemu se nalazi folder `data`, iz koga se učitavaju podaci (`feds.csv`), spakovan pri postavljanju u arhivu zbog svoje veličine.
Skripte za pokretanje, zaustavljanje i postavljanje podataka na HDFS se takođe nalaze u folderu `infrastructure`, kao i `docker-compose.yml` i `hadoop.env`, koji određuju izgled klastera i njegove servise.
Potrebne zavisnosti se nalaze u datotekama `dependencies.txt` i `build_dependencies.txt`. Datoteka `docker-compose.yml` u okviru direktorijuma `bde-cluster` služi za definisanje submit kontejnera i image-a. 
U ovom direktorijumu se nalaze i skripte za pokretanje i zaustavljanje analize.

```bash
bde-cluster/
 |-- app/
 |   |--app.py
 |   |--Dockerfile
 |   |--requirements.txt
 |   |--start.sh
 |-- infrastructure/
 |---- data/
 |     |--feds.csv
 |     docker-compose.yml
 |     hadoop.env
 |     infra_start.sh
 |     infra_stop.sh
 |     infra_upload_to_hdfs.sh
 |analysis_start.sh
 |analysis_stop.sh
 |build_dependencies.sh
 |dependencies.txt
 |docker-compose.yml
 |stop_all.sh
```

## Korišćeni skup podataka

Podaci nad kojima treba izvršiti analizu preuzeti su sa [ove lokacije](https://github.com/BuzzFeedNews/2016-04-federal-surveillance-planes/tree/master/data/feds) i spojeni u fajl `feds.csv`, sa više od 120000 stavki. 
Ove stavke predstavljaju podatke prikupljene o praćenim letelicama u Americi u periodu od 4 meseca, pri čemu je [ovde](https://buzzfeednews.github.io/2016-04-federal-surveillance-planes/analysis.html) objašnjeno koja su značenja različitih tipova podataka koji su prisutni.
Prvu vrstu dokumenta čine nazivi odgovarajućih podataka, a ostale njihove vrednosti. 

## Infrastruktura

Aplikacija se izvršava na lokalnom klasteru Docker kontejnera, koji koriste `bde-spark image-e`.
Infrastruktura je opisana preko `docker-compose.yml` i sadrži Hadoop servise, kao sto su `namenode`, `datanote` i `resourcemanager`, i Spark servise – `pyspark-master` i dva worker čvora:
Definisana je i mreža `bde`, na kojoj se svi kontejneri nalaze.

```yaml
services:
  pyspark-master:
    image: bde2020/spark-master:3.1.1-hadoop3.2
    container_name: pyspark-master
    ...
  pyspark-worker-1:
    image: bde2020/spark-worker:3.1.1-hadoop3.2
    container_name: pyspark-worker-1
    ...
  pyspark-worker-2:
    image: bde2020/spark-worker:3.1.1-hadoop3.2
    container_name: pyspark-worker-2
    ...
  namenode:
    image: bde2020/hadoop-namenode:2.0.0-hadoop3.2.1-java8
    container_name: namenode
    ...
  datanode:
    image: bde2020/hadoop-datanode:2.0.0-hadoop3.2.1-java8
    container_name: datanode
    ...
  resourcemanager:
    image: bde2020/hadoop-resourcemanager:2.0.0-hadoop3.2.1-java8
    container_name: resourcemanager
    ...
  nodemanager1:
    image: bde2020/hadoop-nodemanager:2.0.0-hadoop3.2.1-java8
    container_name: nodemanager
    ...
  historyserver:
    image: bde2020/hadoop-historyserver:2.0.0-hadoop3.2.1-java8
    container_name: historyserver
    ...

volumes:
  hadoop_namenode:
  hadoop_datanode:
  hadoop_historyserver:

networks:
  default:
    external:
      name: bde
```

## "Submit" kontejner

Image pod nazivom `bde2020/spark-submit`, u kontejneru kome se dodeljuje sličan naziv, služi za slanje Python aplikacije na izvršenje na klasteru. 
Ovaj image i kontejner se definišu u `docker-compose.yml` fajlu `bde-cluster` direktorijuma. Definišu se i ime i port mastera, mreža na kojoj se ovaj kontejner nalazi (isto `bde`)
i lokacija nad kojom se vrši build (`./app/`). Takođe, potrebno je obezbediti korišćene zavisnosti u fajlovima `build_dependencies.txt` i `dependencies.txt` (kao što je Python verzija). 

```
version: "3"

services:
  submit:
    build: ./app/
    image: spark-submit:3.1.1-hadoop3.2
    container_name: analysis
    environment:
      SPARK_MASTER_NAME: pyspark-master
      SPARK_MASTER_PORT: 7067
      ENABLE_INIT_DAEMON: "false"

networks:
  default:
    external:
      name: bde
```

## Pokretanje infrastrukture i "submit" kontejnera
 
Najpre treba kreirati zajedničku mrežu za klaster (`bde`), a zatim pokrenuti definisanu infrastrukturu i postaviti `feds.csv` na HDFS (`infra_start.sh`).
Infrastruktura se može stopirati preko skripte `infra_stop.sh`. Nakon pokretanja infrastrukture, treba pokrenuti i prethodno pomenuti submit kontejner. 
Ovo se vrši preko `analysis_start.sh`, a takođe se poziva i `spark-submit` komanda i `spark-master` čvoru šalje Python aplikacija na izvršenje. 
U nastavku su date akcije koje odgovaraju prethodnom opisu.

* `$ docker network create bde`
* `$ cd infrastructure && ./infra_start.sh && ./infra_upload_to_hdfs.sh`
* `$ cd .. && ./analysis_start.sh`

Dockerfile određuje lokaciju aplikacije kao `/app/app.py` i vrednosti promenljivih okruženja, koje će se koristiti u šablonu, datom na [ovoj adresi](https://github.com/big-data-europe/docker-spark/blob/master/submit/submit.sh#L11). 
Pošto je u pitanju lokalni klaster, broj jezgara za izvršenje je postavljen na broj dostupnih, 1. Nakon postavljanja potrebnih promenljivih,
poziva se bash i u njemu izvršava datoteka `start.sh` (koja poziva pomenuti šablon).

```FROM bde2020/spark-python-template:3.1.1-hadoop3.2

ENV SPARK_MASTER spark://pyspark-master:7067
ENV SPARK_APPLICATION_PYTHON_LOCATION app/app.py
ENV SPARK_SUBMIT_ARGS "--total-executor-cores 1 --executor-cores 1 --conf spark.dynamicAllocation.enabled=false"
ENV SPARK_APP_ARG_DATE_FROM 2015-08-18T07:01:39Z
ENV SPARK_APP_ARG_DATE_TO 2015-08-18T07:58:39Z 
ENV SPARK_APP_ARG_LAT 33
ENV SPARK_APP_ARG_LON -118
ENV SPARK_APP_ARG_LAT_PRECISION 2
ENV SPARK_APP_ARG_LON_PRECISION 2
ENV SPARK_APP_ARG_ATTR_NAME "altitude"
ENV SPARK_APP_ARG_ATTR_VALUE 5500
ENV SPARK_APP_ARG_ATTR_TO_SHOW "speed"

ENV HDFS_ROOT hdfs://namenode:9000
ENV HDFS_DATASET_PATH /data/
EXPOSE 7067 9000
  
ADD start.sh /

RUN chmod +x /start.sh

CMD ["/bin/bash", "/start.sh"]
```

## Aplikacija

Aplikacija je napisana u programskom jeziku Python. Najpre treba ubaciti sve potrebne zavisnosti (uglavnom iz biblioteke `pyspark` za rad sa Spark-om). Zatim se poziva main funkcija, gde se kreira Spark sesija i šema, koja definiše naziv i tip podataka, na osnovu koje će se oni čitati. 
 Podaci se iz HDFS-a čitaju tako što se navede format datoteke koja se čita – `csv`, da li je prva linija datoteke header, zatim koji karakter razdvaja podatke (`;`). 
 Takođe se navodi prethodno definisana šema i lokacija na kojoj se fajl nalazi. 
 Opcija `timestampFormat` određuje format u kome je podatak koji se tumači kao `TimestampType` napisan u datoteci. 
 Podaci se smeštaju u data frame, `pyspark` jedinicu podataka koja sliči tabeli. Argumenti na osnovu kojih se vrši filtriranje i izračunavanje 
 su dati preko promenljivih okruženja i njihove vrednosti se učitavaju u određene promenljive. 
 Dobijeni data frame se filtrira po vremenskoj i lokacijskoj osnovi, kao i po vrednosti specificiranog atributa, preko funkcije `filter`. 
 Zatim se preko funkcije `groupBy` kreira data frame, gde se u jednoj koloni nalaze distinktne vrednosti zadatog atributa, a u drugoj brojevi njihovog pojavljivanja. 
 Na kraju se preko `sql` funkcija računaju minimum i maksimum odgovarajuće kolone i prikazuju, kao i njena prosečna vrednost i standardna devijacija.
