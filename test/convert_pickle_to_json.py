import gzip
import pickle
import json
import pandas as pd  # Ensure pandas is imported
import sys

# Get the input and output file names from the command line arguments
pickle_file = sys.argv[1]
json_file = sys.argv[2]

# Load the gzipped pickle file
with gzip.open(pickle_file, 'rb') as f:
    data = pickle.load(f)

# Print data type and some content for debugging
print(f"Data type: {type(data)}")
if isinstance(data, pd.DataFrame):
    print("DataFrame head:", data.head())
    # Convert DataFrame to a dictionary
    data = data.to_dict(orient='records')
else:
    print("Data sample:", str(data)[:500])  # Print a sample of the data

# Try to convert the data to JSON and handle potential errors
try:
    with open(json_file, 'w') as f:
        json.dump(data, f, ensure_ascii=False, indent=4)
except (TypeError, OverflowError) as e:
    print(f"Error converting data to JSON: {e}")
    sys.exit(1)