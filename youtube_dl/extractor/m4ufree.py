from __future__ import unicode_literals

import re
import codecs

from .common import InfoExtractor
from ..utils import (
    ExtractorError,
    urlencode_postdata
)


def unicode_escape(s):
    decoder = codecs.getdecoder('unicode_escape')
    return re.sub(
        r'\\u[0-9a-fA-F]{4,}',
        lambda m: decoder(m.group(0))[0],
        s)


class M4ufreeIE(InfoExtractor):
    IE_NAME = 'm4ufree'
    _VALID_URL = r'''(?x)
                    https?://
                        (?:
                            (?:www\.)?m4ufree\.(?:com|ac)/
                        )
                        (?P<id>[^\.]+)
                        \.html
                    '''
    _TESTS = [{
        'url': 'http://m4ufree.com/watch-oeia-kingsman-the-golden-circle-2017-movie-online-free-m4ufree.html',
        'md5': '9f6ee991fa20323dec04bcf5971317dc',
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

    def _real_extract(self, url):
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
        quality = self._html_search_regex(
            r'Quality:[^\>]+\>(?P<quality>\w+)',
            webpage, 'quality', default=None,
            group='quality') or 'UNKNOWN'

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
        m4u_data = self._html_search_regex(
            r'''(?x)
                    (?:class="singlemv\sactive"\sdata=")(?P<data>[^"]*)
                ''', webpage, 'm4u data', default=None, group='data')

        # if not m4u_data:
        #     m4u_datas = [ m4u_data for m4u_data in re.findall(r'(?:class="singlemv"\sdata=")(?P<data>[^"]*)', webpage)]
        #     print(m4u_datas)

        form_data = {
            'm4u': m4u_data
        }
        # print(form_data, title, php_decode)
        webpage2 = self._download_webpage(
            'http://m4ufree.com/%s' % php_decode[2], None, 'get context list',
            data=urlencode_postdata(form_data),
            headers={
                'Content-Type': 'application/x-www-form-urlencoded',
                'Referer': url,
            })
        # print(webpage2)
        json = None
        try:
            json = self._parse_json(
                self._html_search_regex(
                    r'(?:playerInstance.setup\(\{[^s]+sources:)(?P<json>[^\]]+]),',
                    webpage2,
                    'content path',
                    default=None,
                    group='json'),
                video_id,
                fatal=False)
        except ExtractorError as ee:
            extra = self._html_search_regex(
                r'(?:playerInstance.setup\(\{[^s]+sources:)(?P<json>[^\]]+]),',
                webpage2, 'content path', default=None, group='json')
            extra = re.sub(r"'", "\"", extra)
            # re.purge()
            # print(extra)
            if not re.match(r'[{|,]([^"]?\w+[^"]?):', extra):
                extra = re.sub(
                    r'([{|,])\s*([^"]?\w+[^"]?):',
                    r'\g<1>"\g<2>":',
                    extra)
            json = self._parse_json(extra, video_id, fatal=True)
        # print(webpage2)
        json.sort(key=lambda d: int(d.get('label').replace('p', '')))
        formats = [{
            'url': unicode_escape(url),
            'ext': 'mp4',
            'quality': quality
        } for url in map(lambda _: _.get('file'), json)]
        # formats = [{
        #     'url': unicode_escape(json[-1].get('file')),
        #     'ext': 'mp4'
        # } ]
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
