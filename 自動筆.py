import trafilatura
from openai import OpenAI
import requests
from bs4 import BeautifulSoup
import ast
import json
import time
import random

client = OpenAI(
  base_url = "https://integrate.api.nvidia.com/v1",
  api_key = "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"
)

def crawl_top_10_results(query, nor=10):
    encoded_query = requests.utils.quote(query)
    url = f"https://www.google.com/search?q={encoded_query}"
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36"
    }
    response = requests.get(url, headers=headers)
    response.encoding = 'utf-8'
    soup = BeautifulSoup(response.text, 'html.parser')
    results = []
    for g in soup.find_all('div', class_='tF2Cxc')[:nor]:
        result = {}
        if g.find('h3'):
            result['title'] = g.find('h3').text
        if g.find('a'):
            result['url'] = g.find('a')['href']
        snippet = ''
        if g.find('span', class_='aCOpRe'):
            snippet = g.find('span', class_='aCOpRe').text
        elif g.find('div', class_='IsZvec'):
            snippet = g.find('div', class_='IsZvec').text
        elif g.find('div', class_='VwiC3b'):
            snippet = g.find('div', class_='VwiC3b').text
        elif g.find('div', class_='s3v9rd'):
            snippet = g.find('div', class_='s3v9rd').text    
        result['snippet'] = snippet
        results.append(result)
    
    return results

def extract_list_content(input_string):
    start_index = input_string.find("[")
    end_index = input_string.rfind("]")

    if start_index != -1 and end_index != -1 and start_index < end_index:
        try:
            return ast.literal_eval(input_string[start_index:end_index + 1])
        except (ValueError, SyntaxError):
            return []
    else:
        return []

def extract_json_content(input_string):
    start_index = input_string.find("{")
    end_index = input_string.rfind("}")

    if start_index != -1 and end_index != -1 and start_index < end_index:
        try:
            return ast.literal_eval(input_string[start_index:end_index + 1])
        except (ValueError, SyntaxError):
            return {}
    else:
        return {}

def titler(outline, query, max_retries=3, delay=2):
    attempt = 0
    while attempt < max_retries:
        try:
            full_article = ""
            prompt = f"""
            i want to write a blog article of the keyword {query}.
            here is all the <h2> headers i am going to cover in my blog article:
            {outline}

            i want a title that is clickbait enough, can convey the information I want to discuss about, in moderate length and humanized tone.
            it must be informational intent. words like "盤點", "攻略", "方法" are favored.
            you should SEO optimize the title with the keyword {query} naturally.
            return me a single JSON object with single key 'title' without premable and explanations.
            AGAIN: NO premable and explanation needed.
            """

            completion = client.chat.completions.create(
                model="meta/llama-3.1-405b-instruct",
                messages=[{"role": "user", "content": prompt.strip()}],
                temperature=0.2,
                top_p=0.7,
                max_tokens=8192,
                stream=True
            )

            article_title = ""
            for chunk in completion:
                if chunk.choices[0].delta.content is not None:
                    article_title += chunk.choices[0].delta.content
            
            article_title = extract_json_content(article_title)["title"]
            if article_title:
                  return article_title

        except Exception as e:
            attempt += 1
            if attempt < max_retries:
                sleep_time = delay * (2 ** attempt) + random.uniform(0, 1)
                time.sleep(sleep_time)
            else:
                raise

def structurer(result_list, query, max_retries=3, delay=2):
    attempt = 0
    while attempt < max_retries:
        try:
            full_article = ""
            prompt = f"""
            i want to write a blog article of the keyword {query}.
            here is the top 10 results when i search for this keyword:
            {result_list}

            i want to take some articles as reference. i only want informational intent results, and addressing my topic.
            you should return 5-9 results after filtering.
            return me a list of useful search results in the same format: each list item is a JSON object with title, url and snippet.
            no premable and explanation needed.
            """

            completion = client.chat.completions.create(
                model="meta/llama-3.1-405b-instruct",
                messages=[{"role": "user", "content": prompt.strip()}],
                temperature=0.2,
                top_p=0.7,
                max_tokens=8192,
                stream=True
            )

            filtered_headers = ""
            for chunk in completion:
                if chunk.choices[0].delta.content is not None:
                    filtered_headers += chunk.choices[0].delta.content
            
            filtered_headers = extract_list_content(filtered_headers)
            if filtered_headers:
                  return filtered_headers

        except Exception as e:
            attempt += 1
            if attempt < max_retries:
                sleep_time = delay * (2 ** attempt) + random.uniform(0, 1)
                time.sleep(sleep_time)
            else:
                raise

def topic_definer(website_text, query, max_retries=3, delay=2):
    attempt = 0
    while attempt < max_retries:
        try:
            prompt = f"""
            i want to write a blog article of the keyword {query}.
            here is the website text for a top ranked article writing about the topic:
            {website_text}

            identify the topics that they wrote, and reform them into h2 headers.
            return me a python list of h2 headers.
            NO premable and explanation. I only want the list without other words.
            """

            completion = client.chat.completions.create(
                model="meta/llama-3.1-405b-instruct",
                messages=[{"role": "user", "content": prompt.strip()}],
                temperature=0.2,
                top_p=0.7,
                max_tokens=8192,
                stream=True
            )

            filtered_headers = ""
            for chunk in completion:
                if chunk.choices[0].delta.content is not None:
                    filtered_headers += chunk.choices[0].delta.content

            filtered_headers = extract_list_content(filtered_headers)
            if filtered_headers:
                    return filtered_headers

        except Exception as e:
            attempt += 1
            if attempt < max_retries:
                sleep_time = delay * (2 ** attempt) + random.uniform(0, 1)
                time.sleep(sleep_time)
            else:
                raise

def topic_refiner(topics, query, max_retries=3, delay=2):
    attempt = 0
    while attempt < max_retries:
        try:
            prompt = f"""
            for this keyword: {query}
            here is the headers that top ranked articles write about, without ordering:
            {topics}

            now i want to write a blog article about this topic. expected blog size: large
            from the topics of top ranked articles, PICK best h2 headers with consistent level of specificity, and rewrite me these h2 headers.
            do not give duplicated headers. headers must be DISTINCT and cannot have DUPLICATED ASPECTS. do not give totally unrelated headers.
            the h2 headers given should be distinct, non-repetitive, and focused. no generic or catch-all phrases. specific is MUST. no need elaboration in headers if not mentioned in original header. DO NOT form headers by clustering other's multiple headers. i need PICK and REWRITE.
            my inner content will be slightly different from reference article, so make sure headers are reformed.
            quality should be prioritized, less headers are better than vague and overly broad headers. no generic or catch-all phrases.
            return me a python list of headers only.
            NO premable and explanation needed.
            """

            completion = client.chat.completions.create(
                model="meta/llama-3.1-405b-instruct",
                messages=[{"role": "user", "content": prompt.strip()}],
                temperature=0.2,
                top_p=0.7,
                max_tokens=8192,
                stream=True
            )

            filtered_headers = ""
            for chunk in completion:
                if chunk.choices[0].delta.content is not None:
                    filtered_headers += chunk.choices[0].delta.content
            
            filtered_headers = extract_list_content(filtered_headers)
            filtered_headers = topic_selector(filtered_headers, query)
            if filtered_headers:
                    return filtered_headers

        except Exception as e:
            attempt += 1
            if attempt < max_retries:
                sleep_time = delay * (2 ** attempt) + random.uniform(0, 1)
                time.sleep(sleep_time)
            else:
                raise

def topic_selector(headers, query, max_retries=3, delay=2):
    attempt = 0
    while attempt < max_retries:
        try:
            prompt = f"""
            i want to write a blog article of the keyword {query}.
            now here is the proposed h2 headers for writing. but there might be duplicated aspects, or headers with unclear intent.
            there might be vague headers with different level of specificity as well.
            delete these vague or inappropriate headers ONLY. no need to modify acceptable headers.
            return me a python list of h2 headers.
            NO premable and explanation. I only want the list without other words.
            """

            completion = client.chat.completions.create(
                model="meta/llama-3.1-405b-instruct",
                messages=[{"role": "user", "content": prompt.strip()}],
                temperature=0.2,
                top_p=0.7,
                max_tokens=8192,
                stream=True
            )

            filtered_headers = ""
            for chunk in completion:
                if chunk.choices[0].delta.content is not None:
                    filtered_headers += chunk.choices[0].delta.content

            filtered_headers = extract_list_content(filtered_headers)
            if filtered_headers:
                  return filtered_headers

        except Exception as e:
            attempt += 1
            if attempt < max_retries:
                sleep_time = delay * (2 ** attempt) + random.uniform(0, 1)
                time.sleep(sleep_time)
            else:
                raise

def headerizer(result_list, query):
    url_list = []
    for result in result_list:
        url_list.append(result["url"])

    all_topics = []
    
    for url in url_list:
        downloaded = trafilatura.fetch_url(url)
        website_text = trafilatura.extract(downloaded)
        if website_text:
            topics = topic_definer(website_text, query)
            all_topics.extend(topics)

    all_topics = topic_refiner(all_topics, query)
    return all_topics

def querier(header, query, max_retries=3, delay=2):
    attempt = 0
    while attempt < max_retries:
        try:
            prompt = f"""
            i am writing article with this keyword: {query}
            i need to do information research before writing
            for this specific header in the article {header}, i want you to craft me a web search query that can obtain most accurate information results to write the paragraphs under this header.
            You MUST ensure the search query is accurate information, to prevent search results points to other services or keywords.
            return me a python list object with each list item a JSON object with a single key query without any premable and explanations. you can return more than one JSON object search query in the list.
            NO premable and explanation. Dont give me more than one list.
            """

            completion = client.chat.completions.create(
                model="meta/llama-3.1-405b-instruct",
                messages=[{"role": "user", "content": prompt.strip()}],
                temperature=0.2,
                top_p=0.7,
                max_tokens=8192,
                stream=True
            )

            thequery = ""
            for chunk in completion:
                if chunk.choices[0].delta.content is not None:
                    thequery += chunk.choices[0].delta.content

            thequery = extract_list_content(thequery)
            if thequery:
                  return thequery
        
        except Exception as e:
            attempt += 1
            if attempt < max_retries:
                sleep_time = delay * (2 ** attempt) + random.uniform(0, 1)
                time.sleep(sleep_time)
            else:
                raise

def pf_rewriter(article, header, title):
    full_article = ""
    prompt = f"""
    title of the crawled article:
    {title}

    content of article:
    {article}

    i want to write paragraphs under the header {header}
    generate me point forms for related information ONLY. do not give me related aspects.
    if the information i provided is referring to another service or information instead of the information looking for, return no results is better than wrong information.
    make sure you do not misidentify details. this is a MUST. make sure you did a summary check and ensure the bullet points are 100% correct without misidentifying events or information subject.
    you must label general information if the information is not directly addressing this specific header. (be careful of wrong country, district, human names, if they match the header)
    return me in traditional chinese. no premable and explanation.
    """

    completion = client.chat.completions.create(
        model="meta/llama-3.1-405b-instruct",
        messages=[{"role": "user", "content": prompt.strip()}],
        temperature=0.2,
        top_p=0.7,
        max_tokens=8192,
        stream=True
    )

    for chunk in completion:
        if chunk.choices[0].delta.content is not None:
            full_article += chunk.choices[0].delta.content

    return full_article

def ai_rewriter(bullet_points, header):
    full_article = ""
    prompt = f"""
    {bullet_points}
    i want to write paragraphs under the h2 header {header}
    generate me paragraphs. be detailed. you can elaborate to generate longer paragraphs, but make sure your elaboration is not by guessing or exaggerating.
    do not include promotions. make sure your returned paragraphs are coherent and fluent.
    return me in a HTML form. text must be labelled with html tags.
    return me in traditional chinese. no premable and explanation.
    """

    completion = client.chat.completions.create(
        model="meta/llama-3.1-405b-instruct",
        messages=[{"role": "user", "content": prompt.strip()}],
        temperature=0.2,
        top_p=0.7,
        max_tokens=8192,
        stream=True
    )

    for chunk in completion:
        if chunk.choices[0].delta.content is not None:
            full_article += chunk.choices[0].delta.content

    return full_article

def combine_multiline_strings(*strings):
    return "\n".join(strings)

def get_title_from_url(url):
    try:
        response = requests.get(url)
        response.raise_for_status()
        soup = BeautifulSoup(response.text, 'html.parser')
        title = soup.title.string if soup.title else "No title found"
        return title
    except requests.exceptions.RequestException as e:
        return None

query = "上班族如何培養額外技能？"
outline = headerizer(structurer(crawl_top_10_results(query), query), query)
final_article = ""
title = titler(outline, query)
h1 = "<h1>" + str(title) + "</h1>"
title_tag = "   <title>" + str(title) + "</title>"
final_article += "<html>\n<head>\n"
final_article += title_tag
final_article += "</head>\n\n<body>\n"
final_article += h1
toc = "\n\n<h2>文章目錄</h2>\n<ul>\n"
for item in outline:
    toc += f"  <li>{item}</li>\n"
toc += "</ul>\n\n"
final_article += toc
for header in outline:
    results = []
    bullet_points = ""
    eachquery = querier(header, query)
    for aquery in eachquery:
        thequery = aquery["query"]
        results = crawl_top_10_results(thequery, nor=4)
        for result in results:
            downloaded = trafilatura.fetch_url(result['url'])
            website_text = trafilatura.extract(downloaded)
            title = get_title_from_url(result['url'])
            bulletpt = pf_rewriter(website_text, header, title)
            bullet_points = combine_multiline_strings(bullet_points, bulletpt)
    final = ai_rewriter(bullet_points, header)

    final_article += final
    final_article += "\n\n"

final_article += "</body>\n</html>"

with open(f"{title}.txt", a) as file:
    file.write(final_article)
