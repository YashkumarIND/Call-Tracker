from app import app
from models.models import db
from models.models import ScripCode
import csv
import ast
import json

# Define the path to the data file
data_file = 'scripcode.txt'

# Open the application context
with app.app_context():
    # Read data from the text file and populate the ScripCode table
    with open(data_file, 'r') as file:
        reader = csv.reader(file)
        header = next(reader)  # Skip the header row
        for row in reader:
            # Extract data from the row
            scrip_code = int(row[0])
            tick_size = float(row[1])
            inst_type = row[2]
            company_name = row[3]
            indices_str = row[4]
            industry = row[5]
            isin_code = row[6]
            trading_symbol = row[7]

            # Convert the indices string to a list
            indices = ast.literal_eval(indices_str)

            # Convert indices list to a JSON string
            indices_json = json.dumps(indices)

            # Create a new instance of the ScripCode model
            new_scrip_code = ScripCode(
                scrip_code=scrip_code,
                tick_size=tick_size,
                inst_type=inst_type,
                company_name=company_name,
                indices=indices_json,  # Use the JSON string
                industry=industry,
                isin_code=isin_code,
                trading_symbol=trading_symbol
            )

            # Add the new instance to the session and commit
            db.session.add(new_scrip_code)
            db.session.commit()

print("Data successfully inserted into the database.")
