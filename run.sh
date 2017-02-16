#Removes previous output
hadoop fs -rm -r /output_openrefine
#Run the hadoop job using jar file and sets mapping = 3
hadoop jar hadoop-streaming-2.6.0-cdh5.8.0.jar -D mapred.map.tasks=3 -file ./data/header.csv -file ./refine.mod -file ./requests.mod -file ./operations.json -file ./map.py  -mapper "map.py" -file ./reduce.py -reducer "reduce.py" -input /input_openrefine -output /output_openrefine
#Generate the output to ./data/output.csv
hadoop fs -getmerge /output_openrefine ./data/output_tmp.csv
awk '!seen[$0]++' ./data/output_tmp.csv > ./data/output.csv
