# ParallelRefine
# Author: 
	Original by Dhruv Chand, Sai Teja, SoMi Choi
	Currently Improving by SoMi Choi
# Open source System: 
	1. http://hadoop.apache.org/
	2. http://openrefine.org/
	3. https://github.com/PaulMakepeace/refine-client-py (Open Refine Client)

# Dataset 
	Has 21 field that is related to crime
	We have used from 600, 1200, .... 2,000,000 rows and
	tested the number of columns from 1, 10, 21.
	Inputs are test_600_21.csv, test_6000_21.csv (test_#rows_#fields.csv)
	Other csv files are temporary files that has change in indentation
	Note: big data sets were excluded due to huge file size
	We have measured the performance using localhost:8088 (hadoop ui tool)
	which includes the elapsed time in job submission
# How to run
	Prerequisite: OpenRefine and Refine client must be installed
	1. Download Hadoop and OpenRefine from url link
	2. Install 3. Open Refine client by following command (refer the 3.link)
		a. unzip refine-client-py-master.zip(in ParallelRefine directory it has the refine-client-py-master.zip in it)
		b. cd refine-client-py-master
		c. sudo pip install -r requirements.txt
		d. sudo python setup.py test (it is okay if 2 test fails it still works) Note. OpenRefine should be running first
		f. sudo python setup.py build
		e. sudo python setup.py install
	3. Run OpenRefine in the Downloaded OpenRefine directory 
	it should have 127.0.0.1:3333 running (Hadoop should be running too)
	4. sh load.sh
	5. sh run.sh (This will generate the URL)
	6. The output will be in the ./data/output.csv

NOTE: If you have problem running the program please email schoi388@gatech.edu
	Also please reference the screenshot attached in the report
