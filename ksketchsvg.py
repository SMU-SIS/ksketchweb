__author__ = 'ramvibhakar'
import math
import collections
import json

class ksketchsvg:

    @staticmethod
    def get_polyline(stroke):

        points_arr = stroke.attrib['points'].split()
        first_point = points_arr[0].split(',')
        result = 'M' + first_point[0] + ' ' + first_point[1]
        for point in points_arr[1:]:
            x, y = point.split(',')
            result += ' L' + x + ' ' + y
        return result

    @staticmethod
    def get_transformation_mat(sx, sy, angle, tx, ty, cx, cy):
        sx += 1
        sy += 1

        a = sx * math.cos(angle)
        b = sy * math.sin(angle)
        c = (-1) * sx * math.sin(angle)
        d = sy * math.cos(angle)
        e = (-1) * cx * sx * math.cos(angle) + sx * cy * math.sin(angle) + cx + tx
        f = (-1) * cx * sy * math.sin(angle) - cy * sy * math.cos(angle) + cy + ty
        return '('+str(a)+','+str(b)+','+str(c)+','+str(d)+','+str(e)+','+str(f)+')'

    @staticmethod
    def convert_color(color):
        rgbint = int(color)
        blue = rgbint & 255
        green = (rgbint >> 8) & 255
        red = (rgbint >> 16) & 255
        return "rgb(" + str(red) + "," + str(blue) + "," + str(green) + ")"

    @staticmethod
    def createTag(objectID, path, color, width, centroid):
        soup = BeautifulSoup()
        g_tag = Tag(soup, name='g')
        x,y = [float(i) for i in centroid.split(',')]
        g_tag['centreX'] = x
        g_tag['centreY'] = y
        g_tag['id'] = objectID
        path_tag = Tag(soup, name='path')
        path_tag['id'] = "p" + objectID
        path_tag['stroke'] = color
        path_tag['stroke-width'] = width
        path_tag['fill'] = 'none'
        path_tag['d'] = path

        g_tag.insert(0, path_tag)
        return g_tag

    @staticmethod
    def createGroup(objectID, centroid):
        soup = BeautifulSoup()
        g_tag = Tag(soup, name='g')
        x,y = [float(i) for i in centroid.split(',')]
        g_tag['centreX'] = x
        g_tag['centreY'] = y
        g_tag['id'] = objectID
        return g_tag

    @staticmethod
    def get_svg(xml):

        root = ET.fromstring(xml)
        result_soup = BeautifulSoup()
        for kobject in root.findall('.//KObject'):
            objectID = kobject.attrib['id']
            parent = kobject.find('parent')
            parentID = parent.attrib['id']
            stroke = kobject.find('strokeData')
            if stroke is not None:
                path = ksketchsvg.get_polyline(stroke)
                color = ksketchsvg.convert_color(stroke.attrib['color'])
                thickness = stroke.attrib['thickness']
                tag = ksketchsvg.createTag(objectID, path, color, thickness, kobject.attrib['centroid'])
                if parentID == "0":
                    result_soup.insert(len(result_soup.find_all('g', recursive=False)), tag)
                else:
                    grp = result_soup.find('g', {'id': parentID})
                    if grp:
                        grp.insert(len(grp.find_all('g', recursive=False)), tag)
            else:
                tag = ksketchsvg.createGroup(objectID, kobject.attrib['centroid'])
                if parentID == "0":
                    result_soup.insert(len(result_soup.find_all('g', recursive=False)), tag)
                else:
                    grp = result_soup.find('g', {'id': parentID})
                    if grp:
                        grp.insert(len(grp.find_all('g', recursive=False)), tag)
        soup = BeautifulSoup()
        g_tag = Tag(soup, name='g')
        g_tag['id'] = "0"
        g_tag.insert(0, result_soup)
        return g_tag.prettify()

    @staticmethod
    def get_svg(xml):

        root = ET.fromstring(xml)
        result_soup = BeautifulSoup()
        for kobject in root.findall('.//KObject'):
            objectID = kobject.attrib['id']
            parent = kobject.find('parent')
            parentID = parent.attrib['id']
            stroke = kobject.find('strokeData')
            if stroke is not None:
                path = ksketchsvg.get_polyline(stroke)
                color = ksketchsvg.convert_color(stroke.attrib['color'])
                thickness = stroke.attrib['thickness']
                tag = ksketchsvg.createTag(objectID, path, color, thickness, kobject.attrib['centroid'])
                if parentID == "0":
                    result_soup.insert(len(result_soup.find_all('g', recursive=False)), tag)
                else:
                    grp = result_soup.find('g', {'id': parentID})
                    if grp:
                        grp.insert(len(grp.find_all('g', recursive=False)), tag)
            else:
                tag = ksketchsvg.createGroup(objectID, kobject.attrib['centroid'])
                if parentID == "0":
                    result_soup.insert(len(result_soup.find_all('g', recursive=False)), tag)
                else:
                    grp = result_soup.find('g', {'id': parentID})
                    if grp:
                        grp.insert(len(grp.find_all('g', recursive=False)), tag)
        soup = BeautifulSoup()
        g_tag = Tag(soup, name='g')
        g_tag['id'] = "0"
        g_tag.insert(0, result_soup)
        return g_tag.prettify()

    @staticmethod
    def point_from_str(point):
        return [float(i) for i in point.split(',')]

    @staticmethod
    def get_transformations(xml):

        root = ET.fromstring(xml)
        object_timeframes = dict()
        for kobject in root.findall('.//KObject'):
            time_frame = collections.OrderedDict()
            objectID = kobject.attrib['id']
            prev_key = 0
            print "---------- "+ objectID + "------------"
            for spatialKey in kobject.findall('.//spatialkey'):
                currentKey = float(spatialKey.attrib['time'])
                ncx, ncy = ksketchsvg.point_from_str(spatialKey.attrib['center'])
                c_off_x = ncx
                c_off_y = ncy
                for path in spatialKey.findall('path'):
                    path_type = path.attrib['type']
                    if path_type == 'translate':
                        points = path.attrib['points']
                        if points != '':
                            for point in points.split():
                                x, y, t = ksketchsvg.point_from_str(point)
                                time = round(prev_key + t, 2)
                                if time in time_frame:
                                    arr = time_frame[time]
                                    arr[0] = [x, y]
                                else:
                                    arr = [[], [], []]
                                    arr[0] = [x, y]
                                    time_frame[time] = arr
                    elif path_type == 'rotate':
                        points = path.attrib['points']
                        if points != '':
                            for point in points.split():
                                x, y, t = ksketchsvg.point_from_str(point)
                                time = round(prev_key + t, 2)
                                if time in time_frame:
                                    arr = time_frame[time]
                                    arr[1] = [x, c_off_x, c_off_y]
                                else:
                                    arr = [[], [], []]
                                    arr[1] = [x, c_off_x, c_off_y]
                                    time_frame[time] = arr
                    elif path_type == 'scale':
                        points = path.attrib['points']
                        if points != '':
                            for point in points.split():
                                x, y, t = ksketchsvg.point_from_str(point)
                                time = round(prev_key + t,2)
                                if time in time_frame:
                                    arr = time_frame[time]
                                    arr[2] = [x, c_off_x, c_off_y]
                                else:
                                    arr = [[], [], []]
                                    arr[2] = [x, c_off_x, c_off_y]
                                    time_frame[time] = arr
                prev_key = currentKey
            if len(time_frame) != 0:
                object_timeframes[objectID] = dict(time_frame)
        time_line = dict()
        for key in object_timeframes:
            for time in object_timeframes[key]:
                if time == 2812.5:
                    print "Here"
                trans_arr, rotate_arr, scale_arr = object_timeframes[key][time]
                c_off_x = 0
                c_off_y = 0
                if len(scale_arr) > 0:
                    sx = sy = scale_arr[0]
                    c_off_x = scale_arr[1]
                    c_off_y = scale_arr[2]
                else:
                    sx = sy = 0
                if len(rotate_arr) > 0:
                    angle = rotate_arr[0]
                    c_off_x = rotate_arr[1]
                    c_off_y = rotate_arr[2]
                else:
                    angle = 0

                if len(trans_arr) > 0:
                    tx, ty = trans_arr
                else:
                    tx = ty = 0
                if time == 2750:
                    print(time)
                matrix = ksketchsvg.get_transformation_mat(sx, sy, angle, tx, ty, c_off_x, c_off_y)
                if time in time_line:
                    time_line[time].append({"obj":key, "trans":matrix})
                else:
                    time_line[time] = [{"obj":key, "trans":matrix}]

        sort_time = sorted(time_line.items())
        events = []
        for time,values in sort_time:
            events.append({"t": time, "e": values})
        json_obj = {"timeline": json.dumps(events)}
        return json_obj

import xml.etree.ElementTree as ET
from bs4 import BeautifulSoup, Tag

xml = "<KSketch date=\"Fri Feb 13 12:09:49 GMT+0800 2015\">   <thumbnail data=\"/9j/4AAQSkZJRgABAQAAAQABAAD/2wCEABALDA4MChAODQ4SERATGCgaGBYWGDEjJR0oOjM9PDkz&#xA;ODdASFxOQERXRTc4UG1RV19iZ2hnPk1xeXBkeFxlZ2MBERISGBUYLxoaL2NCOEJjY2NjY2NjY2Nj&#xA;Y2NjY2NjY2NjY2NjY2NjY2NjY2NjY2NjY2NjY2NjY2NjY2NjY2NjY//AABEIAFoAoAMBEQACEQED&#xA;EQH/xAGiAAABBQEBAQEBAQAAAAAAAAAAAQIDBAUGBwgJCgsQAAIBAwMCBAMFBQQEAAABfQECAwAE&#xA;EQUSITFBBhNRYQcicRQygZGhCCNCscEVUtHwJDNicoIJChYXGBkaJSYnKCkqNDU2Nzg5OkNERUZH&#xA;SElKU1RVVldYWVpjZGVmZ2hpanN0dXZ3eHl6g4SFhoeIiYqSk5SVlpeYmZqio6Slpqeoqaqys7S1&#xA;tre4ubrCw8TFxsfIycrS09TV1tfY2drh4uPk5ebn6Onq8fLz9PX29/j5+gEAAwEBAQEBAQEBAQAA&#xA;AAAAAAECAwQFBgcICQoLEQACAQIEBAMEBwUEBAABAncAAQIDEQQFITEGEkFRB2FxEyIygQgUQpGh&#xA;scEJIzNS8BVictEKFiQ04SXxFxgZGiYnKCkqNTY3ODk6Q0RFRkdISUpTVFVWV1hZWmNkZWZnaGlq&#xA;c3R1dnd4eXqCg4SFhoeIiYqSk5SVlpeYmZqio6Slpqeoqaqys7S1tre4ubrCw8TFxsfIycrS09TV&#xA;1tfY2dri4+Tl5ufo6ery8/T19vf4+fr/2gAMAwEAAhEDEQA/APQKACgAoAKACgAoAKACgAoAKACg&#xA;AoAKACgAoAKACgAoAKACgAoAKACgAoAKACgAoAKACgAoAKACgAoAKACgAoAKACgAoAKACgAoAKAE&#xA;YhVLMQABkk9qBpX0RBDe205xFMr84BB4b6Hv+FSpJ7Fzozh8S/rz7FiqMwoAKACgAoAKACgAoAKA&#xA;CgAoAKACgAoAKACgAoAoalqa2AUeTLK7/dCrwfb3PsAT7VMpWdjelR54uTdkvm/u/wCGRRS7SVhJ&#xA;qMV6/ORGtnL5afhjLfU/kKXLf4inWUVakrefX/gfL7xsN9pl9q9551xAcJHHGrsFYEZYkZ5BBb8K&#xA;ppPcxhOUHeLNFZ3tBmeQSWx+7N3T/e9vf8/Wpu477GvLGr8CtLt39P8AL7uxdBBGRyKs5xaACgAo&#xA;AKACgAoAKACgAoAKACgAoAKACgAoAZLEk0ZjkUMp6g0mr7lRk4u8SnHJLZTCG4ZpIJGxFKeSpP8A&#xA;C39D+fPWU3F2ZvKMaseaGjW6/Vfqv6VS2lh83UTJCZnkvCEj2gltqIueeAPl61TdjKnTc/JdxYvD&#xA;1nJcC4uLS2Q53CKGMKoPqxH3j+ntU2b3NHUjBWprXv1+Xb8zYUBVCqAABgAdqswbvqxaBBQAUAFA&#xA;BQAUAFABQAUAFABQAUAFABQAUAFADXRZEKOoZWGCD0NG403F3Rl6ZbLp+o3FsGaTzQZ0kY5YAscq&#xA;T6ZPH1PpUqNmbVKqnFJK29+xrVRgFABQAUAFABQAUAFABQAUAFABQAUAFABQAUAFABQAUAZ2lHzp&#xA;bu5kbM5maJl/55Kp+VfxB3f8C9MUAaNABQAUAFABQAUAFABQAUAFABQAUAFABQAUAFABQAUAFAGb&#xA;aEyazfSRqViUJG5PR5AM5H0DAE/4UAaVABQAUAFABQAUAFABQAUAFABQAUAFABQAUAFABQAUAFAE&#xA;MFukDzMhb99J5jZPQ4A4/KgCagAoAKACgAoAKACgAoAKACgAoAKACgAoAKACgAoAKACgAoAKACgA&#xA;oAKACgAoAKACgAoAKACgAoAKACgAoAKACgAoAKACgAoAKACgAoAKACgAoAKACgAoAKACgAoAKACg&#xA;AoAKACgAoAKACgAoAKACgAoAKACgAoAKACgAoAKACgAoAKAP/9k=\"/>   <scene>     <KObject id=\"32\" creationTime=\"0\" centroid=\"273.7875,348.4125\" type=\"group\">       <parent id=\"0\"/>       <Activity>         <keylist type=\"visibility\">           <visibilitykey time=\"0\" visibility=\"true\"/>         </keylist>       </Activity>       <transform type=\"single\">         <keylist type=\"referenceframe\">           <spatialkey time=\"0\" center=\"8.98846567431157e+307,8.98846567431157e+307\" passthrough=\"true\">             <path type=\"translate\" points=\"\"/>             <path type=\"rotate\" points=\"\"/>             <path type=\"scale\" points=\"\"/>           </spatialkey>           <spatialkey time=\"3062.5\" center=\"273.7875,348.4125\" passthrough=\"true\">             <path type=\"translate\" points=\"0,0,0 0.07982261640800041,4.390243902439025,62.5 0.07982261640800041,7.583148558758315,125 0.07982261640800041,9.17960088691796,187.5 1.6762749445676457,12.372505543237251,250 4.869179600886937,20.354767184035477,312.5 6.465631929046581,33.12638580931264,375 6.465631929046581,47.494456762749444,437.5 0.07982261640800041,53.88026607538803,500 6.465631929046581,53.88026607538803,625 17.640798226164097,50.687361419068736,687.5 36.79822616407984,49.09090909090909,750 54.35920177383594,49.09090909090909,812.5 70.32372505543239,53.88026607538803,875 86.28824833702885,58.669623059866964,937.5 100.65631929046565,66.65188470066519,1000 111.83148558758317,68.24833702882484,1062.5 126.19955654101997,73.03769401330376,1125 156.53215077605324,76.23059866962306,1187.5 198.039911308204,84.21286031042129,1250 228.37250554323728,89.00221729490022,1312.5 249.12638580931267,90.59866962305986,1375 261.89800443458984,92.19512195121952,1437.5 277.86252771618626,95.3880266075388,1500 295.42350332594236,96.98447893569845,1562.5 320.9667405764967,96.98447893569845,1625 346.50997782705105,90.59866962305986,1687.5 364.07095343680714,89.00221729490022,1750 388.0177383592018,82.61640798226163,1812.5 418.35033259423506,74.63414634146342,1875 450.27937915742797,63.4589800443459,1937.5 496.5764966740577,47.494456762749444,2000 522.119733924612,34.72283813747229,2062.5 530.1019955654102,28.337028824833702,2125 542.8736141906874,18.75831485587583,2187.5 557.2416851441242,2.7937915742793793,2250 565.2239467849224,-8.381374722838137,2312.5 574.8026607538803,-19.556541019955656,2375 585.9778270509978,-33.92461197339246,2437.5 593.960088691796,-46.69623059866962,2500 597.1529933481153,-51.48558758314856,2562.5 600.3458980044346,-56.27494456762749,2625 601.9423503325943,-59.467849223946786,2687.5 603.538802660754,-61.06430155210643,2750 605.1352549889135,-65.85365853658537,2812.5 605.1352549889135,-70.6430155210643,2875 \"/>             <path type=\"rotate\" points=\"0,0,0 -0.21064458259755803,0,62.5 -0.3183336473632892,0,125 -0.39446104385699154,0,187.5 -0.3843711263558244,0,250 -0.29211958373600394,0,312.5 -0.15971547034523995,0,375 -0.021746241039815276,0,437.5 0.13942671071186485,0,500 0.3257307104789785,0,562.5 0.3476412381543587,0,687.5 0.30195534919164574,0,750 0.16412738571584645,0,812.5 0.04080448687897936,0,875 -0.07969284896010903,0,937.5 -0.23239157541739092,0,1000 -0.27163051917710407,0,1062.5 -0.3011416169358406,0,1125 -0.34168305612995203,0,1187.5 -0.320999117182898,0,1250 -0.2819652379094428,0,1312.5 -0.1910232924451679,0,1375 -0.10122927004200147,0,1437.5 -0.019424736469592765,0,1500 0.12202146991822906,0,1562.5 0.1826921579160271,0,1625 0.25672593273657096,0,1687.5 0.32024802050676454,0,1750 0.36837789049598296,0,1812.5 0.40388090454496234,0,1875 0.45969061787867016,0,1937.5 0.513581673084171,0,2000 0.588299698095508,0,2062.5 0.6618934937117525,0,2125 0.6200232359743493,0,2187.5 0.5360643928848045,0,2250 0.2771844449186719,0,2312.5 0.15635903945929297,0,2375 0.047312933897704856,0,2437.5 -0.07143238910183125,0,2500 -0.14352268068560992,0,2562.5 -0.15178636778896992,0,2687.5 -0.13221822254950183,0,2750 -0.03655649616311003,0,2812.5 -0.01671732549374244,0,2821.823529411765 \"/>             <path type=\"scale\" points=\"0,0,0 -0.022539055082753556,0,62.5 -0.028274894052509048,0,125 -0.04440861793771278,0,187.5 -0.07721031551147772,0,250 -0.10421778459006237,0,312.5 -0.12607344654612296,0,375 -0.1580548489851923,0,625 -0.0866720178394964,0,687.5 -0.031206596108848017,0,750 0.00249415448990864,0,812.5 0.03138214039240528,0,875 0.04830545344224357,0,1000 0.05918848878614158,0,1125 0.05436387325246139,0,1250 4.496064933690036e-7,0,1312.5 -0.060439744768362114,0,1375 -0.09436417595981872,0,1437.5 -0.1161118289125116,0,1500 -0.13173722020515577,0,1562.5 -0.1534535811512504,0,1625 -0.179828491192773,0,1687.5 -0.206097988007377,0,1750 -0.2430478578386427,0,1812.5 -0.2754101171600757,0,1875 -0.30331986737548955,0,1937.5 -0.3248725471756184,0,2000 -0.34640218126517064,0,2062.5 -0.35499777084971074,0,2187.5 -0.33128734088765743,0,2250 -0.266463985682205,0,2312.5 -0.23989450752854358,0,2375 -0.21300320423903307,0,2437.5 -0.19264285929866276,0,2500 -0.16879283099102516,0,2562.5 -0.13742080798612089,0,2625 -0.10225911108253516,0,2687.5 -0.06681624421114662,0,2750 -0.03828038989132043,0,2812.5 0.0004769188706734706,0,2875 -0.00444411740246948,0,3007.2549019607845 \"/>           </spatialkey>           <spatialkey time=\"3187.5\" center=\"273.7875,348.4125\" passthrough=\"true\">             <path type=\"translate\" points=\"\"/>             <path type=\"rotate\" points=\"0,0,0 0.1131521153634571,0,53.176470588235134 0.293148860360715,0,115.67647058823513 \"/>             <path type=\"scale\" points=\"0,0,0 -0.0022500004562636044,0,55.24509803921546 -0.0450878745904038,0,117.74509803921546 -0.04908805151644951,0,122.87009803921546 \"/>           </spatialkey>           <spatialkey time=\"3500\" center=\"273.7875,348.4125\" passthrough=\"true\">             <path type=\"translate\" points=\"\"/>             <path type=\"rotate\" points=\"\"/>             <path type=\"scale\" points=\"0,0,0 -0.04478246851353607,0,57.375 -0.07308335125183985,0,119.875 -0.10446928082330686,0,182.375 -0.13581322878346747,0,244.875 -0.14979942169434024,0,307.375 \"/>           </spatialkey>         </keylist>       </transform>     </KObject>     <KObject id=\"26\" creationTime=\"0\" centroid=\"222.7,268.20000000000005\" type=\"stroke\">       <parent id=\"32\"/>       <Activity>         <keylist type=\"visibility\">           <visibilitykey time=\"0\" visibility=\"true\"/>         </keylist>       </Activity>       <transform type=\"single\">         <keylist type=\"referenceframe\">           <spatialkey time=\"0\" center=\"222.7,268.20000000000005\" passthrough=\"true\">             <path type=\"translate\" points=\"\"/>             <path type=\"rotate\" points=\"\"/>             <path type=\"scale\" points=\"\"/>           </spatialkey>         </keylist>       </transform>       <strokeData color=\"16711680\" thickness=\"9\" points=\"282.6,178.8 274.6,181.95 268.2,185.15 258.65,188.35 253.85,189.95 244.25,196.35 237.9,199.55 229.9,204.3 225.1,207.5 217.1,212.3 209.15,217.1 201.15,221.9 193.2,226.7 185.2,229.85 175.6,233.05 167.65,236.25 162.85,239.45 159.65,241.05 156.45,241.05 156.45,242.65 158.05,242.65 159.65,242.65 161.25,244.25 162.85,244.25 167.65,247.45 175.6,253.8 182,258.6 186.8,261.8 191.6,266.6 201.15,272.95 209.15,280.95 218.7,288.95 226.7,298.5 236.3,306.5 244.25,316.1 252.25,324.05 260.25,332.05 269.8,340 276.2,346.4 282.6,351.2 285.75,354.4 287.35,356 288.95,357.6 \"/>     </KObject>     <KObject id=\"28\" creationTime=\"0\" centroid=\"324.875,263.375\" type=\"stroke\">       <parent id=\"32\"/>       <Activity>         <keylist type=\"visibility\">           <visibilitykey time=\"0\" visibility=\"true\"/>         </keylist>       </Activity>       <transform type=\"single\">         <keylist type=\"referenceframe\">           <spatialkey time=\"0\" center=\"324.875,263.375\" passthrough=\"true\">             <path type=\"translate\" points=\"\"/>             <path type=\"rotate\" points=\"\"/>             <path type=\"scale\" points=\"\"/>           </spatialkey>         </keylist>       </transform>       <strokeData color=\"16711680\" thickness=\"9\" points=\"293.75,185.15 296.95,188.35 300.15,191.55 309.7,196.35 316.1,201.15 320.9,204.3 327.3,209.1 332.05,213.9 338.45,218.7 349.65,226.7 357.6,233.05 365.6,239.45 372,244.25 376.75,249.05 378.35,252.2 381.55,253.8 384.75,255.4 386.35,257 384.75,257 383.15,258.6 381.55,258.6 376.75,261.8 373.6,263.4 368.8,265 364,266.6 357.6,271.4 346.45,279.35 335.25,284.15 327.3,290.55 320.9,295.3 316.1,298.5 306.55,303.3 303.35,306.5 296.95,311.3 295.35,312.9 293.75,316.1 290.55,319.25 285.75,322.45 284.15,325.65 282.6,327.25 281,330.45 279.4,332.05 277.8,333.65 276.2,333.65 276.2,335.25 274.6,335.25 274.6,336.85 273,336.85 273,338.45 269.8,340 265,340 265,341.6 263.4,341.6 \"/>     </KObject>     <KObject id=\"29\" creationTime=\"0\" centroid=\"276.175,266.575\" type=\"stroke\">       <parent id=\"32\"/>       <Activity>         <keylist type=\"visibility\">           <visibilitykey time=\"0\" visibility=\"true\"/>         </keylist>       </Activity>       <transform type=\"single\">         <keylist type=\"referenceframe\">           <spatialkey time=\"0\" center=\"276.175,266.575\" passthrough=\"true\">             <path type=\"translate\" points=\"\"/>             <path type=\"rotate\" points=\"\"/>             <path type=\"scale\" points=\"\"/>           </spatialkey>         </keylist>       </transform>       <strokeData color=\"0\" thickness=\"9\" points=\"285.75,189.95 285.75,193.15 285.75,196.35 285.75,201.15 285.75,204.3 284.15,207.5 282.6,210.7 282.6,213.9 281,221.9 279.4,228.25 279.4,237.85 277.8,241.05 277.8,245.85 276.2,250.6 276.2,255.4 276.2,260.2 276.2,265 276.2,269.8 274.6,276.15 274.6,282.55 274.6,288.95 274.6,293.75 273,300.1 273,308.1 271.4,316.1 271.4,319.25 269.8,324.05 269.8,325.65 269.8,328.85 268.2,332.05 268.2,335.25 268.2,336.85 268.2,340 266.6,341.6 266.6,343.2 \"/>     </KObject>     <KObject id=\"30\" creationTime=\"0\" centroid=\"276.175,253.02499999999998\" type=\"stroke\">       <parent id=\"32\"/>       <Activity>         <keylist type=\"visibility\">           <visibilitykey time=\"0\" visibility=\"true\"/>         </keylist>       </Activity>       <transform type=\"single\">         <keylist type=\"referenceframe\">           <spatialkey time=\"0\" center=\"276.175,253.02499999999998\" passthrough=\"true\">             <path type=\"translate\" points=\"\"/>             <path type=\"rotate\" points=\"\"/>             <path type=\"scale\" points=\"\"/>           </spatialkey>         </keylist>       </transform>       <strokeData color=\"0\" thickness=\"9\" points=\"175.6,245.85 178.8,245.85 183.6,245.85 188.4,242.65 194.75,242.65 199.55,242.65 202.75,242.65 205.95,242.65 210.75,242.65 218.7,242.65 226.7,242.65 237.9,242.65 245.85,244.25 252.25,244.25 260.25,245.85 265,247.45 271.4,249.05 277.8,250.6 287.35,250.6 296.95,253.8 304.95,253.8 311.3,255.4 317.7,257 322.5,257 328.9,258.6 332.05,258.6 340.05,260.2 344.85,260.2 352.8,261.8 357.6,261.8 360.8,261.8 362.4,261.8 364,261.8 365.6,261.8 367.2,261.8 367.2,263.4 368.8,263.4 370.4,263.4 372,263.4 373.6,263.4 375.15,263.4 376.75,263.4 \"/>     </KObject>     <KObject id=\"31\" creationTime=\"0\" centroid=\"277.775,443.8\" type=\"stroke\">       <parent id=\"32\"/>       <Activity>         <keylist type=\"visibility\">           <visibilitykey time=\"0\" visibility=\"true\"/>         </keylist>       </Activity>       <transform type=\"single\">         <keylist type=\"referenceframe\">           <spatialkey time=\"0\" center=\"277.775,443.8\" passthrough=\"true\">             <path type=\"translate\" points=\"\"/>             <path type=\"rotate\" points=\"\"/>             <path type=\"scale\" points=\"\"/>           </spatialkey>         </keylist>       </transform>       <strokeData color=\"0\" thickness=\"9\" points=\"284.15,356 287.35,359.2 287.35,360.8 287.35,362.35 288.95,365.55 288.95,368.75 288.95,371.95 288.95,376.75 287.35,383.15 285.75,387.9 282.6,392.7 279.4,397.5 277.8,400.7 274.6,407.05 273,408.65 271.4,410.25 269.8,411.85 268.2,416.65 266.6,419.85 266.6,424.65 266.6,429.4 268.2,434.2 271.4,437.4 273,439 274.6,442.2 277.8,448.6 279.4,451.8 281,454.95 282.6,459.75 285.75,466.15 287.35,470.95 288.95,474.15 288.95,477.3 288.95,478.9 287.35,482.1 284.15,485.3 277.8,493.3 274.6,502.85 273,507.65 273,510.85 273,514.05 273,515.65 273,517.25 273,518.85 273,520.4 273,525.2 273,526.8 274.6,528.4 276.2,530 277.8,531.6 279.4,531.6 \"/>     </KObject>   </scene>   <log/> </KSketch>"
# #print ksketchsvg.get_svg(xml)
print ksketchsvg.get_transformations(xml)