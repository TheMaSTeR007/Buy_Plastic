prod_link_status_query = '''CREATE TABLE IF NOT EXISTS prod_link_status (
                            id INT AUTO_INCREMENT PRIMARY KEY,
                            product_link VARCHAR(255) UNIQUE,
                            product_status VARCHAR(10) DEFAULT 'pending'
                            );'''

product_data_query = '''CREATE TABLE IF NOT EXISTS prod_data (
                        id INT AUTO_INCREMENT PRIMARY KEY,
                        product_name VARCHAR(255),
                        variant_name VARCHAR(255),
                        product_link VARCHAR(255),
                        product_price INT,
                        currency_symbol VARCHAR(10) DEFAULT '$',
                        product_sku_id VARCHAR(255),
                        product_stock INT,
                        product_bulk_rates JSON,
                        product_description TEXT,
                        product_advantages VARCHAR(255),
                        product_applications VARCHAR(255),
                        product_capabilities VARCHAR(255),
                        product_engraving_methods VARCHAR(255),
                        product_cautions TEXT,
                        product_specs JSON,
                        product_length_cut_tolerance VARCHAR(255)
                        );'''