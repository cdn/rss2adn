#!/usr/bin/env python
# vim:ts=4:sw=4:ft=python:fileencoding=utf-8
"""Checks rss feed and posts elsewhere.

Check an rss feed and if the latest entry is different then post it to a social network.

"""


import sys
import os
import traceback
import cPickle
from ConfigParser import SafeConfigParser
from optparse import OptionParser
from six.moves.html_parser import HTMLParser

import feedparser
import adnpy

__version__ = '0.0.3'

config = None

def post_update(status):
    global config
    consumer_key = config.get('adn', 'key')
    consumer_secret = config.get('adn', 'secret')
    access_token = config.get('adn', 'token')
    adnpy.api.add_authorization_token(access_token)
    try:
#       post, meta = adnpy.api.create_post(data={'text': 'Hello World'})
        post, meta = adnpy.api.create_post(data=status)
    except Exception, e:
        print "Error occurred while updating status:", e
        sys.exit(1)
    else:
        return True


def main():
    """The main function."""
    global config
    parser = OptionParser(version='%prog v' + __version__)
    parser.add_option('-c', '--config', default='config.ini',
                      help='Location of config file (default: %default)',
                      metavar='FILE')
    parser.add_option('-a', '--all', action='store_true', default=False,
                      dest='all',
                      help='Send all RSS items as tweet')
    parser.add_option('-l', '--limit', dest='limit',
                      default=10,
                      help='Use with all parameters, send the first 10 feeds as a tweet')
    (options, args) = parser.parse_args()
    config = SafeConfigParser()
    if not config.read(options.config):
        print 'Could not read config file'
        sys.exit(1)
    rss_uri = config.get('rss', 'uri')
    feed = feedparser.parse(rss_uri)
    # lots of scary warnings about possible security risk using this method
    # but for local use I'd rather do this than a try-catch with open()
    cachefile = config.get('cache', 'file')
    if not os.path.isfile(cachefile):
        # make a blank cache file
        cPickle.dump({'id': None}, open(cachefile, 'wb'), -1)

    cache = cPickle.load(open(cachefile))
    h = HTMLParser()
    if options.all:
        tweet_count = 0
        for entry in feed['entries']:
            rss = {
                'id': entry['id'],
                'link': entry['link'],
                'title': h.unescape(entry['title']),
                'author': entry['author'],
                'summary': entry['summary'],
            }

            if 'media_content' in entry:
                rss['media_content'] = entry['media_content']
                print(rss['media_content'])
            if 'media_thumbnail' in entry:
                rss['media_thumbnail'] = entry['media_thumbnail']
                print(rss['media_thumbnail'])

#            post_update({"text": "%s %s"} % (rss['title'], rss['link']))
#            post_update({"text": rss['title'] + " " + rss['link']})
#            post_update({"text": "[" + rss['title'] + "](" + rss['link'] + ")", "entities": {"parse_markdown_links": True}})
            post_text = "[" + rss['title'] + "](" + rss['link'] + ")"
            entity = {"parse_markdown_links": True}
            anno = [{"type": "net.app.core.crosspost", "value": {"canonical_url": rss['link']}}]

# mashable 720x480 *
# mental_floss 640x430
# techcrunch 680x453
            if 'media_thumbnail' in rss:
                embed = {
                    "type": "net.app.core.oembed",
                    "value": {
                        "embeddable_url": rss['link'],
                        "height": rss['media_thumbnail'][0]['height'],
                        "thumbnail_height": 480,
                        "thumbnail_url": rss['media_thumbnail'][0]['url'],
                        "thumbnail_width": rss['media_thumbnail'][0]['width'],
                        "title": rss['title'],
                        "type": "photo",
                        "url": rss['media_thumbnail'][0]['url'],
                        "version": "1.0",
                        "width": 720
                    }
                }
                anno.append(embed)

            cite = {"type":"nl.chrs.pooroeuvre.item.author","value":{"author": rss['author']}}
            anno.append(cite)
            post_update({"text": post_text, "entities": entity, "annotations": anno})

            # We keep the first feed in the cache, to use rss2twitter in normal mode the next time
            if tweet_count == 0:
                cPickle.dump(rss, open(cachefile, 'wb'), -1)

            tweet_count += 1
            if tweet_count >= options.limit:
                break
    else:
        rss = {
            'id': feed['entries'][0]['id'],
            'link': feed['entries'][0]['link'],
            'title': h.unescape(feed['entries'][0]['title']),
            'author': feed['entries'][0]['author'],
            'summary': feed['entries'][0]['summary'],
        }

        if 'media_content' in feed['entries'][0]:
            rss['media_content'] = feed['entries'][0]['media_content']
            print(rss['media_content'])
        if 'media_thumbnail' in feed['entries'][0]:
            rss['media_thumbnail'] = feed['entries'][0]['media_thumbnail']
            print(rss['media_thumbnail'])

#        print(rss['media_content'])
#        print(rss['media_thumbnail'])
#        sys.exit(0)

        # compare with cache
        if cache['id'] != rss['id']:
            #print 'new post'
            post_text = "[" + rss['title'] + "](" + rss['link'] + ")"
            post_text = "[%s](%s)" % (rss['title'], rss['link'])
            entity = {"parse_markdown_links": True}
            anno = [{"type": "net.app.core.crosspost", "value": {"canonical_url": rss['link']}}]

# mashable 720x480
# techcrunch 680x453
            if 'media_thumbnail' in rss:
                if 'height' in rss['media_thumbnail'][0]:
                    h = rss['media_thumbnail'][0]['height']
                    w = rss['media_thumbnail'][0]['width']
                else:
                    h = 453
                    w = 680
                embed = {
                    "type": "net.app.core.oembed",
                    "value": {
                        "embeddable_url": rss['link'],
                        "height": h,
                        "thumbnail_height": h,
                        "thumbnail_url": rss['media_thumbnail'][0]['url'],
                        "thumbnail_width": w,
                        "title": rss['title'],
                        "type": "photo",
                        "url": rss['media_thumbnail'][0]['url'],
                        "version": "1.0",
                        "width": w
                    }
                }
                anno.append(embed)
# guardian 460x276/140x84
            elif 'media_content' in rss:
                if 'width' in rss['media_content'][1]:
                    h = 276
                    w = rss['media_content'][1]['width']
                embed = {
                    "type": "net.app.core.oembed",
                    "value": {
                        "embeddable_url": rss['link'],
                        "height": h,
                        "thumbnail_height": h,
                        "thumbnail_url": rss['media_content'][1]['url'],
                        "thumbnail_width": w,
                        "title": rss['title'],
                        "type": "photo",
                        "url": rss['media_content'][1]['url'],
                        "version": "1.0",
                        "width": w
                    }
                }
                anno.append(embed)

            cite = {"type":"nl.chrs.pooroeuvre.item.author","value":{"author": rss['author']}}
            anno.append(cite)

            post_update({"text": post_text, "entities": entity, "annotations": anno})
            cPickle.dump(rss, open(cachefile, 'wb'), -1)


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt, e:
        # Ctrl-c
        raise e
    except SystemExit, e:
        # sys.exit()
        raise e
    except Exception, e:
        print "ERROR, UNEXPECTED EXCEPTION"
        print str(e)
        traceback.print_exc()
        sys.exit(1)
    else:
        # Main function is done, exit cleanly
        sys.exit(0)
