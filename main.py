from bs4 import BeautifulSoup
import urllib3
import urllib
import re
import os
import sys
import zipfile
import parmap
import shutil
import multiprocessing
import tqdm

MANAMOA_URL = 'https://manamoa.net'

urllib3.disable_warnings()


def downloader(i, downloadPath, mangaTitle):
    os.mkdir('./tmp/%s' % i[0])

    while True:
        try:
            images = []

            while True:
                try:
                    mangaHtml = http.request('GET', MANAMOA_URL + i[1]).data.decode('utf-8')

                    n = 1

                    with zipfile.ZipFile('%s/%s/%s.cbz' % (downloadPath, mangaTitle, i[0]), 'w') as z:
                        for j in (j.replace('\\', '') for j in
                                  re.search(r'(?<=img_list = \[\").*(?=\"\])', mangaHtml).group().split('","')):
                            fileName = '%d.%s' % (n, j.split('.')[-1])
                            with open('./tmp/%s/%s' % (i[0], fileName), 'wb') as f:
                                f.write(http.request('GET', j).data)

                            z.write('./tmp/%s/%s' % (i[0], fileName))

                            n += 1

                        z.close()

                        shutil.rmtree('./tmp/%s' % i[0])

                    break

                except urllib3.exceptions.SSLError:
                    pass

                except urllib3.exceptions.MaxRetryError:
                    pass

            break

        except urllib3.exceptions.SSLError:
            pass

        except urllib3.exceptions.MaxRetryError:
            pass


if __name__ == "__main__":
    http = urllib3.PoolManager()

    downloadPath = input('다운로드할 주소: ')

    # search
    while True:
        word = input('검색어 입력: ')

        mangaListHtml = http.request('GET', MANAMOA_URL + '/bbs/search.php?' + urllib.parse.urlencode({
            'stx': word
        })).data.decode('utf-8')

        soup = BeautifulSoup(mangaListHtml, 'html.parser')

        mangaCandidates = []
        mangaSubjectList = tuple(map(str, soup.findAll('div', {'class': 'manga-subject'})))

        if len(mangaSubjectList) == 0:
            print('검색 결과가 없습니다')
            continue

        for i in mangaSubjectList:
            mangaCandidates.append((re.search(r'(?<=\d\">)(.|\n)*(?=</a>)', i).group().strip(),
                                    re.search(r'(?<=<a href=\").*(?=\">)', i).group().replace('&amp;', '&').strip()))

        for i in range(len(mangaCandidates)):
            print('%d) %s' % (i + 1, mangaCandidates[i][0]))

        while True:
            n = int(input())

            if 1 <= n <= len(mangaCandidates):
                break
            else:
                print('다시 입력해주세요')

        mangaTitle, mangaListUrl = mangaCandidates[n - 1]
        mangaTitle = mangaTitle.replace('/', '_')

        break

    mangaList = []

    html = http.request('GET', MANAMOA_URL + mangaListUrl).data.decode('utf-8')

    soup = BeautifulSoup(html, 'html.parser')

    if not os.path.exists('%s/%s' % (downloadPath, mangaTitle)):
        os.mkdir('%s/%s' % (downloadPath, mangaTitle))

    for i in map(str, soup.findAll('div', {'class': 'slot'})):
        mangaList.append((re.search(r'.*(?=<span[^>])', i).group().replace(mangaTitle, '').strip(),
                          re.search(r'(?<=<a href=").*(?=">)', i).group().replace('&amp;', '&')))

    if os.path.exists('./tmp/'):
        shutil.rmtree('./tmp/')

    os.mkdir('./tmp/')

    parmap.map(downloader, mangaList, downloadPath, mangaTitle, pm_pbar=True, pm_processes=multiprocessing.cpu_count())
