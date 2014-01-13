#!/usr/bin/python
# -*- encoding: utf-8 -*-

import requests
from bs4 import BeautifulSoup
import re


class Movie:
    def __init__(self, hl='en'):
        '''hl will be the language that google uses to query.'''

        self.base_url = 'http://www.google.com'
        self.hl = hl

    def searchByCoordinates(self, latitude, longitude):
        '''Latitude and longitude should be double.
           Like (25.0333, 121.63333)'''

        self.near = '{0},{1}'.format(latitude, longitude)

    def searchByLocation(self, location):
        '''The place name of the theater.'''

        self.near = location

    def __makeUrl(self, sort=None, start=None, mid=None, tid=None):
        url = self.base_url + '/movies?'
        url += 'hl={0}'.format(self.hl)
        url += '&near={0}'.format(self.near)

        ''' sort = 0: sort by theater
                   1: sort by movie
        '''
        if sort is None:
            url += '&sort=1'
        else:
            url += '&sort={0}'.format(sort)

        ''' start = only show the times after this parameter.'''
        if start is not None:
            url += '&start={0}'.format(start)

        ''' mid = movie id.'''
        if mid is not None:
            url += '&mid={0}'.format(mid)

        ''' tid = theater id.'''
        if tid is not None:
            url += '&tid={0}'.format(tid)
        return url

    def __getPageIndexes(self):
        '''Retrieve all page indexes from the first page.'''

        url = self.__makeUrl()
        pages = []

        response = requests.get(url)
        soup = BeautifulSoup(response.content)
        navbar = soup.find('div', id='navbar')

        if navbar is None:
            return pages

        for td in navbar.find_all('td'):
            # text may be "next page" or "previous page",
            # but we only want the number.
            for text in td.stripped_strings:
                if text.isdigit() and int(text) not in pages:
                    pages.append(int(text))
        return pages

    def __getMovieLinkInOnePage(self, start):
        '''Get all the links of movies in the specifc page.'''

        url = self.__makeUrl(start=start)
        links = []

        response = requests.get(url)
        soup = BeautifulSoup(response.content)
        for title in soup.find_all('h2', itemprop='name'):
            a = title.find('a')
            if a:
                links.append(self.base_url + a['href'])
        return links

    def getMovieLinks(self):
        '''Get all the movie links in every page.'''

        links = []
        pages = self.__getPageIndexes()
        for page in pages:
            page = (page - 1) * 10
            page_links = self.__getMovieLinkInOnePage(page)
            links.extend(page_links)
        return links

    def __getMovieId(self, url):
        '''Parse the url which key is "mid"'''

        mid = ''
        for segment in url.split('&'):
            if 'mid' in segment:
                mid = segment.split('=')[1]
        return mid

    def getMovieDetail(self, url):
        mid = self.__getMovieId(url)
        url = self.__makeUrl(mid=mid)

        time_re = re.compile(r' &nbsp.*?(\d{2}:\d{2})')
        theaters = []

        response = requests.get(url)
        soup = BeautifulSoup(response.content)

        movie_name = soup.find('h2', itemprop='name').get_text()

        # First get "less" segment, then get "more" segment.
        # But the "more" text is a child node of "#synopsisSecond0",
        # so we just should only get the first one.
        movie_description = soup.find(
            'span', itemprop='description').get_text()
        description = soup.find('span', id='SynopsisSecond0')
        if description:
            movie_description += list(description.stripped_strings)[0]

        infos = soup.find('div', class_='info').get_text()
        movie_info = [info.strip() for info in infos.split('-')]

        movie_length = ''
        movie_genre = ''
        movie_language = ''
        movie_subtitle = ''
        movie_actors = ''
        for counter, text in enumerate(movie_info):
            if counter == 0:
                movie_length = text
            elif counter == 1:
                movie_genre = text
            elif counter == 2:
                movie_language = text
            elif counter == 3:
                movie_subtitle = text
            elif counter == 4:
                movie_actors = text

        for theater in soup.find_all('div', class_='theater'):
            theater_name = theater.find('div', class_='name').get_text()
            theater_address = theater.find('div', class_='address').get_text()

            theater_times = []
            time = theater.find('div', class_='times')
            for span in time.find_all('span'):
                time_match = time_re.search(span.get_text())
                if time_match:
                    theater_times.append(time_match.group(1))
            theaters.append({'theater_name': theater_name,
                             'theater_address': theater_address,
                             'theater_times': theater_times})

        return {'movie_name': movie_name,
                'movie_description': movie_description,
                'movie_length': movie_length,
                'movie_genre': movie_genre,
                'movie_language': movie_language,
                'movie_subtitle': movie_subtitle,
                'movie_actors': movie_actors,
                'theater': theaters}

    def getMovies(self):
        movies = []

        links = self.getMovieLinks()
        for link in links:
            movie = self.getMovieDetail(link)
            movies.append(movie)
        return movies


def main():
    movie = Movie(hl='zh-TW')

    # Search by the latitude and longitude
    #movie.searchByCoordinates(25.0333, 121.6333)
    # or search by the location name
    movie.searchByLocation('Taipei')
    movie.getMovies()


if __name__ == '__main__':
    main()
