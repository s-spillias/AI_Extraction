import os
import random

# Your directory path goes here
directory_path = 'CBFM/pdfs'

# Sorting the PDFs
underscore_files = []
non_underscore_files = []

# Walk through the directory
for filename in os.listdir(directory_path):
    if filename.endswith('.pdf'):
        if filename.startswith('_') and not filename.startswith('__'):
            underscore_files.append(filename)
        else:
            non_underscore_files.append(filename)

# Shuffle for randomness
random.shuffle(underscore_files)
random.shuffle(non_underscore_files)

# Divide files into 5 lists, trying to balance the counts
lists = [[] for _ in range(5)]
for i, filename in enumerate(underscore_files):
    lists[i % 5].append(filename)

for i, filename in enumerate(non_underscore_files):
    lists[i % 5].append(filename)

# Writing to CSV files
for i, pdf_list in enumerate(lists):
    with open(f'CBFM/full_text_assignments/pdf_list_{i+1}.csv', 'w', newline='', encoding='utf-8') as file:
        for pdf in pdf_list:
            file.write(f"{pdf}\n")

print("Equitable PDF distribution complete! Your CSV files are ready.")
