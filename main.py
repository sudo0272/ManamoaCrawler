from bs4 import BeautifulSoup
import urllib3
import urllib
import re
import os
import sys
import zipfile

MANAMOA_URL = 'https://manamoa.net'

urllib3.disable_warnings()

if __name__ == "__main__":
    http = urllib3.PoolManager()

    downloadPath = input('다운로드할 주소: ')

    # search
    while True:
        word = input('검색어 입력: ')

        mangaListHtml = http.request('GET', MANAMOA_URL + '/bbs/search.php?' + urllib.parse.urlencode(
            {'stx': word})).data.decode('utf-8')
        soup = BeautifulSoup(mangaListHtml, 'html.parser')

        mangaCandidates = []
        mangaSubjectList = tuple(map(str, soup.findAll('div', {'class': 'manga-subject'})))

        if len(mangaSubjectList) == 0:
            print('검색 결과가 없습니다')
            continue

        for i in mangaSubjectList:
            mangaCandidates.append((re.search(r'(?<=\d\">)(.|\n)*(?=<\/a>)', i).group().strip(),
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

        break

    mangaList = []

    html = http.request('GET', MANAMOA_URL + mangaListUrl).data.decode('utf-8')

    soup = BeautifulSoup(html, 'html.parser')

    if not os.path.exists('%s/%s' % (downloadPath, mangaTitle)):
        os.mkdir('%s/%s' % (downloadPath, mangaTitle))

    for i in map(str, soup.findAll('div', {'class': 'slot'})):
        mangaList.append((re.search(r'.*(?=<span[^>])', i).group().replace(mangaTitle, '').strip(),
                          re.search(r'(?<=<a href=").*(?=">)', i).group().replace('&amp;', '&')))

    os.mkdir('./tmp/')

    for i in mangaList:
        while True:
            try:
                images = []

                while True:
                    try:
                        print('%s html파일 다운로드중...' % (i[0]))
                        mangaHtml = http.request('GET', MANAMOA_URL + i[1]).data.decode('utf-8')

                        print('%s html파일 파싱중...' % (i[0]))
                        n = 1

                        with zipfile.ZipFile('%s/%s/%s.cbz' % (downloadPath, mangaTitle, i[0]), 'w') as z:
                            for j in (j.replace('\\', '') for j in
                                      re.search(r'(?<=img_list = \[\").*(?=\"\])', mangaHtml).group().split('","')):
                                fileName = '%d.%s' % (n, j.split('.')[-1])
                                with open('./tmp/%s' % fileName, 'wb') as f:
                                    print('%s의 %d번째 파일 다운로드중...' % (i[0], n))
                                    f.write(http.request('GET', j).data)

                                z.write('./tmp/%s' % fileName)

                                n += 1

                            z.close()

                            for i in os.listdir('./tmp/'):
                                os.remove('./tmp/%s' % i)

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

    # print(mangaList,  end='\n\n\n')