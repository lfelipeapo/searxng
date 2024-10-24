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
    "website": 'https://www.zoom.com.br',
    "wikidata_id": 'Q1052209',
    "use_official_api": False,
    "require_api_key": False,
    "results": 'HTML',
}

categories = ['general', 'web']
paging = True
max_page = 50

# specific xpath variables conforme os settings
products_xpath = './/div[contains(@class, "ProductCard_ProductCard")]'
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
    accept_languages = ['en-US,en;q=0.9', 'pt-BR,pt;q=0.8,en-US;q=0.6', 'es-ES,es;q=0.8,en;q=0.5']
    accept_encodings = ['gzip, deflate, br', 'gzip, deflate', 'br']

    headers = {
        'User-Agent': user_agent,
        'Accept-Language': random.choice(accept_languages),
        'Accept-Encoding': random.choice(accept_encodings),
        'Connection': 'keep-alive',
        'Cache-Control': 'no-cache',
        'Upgrade-Insecure-Requests': '1',
        'Referer': 'https://www.google.com/'  # Adiciona um referer genérico para parecer uma navegação legítima
    }
    return headers

def request(query, params):
    """Cria a URL de consulta para buscar os resultados e adiciona proteções contra bloqueios de scraping."""
    query_url = (
        'https://www.zoom.com.br/search'
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

    # Itera sobre os produtos encontrados pelo XPath
    for product in eval_xpath_list(dom, products_xpath):
        try:
            # Extraindo os campos usando os seletores XPath configurados
            title = extract_text(eval_xpath_getindex(product, title_xpath, 0))
            url = eval_xpath_getindex(product, url_xpath, 0, None)
            price = extract_text(eval_xpath_getindex(product, price_xpath, 0))
            description = extract_text(eval_xpath_getindex(product, description_xpath, 0))
            image = eval_xpath_getindex(product, image_xpath, 0, None)
            installment = extract_text(eval_xpath_getindex(product, installment_xpath, 0))
            rating = extract_text(eval_xpath_getindex(product, rating_xpath, 0))
            merchant = extract_text(eval_xpath_getindex(product, merchant_xpath, 0))
            thumbnail = extract_text(eval_xpath_getindex(product, thumbnail_xpath, 0))
            cashback = extract_text(eval_xpath_getindex(product, cashback_xpath, 0))

            # Verifica se os campos obrigatórios têm dados válidos
            if not title or not url:
                continue  # Pula o item se os campos obrigatórios estiverem ausentes

            # Monta o dicionário de resultados
            result = {
                'title': title,
                'url': f'https://www.zoom.com.br{url}' if url else None,  # Completa o URL se necessário
                'price': price,
                'description': description,
                'image': image,
                'installment': installment,
                'rating': rating,
                'merchant': merchant,
                'thumbnail': thumbnail,
                'cashback': cashback,
            }

            # Exibe um log informativo com o título e preço do produto
            logger.debug(f'Produto encontrado: {title} | Preço: {price}')

            results.append(result)

        except Exception as e:
            # Captura qualquer erro durante a extração dos campos e exibe no log
            logger.error(f"Erro ao processar o produto: {e}", exc_info=True)
            continue

    # Exibe um log final com a quantidade de resultados processados
    logger.info(f'{len(results)} resultados extraídos com sucesso.')

    return results
