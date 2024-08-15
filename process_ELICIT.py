import pandas as pd

def reorganize_csv(file_path):
    # Load the CSV file
    sheet_data = pd.read_csv(file_path)

    # Retain only the 'Title' column from the metadata
    metadata = sheet_data[['Title']]

    # Identify the data columns
    data_columns = sheet_data.columns[7:18]  # Assuming the first 7 columns are metadata

    # Initialize a dictionary to store the concatenated data with column names
    concatenated_data_dict = {}

    # Process each data column and its corresponding 'Supporting' and 'Reasoning' columns
    for i, data_col in enumerate(data_columns, start=1):
        # 'Supporting' and 'Reasoning' columns follow the data columns
        supporting_col = sheet_data.columns[17 + i * 2 - 1]
        reasoning_col = sheet_data.columns[17+ i * 2]

        # Concatenate the data, supporting, and reasoning for each row
        concatenated_col = sheet_data[data_col].astype(str) + ";\n Context: \n" + \
                           sheet_data[supporting_col].astype(str) #+ ";\n Reasoning Context: \n" + \
                          # sheet_data[reasoning_col].astype(str)
        
        # Store the concatenated data in the dictionary with the data column name
        concatenated_data_dict[data_col] = concatenated_col

    # Create a new DataFrame with the concatenated data using the original data column names
    new_data_with_names = pd.DataFrame(concatenated_data_dict)

    # Combine the metadata and the new concatenated data
    reorganized_data_with_names = pd.concat([metadata, new_data_with_names], axis=1)

    return reorganized_data_with_names



# Replace 'your_file_path_here.xlsx' with your actual file path and 'YourSheetName' with your sheet name
file_path = 'CBFM/Extraction_Output/Elicit_raw.csv'
#sheet_name = 'YourSheetName'
reorganized_data = reorganize_csv(file_path)

# To view the first few rows of the reorganized data
print(reorganized_data.head())

# To save the reorganized data to a new Excel file
output_file_path = 'CBFM/Extraction_Output/Elicit_processed.csv'
reorganized_data.to_csv(output_file_path, index=False)
