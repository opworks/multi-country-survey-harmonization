import os
import pandas as pd
import re

# Define the folder containing the Excel files
folder_path = "C:\\Users\\jidea\\Downloads\\USA"
output_file = os.path.join(folder_path, "Master_Survey_Data_USA_NS_PI_Fixed.xlsx")

# Define the specific sheets to check
specific_sheets_to_check = [
    "Table 196", "Table 197"
]

# Regex pattern to extract country name from the filename
country_pattern = re.compile(r"P030045_89up_European_Poll_(.*?)_wtd_Tables")

# Define **fixed** age group headers
age_group_columns = ["18-24", "25-34", "35-44", "35+","45+","45-54", "55-64", "55+","65+", "NET: 18-34", "NET: 35-54", "NET: 35+", "NET: 55+"]

# Define master column structure (including Question column)
master_columns = ["Country", "Sheet", "Metric/Question", "Total Resp", "Male", "Female"] + age_group_columns

# List to store extracted data
all_data = []

# Loop through all Excel files in the folder
for file in os.listdir(folder_path):
    if file.endswith(".xlsx") and not file.startswith("~$"):  # Ignore temporary files
        file_path = os.path.join(folder_path, file)

        try:
            # Extract country name from file name using regex
            match = country_pattern.search(file)
            country = match.group(1) if match else "Unknown"

            print(f"\nProcessing file: {file} | Country: {country}")

            # Load workbook
            xls = pd.ExcelFile(file_path, engine="openpyxl")
            sheets_to_check = [sheet for sheet in xls.sheet_names if sheet in specific_sheets_to_check]

            if not sheets_to_check:
                continue

            for sheet in sheets_to_check:
                try:
                    df = pd.read_excel(xls, sheet_name=sheet, header=None)

                    # Ensure the sheet has enough rows to extract headers
                    if len(df) <= 6:
                        print(f"⚠️ Skipping {sheet} in {file} - Not enough rows")
                        continue

                    # Extract headers from C7:N7 (Row index 6, Columns C-N)
                    headers = df.iloc[6, 2:14].dropna().tolist()

                    # Fix positions for known response columns (Total, Male, Female)
                    response_positions = {
                        "Total Resp": 2,  # Column C
                        "Male": 3,  # Column D
                        "Female": 4,  # Column E
                    }

                    # Map fixed age group columns to actual positions if they exist in the sheet
                    age_column_positions = {col: (headers.index(col) + 2 if col in headers else None) for col in age_group_columns}

                    # Extract values for **B9 and B10** to be used as column headers
                    column_name_1 = df.iloc[8, 1] if len(df) > 8 and not pd.isna(df.iloc[8, 1]) else "Unknown_1"
                    column_name_2 = df.iloc[9, 1] if len(df) > 9 and not pd.isna(df.iloc[9, 1]) else "Unknown_2"

                    # Extract data for **B9 and B10 only**
                    for row, column_name in zip([8, 9], [column_name_1, column_name_2]):
                        try:
                            # Extract responses based on fixed positions
                            responses = {
                                "Total Resp": df.iloc[row, response_positions["Total Resp"]] if len(df.columns) > response_positions["Total Resp"] else "N/A",
                                "Male": df.iloc[row, response_positions["Male"]] if len(df.columns) > response_positions["Male"] else "N/A",
                                "Female": df.iloc[row, response_positions["Female"]] if len(df.columns) > response_positions["Female"] else "N/A",
                            }

                            # Extract values for the fixed age groups (use actual positions if available)
                            for age_group in age_group_columns:
                                responses[age_group] = (
                                    df.iloc[row, age_column_positions[age_group]]
                                    if age_column_positions[age_group] is not None and len(df.columns) > age_column_positions[age_group]
                                    else "N/A"
                                )

                            # Append data to master list
                            all_data.append([country, sheet, column_name] + list(responses.values()))

                        except Exception as e:
                            print(f"⚠️ Error processing B9/B10 in {sheet} of {file}: {e}")

                    # Extract **Questions from B11 Onward**
                    for row in range(10, df.shape[0]):  # Start from row index 10 (B11)
                        try:
                            question = df.iloc[row, 1]

                            # Check if columns C to N have at least one non-empty value (valid responses)
                            if isinstance(question, str) and not df.iloc[row, 2:14].isnull().all():
                                responses = {
                                    "Total Resp": df.iloc[row, response_positions["Total Resp"]] if len(df.columns) > response_positions["Total Resp"] else "N/A",
                                    "Male": df.iloc[row, response_positions["Male"]] if len(df.columns) > response_positions["Male"] else "N/A",
                                    "Female": df.iloc[row, response_positions["Female"]] if len(df.columns) > response_positions["Female"] else "N/A",
                                }

                                # Extract values for age groups
                                for age_group in age_group_columns:
                                    responses[age_group] = (
                                        df.iloc[row, age_column_positions[age_group]]
                                        if age_column_positions[age_group] is not None and len(df.columns) > age_column_positions[age_group]
                                        else "N/A"
                                    )

                                # Append question data to master list
                                all_data.append([country, sheet, question] + list(responses.values()))

                        except Exception as e:
                            print(f"⚠️ Error processing question at row {row} in {sheet} of {file}: {e}")

                except Exception as e:
                    print(f"⚠️ Error processing sheet {sheet} in {file}: {e}")

        except Exception as e:
            print(f"⚠️ Skipping file {file} due to error: {e}")

# Convert extracted data into a DataFrame
output_df = pd.DataFrame(all_data, columns=master_columns)

# Save to an Excel file
output_df.to_excel(output_file, index=False)

print(f"\n✅ Data extraction complete. Output saved to: {output_file}")
