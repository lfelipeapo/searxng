# SPDX-License-Identifier: AGPL-3.0-or-later
"""The JSON engine is um engine genérico para configurar motores de busca no settings.
"""

from collections.abc import Iterable
from json import loads
from urllib.parse import urlencode
from searx.utils import to_string, html_to_text


search_url = None
url_query = None
url_prefix = ""
content_query = None
title_query = None
description_query = None  # Adicionando o campo para description
price_query = None  # Adicionando o campo para price
rating_query = None  # Adicionando o campo para rating
merchant_query = None  # Adicionando o campo para merchant
image_query = None  # Adicionando o campo para image
snippet_query = None  # Adicionando o campo para snippet
brand_model_query = None  # Adicionando o campo para brand/model
installment_query = None  # Adicionando o campo para installment
cashback_query = None  # Adicionando o campo para cashback

content_html_to_text = False
title_html_to_text = False
paging = False
suggestion_query = ''
results_query = ''

cookies = {}
headers = {}

# Número de resultados por página
page_size = 1
first_page_num = 1


def iterate(iterable):
    if isinstance(iterable, dict):
        items = iterable.items()
    else:
        items = enumerate(iterable)
    for index, value in items:
        yield str(index), value


def is_iterable(obj):
    if isinstance(obj, str):
        return False
    return isinstance(obj, Iterable)


def parse(query):  # pylint: disable=redefined-outer-name
    q = []  # pylint: disable=invalid-name
    for part in query.split('/'):
        if part == '':
            continue
        q.append(part)
    return q


def do_query(data, q):  # pylint: disable=invalid-name
    ret = []
    if not q:
        return ret

    qkey = q[0]

    for key, value in iterate(data):

        if len(q) == 1:
            if key == qkey:
                ret.append(value)
            elif is_iterable(value):
                ret.extend(do_query(value, q))
        else:
            if not is_iterable(value):
                continue
            if key == qkey:
                ret.extend(do_query(value, q[1:]))
            else:
                ret.extend(do_query(value, q))
    return ret


def query(data, query_string):
    q = parse(query_string)

    return do_query(data, q)


def request(query, params):  # pylint: disable=redefined-outer-name
    query = urlencode({'q': query})[2:]

    fp = {'query': query}  # pylint: disable=invalid-name
    if paging and search_url.find('{pageno}') >= 0:
        fp['pageno'] = (params['pageno'] - 1) * page_size + first_page_num

    params['cookies'].update(cookies)
    params['headers'].update(headers)

    params['url'] = search_url.format(**fp)
    params['query'] = query

    return params


def identity(arg):
    return arg


def response(resp):
    results = []
    json = loads(resp.text)

    title_filter = html_to_text if title_html_to_text else identity
    content_filter = html_to_text if content_html_to_text else identity

    if results_query:
        rs = query(json, results_query)  # pylint: disable=invalid-name
        if not rs:
            return results
        for result in rs[0]:
            try:
                url = query(result, url_query)[0]
                title = query(result, title_query)[0]
                description = query(result, description_query)[0] if description_query else ""
                price = query(result, price_query)[0] if price_query else ""
                rating = query(result, rating_query)[0] if rating_query else ""
                merchant = query(result, merchant_query)[0] if merchant_query else ""
                image = query(result, image_query)[0] if image_query else ""
                snippet = query(result, snippet_query)[0] if snippet_query else ""
                brand_model = query(result, brand_model_query)[0] if brand_model_query else ""
                installment = query(result, installment_query)[0] if installment_query else ""
                cashback = query(result, cashback_query)[0] if cashback_query else ""
            except:  # pylint: disable=bare-except
                continue
            try:
                content = query(result, content_query)[0]
            except:  # pylint: disable=bare-except
                content = ""
            results.append(
                {
                    'url': url_prefix + to_string(url),
                    'title': title_filter(to_string(title)),
                    'description': to_string(description),
                    'content': content_filter(to_string(content)),
                    'price': to_string(price),
                    'rating': to_string(rating),
                    'merchant': to_string(merchant),
                    'image': to_string(image),
                    'snippet': to_string(snippet),
                    'brand_model': to_string(brand_model),
                    'installment': to_string(installment),
                    'cashback': to_string(cashback)
                }
            )
    else:
        for result in json:
            url = query(result, url_query)[0]
            title = query(result, title_query)[0]
            content = query(result, content_query)[0]

            results.append(
                {
                    'url': url_prefix + to_string(url),
                    'title': title_filter(to_string(title)),
                    'content': content_filter(to_string(content)),
                }
            )

    if not suggestion_query:
        return results
    for suggestion in query(json, suggestion_query):
        results.append({'suggestion': suggestion})
    return results
