# SPDX-License-Identifier: AGPL-3.0-or-later
"""The XPath engine is a *generic* engine with which it is possible to configure
engines in the settings.

.. _XPath selector: https://quickref.me/xpath.html#xpath-selectors

Configuration
=============

Request:

- :py:obj:`search_url`
- :py:obj:`lang_all`
- :py:obj:`soft_max_redirects`
- :py:obj:`cookies`
- :py:obj:`headers`

Paging:

- :py:obj:`paging`
- :py:obj:`page_size`
- :py:obj:`first_page_num`

Time Range:

- :py:obj:`time_range_support`
- :py:obj:`time_range_url`
- :py:obj:`time_range_map`

Safe-Search:

- :py:obj:`safe_search_support`
- :py:obj:`safe_search_map`

Response:

- :py:obj:`no_result_for_http_status`

`XPath selector`_:

- :py:obj:`results_xpath`
- :py:obj:`url_xpath`
- :py:obj:`title_xpath`
- :py:obj:`description_xpath`
- :py:obj:`content_xpath`
- :py:obj:`price_xpath`
- :py:obj:`rating_xpath`
- :py:obj:`merchant_xpath`
- :py:obj:`image_xpath`
- :py:obj:`snippet_xpath`
- :py:obj:`brand_model_xpath`
- :py:obj:`installment_xpath`
- :py:obj:`cashback_xpath`
- :py:obj:`thumbnail_xpath`
- :py:obj:`suggestion_xpath`

"""

from urllib.parse import urlencode

from lxml import html
from searx.utils import extract_text, extract_url, eval_xpath, eval_xpath_list
from searx.network import raise_for_httperror

search_url = None
"""
Search URL of the engine.  Example::

    https://example.org/?search={query}&page={pageno}{time_range}{safe_search}

"""

lang_all = 'en'

no_result_for_http_status = []

soft_max_redirects = 0

# Definindo os campos adicionais
results_xpath = ''
url_xpath = None
title_xpath = None
description_xpath = None  # Adicionado o campo description_xpath
content_xpath = None
price_xpath = None  # Adicionado o campo price_xpath
rating_xpath = None  # Adicionado o campo rating_xpath
merchant_xpath = None  # Adicionado o campo merchant_xpath
image_xpath = None  # Adicionado o campo image_xpath
snippet_xpath = None  # Adicionado o campo snippet_xpath
brand_model_xpath = None  # Adicionado o campo brand_model_xpath
installment_xpath = None  # Adicionado o campo installment_xpath
cashback_xpath = None  # Adicionado o campo cashback_xpath
thumbnail_xpath = False
suggestion_xpath = ''

cached_xpath = ''
cached_url = ''

cookies = {}

headers = {}

paging = False

page_size = 1

first_page_num = 1

time_range_support = False

time_range_url = '&hours={time_range_val}'

time_range_map = {
    'day': 24,
    'week': 24 * 7,
    'month': 24 * 30,
    'year': 24 * 365,
}

safe_search_support = False

safe_search_map = {0: '&filter=none', 1: '&filter=moderate', 2: '&filter=strict'}

def request(query, params):
    '''Build request parameters (see :ref:`engine request`).'''
    lang = lang_all
    if params['language'] != 'all':
        lang = params['language'][:2]

    time_range = ''
    if params.get('time_range'):
        time_range_val = time_range_map.get(params.get('time_range'))
        time_range = time_range_url.format(time_range_val=time_range_val)

    safe_search = ''
    if params['safesearch']:
        safe_search = safe_search_map[params['safesearch']]

    fargs = {
        'query': urlencode({'q': query})[2:],
        'lang': lang,
        'pageno': (params['pageno'] - 1) * page_size + first_page_num,
        'time_range': time_range,
        'safe_search': safe_search,
    }

    params['cookies'].update(cookies)
    params['headers'].update(headers)

    params['url'] = search_url.format(**fargs)
    params['soft_max_redirects'] = soft_max_redirects

    params['raise_for_httperror'] = False

    return params

def response(resp):  # pylint: disable=too-many-branches
    '''Scrap *results* from the response (veja :ref:`engine results`).'''
    if no_result_for_http_status and resp.status_code in no_result_for_http_status:
        return []

    raise_for_httperror(resp)

    results = []
    dom = html.fromstring(resp.text)
    is_onion = 'onions' in categories

    if results_xpath:
        for result in eval_xpath_list(dom, results_xpath):

            # Extração dos novos elementos adicionados
            url = extract_url(eval_xpath_list(result, url_xpath, min_len=1), search_url)
            title = extract_text(eval_xpath_list(result, title_xpath, min_len=1))
            description = extract_text(eval_xpath_list(result, description_xpath))  # description_xpath
            content = extract_text(eval_xpath_list(result, content_xpath))
            price = extract_text(eval_xpath_list(result, price_xpath))  # price_xpath
            rating = extract_text(eval_xpath_list(result, rating_xpath))  # rating_xpath
            merchant = extract_text(eval_xpath_list(result, merchant_xpath))  # merchant_xpath
            image = extract_text(eval_xpath_list(result, image_xpath))  # image_xpath
            snippet = extract_text(eval_xpath_list(result, snippet_xpath))  # snippet_xpath
            brand_model = extract_text(eval_xpath_list(result, brand_model_xpath))  # brand_model_xpath
            installment = extract_text(eval_xpath_list(result, installment_xpath))  # installment_xpath
            cashback = extract_text(eval_xpath_list(result, cashback_xpath))  # cashback_xpath
            
            # Construir o dicionário de resultados com os novos elementos
            tmp_result = {
                'url': url,
                'title': title,
                'description': description,  # Adicionando description no resultado
                'content': content,
                'price': price,
                'rating': rating,
                'merchant': merchant,
                'image': image,
                'snippet': snippet,
                'brand_model': brand_model,
                'installment': installment,
                'cashback': cashback
            }

            # Adiciona thumbnail se disponível
            if thumbnail_xpath:
                thumbnail_xpath_result = eval_xpath_list(result, thumbnail_xpath)
                if len(thumbnail_xpath_result) > 0:
                    tmp_result['thumbnail'] = extract_url(thumbnail_xpath_result, search_url)

            if is_onion:
                tmp_result['is_onion'] = True

            results.append(tmp_result)

    logger.debug("found %s results", len(results))
    return results
