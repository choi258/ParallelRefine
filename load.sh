hadoop fs -rm -r /input_openrefine
hadoop fs -rm -r /output_openrefine
python loadData.py
hadoop fs -put ./data/input.csv /input_openrefine

