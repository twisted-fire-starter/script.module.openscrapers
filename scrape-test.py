import os
import sys
import threading
import time
import urllib
import json
import requests
import random

sys.path.append(os.path.join(os.path.curdir, 'lib'))

arguments = {}

for i in sys.argv:
    try:
        i = i.split('=')
        arguments.update({i[0]:i[1]})
    except:
        pass

print(arguments)

folders = arguments.get('folders', None)

if folders is not None:
    folders = folders.split(',')
else:
    folders = ['en', 'en_DebridOnly']

test_type = int(arguments.get('test_type', 1))

test_mode = arguments.get('test_mode', 'movie')

TIMEOUT_MODE = arguments.get('timeout_mode', False)

no_tests = arguments.get('number_of_tests', '10')

if TIMEOUT_MODE in ['true', 'True', 'y']:
    no_tests = 1
    TIMEOUT_MODE = True
else:
    TIMEOUT_MODE = False

from lib import openscrapers

print('Testing Folders: %s' % ' | '.join(folders))
print('Running %s tests' % no_tests)

# Test information
movie_meta = []
episode_meta = []
trakt_api_key = 'c1d7d1519b5d70158fc568c42b8c7a39b4f73a73e17e25c0e85152a542cd1664' # Soz Not Soz ExodusRedux

trakt_movies_url = 'https://api.trakt.tv/movies/popular?extended=full&limit=%s' % no_tests
trakt_shows_url = 'https://api.trakt.tv/shows/popular?extended=full&limit=%s' % no_tests
trakt_episodes_url = 'https://api.trakt.tv/shows/%s/seasons?extended=episodes'

print('######################################')
print('GETTING META FROM TRAKT ....')
print('######################################')

trakt_headers = {'trakt-api-version': '2', 'trakt-api-key': trakt_api_key, 'Content-Type': 'application/json'}

if test_mode == 'movie':
    resp = requests.get(trakt_movies_url, headers=trakt_headers)
    resp = json.loads(resp.text)

    for movie in resp:
        print('Adding Movie: %s' % movie['title'])
        movie_meta.append({'imdb': movie['ids']['imdb'], 'title': movie['title'], 'localtitle': movie['title'],
                           'year': str(movie['year']), 'aliases': []})

else:
    resp = requests.get(trakt_shows_url, headers=trakt_headers)
    resp = json.loads(resp.text)

    for show in resp:

        episodes = requests.get(trakt_episodes_url % show['ids']['trakt'], headers=trakt_headers)
        episodes = json.loads(episodes.text)
        episodes = [episode for season in episodes for episode in season['episodes']]
        random.shuffle(episodes)
        episode = episodes[0]
        print('Adding Episode: %s - S%sE%s' % (show['title'], episode['season'], episode['number']))
        episode_meta.append({'show_imdb': show['ids']['imdb'], 'show_tvdb': show['ids']['tvdb'],
                             'tvshowtitle': show['title'], 'localtvshowtitle': show['title'], 'aliases': [],
                             'year': show['year'], 'imdb': episode['ids']['imdb'], 'tvdb': episode['ids']['tvdb'],
                             'title': episode['title'], 'premiered': '', 'season': episode['season'],
                             'episode': episode['number']})


RUNNING_PROVIDERS = []
TOTAL_SOURCES = []
PROVIDER_LIST = openscrapers.sources(folders)
FAILED_PROVIDERS = []
PASSED_PROVIDERS = []
workers = []
TOTAL_RUNTIME = 0
TIMEOUT = 10

hosts = [u'4shared.com', u'openload.co', u'rapidgator.net', u'sky.fm', u'thevideo.me', u'filesmonster.com',
         u'youtube.com', u'icerbox.com', u'nitroflare.com', u'1fichier.com', u'docs.google.com', u'mediafire.com',
         u'hitfile.net', u'2shared.com', u'rapidvideo.com', u'filerio.com', u'extmatrix.com', u'datafile.com',
         u'solidfiles.com', u'dl.free.fr', u'inclouddrive.com', u'zippyshare.com', u'unibytes.com', u'flashx.tv',
         u'canalplus.fr', u'redbunker.net', u'nowvideo.club', u'dailymotion.com', u'load.to', u'uploaded.net',
         u'scribd.com', u'big4shared.com', u'rockfile.eu', u'uptobox.com', u'filesabc.com', u'streamcherry.com',
         u'isra.cloud', u'filefactory.com', u'youporn.com', u'oboom.com', u'vimeo.com', u'real-debrid.com',
         u'redtube.com', u'file.al', u'faststore.org', u'soundcloud.com', u'gigapeta.com', u'share-online.biz',
         u'datei.to', u'datafilehost.com', u'depositfiles.com', u'rutube.ru', u'upstore.net', u'salefiles.com',
         u'streamango.com', u'cbs.com', u'worldbytez.com', u'turbobit.net', u'mega.co.nz', u'tusfiles.net',
         u'uploadc.com', u'wipfiles.net', u'hulkshare.com', u'rarefile.net', u'sendspace.com', u'vidoza.net',
         u'alfafile.net', u'keep2share.cc', u'yunfile.com', u'vidlox.tv', u'catshare.net', u'vk.com',
         u'clicknupload.me', u'userscloud.com', u'ulozto.net', u'easybytez.com']


def worker_thread(provider_name, provider_source):
    global RUNNING_PROVIDERS
    global TOTAL_SOURCES
    global PASSED_PROVIDERS
    global FAILED_PROVIDERS
    global providers_no_results
    RUNNING_PROVIDERS.append(provider_name)
    try:
        # Confirm Provider contains the movie function
        if not getattr(provider_source, test_mode, False):
            RUNNING_PROVIDERS.remove(provider_name)
            return

        if not getattr(provider_source, 'unit_test', False):
            if test_mode == 'movie':
                test_objects = movie_meta
            else:
                test_objects = episode_meta

            provider_results = []
            url = []
            start_time = time.time()
            current_meta = {}
            for i in test_objects:
                if TOTAL_RUNTIME > TIMEOUT and TIMEOUT_MODE: break

                print('')
                print('%s: Now testing -> %s' % (provider_name.upper(), i))
                print('')
                start_time = time.time()
                if len(provider_results) != 0:
                    break
                # Run movie Call
                if test_mode == 'movie':
                    url = provider_source.movie(i['imdb'], i['title'], i['localtitle'], i['aliases'], i['year'])
                    if url is None:
                        continue

                elif test_mode == 'episode':
                    url = provider_source.tvshow(i['show_imdb'], i['show_tvdb'], i['tvshowtitle'],
                                                 i['localtvshowtitle'], i['aliases'], i['year'])
                    if url is None:
                        continue

                    url = provider_source.episode(url, i['imdb'], i['tvdb'], i['title'], i['premiered'], i['season'],
                                                  i['episode'])
                    if url is None:
                        continue
                else:
                    raise Exception('wrong test type dumbass')

                # Run source call
                url = provider_source.sources(url, hosts, [])
                if url is None:
                    continue
                else:
                    if len(url) > 0:
                        provider_results = url
                        TOTAL_SOURCES += url
                    else:
                        continue
            if url is None: url = []
            # Gather time analytics
            runtime = time.time() - start_time

            PASSED_PROVIDERS.append((provider_name, url, runtime))
        else:
            start_time = time.time()
            # Provider has unit test entry point, run provider with it
            try:
                unit_test = provider_source.unit_test('movie', hosts)
            except Exception as e:
                FAILED_PROVIDERS.append((provider_name, e))
                return

            if unit_test is None:
                FAILED_PROVIDERS.append((provider_name, 'Unit Test Returned None'))
                return
            else:
                TOTAL_SOURCES += unit_test

            runtime = time.time() - start_time

            PASSED_PROVIDERS.append((provider_name, unit_test, runtime))

        RUNNING_PROVIDERS.remove(provider_name)

    except Exception as e:
        import traceback
        traceback.print_exc()
        RUNNING_PROVIDERS.remove(provider_name)
        # Appending issue provider to failed providers
        FAILED_PROVIDERS.append((provider_name, e))


if __name__ == '__main__':

    TOTAL_RUNTIME = 0

    print('Running Unit Tests. Please Wait...')

    # Build and run threads
    if test_type == 1:
        for provider in PROVIDER_LIST:
            workers.append(threading.Thread(target=worker_thread, args=(provider[0], provider[1])))

        for worker in workers:
            worker.start()
        time.sleep(1)

        while len(RUNNING_PROVIDERS) > 0:
            if TIMEOUT_MODE:
                if TOTAL_RUNTIME > TIMEOUT: break
            print('Running Providers [%s]: %s' % (len(RUNNING_PROVIDERS),
                                                  ' | '.join([i.upper() for i in RUNNING_PROVIDERS])))
            time.sleep(1)
            TOTAL_RUNTIME +=1

    else:
        print('Please Select a provider:')
        for idx, provider in enumerate(PROVIDER_LIST):
            print('%s) %s' % (idx, provider[0]))

        while True:
            try:
                choice = int(raw_input())
                provider = PROVIDER_LIST[choice]
                break
            except ValueError:
                print('Please enter a number')
            except IndexError:
                print("You've entered and incorrect selection")

        RUNNING_PROVIDERS.append('')
        worker_thread(provider[0], provider[1])

    # Print any failures to the console
    print(' ')
    print('Provider Failures:')
    print('##################')
    if len(FAILED_PROVIDERS) == 0:
        print('None')
        print(' ')
    else:
        for provider in FAILED_PROVIDERS:
            print('Provider Name: %s' % provider[0].upper())
            print('Exception: %s' % provider[1])
            print(' ')

    # TODO Expand analytical information
    print('Analytical Data:')
    print('################')
    if test_type == 1:
        print('Total Runtime: %s' % TOTAL_RUNTIME)
        print('Total Passed Providers: %s' % len(PASSED_PROVIDERS))
        print('Total Failed Providers: %s' % len(FAILED_PROVIDERS))
        print('Skipped Providers: %s' % (len(PROVIDER_LIST) - (len(PASSED_PROVIDERS) + len(FAILED_PROVIDERS))))
        pre_dup = TOTAL_SOURCES
        post_dup = {}
        for i in TOTAL_SOURCES:
            post_dup.update({str(i['url']): i})
        total_duplicates = len(pre_dup) - len([i for i in post_dup])
        print('Total Sources: %s' % len(post_dup))
        print('Total Duplicates: %s' % total_duplicates)
        print('   ')
        print('#################')
        print('Passed Providers:')


        base_output_path = os.path.join(os.getcwd(), 'test-results', '-'.join(folders))
        output_filename = 'results-%s.csv' % time.time()

        if not os.path.exists(base_output_path):
            os.makedirs(base_output_path)

        with open(os.path.join(base_output_path, output_filename), 'w+') as output:
            output.write('Provider Name,Number Of Sources,Runtime\n')
            for i in PASSED_PROVIDERS:
                try:
                    if i[1] is not None:
                        output.write('%s,%s,%s\n' % (i[0], len(i[1]), i[2]))
                except:
                    pass

    elif test_type == 0:
        all_sources = PASSED_PROVIDERS[0][1]
        if all_sources is None:
            all_sources = []
        print('Total No. Sources: %s' % len(all_sources))