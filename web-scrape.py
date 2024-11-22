# Import required packages
import sys
import numpy
from bs4 import BeautifulSoup
import pandas as pd
import time, re, requests

# Set pandas to show all cols when printing
pd.set_option('display.max_columns', None)

# Add urls of books to track prices of
urls = []
urls.append("https://www.indigo.ca/en-ca/intermezzo-a-novel/9780735281820.html")
urls.append('https://www.indigo.ca/en-ca/born-of-blood-and-ash-indigo-exclusive-edition-a-flesh-and-fire-novel/9781957568799.html')
urls.append('https://www.indigo.ca/en-ca/twenty-thousand-leagues-under-the-sea/9780141394930.html')

# Define header - this is sent with the GET request for the website to identify the request
header = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/129.0.0.0 Safari/537.36'}

# Create empty list to add books and prices to
df = []

# Create function to pull price from the website
def get_price(url):

    # Send GET request to website
    response_i = requests.get(url, header)

    # Check status - stop code if this does not equal 200
    if response_i.status_code == 200:
        print("Good Request")
    else:
        sys.exit("Bad Request - Code terminated")

    # Read HTML code from the request
    indigo_soup = BeautifulSoup(response_i.text, 'html.parser')

    # Extract title and author from the HTML code
    title = indigo_soup.find('h1', class_="product-name font-weight-mid").text
    author = indigo_soup.find('span', class_="contributor__name").text

    # Is the book on sale?
    on_sale = indigo_soup.find('span', class_="price-wrapper").find('del')

    # We will look to see if a specific span exists in the html
    # If it does not exist the book is not on sale and if it does exist then it is on sale
    if on_sale is None:
        sale = "No"
        price = indigo_soup.find('span', class_="sales sale-false").find('span', class_="value").text
        normal_price = price
    else:
        sale = "Yes"
        price = indigo_soup.find('span', class_="sales sale-true").find('span', class_="value").text
        normal_price = indigo_soup.find('span', class_="price-wrapper").find('del').find('span', class_="value").text
        normal_price = re.sub(r"Price reduced from|to", "", normal_price)

    # Clean values and add them into a list

    # Select vars to keep
    to_add = [title, author, price, sale, normal_price, url]
    # Remove where there are new lines in the values extracted
    to_add_clean = [x.strip('\n') for x in to_add]

    # Return a list that will be added to a list with all books of interest
    return to_add_clean

# For each book url scrape the price from the website and add them to a list
for i in urls:
    df.append(get_price(i))
    # Add in a short pause to avoid being blocked with multiple requests
    time.sleep(0.5)

# This produces a list of lists
# We can convert list into a pandas dataframe for analysis
final = pd.DataFrame(df, columns = ["title", "author", "current_price", "on_sale", "normal_price", "url"])

# Create function to turn the price $ string into a float
def dols_to_val(dollars):
    parsed_string = re.sub(r'\$', '', dollars)
    return float(parsed_string)

# Apply function as lambda function to turn price into floats
# This will allow us to check if the price has changed
final_formatted = final.assign(
    current_price = lambda x: x['current_price'].map(lambda var: dols_to_val(var)),
    normal_price = lambda x: x['normal_price'].map(lambda var: dols_to_val(var))
)

# Now we check if the new prices scraped are different from the last time we scraped prices:

# Import previous prices dataset
old_prices = pd.read_csv("compare/old_prices.csv")[["title", "author", "old_price"]]
#final_formatted.to_csv("compare/old_prices.csv")

# Join old and new prices together
compare = pd.merge(final_formatted, old_prices,
                   how = "left", on = ["title", "author"])

# Define a function to check the old and new price and determine if the
# book is on sale and was not previously
def give_result(new, old, sale):

    if new == old:
        if sale == "No": res = "NO"
        else: res = "OLD"
    elif new < old:
        res = "NEW"
    else:
        res = "ERR"

    return res

# Vectorize this function to pass to compare
v_func = numpy.vectorize(give_result)

# Apply the vectorized function to each of the relevant columns
# and add this as a new column to the dataframe
compare["sale_test"] = v_func(compare["current_price"], compare["old_price"], compare["on_sale"])

#to_email = compare.query('sale_test == "NEW"')
to_email = compare.loc[compare.sale_test == "NEW"]

to_email["reduction"] = round((to_email["normal_price"] - to_email["current_price"])/to_email["normal_price"]*100)
to_email["change"] = to_email["reduction"].astype(str) + "%"

to_email_final = to_email[["title", "author", "current_price", "change", "url"]]

# Print final dataset
print(to_email_final)