The file include project3.py and input.csv where:
	project3.py: implements the command-line B-tree using 512-byte blocks, it has a max key of 19 and max children of 20. In BTreeNode class, I implemented serialize() to convert nodes into binary and deserialize() to read nodes from binary. In BTreeIndex, I implemented create(), insert(), search(), print_all() to perform operations with the nodes, extract() to exports all key-value pairs to a csv file and load_from_csv() to load key-value pairs from csv file. In main(), I parse the command-line arguments and call the functions.
	input.csv: includes the test and results from executing the project3.py file.


This is my testing commands:
➜  4348-project-3 git:(main) python3 project3.py create test.idx
Created index file test.idx
➜  4348-project-3 git:(main) ✗ python3 project3.py insert test.idx 15 100
Inserted root key 15, value 100 into block 1
➜  4348-project-3 git:(main) ✗ python3 project3.py search test.idx 15 
Found: key=15, value=100
➜  4348-project-3 git:(main) ✗ python3 project3.py load test.idx input.csv
Inserted key 3, value 30 into root node
Inserted key 5, value 50 into root node
Inserted key 8, value 80 into root node
Loaded data from input.csv


I don’t know why my zip file does not have .git file where the commits can be seen, but I have 15 commits in total and this is the github link for the project: https://github.com/ngocphatle17/4348-project-3.git

I apologize if this creates any inconvenience!
