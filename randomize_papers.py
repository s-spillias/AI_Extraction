import os
import random

directory = 'CBFM/pdfs'


# Get a list of all PDF files in the directory
pdf_files = [file for file in os.listdir(directory) if file.endswith('.pdf')]

# Randomly select 50 PDF files
selected_files = random.sample(pdf_files, 50)

# Rename the selected files
for file_name in selected_files:
    # Define the old and new file paths
    old_file_path = os.path.join(directory, file_name)
    new_file_name = "_" + file_name
    new_file_path = os.path.join(directory, new_file_name)
    
    # Rename the file
    os.rename(old_file_path, new_file_path)

print(f"Renamed {len(selected_files)} files.")

# Get a list of all files that start with '_'
prefixed_files = [file for file in os.listdir(directory) if file.startswith('_')]

# Randomly select 3 of those files
selected_files_for_p = random.sample(prefixed_files, 3)

# Rename the selected files by appending 'p' to the filename
for file_name in selected_files_for_p:
    # Define the old and new file paths
    old_file_path = os.path.join(directory, file_name)
    # Insert 'p' before the file extension
    name_part, extension = os.path.splitext(file_name)
    new_file_name = f"00_{name_part}{extension}"
    new_file_path = os.path.join(directory, new_file_name)
    
    # Rename the file
    os.rename(old_file_path, new_file_path)

print(f"Appended 'p' to {len(selected_files_for_p)} files.")