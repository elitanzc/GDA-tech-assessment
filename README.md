# GDA-assignment
 Take-home Assignment for Data Engineer Intern

# How to run
## Installation
1. MongoDB needs to be installed, as it will be used for storing and querying data (https://www.mongodb.com/docs/manual/administration/install-community/)
2. Pymongo and Pandas need to be installed too. To install, run command:
```
pip3 install pymongo pandas
```
## Running code
Download both `Country-Code.xlsx` and `code.py` into the same folder, then navigate to the folder in Terminal, and run:
```
python3 code.py
```
## Output
1. Running the code will create a database named **Restaurants** in MongoDB locally, containing 2 collections **restaurants** and **countrycode**.
2. The following CSV files will also be saved into the same folder where `code.py` is:
    * restaurants.csv
    * restaurant_events.csv

    (\* Note: The *Photo URL* field in restaurant_events.csv is assumed to be the URL of the first photo of the event if any, as some events have multiple photos.)
3. The thresholds for the ratings will be printed in the Terminal after running the code.