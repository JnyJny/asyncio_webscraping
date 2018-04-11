import asyncio
from contextlib import closing
from time import sleep, time

from bs4 import BeautifulSoup
from requests import get
from requests.exceptions import RequestException


def simple_get(url):
    """
    Attempts to get the content at 'url' by making an HTTP GET request.
    If the content-type of response is some kind of HTML/XML, return the
    text content, otherwise return None.
    """
    try:
        with closing(get(url, stream=True)) as resp:
            return resp.content if is_good_response(resp) else None
    except RequestException as e:
        log_error(f'Error during requests to {url}: {str(e)}')
        return None


def is_good_response(resp):
    """
    Returns True if the response seems to be HTML, False otherwise.
    """
    content_type = resp.headers['Content-Type'].lower()
    return (resp.status_code == 200
            and content_type is not None
            and content_type.find('html') > -1)


def log_error(e):
    """
    It is always a good idea to log errors.
    This function just prints them, but you can make it do anything.
    """
    print(e)


def get_names():
    """
    Downloads the page where the list of mathematicians is found
    and returns a list of strings, one per mathematician.
    """
    url = 'http://www.fabpedigree.com/james/mathmen.htm'
    response = simple_get(url)

    if response:
        html = BeautifulSoup(response, 'html.parser')
        names = set()
        for li in html.select('li'):
            for name in li.text.split('\n'):
                if len(name) > 0:
                    names.add(name.strip())
        return list(names)

    # Raise an exception if we failed to get any data from the url
    raise Exception(f'Error retrieving content from {url}.')


async def get_hits(name):
    url = f'https://xtools.wmflabs.org/articleinfo/en.wikipedia.org/{name}'
    response = simple_get(url)

    if response:
        html = BeautifulSoup(response, 'html.parser')

        hit_link = [a for a in html.select('a') 
                    if a['href'].find('latest-60') > -1]
        
        if len(hit_link) > 0:
            # strip commas
            link_text = hit_link[0].text.replace(',', '')
            try:
                # convert to integer
                return int(link_text), name
            except ValueError:
                log_error(f'Could not parse {link_text} as an "int".')
    
    log_error(f'No pageviews found for {name}.')
    return -1, name


def show_results(tasks):
    """
    Takes a list of asyncio tasks and prints its results.
    """
    results = [task.result() for task in tasks]
    results.sort()
    results.reverse()

    top_marks = results[:5] if len(results) > 5 else results

    print('\nThe most popular mathematicians are:\n')
    for mark, mathematician in top_marks:
        print(f'{mathematician} with {mark} page views')
    
    no_results = len([res for res in results if res[0] == -1])
    print(f'\n{no_results} mathematicians on the list had no results')


def main():
    start = time()
    print('Getting the list of names...')
    names = get_names()
    print(f'Found: {len(names)}')

    print('Getting stats for each name...')
    loop = asyncio.get_event_loop()
    tasks = [loop.create_task(get_hits(name)) for name in names]
    wait_tasks = asyncio.wait(tasks)
    loop.run_until_complete(wait_tasks)
    loop.close()
    show_results(tasks)
    print('... done.\n')
    print(f'Took {time() - start} seconds to complete.')


if __name__ == '__main__':
    main()
