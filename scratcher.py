import itertools

import requests
from lxml import html

r = requests.get('https://buyplastic.com/products/ptfe-plastic-rod.html')

html_text = r.text
parsed_html = html.fromstring(html_text)

variant_tags = parsed_html.xpath('//div[@data-product-attribute="set-rectangle"]')
id_list = [id_tags.xpath('./div[@class="form-option-wrapper"]//@name') for id_tags in variant_tags]
values_list = [values_tags.xpath('./div[@class="form-option-wrapper"]//@value') for values_tags in variant_tags]
print(variant_tags)
print(id_list)
print(values_list)

label_values_list = [value_tags.xpath('./div[@class="form-option-wrapper"]//span/text()') for value_tags in variant_tags]
print(label_values_list)

product_name = parsed_html.xpath('//h1[@class="productView-title"]/text()')
print(product_name)

post_data = dict()
for id_comb, value_comb, variant_comb in zip(itertools.product(*id_list), itertools.product(*values_list), itertools.product(*label_values_list)):
    print(id_comb)
    print(value_comb)
    print(product_name[0] + '-' + '-'.join(variant_comb))

