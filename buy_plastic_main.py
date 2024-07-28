import gzip, hashlib, os, requests, pymysql
from lxml import html
from table_queries import prod_link_status_query

start = 1
end = 45


def req_sender(url: str, method: str) -> bytes or None:
    # Prepare headers for the HTTP request

    # Send HTTP request
    _response = requests.request(method=method, url=url)
    # Check if response is successful
    if _response.status_code != 200:
        print(f"HTTP Status code: {_response.status_code}")  # Print status code if not 200
        return None
    return _response  # Return the response if successful


def ensure_dir_exists(path: str):
    # Check if directory exists, if not, create it
    if not os.path.exists(path):
        os.makedirs(path)
        print(f'Directory {path} Created')  # Print confirmation of directory creation


def page_checker(url: str, method: str, directory_path: str):
    # Create a unique hash for the URL to use as the filename
    page_hash = hashlib.sha256(string=url.encode(encoding='UTF-8', errors='backslashreplace')).hexdigest()
    ensure_dir_exists(path=directory_path)  # Ensure the directory exists
    file_path = os.path.join(directory_path, f"{page_hash}.html.gz")  # Define file path
    if os.path.exists(file_path):  # Check if the file already exists
        print("File exists, reading it...")  # Notify that the file is being read
        print(f"Filename is {page_hash}")
        with gzip.open(filename=file_path, mode='rb') as file:
            file_text = file.read().decode(encoding='UTF-8', errors='backslashreplace')  # Read and decode file
        return file_text  # Return the content of the file
    else:
        print("File does not exist, Sending request & creating it...")  # Notify that a request will be sent
        _response = req_sender(url=url, method=method)  # Send the HTTP request
        if _response is not None:
            print(f"Filename is {page_hash}")
            with gzip.open(filename=file_path, mode='wb') as file:
                if isinstance(_response, str):
                    file.write(_response.encode())  # Write response if it is a string
                    return _response
                file.write(_response.content)  # Write response content if it is bytes
            return _response.text  # Return the response text


class Scraper():
    def __init__(self):
        # Connecting to the Database
        connection = pymysql.connect(host='localhost', user='root', database='buy_plastic_db', password='actowiz', charset='utf8mb4', autocommit=True)
        if connection.open:
            print('Database connection Successful!')
        else:
            print('Database connection Un-Successful.')
        self.cursor = connection.cursor()
        try:
            self.cursor.execute(query=prod_link_status_query)
        except Exception as e:
            print(e)

        self.cat_page1_url = 'https://buyplastic.com/categories?page=1'

        # Creating Saved Pages Directory for this Project if not Exists
        project_name = 'Buy_Plastic'

        self.project_files_dir = f'C:\\Project Files\\{project_name}_Project_Files'
        ensure_dir_exists(path=self.project_files_dir)

    def scrape(self):
        page_1_response = page_checker(url=self.cat_page1_url, method='GET', directory_path=os.path.join(self.project_files_dir, 'Main_Pages'))

        parsed_html_page1 = html.fromstring(page_1_response)
        xpath_product_links = '//a[@class="card-figure__link"]/@href'
        prod_links_page1_list = parsed_html_page1.xpath(xpath_product_links)
        prod_links_list = list()
        prod_links_list.extend(prod_links_page1_list)

        xpath_page_2_link = '//a[@aria-label="Next"]/@href'
        next_page_link = parsed_html_page1.xpath(xpath_page_2_link)[0]
        page_2_response = page_checker(url=next_page_link, method='GET', directory_path=os.path.join(self.project_files_dir, 'Main_Pages'))
        parsed_html_page2 = html.fromstring(page_2_response)
        prod_links_page2_list = parsed_html_page2.xpath(xpath_product_links)
        prod_links_list.extend(prod_links_page2_list)

        # Inserting into DB Table
        for prod_link in prod_links_list:
            insert_query = f'''INSERT INTO `prod_link_status` (product_link)
                                VALUES (%s);'''
            try:
                self.cursor.execute(insert_query, args=(prod_link,))
            except Exception as e:
                print(e)

        # Reading links from DB Table
        select_query = f'''SELECT * FROM prod_link_status WHERE product_status = 'pending' and id between {start} and {end};'''
        self.cursor.execute(select_query)
        product_links_list = self.cursor.fetchall()
        for prod_tuple in product_links_list:
            prod_id = prod_tuple[0]
            prod_link = prod_tuple[1]
            page_checker(url=prod_link, method='GET', directory_path=os.path.join(self.project_files_dir, 'products_pages'))

            # Updating status of each product_link
            update_query = f'''UPDATE prod_link_status SET product_status = 'Done' WHERE id = {prod_id};'''
            self.cursor.execute(update_query)
        print('Saved all product pages!')


Scraper().scrape()
