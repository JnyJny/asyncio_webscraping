#!/usr/bin/env python3

'''
'''

import asyncio
import requests
from bs4 import BeautifulSoup


class ContentFromURL(object):
    '''
    '''
    def __init__(self, url):
        self.url = url

    def _valid(valid, response):
        '''
        '''
        if response.status_code != 200:
            return False
        if 'html' not in response.headers['Content-Type'].lower():
            return False
        return True

    @property
    def response(self):
        try:
            return self._response
        except AttributeError:
            pass
        self._response = requests.get(self.url, stream=True)
        return self._response
    
    @property
    def content(self):
        try:
            return self._content
        except AttributeError:
            pass
        self._content = self.response.content
        return self._content
    
    @property
    def html(self):
        try:
            return self._html
        except AttributeError:
            pass
        self._html = BeautifulSoup(self.content, 'html.parser')
        return self._html



class Mathematicians(ContentFromURL):

    def __init__(self, url=None):
        super().__init__(url or 'http://www.fabpedigree.com/james/mathmen.htm')

    @property
    def names(self):
        try:
            return self._names
        except AttributeError:
            pass
        s = set()
        
        for li in self.html.select('li'):
            for name in li.text.split('\n'):
                if len(name):
                    name = name.strip().replace('  ', ' ')
                    s.add(name)
        self._names = list(s)
        return self._names


class Wikipedia(ContentFromURL):

    def __init__(self, name):
        self.name = name
        base_url = 'https://xtools.wmflabs.org/articleinfo/en.wikipedia.org/'
        super().__init__(base_url + self.name)

    def __str__(self):
        return f'{self.name} hits are {self.interest}'

    @property
    def interest(self):
        try:
            return self._interest
        except AttributeError:
            pass

        self._interest = 0
        for a in self.html.select('a'):
            if 'latest-60' in  a['href']:
                self._interest = int(a.text.replace(',', ''))
                break
        return self._interest

    async def __call__(self, *args, **kwds):
        i = self.interest
        return self

def synchronous(names):

    return [Wikipedia(n) for n in names]


def asynchronous(names):

    async def get_interest(name):
        # await wants a callable I guess, gave it one.
        w = Wikipedia(name)
        await w()
        return w
    
    async def process_names(names):
        tasks = [get_interest(n) for n in names]
        return [await t for t in asyncio.as_completed(tasks)]
    
    loop = asyncio.get_event_loop()
    results = loop.run_until_complete(process_names(names))
    loop.close()

    return results
    

if __name__ == '__main__':

    mathematicians = Mathematicians()

    # results = synchronous(mathematicians.names)
    
    results = asynchronous(mathematicians.names[0:10])

    results.sort(key=lambda w:w.interest)

    for rank, w in enumerate(reversed(results)):
         print(f'rank {rank+1} -> {w!s}')
