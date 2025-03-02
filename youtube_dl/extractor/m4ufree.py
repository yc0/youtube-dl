from __future__ import unicode_literals

import re
import codecs

from .common import InfoExtractor
from ..utils import (
    ExtractorError,
    urlencode_postdata,
    unsmuggle_url,
    std_headers
)


def unicode_escape(s):
    decoder = codecs.getdecoder('unicode_escape')
    return re.sub(
        r'\\u[0-9a-fA-F]{4,}',
        lambda m: decoder(m.group(0))[0],
        s)


class M4ufreeIE(InfoExtractor):
    IE_NAME = 'm4ufree'
    _USER_AGENT = 'Mozilla/5.0 (X11; Linux i686; rv:47.0) Gecko/20100101 Firefox/47.0'
    _VALID_URL = r'''(?x)
                    https?://
                        (?:
                            (?:www\.)?m4ufree\.(?:com|ac|io|tv|co)/
                        )
                        (?P<id>[^\.]+)
                        \.html
                    '''
    _TESTS = [{
        'url': 'http://m4ufree.com/watch-oeia-kingsman-the-golden-circle-2017-movie-online-free-m4ufree.html',
        'md5': '7a67a6082f23f7c18e1c9006bab6627f',
        'info_dict': {
            'id': 'watch-oeia-kingsman-the-golden-circle-2017-movie-online-free-m4ufree',
            'ext': 'mp4',
            'title': 'Kingsman: The Golden Circle (2017)'
        }
    }, {
        'url': 'http://m4ufree.com/watch-oei8-the-foreigner-2017-movie-online-free-m4ufree.html',
        'md5': '52e49c3a7b0ea419f090b50103d1c1e2',
        'info_dict': {
            'id': 'watch-oei8-the-foreigner-2017-movie-online-free-m4ufree',
            'ext': 'mp4',
            'title': 'The Foreigner (2017)'
        }
    }, {
        'url': 'http://m4ufree.com/watch-y0ti-olafs-frozen-adventure-2017-movie-online-free-m4ufree.html',
        'only_matching': True
    }]

    def _retrieve_url(self, video_id, web, _url):
        web = re.sub(r'([^"|^\'])(file|type|label)([^"|^\'])',r'\g<1>"\g<2>"\g<3>',web)
        web = re.sub(r"'", "\"", web)
        # self.to_screen(web)
        if re.search(r'src="https://openload.co/embed', web):
            url = self._html_search_regex(
                r'iframe[^s]+src="(?P<url>[^"]+)"',
                web, 'openload url retrieve', default=None, group='url')
            headers = std_headers
            headers['Referer'] = url
            return [{'file': url, 'label': '720p'}]
        if re.search(r'src="https://drive.google', web):
            return []
        try:
            json = self._parse_json(
                self._html_search_regex(
                    r'(?:playerInstance.setup\(\{[^s]+sources:)(?P<json>[^\]]+]),',
                    web,
                    'content path',
                    default=None,
                    group='json'),
                video_id,
                fatal=False)
        except ExtractorError as ee:
            extra = self._html_search_regex(
                r'(?:playerInstance.setup\(\{[^s]+sources:)(?P<json>[^\]]+]),',
                web, 'content path', default=None, group='json')
            extra = re.sub(r"'", "\"", extra)
            # re.purge()
            # print(extra)
            if not re.match(r'[{|,]([^"]?\w+[^"]?):', extra):
                extra = re.sub(
                    r'([{|,])\s*([^"]?\w+[^"]?):',
                    r'\g<1>"\g<2>":',
                    extra)
        except TypeError as ee:
            self.to_screen(ee)
            return []

        self._validate(json)
        return json if json[-1].get('file') and self._request_webpage(
            json[-1].get('file'), video_id, note='Requesting source file',
            errnote='Unable to request source file', headers={
                'Referer': _url,
                'User-Agent': "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_13_2) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/63.0.3239.132 Safari/537.36",
                'Range' : 'bytes=0-',
                'Accept-Encoding':'identity;q=1, *;q=0'
            }, fatal=False) else []

    def _validate(self, j):
        s = j[-1].get('file')
        if s:
            if re.search(r'view\.php\?v=', j[-1].get('file')):
                j[-1]['file'] = re.sub(r'(view\.php\?v=[^"]+)',
                                       r'https://m4ufree.co/\g<1>', s)

    def _real_extract(self, url):
        url, data = unsmuggle_url(url, {})
        headers = std_headers
        # if 'http_headers' in data:
        #     headers = headers.copy()
        #     headers.update(data['http_headers'])
        if 'Referer' not in headers:
            headers['Referer'] = url
            headers['Range'] = 'bytes=0-'
            headers['User-Agent'] = "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_13_2) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/63.0.3239.132 Safari/537.36"
            headers['Accept-Encoding'] = 'identity;q=1, *;q=0'

        
        video_id = self._match_id(url)
        webpage = self._download_webpage(
            'http://m4ufree.com/%s.html' % video_id, video_id)

        # mobj = re.search(r'<h1 class="inlineError">(.+?)</h1>', webpage)
        # if mobj:
        #     raise ExtractorError('%s said: %s' % (self.IE_NAME, clean_html(mobj.group(1))), expected=True)

        title = self._html_search_regex(
            r'(?:class="h3-detail"\ssrc="images/dl.png" .*alt=")(?P<title>[^"]*)',
            webpage, 'title', default=None,
            group='title') or self._og_search_title(webpage)
        # quality = self._html_search_regex(
        #     r'Quality:[^\>]+\>(?P<quality>\w+)',
        #     webpage, 'quality', default=None,
        #     group='quality') or 'UNKNOWN'

        # thumbnail = self._search_regex(
        #     r'url_bigthumb=(.+?)&amp', webpage, 'thumbnail', fatal=False)
        # duration = int_or_none(self._og_search_property(
        #     'duration', webpage, default=None)) or parse_duration(
        #     self._search_regex(
        #         r'<span[^>]+class=["\']duration["\'][^>]*>.*?(\d[^<]+)',
        #         webpage, 'duration', fatal=False))

        php_encode = self._html_search_regex(
            r'(?:var _[^\=]*)=(?P<php>[^;]*);\$\(do',
            webpage, 'php_path', default=None, group='php')

        php_decode = eval(php_encode)
        # m4u_data = self._html_search_regex(
        #     r'''(?x)
        #             (?:class="singlemv\sactive"\sdata=")(?P<data>[^"]*)
        #         ''', webpage, 'm4u data', default=None, group='data')

        # form_data = {
        #     'm4u': m4u_data
        # }
        # print(php_decode)
        # webpage2 = self._download_webpage(
        #     'http://m4ufree.com/%s' % php_decode[2], None, 'get m4u content',
        #     data=urlencode_postdata(form_data),
        #     headers={
        #         'Content-Type': 'application/x-www-form-urlencoded',
        #         'Referer': url,
        #     })
        # json = []
        # json += self._retrieve_url(video_id,webpage2)
        # self._validate(json)
        # print(json)
        # urlh = self._request_webpage(
        #     json[-1].get('file'), video_id, note='Requesting source file',
        #     errnote='Unable to request source file', fatal=False)
        # print(urlh)
        # if not urlh:
        json = []
        # self.to_screen(webpage)
        for m4u in re.findall(
            r'(?:class="singlemv[^"]*"[^d]+data=")(?P<data>[^"]*)',
                webpage):
            print(m4u)
            form_data = {
                'm4u': m4u
            }
            m4u_msg = 'get m4u: %s' % m4u
            webpage2 = self._download_webpage(
                'http://m4ufree.com/%s' % php_decode[2], None, m4u_msg,
                data=urlencode_postdata(form_data),
                headers={
                    'Content-Type': 'application/x-www-form-urlencoded',
                    'Referer': url,
                }, fatal=False)
            # print(webpage2)
            json += self._retrieve_url(video_id, webpage2, url)
        json.sort(key=lambda d: (
            int(d.get('label').replace('p', '')), len(d.get('file'))))

        # print(webpage2)
        # formats = [{
        #     'url': unicode_escape(url),
        #     'ext': 'mp4',
        #     'quality': quality
        # } for url in map(lambda _: _.get('file'), json)]
        if not json:
            errmsg = '%s: Failed to get a movie ' % video_id
            raise ExtractorError(errmsg)
        # print(json)
        formats = [{
            'url': unicode_escape(json[-1].get('file')),
            'ext': 'mp4'
        }]
        # print(formats)
        self._sort_formats(formats)

        return {
            'id': video_id,
            'formats': formats,
            'title': title
            # 'duration': duration,
            # 'thumbnail': thumbnail,
            # 'age_limit': 18,
        }
