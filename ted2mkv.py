#!/usr/bin/env python
# ted2mkv.py - Download TED video with its subtitles and metadata and
#              create an MKV out of it.
# Copyright (C) 2012  Mansour <mansour@oxplot.com>
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program.  If not, see <http://www.gnu.org/licenses/>.

from __future__ import division
from __future__ import print_function
from __future__ import unicode_literals
from subprocess import Popen, PIPE
import argparse
import json
import os
import re
import sys

# Version dependent imports

try:
  from cStringIO import StringIO
except ImportError:
  from io import BytesIO as StringIO

try:
  from urllib2 import urlopen, Request, HTTPError
except ImportError:
  from urllib.request import urlopen, Request
  from urllib.error import HTTPError

_progname = 'ted2mkv'
_USERAGENT = 'Mozilla/5.0 (X11; U; Linux x86_64; en-US; rv:1.9.0.5)' \
            ' Gecko/2008121622 Ubuntu/8.04 (hardy) Firefox/3.0.5'
_devnull = open(os.devnull, 'wb')
monmap = {'jan': 1, 'feb': 2, 'mar': 3, 'apr': 4, 'may': 5, 'jun': 6,
  'jul': 7, 'aug': 8, 'sep': 9, 'oct': 10, 'nov': 11, 'dec': 12}

class TED2MKVError(Exception):
  pass

class TED2MKV(object):

  def __init__(self, url, outdir = '.'):

    self.url = url
    self.outdir = outdir
    self.clear_before = False
    self.keep_after = False
    self.overwrite_mkv = False

  def convert(self):
    try:
      self._convert()
    except KeyboardInterrupt:
      raise TED2MKVError('interrupted, use without -c to resume')

  def _convert(self):
    self._load_talk()

    if not self.overwrite_mkv and os.path.exists(self._mkv_path):
      raise TED2MKVError('mkv exists, skipping')

    if self.clear_before:
      self._clear()

    self._write_tags()
    self._download_media()
    self._download_subtitles()
    self._download_video()
    self._make_mkv()

    if not self.keep_after:
      self._clear()

  def _clear(self):
    for f in os.listdir(self.outdir):
      if f.startswith(".%s." % self._name):
        os.unlink(os.path.join(self.outdir, f))

  def _load_talk(self):

    # Download the talk page

    headers = {"User-Agent": _USERAGENT}
    talk_page = urlopen(Request(self.url, headers=headers)).read()
    talk_page = talk_page.decode('utf8')

    # Get the talk ID and name and headline

    m = re.search(
      r'<div id="share_and_save"[^>]*?data-id="(\d+)"'
      r'.*?data-slug="([^"]+)"',
      talk_page, re.DOTALL)
    self._id = int(m.group(1))
    self._name = m.group(2)

    # Get the dates and headline

    self._summary = re.sub(r'<[^>]+>', ' ', re.search(
      r'<p id="tagline"\s*>(.+?)</p>',
      talk_page, re.DOTALL).group(1).strip())
    self._headline = re.search(
      r'<span\s+id="altHeadline"\s*>([^<]+)</span>',
      talk_page).group(1).strip()
    m = re.search(
      r'<strong>Filmed</strong>\s*([A-Za-z]{3})\s+(\d{4})',
      talk_page)
    self._filmed = (int(m.group(2)), monmap[m.group(1).lower()])
    m = re.search(
      r'<strong>Posted</strong>\s*([A-Za-z]{3})\s+(\d{4})',
      talk_page)
    self._posted = (int(m.group(2)), monmap[m.group(1).lower()])
    self._keywords = re.search(
      r'<meta name="keywords" content="([^"]+)"',
      talk_page).group(1)

    # Get the list of subtitles

    self._langs = re.findall(
      r'<option value="([^"]+)"[^>]*>([^<]+)</option>',
      (re.search(r'<select name="subtitles_language_select"[^>]*>'
                r'(.+?)</select>', talk_page, re.DOTALL)
        or re.search('()', ''))
      .group(1))

    # Get the subtitle time offset

    self._subt_off = int(float(re.search(
      r'var pad_seconds = ([0-9.]+)', talk_page).group(1)
      ) * 1000)

    # Get the URL for video

    vid_filename = re.search(
      r'<a id="no-flash-video-download"'
      r' href="http://download.ted.com/talks/([^"]+?)\.mp4"',
      talk_page).group(1)
    self._vid_url = 'http://download.ted.com/talks/' \
      + vid_filename + '-480p.mp4?apikey=TEDDOWNLOAD'

    # Get the URL for cover

    self._cover_url = re.search(
      r'<meta property="og:image" content="([^"]+)"',
      talk_page).group(1)

    # Some convenience stuff

    self._mkv_path = os.path.join(
      self.outdir, '%s.mkv' % self._name)
    self._tags_path = os.path.join(
      self.outdir, '.%s.tags' % self._name)
    self._cover_path = os.path.join(
      self.outdir, '.%s.cover' % self._name)
    self._vid_path = os.path.join(
      self.outdir, '.%s.mp4' % self._name)

  def _download_media(self):

    if os.path.exists(self._cover_path):
      return

    tmppath = self._cover_path + ".tmp"
    headers = {"User-Agent": _USERAGENT}
    open(tmppath, 'wb').write(
      urlopen(Request(self._cover_url, headers=headers)).read())
    os.rename(tmppath, self._cover_path)

  def _download_video(self):

    lfile = open(self._vid_path, 'ab')
    headers = {"Range": "bytes=%d-" % lfile.tell(),
      "User-Agent": _USERAGENT}
    try:
      rfile = urlopen(Request(self._vid_url, headers=headers))
    except HTTPError as e:
      if e.code == 416:
        return
      else:
        raise e
    try:
      if rfile.code != 206:
        raise TED2MKVError("couldn't download video")
      while True:
        din = rfile.read(32000)
        if not din:
          break
        lfile.write(din)
    finally:
      lfile.close()
      rfile.close()

  def _download_subtitles(self):

    avail_subs = []
    for ln, lnname in self._langs:

      path = os.path.join(
        self.outdir, '.%s.%s.srt' % (self._name, ln))
      if os.path.exists(path):
        avail_subs.append((ln, lnname))
        continue
      tmppath = path + ".tmp"

      url = 'http://www.ted.com/talks/subtitles/id/%d/lang/%s' \
        % (self._id, ln)
      headers = {"User-Agent": _USERAGENT}
      try:
        jsonsubt = urlopen(Request(url, headers=headers)).read()
      except HTTPError as e:
        if e.code == 404:
          print("%s: subtitle for %s (%s) is not found on server"
                % (_progname, lnname, ln), file=sys.stderr)
        else:
          raise e
      else:
        srtsubt = self._tosrt(json.loads(jsonsubt.decode('utf8')))
        open(tmppath, 'wb').write(srtsubt)

        os.rename(tmppath, path)
        avail_subs.append((ln, lnname))

    self._langs = avail_subs

  def _write_tags(self):

    tpl = '<Simple><Name>%s</Name><String>%s</String></Simple>'
    tagtpl = '<?xml version="1.0" encoding="utf-8"?>' \
             '<!DOCTYPE Tags SYSTEM "matroskatags.dtd">' \
             '<Tags><Tag><Targets><TargetType>EPISODE</TargetType>' \
             '</Targets>%s</Tag></Tags>'
    static_xml = tpl % ('ARTIST', 'TED')
    static_xml += tpl % ('PUBLISHER', 'TED')
    static_xml += tpl % ('ENCODED_BY', _progname)
    static_xml += tpl % ('COPYRIGHT', 'TED Conferences, LLC')
    static_xml += tpl % ('LICENSE', 'TED Creative Commons License')
    static_xml += tpl % ('GENRE', 'Podcast')
    summary_xml = tpl % ('SUMMARY', self._summary)
    summary_xml += tpl % ('DESCRIPTION', self._summary)
    keywords_xml = tpl % ('KEYWORDS', self._keywords)
    title_xml = tpl % ('TITLE', self._headline)
    filmed_xml = tpl % ('DATE_RECORDED', '%04d-%02d' % self._filmed)
    posted_xml = tpl % ('DATE_RELEASED', '%04d-%02d' % self._posted)
    url_xml = tpl % (
      'URL','http://www.ted.com/talks/%s.html' % self._name)
    final_xml = tagtpl % (
      title_xml + filmed_xml + posted_xml + url_xml + static_xml
      + summary_xml + keywords_xml
    )
    open(self._tags_path, 'wb').write(final_xml.encode('utf8'))

  def _make_mkv(self):

    tmpmkvpath = os.path.join(
      self.outdir, '.%s.mkv.tmp' % self._name)

    args = [
      'mkvmerge', '--default-language', 'eng', '-q',
      '-o', tmpmkvpath,
      '--global-tags', self._tags_path,
      '--attachment-description', 'Cover Art',
      '--attachment-mime-type', 'image/jpeg',
      '--attachment-name', 'cover_land.jpg',
      '--attach-file', self._cover_path
    ]

    for ln, lnname in self._langs:
      path = os.path.join(
        self.outdir, '.%s.%s.srt' % (self._name, ln))
      if ln == 'en':
        args.extend(['--default-track', '0'])
      args.extend(['--sub-charset', '0:utf-8',
        '--track-name', '0:%s' % lnname,
        '--language', '0:%s' % ln.split('-')[0], path
        ])

    args.append(self._vid_path)
    proc = Popen(args)
    proc.communicate()
    ecode = proc.wait()
    if ecode == 2:
      raise TED2MKVError('mkvmerge failed')

    os.rename(tmpmkvpath, self._mkv_path)

  def _tosrt(self, jsonsubt):
    buf = StringIO()
    num = 1
    fmt = '%d\r\n%02d:%02d:%02d,%03d -->' \
          ' %02d:%02d:%02d,%03d\r\n%s\r\n\r\n'
    for part in jsonsubt['captions']:
      start = part['startTime'] + self._subt_off
      end = start + part['duration']
      text = part['content']
      buf.write((fmt % (
        (num,) + _ts_parts(start) + _ts_parts(end) + (text,)
      )).encode('utf8'))
      num += 1
    return buf.getvalue()

def _ts_parts(ts):

  ms = ts % 1000
  ts = ts // 1000
  h = ts // 3600
  m = (ts % 3600) // 60
  s = ts % 60
  return (h, m, s, ms)

def main():

  parser = argparse.ArgumentParser(
    formatter_class=argparse.RawDescriptionHelpFormatter,
    description='TED scraper'
  )
  parser.add_argument(
    'url',
    metavar='<url>',
    help='url to TED talk'
  )
  parser.add_argument(
    '-o', '--outdir',
    default='.',
    metavar='<dir>',
    help='directory path where the MKV file will be saved to -'
         ' default is current directory'
  )
  parser.add_argument(
    '-c', '--clear-before',
    action='store_true',
    help='clear cache for this video before starting'
  )
  parser.add_argument(
    '-k', '--keep-after',
    action='store_true',
    help='keep the cache for this video after saving the mkv'
  )
  parser.add_argument(
    '-f', '--overwrite-mkv',
    action='store_true',
    help='do not skip if final mkv file present'
  )
  args = parser.parse_args()

  try:
    converter = TED2MKV(args.url)
    converter.outdir = args.outdir
    converter.clear_before = args.clear_before
    converter.keep_after = args.keep_after
    converter.overwrite_mkv = args.overwrite_mkv
    converter.convert()
  except TED2MKVError as e:
    print('%s: error: %s' % (_progname, e.args[0]), file=sys.stderr)
    exit(2)

if __name__ == '__main__':
  main()
