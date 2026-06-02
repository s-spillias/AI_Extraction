from nltk import agreement
import xlrd
import glob
import pandas as pd

####################################
# Inter-rater reliability

def get_k(data):
    taskdata = []  # Create an empty list to hold the task data

        # Loop over each rater and their ratings
    for rater_id in range(len(data)):
       # print(rater_id)
        for item_id, rating in enumerate(data[rater_id]):
            taskdata.append([rater_id, str(item_id), str(rating)])

    ratingtask = agreement.AnnotationTask(data=taskdata)
    #print("kappa " +str(ratingtask.kappa()))
    print("fleiss " + str(ratingtask.multi_kappa()))
   # print("alpha " +str(ratingtask.alpha()))
 #   print("scotts " + str(ratingtask.pi()))

all_files = glob.glob("./Paper-Results/*kappa*")
#human = pd.read_csv(all_files[1])
# Get independent kappas
for file in all_files:
    print(file)
    data = pd.read_csv(file)
    data = [data[column] for column in data]
    if 'human' in file:
        human = data
    get_k(data)

# Get collaborative kappas
all_cols = pd.read_csv(all_files[0])
import copy
for column_name in all_cols:
    print(column_name)
    column_data = all_cols[column_name]
    join = copy.copy(human)
    join.append(column_data)
    get_k(join)