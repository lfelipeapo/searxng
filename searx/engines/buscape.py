# SPDX-License-Identifier: AGPL-3.0-or-later
"""This is the implementation of the Buscapé shopping engine."""

from typing import TYPE_CHECKING
import re
from urllib.parse import urlencode
from lxml import html
from searx.utils import extract_text, eval_xpath, eval_xpath_list, eval_xpath_getindex
from searx.network import get
from searx.enginelib.traits import EngineTraits

if TYPE_CHECKING:
    import logging
    logger: logging.Logger

traits: EngineTraits

# about
about = {
    "website": 'https://www.buscape.com.br',
    "wikidata_id": 'Q674240',
    "use_official_api": False,
    "require_api_key": False,
    "results": 'HTML',
}

categories = ['shopping']
paging = True
max_page = 50

# specific xpath variables
results_xpath = './/div[contains(@class, "ProductCard_ProductCard")]'
title_xpath = './/h2[contains(@class, "ProductCard_ProductCard_Name")]'
href_xpath = './/a[contains(@class, "ProductCard_ProductCard_Inner")]/@href'
price_xpath = './/p[contains(@class, "ProductCard_ProductCard_Price")]'
description_xpath = './/div[contains(@class, "ProductCard_ProductCard_Description")]'
image_xpath = './/img[contains(@class, "ProductCard_ProductCard_Image")]/@src'
brand_xpath = './/span[contains(@class, "ProductCard_ProductCard_Brand")]'
installment_xpath = './/span[contains(@class, "ProductCard_ProductCard_Installment")]'
review_score_xpath = './/div[contains(@class, "ProductCard_ProductCard_Rating")]//text()'


def request(query, params):
    offset = (params['pageno'] - 1) * 10
    query_url = (
        'https://www.buscape.com.br/search'
        + "?"
        + urlencode({'q': query, 'page': offset})
    )
    params['url'] = query_url
    return params


def response(resp):
    results = []
    dom = html.fromstring(resp.text)
    
    for result in eval_xpath_list(dom, results_xpath):
        try:
            title = extract_text(eval_xpath_getindex(result, title_xpath, 0))
            url = eval_xpath_getindex(result, href_xpath, 0, None)
            price = extract_text(eval_xpath_getindex(result, price_xpath, 0))
            description = extract_text(eval_xpath_getindex(result, description_xpath, 0))
            image = eval_xpath_getindex(result, image_xpath, 0, None)
            brand = extract_text(eval_xpath_getindex(result, brand_xpath, 0))
            installment = extract_text(eval_xpath_getindex(result, installment_xpath, 0))
            review_score = extract_text(eval_xpath_getindex(result, review_score_xpath, 0))
            
            results.append({
                'title': title,
                'url': url,
                'price': price,
                'description': description,
                'image': image,
                'brand': brand,
                'installment': installment,
                'review_score': review_score,
            })
        except Exception as e:
            logger.error(e, exc_info=True)
            continue

    return results
