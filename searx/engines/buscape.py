# SPDX-License-Identifier: AGPL-3.0-or-later
"""This is the implementation of the Zoom shopping engine."""

from typing import TYPE_CHECKING
import random
from urllib.parse import urlencode
from lxml import html
from searx.utils import extract_text, eval_xpath, eval_xpath_list, eval_xpath_getindex, gen_useragent
from searx.network import get
from searx.enginelib.traits import EngineTraits

if TYPE_CHECKING:
    import logging
    logger: logging.Logger

traits: EngineTraits

# about
about = {
    "website": 'https://www.buscape.com.br',
    "wikidata_id": 'Q1052209',
    "use_official_api": False,
    "require_api_key": False,
    "results": 'HTML, JSON',
}

categories = ['general', 'web']
paging = True
max_page = 10

# specific xpath variables conforme os settings
products_xpath = './/div[@data-testid="product-card"]'
title_xpath = "//h2[@data-testid='product-card::name'] | //h2[contains(@class, 'ProductCard_ProductCard_Name')]"
url_xpath = "//a[@data-testid='product-card::card']/@href | //a[contains(@class, 'ProductCard_ProductCard_Inner')]/@href"
price_xpath = "//p[@data-testid='product-card::price'] | //p[contains(@class, 'ProductCard_ProductCard_Price')]"
description_xpath = "//div[@data-testid='product-card::description'] | //div[contains(@class, 'ProductCard_ProductCard_Description')]"
image_xpath = "//div[@data-testid='product-card::image']//img/@src | //div[contains(@class, 'ProductCard_ProductCard_Image')]//img/@src"
installment_xpath = "//span[@data-testid='product-card::installment'] | //span[contains(@class, 'ProductCard_ProductCard_Installment')]"
rating_xpath = ".//div[@data-testid='product-card::rating']/text()"
merchant_xpath = ".//div[@data-testid='product-card::description']//h3[contains(@class, 'ProductCard_ProductCard_BestMerchant__JQo_V')]/text()"
thumbnail_xpath = "//meta[@property='og:image']/@content | //link[@rel='icon']/@href | //img/@src | //div[@data-testid='product-card::image']//img/@src"
cashback_xpath = "//span[@data-testid='product-card::cashback'] | //span[contains(@class, 'ProductCard_ProductCard_CashbackInfo')]"


def generate_random_headers():
    """Gera headers aleatórios para evitar bloqueios de scraping."""
    user_agent = gen_useragent()  # Gera um User-Agent aleatório

    # Lista de valores de aceitação de idiomas e encodings para adicionar variação
    accept_languages = ['en-US,en;q=0.9',
                        'pt-BR,pt;q=0.8,en-US;q=0.6', 'es-ES,es;q=0.8,en;q=0.5']
    accept_encodings = ['gzip, deflate, br', 'gzip, deflate', 'br']

    headers = {
        'User-Agent': user_agent,
        'Accept-Language': random.choice(accept_languages),
        'Accept-Encoding': random.choice(accept_encodings),
        'Connection': 'keep-alive',
        'Cache-Control': 'no-cache',
        'Upgrade-Insecure-Requests': '1',
        # Adiciona um referer genérico para parecer uma navegação legítima
        'Referer': 'https://www.google.com/'
    }
    return headers


def request(query, params):
    """Cria a URL de consulta para buscar os resultados e adiciona proteções contra bloqueios de scraping."""
    # Inicializa a paginação na página 1, se não for passada nos parâmetros
    if 'pageno' not in params:
        params['pageno'] = 1

    query_url = (
        'https://www.buscape.com.br/search'
        + "?"
        + urlencode({'q': query, 'page': params['pageno']})
    )

    # Gera headers aleatórios e os adiciona ao params
    headers = generate_random_headers()
    params['url'] = query_url
    params['headers'].update(headers)

    return params


def response(resp):
    """Processa a resposta HTML e extrai os resultados conforme os seletores."""
    results = []
    dom = html.fromstring(resp.text)

    url = str(resp.request.url)
    params = {
        'q': url.split("q=")[1].split("&")[0] if "q=" in url else '',
        'pageno': int(url.split("page=")[1].split("&")[0]) if "page=" in url else 1,
        'headers': resp.request.headers  # Reutiliza headers da requisição original
    }

    # Log para verificar o conteúdo do HTML/JSON
    print("Conteúdo da resposta:")
    # Exibe os primeiros 500 caracteres para verificar se estamos recebendo a resposta certa
    print(resp.text[:500])

    while params['pageno'] <= max_page:
        products = eval_xpath_list(dom, products_xpath)
        print(
            f"Total de produtos encontrados na página {params['pageno']}: {len(products)}")

        for i, product in enumerate(products):
            try:
                # Extraindo os campos usando os seletores XPath configurados
                title = extract_text(
                    eval_xpath_getindex(product, title_xpath, 0))
                url_prod = eval_xpath_getindex(product, url_xpath, 0)
                price = extract_text(
                    eval_xpath_getindex(product, price_xpath, 0))
                description = extract_text(
                    eval_xpath_getindex(product, description_xpath, 0))
                image = eval_xpath_getindex(product, image_xpath, 0)

                # Campos opcionais
                installment = extract_text(eval_xpath_getindex(
                    product, installment_xpath, 0, None))
                rating = extract_text(eval_xpath_getindex(
                    product, rating_xpath, 0, None))
                merchant = extract_text(eval_xpath_getindex(
                    product, merchant_xpath, 0, None))
                thumbnail = eval_xpath_getindex(
                    product, thumbnail_xpath, 0, None)
                cashback = extract_text(eval_xpath_getindex(
                    product, cashback_xpath, 0, None))

                # Monta o dicionário de resultados
                result = {
                    'title': title,
                    'url': f'https://www.buscape.com.br{url_prod}',
                    'price': price,
                    'description': description,
                    'image': image,
                    'installment': installment,
                    'rating': rating,
                    'merchant': merchant,
                    'thumbnail': thumbnail,
                    'cashback': cashback,
                }

                results.append(result)

            except Exception as e:
                # Captura qualquer erro durante a extração dos campos e exibe no log
                print(
                    f"Erro ao processar o produto {i + 1} na página {params['pageno']}: {e}")
                continue

        # Se não houver mais produtos, interrompe o loop
        if len(products) == 0:
            break

        # Incrementa o número da página para a próxima requisição
        params['pageno'] += 1
        if params['pageno'] > max_page:
            break

        # Constrói a URL para a próxima página
        next_url = 'https://www.buscape.com.br/search?' + \
            urlencode(
                {'q': params['q'], 'page': params['pageno'], 'format': 'json'})
        print(f"Buscando a página {params['pageno']} com a URL: {next_url}")

        # Faz a requisição para a próxima página
        resp = get(next_url, headers=params['headers'])
        dom = html.fromstring(resp.text)

    # Log final com a quantidade de resultados processados
    print(f'{len(results)} resultados extraídos com sucesso.')

    return results
