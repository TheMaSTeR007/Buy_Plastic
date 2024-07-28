import itertools
import gzip, hashlib, json, os, requests, pymysql
from lxml import html
from table_queries import prod_link_status_query, product_data_query

from sys import argv

start = argv[1]
end = argv[2]


def req_sender(url: str, method: str, cookies: dict = None, headers: dict = None, data: dict = None) -> bytes or None:
    # Send HTTP request
    _response = requests.request(method=method, url=url, cookies=cookies, headers=headers, data=data)
    # Check if response is successful
    if _response.status_code != 200:
        print(f"HTTP Status code: {_response.status_code}")  # Print status code if not 200
        return None
    return _response  # Return the response if successful


def ensure_dir_exists(path: str):
    # Check if directory exists, if not, create it
    if not os.path.exists(path):
        os.makedirs(path)
        print(f'Directory {path} Created.')  # Print confirmation of directory creation


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


def page_checker_json(url: str, method: str, directory_path: str, cookies: dict = None, headers: dict = None, data: dict = None):
    # Create a unique hash for the URL and data to use as the filename
    hash_input = url + json.dumps(data, sort_keys=True)  # Combine URL and data for hashing
    page_hash = hashlib.sha256(hash_input.encode('UTF-8')).hexdigest()
    ensure_dir_exists(path=directory_path)  # Ensure the directory exists
    file_path = os.path.join(directory_path, f"{page_hash}.json")  # Define file path

    if os.path.exists(file_path):  # Check if the file already exists
        print("File exists, reading it...")  # Notify that the file is being read
        print(f"Filename is {page_hash}")
        with open(file_path, 'r', encoding='UTF-8') as file:
            file_text = file.read()  # Read the file
        return json.loads(file_text)  # Return the content as a dictionary

    else:
        print("File does not exist, Sending request & creating it...")  # Notify that a request will be sent
        _response = req_sender(url=url, method=method, cookies=cookies, headers=headers, data=data)  # Send the POST request

        if _response is not None:
            response_json = _response.json()  # Get the JSON response
            print(f"Filename is {page_hash}")
            with open(file_path, 'w', encoding='UTF-8') as file:
                json.dump(response_json, file, ensure_ascii=False, indent=4)  # Write JSON response to file
            return response_json  # Return the JSON response as a dictionary


class Scraper:
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
            self.cursor.execute(query=product_data_query)
        except Exception as e:
            print(e)

        # Creating Saved Pages Directory for this Project if not Exists
        project_name = 'Buy_Plastic'

        self.project_files_dir = f'C:\\Project Files\\{project_name}_Project_Files'
        ensure_dir_exists(path=self.project_files_dir)

    def scrape(self):
        # Reading links from DB Table
        select_query = f'''SELECT * FROM prod_link_status WHERE product_status = 'pending' and id between {start} and {end};'''
        self.cursor.execute(select_query)
        product_links_list = self.cursor.fetchall()
        count = 1
        for prod_tuple in product_links_list:
            product_id_sql = prod_tuple[0]
            product_link = prod_tuple[1]
            this_product_html = page_checker(url=product_link, method='GET', directory_path=os.path.join(self.project_files_dir, 'products_pages'))
            parsed_html = html.fromstring(this_product_html)

            # Getting data available from page using Xpath
            product_name = ' '.join(parsed_html.xpath('//h1[@class="productView-title"]/text()'))
            print('Product Name: ', product_name)
            product_id = ' '.join(parsed_html.xpath('//body/@class')).rstrip()[31:]
            print('Product Id: ', product_id)
            print('Product Link: ', product_link)
            product_description_ = ' '.join(parsed_html.xpath('//div[@class="productView-description"]/p/text()'))
            product_description = product_description_ if product_description_ else 'N/A'
            product_engraving_methods_ = ', '.join(parsed_html.xpath('//h3[contains(text(), "Engraving Methods")]/following-sibling::ul[1]/li/text()'))
            product_engraving_methods = product_engraving_methods_ if product_engraving_methods_ else "N/A"
            product_advantages_ = ', '.join(parsed_html.xpath('//h3[contains(text(), "Advantages")]/following-sibling::ul[1]/li/text()'))
            product_advantages = product_advantages_ if product_advantages_ else 'N/A'
            product_applications_ = ', '.join(parsed_html.xpath('//h3[contains(text(), "Applications")]/following-sibling::ul[1]/li/text()'))
            product_applications = product_applications_ if product_applications_ else 'N/A'
            product_capabilities_ = ', '.join(parsed_html.xpath("//h3[contains(text(), 'Capabilites')]/following-sibling::ul[1]/li/text()"))
            product_capabilities = product_capabilities_ if product_capabilities_ else 'N/A'
            product_cautions_ = ', '.join(parsed_html.xpath('//p/em/text()'))
            product_cautions = product_cautions_ if product_cautions_ else 'N/A'
            specs_name_list = parsed_html.xpath('//div[@class="specsTable"]//tbody/tr/td[@class="specs-info-name"]/text()')
            specs_values_list = parsed_html.xpath('//div[@class="specsTable"]//tbody/tr/td[@class="specs-info-name"]/text()')
            product_specs_ = {key: value for (key, value) in zip(specs_name_list, specs_values_list)}
            product_specs = json.dumps(product_specs_) if product_specs_ else json.dumps({'N/A': 'N/A'})
            product_length_cut_tolerance_ = ' '.join(parsed_html.xpath('//strong[contains(text(), "Length Cut Tolerance")]/text()'))
            product_length_cut_tolerance = product_length_cut_tolerance_ if product_length_cut_tolerance_ else 'N/A'

            variant_tags = parsed_html.xpath('//div[@data-product-attribute="set-rectangle"]')
            id_list = [id_tags.xpath('./div[@class="form-option-wrapper"]//@name') for id_tags in variant_tags]
            values_list = [values_tags.xpath('./div[@class="form-option-wrapper"]//@value') for values_tags in variant_tags]
            label_values_list = [value_tags.xpath('./div[@class="form-option-wrapper"]//span/text()') for value_tags in variant_tags]
            print('id list : ', id_list)
            print('value list: ', values_list)
            print('Label Value list: ', label_values_list)

            cookies = {
                'fornax_anonymousId': '9ce863f0-1b3d-41a4-8296-af3718e59b7c',
                'SF-CSRF-TOKEN': 'e0dff87a-b0af-49a1-8124-cfc29341cc44',
                'XSRF-TOKEN': '5e0b28eff8517625b2b1b7a5756e39f508c693bea7abbc3a8a0702960cf4018d',
                'SHOP_SESSION_TOKEN': '48f5f2ae-462e-4bbf-a5fa-a8d893e1408f',
                '_gcl_au': '1.1.1630085230.1721279517',
                '_fbp': 'fb.1.1721279517915.695573788580814131',
                'lastVisitedCategory': '0',
                '_gid': 'GA1.2.102200525.1721574549',
                'STORE_VISITOR': '1',
                'athena_short_visit_id': '1698289e-2248-4a78-907a-2eb49f20110c:1721621931',
                '_clck': 'hw2ucc%7C2%7Cfno%7C0%7C1660',
                '__cf_bm': 'XVxGTxAeRFE17JA6hw8eW1ELHI5ix3oltYvR3Cu3_Ds-1721623107-1.0.1.1-e3Wefy7V.LRRtDGtPIV6ekrXP7vL06IoJe0zXFIJod8eeSO0wUI5jM33t.hOZNJZR5UjfGXrPzwvYppA167B2Q',
                '_ga': 'GA1.1.1053635303.1721279516',
                '_uetsid': '2e91c4b0477311efa22d7de2d1bdea19',
                '_uetvid': '415258c044c411efaef7d9656d9e869e',
                '_ga_YBZ6F6339N': 'GS1.1.1721621934.15.1.1721623135.0.0.0',
                'Shopper-Pref': 'AC951E22F0D8B45F88241A0F5EC7A0D61CB1452B-1722228019663-x%7B%22cur%22%3A%22USD%22%7D',
                '_ga_50BLGJTDSB': 'GS1.1.1721621934.14.1.1721623311.60.0.0',
                '_clsk': '9suv6d%7C1721624618816%7C7%7C1%7Cv.clarity.ms%2Fcollect',
            }

            headers = {
                'accept': '*/*',
                'accept-language': 'en-US,en;q=0.9',
                'content-type': 'application/x-www-form-urlencoded; charset=UTF-8',
                'origin': 'https://buyplastic.com',
                'priority': 'u=1, i',
                'referer': 'https://buyplastic.com/acetal-copolymer-plastic-sheet-various-sizes-and-colors/',
                'sec-ch-ua': '"Not/A)Brand";v="8", "Chromium";v="126", "Google Chrome";v="126"',
                'sec-ch-ua-mobile': '?0',
                'sec-ch-ua-platform': '"Windows"',
                'sec-fetch-dest': 'empty',
                'sec-fetch-mode': 'cors',
                'sec-fetch-site': 'same-origin',
                'stencil-config': '{}',
                'stencil-options': '{"render_with":"products/bulk-discount-rates"}',
                'user-agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/126.0.0.0 Safari/537.36',
                'x-requested-with': 'stencil-utils',
                'x-sf-csrf-token': 'e0dff87a-b0af-49a1-8124-cfc29341cc44',
                'x-xsrf-token': '5e0b28eff8517625b2b1b7a5756e39f508c693bea7abbc3a8a0702960cf4018d',
            }

            counter = 1
            for id_comb, value_comb, variant_comb in zip(itertools.product(*id_list), itertools.product(*values_list), itertools.product(*label_values_list)):
                print(id_comb)
                print(value_comb)
                variant_name = product_name[0] + '-' + '-'.join(variant_comb)
                post_data = dict()
                for key in range(len(id_comb)):
                    post_data[id_comb[key]] = value_comb[key]
                print('Variant Name:', variant_name.rstrip())

                # POST DATA Dict is ready to send in POST request...
                post_data.update((('product_id', product_id), ('qty[]', '1')))
                print('Post Data: ', post_data)

                post_response = page_checker_json(url=f'https://buyplastic.com/remote/v1/product-attributes/{product_id}', method='POST', cookies=cookies, headers=headers, data=post_data, directory_path=os.path.join(self.project_files_dir, 'variant_pages'))
                print(post_response)
                json_response = post_response
                sql_data = dict()
                sql_data['product_name'] = product_name
                sql_data['variant_name'] = variant_name
                sql_data['product_link'] = product_link
                sql_data['product_price'] = json_response.get('data').get('price').get('without_tax').get('value')
                sql_data['product_sku_id'] = json_response.get('data').get('sku')
                sql_data['product_stock'] = json_response.get('data').get('stock')
                sql_data['product_bulk_rates'] = json.dumps(json_response.get('data').get('bulk_discount_rates'))
                sql_data['product_description'] = product_description
                sql_data['product_advantages'] = product_advantages
                sql_data['product_applications'] = product_applications
                sql_data['product_capabilities'] = product_capabilities
                sql_data['product_engraving_methods'] = product_engraving_methods
                sql_data['product_cautions'] = product_cautions
                sql_data['product_specs'] = product_specs
                sql_data['product_length_cut_tolerance'] = product_length_cut_tolerance

                # Inserting into Database
                print('Storing into Database')
                cols = sql_data.keys()
                rows = sql_data.values()
                insert_query = f'''INSERT INTO `prod_data` ({', '.join(tuple(cols))}) VALUES ({('%s, ' * len(sql_data)).rstrip(", ")});'''
                try:
                    self.cursor.execute(query=insert_query, args=tuple(rows))
                except Exception as e:
                    print(e)
                print(counter)
                counter += 1
                print('-' * 30)

            print(f'{count}th product done...')
            count += 1
            # Updating status of each product_link
            update_query = f'''UPDATE prod_link_status SET product_status = 'Done' WHERE id = {product_id_sql};'''
            self.cursor.execute(update_query)


Scraper().scrape()
