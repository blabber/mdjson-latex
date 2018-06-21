# "THE BEER-WARE LICENSE" (Revision 42):
# <tobias.rehbein@web.de> wrote this file. As long as you retain this notice
# you can do whatever you want with this stuff. If we meet some day, and you
# think this stuff is worth it, you can buy me a beer in return.
#                                                             Tobias Rehbein

import argparse
import urllib.request
import ssl
import json

class JSendError(Exception):
    pass

def load_data(url):
    with open_request(url) as f:
        d = json.loads(f.read().decode('utf-8'))

    if d and d['status'] == "error":
        raise JSendError(d['message'])

    return d

def open_request(url):
    ctx = ssl.create_default_context()
    ctx.check_hostname = False
    ctx.verify_mode = ssl.CERT_NONE

    return urllib.request.urlopen(url=url, context=ctx, timeout=20)

def remove_third_stage(data):
    nd = []
    for d in data['days']:
        ns = []
        for s in d['stages']:
            if s['label'] != 'Newforces Stage':
                ns.append(s)
        if len(ns) > 0:
            d['stages'] = ns
            nd.append(d)
    data['days'] = nd

def timestamps_for_event(event):
    time = event['time'].strip()

    if time == '-':
        return (-1, -1)

    timeSplit = time.split(' - ')

    startSplit = timeSplit[0].split(':')
    startHours = int(startSplit[0])
    if startHours < 10:
        startHours = startHours + 24
    startMinutes = int(startSplit[1])
    start = (startHours * 60) + startMinutes

    endSplit = timeSplit[1].split(':')
    endHours = int(endSplit[0])
    if endHours < 10:
        endHours = endHours + 24
    endMinutes = int(endSplit[1])
    end = (endHours * 60) + endMinutes

    return (start, end)

def get_time_range(data):
    minTimestamp = 0
    maxTimestamp = 0

    for d in data['days']:
        for s in d['stages']:
            start, end = timestamps_for_event(s['events'][0])
            if maxTimestamp == 0 or maxTimestamp < end:
                maxTimestamp = end
    
            start, end = timestamps_for_event(s['events'][len(s['events']) - 1])
            if minTimestamp == 0 or minTimestamp > start:
                minTimestamp = start

    return (minTimestamp, maxTimestamp)

if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='Turn mdjson output into a latex fragment.')
    parser.add_argument('--url', help='The mdjson url.', default='https://gist.githubusercontent.com/blabber/babc4803141b0ec13fd613cc84eae074/raw')
    args = parser.parse_args()

    data = load_data(args.url)['data']
    remove_third_stage(data)
    dayOffset, dayMax = get_time_range(data)

    ltxDayHeight = 19
    lengthMinute = ltxDayHeight / (dayMax - dayOffset)
    lengthMinute = -lengthMinute

    ltxStageWidth = 2.7
    ltxDayWidth = 5.4
    ltxDayPadding = 0.25

    drawing = ''
    for di in range(0, len(data['days'])):
        d = data['days'][di]
        dayX = di * (ltxDayWidth + ltxDayPadding)
        for si in range(0, len(d['stages'])):
            stageX = dayX + (si * ltxStageWidth)
            s = d['stages'][si]
            for e in s['events']:
                eStart, eEnd = timestamps_for_event(e)

                eX1 = stageX
                eY1 = (eStart - dayOffset) * lengthMinute
                eX2 = stageX + ltxStageWidth
                eY2 = (eEnd - dayOffset) * lengthMinute

                eXCenter = eX1 + (ltxStageWidth / 2)
                eYCenter = eY1 - ((eY1 - eY2) / 2)

                eDrawing = '\\draw ({0},{1}) rectangle ({2},{3});\n'.format(eX1, eY1, eX2, eY2)
                drawing = drawing + eDrawing

                eDrawing = '\\node at ({0},{1}) [text width = {2}cm, text centered] {{\\tiny{{}}{3}\\\\\\footnotesize{{}}{4}}};\n'.format(eXCenter, eYCenter, ltxStageWidth, e['time'],  e['label'])
                drawing = drawing + eDrawing

    with open('mdjson.tex', 'w') as f:
        f.write(drawing)
