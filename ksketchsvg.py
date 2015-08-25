'''
Copyright 2015 Singapore Management University

This Source Code Form is subject to the terms of the
Mozilla Public License, v. 2.0. If a copy of the MPL was
not distributed with this file, You can obtain one at
http://mozilla.org/MPL/2.0/.
'''

import math
import collections

class ksketchsvg:
    # Ad-hoc data types used by methods of this class
    # Path List (path_list):
    #   list of
    #       3-tuple:
    #           float   # x or r or s
    #           float   # y
    #           float   # time in milliseconds
    #   Example: [(1, 1, 0), (2, 2, 1000)]
    #
    #
    # Spatial Keys (spatial_keys or skeys)
    #   list of Spatial Key
    #
    # Spatial Key (spatial_key or skey)
    #   dict:
    #      "time" : float  # in milliseconds
    #      "translate", "rotate", "scale", or "scale2": Path List
    #   Example: {
    #                'time': 0
    #                'translate': [(1, 1, 0), (2, 2, 1000)],
    #                'rotate': [(3, 0, 0), (4, 0, 1000)],
    #                'scale2': [(1, 0, 0), (5, 0, 1000)]
    #            }
    #
    #
    # Visibility Keys (visibility_keys or vkeys)
    #   list of Visibility Key
    #
    # Visibility Key (visibility_key or vkey)
    #   dict:
    #       "time" : float         # in milliseconds
    #       "v": float # 0 or 1
    #   Example: {
    #                   'time': 0
    #                   'v': 0
    #            }
    #
    #
    # Frame
    #    dict:
    #       'x': float   # x translation
    #       'y': float   # y translation
    #       'r': float   # rotation
    #       's': float   # scale2
    #       'v': int     # visibility (1 or 0)
    #   Example: { 'x':0, 'y':0, 'r':0, 's':1, 'v':1 }
    #
    #  Spatial Frame (spatial_frame or sframe)
    #    dict:
    #       'x': float   # x translation
    #       'y': float   # y translation
    #       'r': float   # rotation
    #       's': float   # scale2
    #   Example: { 'x':0, 'y':0, 'r':0, 's':1 }
    #
    # TimelineFrame
    #   dict:
    #      'id': int    # The object id
    #      'x': float   # x translation,       missing if no change (along with y)
    #      'y': float   # y translation,       missing if no change (along with x)
    #      'r': float   # rotation,            missing if no change
    #      's': float   # scale2,              missing if no change
    #      'v': int     # visibility (1 or 0), missing if no change
    #   Example: { 'id':165, 'x':0, 'y':0, 'r':0, 's':1, 'v':1 }
    #
    #
    # Object Timeline
    #   OrderedDict
    #       key: int           # time in milliseconds, with fractions of a millisecond truncated
    #       val: TimelineFrame
    #   Example: {
    #               "0" :     { 'id':154, 'x':0,   'y':0,   'r':0                 },
    #               "1065":   { 'id':154, 'x':100, 'y':100,          's':2, 'v':1 }
    #           }
    #
    #
    # Transformations
    #    OrderedDict:
    #       'time_step': float              # milliseconds between frames
    #       'max_time': float               # maximum time in milliseconds
    #       'default_frame': Frame          # the default frame used by this data
    #       'centers': dict
    #          key: int                     # object id
    #          val: dict:
    #               'x': float              # center x
    #               'y': float              # center y
    #       'timeline': OrderedDict
    #          key: int                     # time in milliseconds, with fractions of a millisecond truncated
    #          val: Array of TimelineFrame

    # Default values for animated variables
    def_x = 0
    def_y = 0
    def_r = 0
    def_s = 1
    def_v = 0
    default_frame = { 'x':def_x, 'y':def_y, 'r':def_r, 's':def_s, 'v':def_v }
    default_sframe = { 'x':def_x, 'y':def_y, 'r':def_r, 's':def_s }
    time_step = 1000/16.0

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
        return '(' + str(a) + ',' + str(b) + ',' + str(c) + ',' + str(d) + ',' + str(e) + ',' + str(f) + ')'

    @staticmethod
    def convert_color(color):
        rgbint = int(color)
        blue = rgbint & 255
        green = (rgbint >> 8) & 255
        red = (rgbint >> 16) & 255
        return "rgb(" + str(red) + "," + str(green) + "," + str(blue) + ")"

    @staticmethod
    def createTag(objectID, path, color, width, centroid):
        soup = BeautifulSoup()
        g_tag = Tag(soup, name='g')
        x, y = [float(i) for i in centroid.split(',')]
        g_tag['centreX'] = x
        g_tag['centreY'] = y
        g_tag['id'] = objectID
        g_tag['style'] = "opacity:0;"
        path_tag = Tag(soup, name='path')
        path_tag['id'] = "p" + objectID
        path_tag['stroke'] = color
        path_tag['stroke-width'] = width
        path_tag['fill'] = 'none'
        path_tag['d'] = path
        path_tag['stroke-linecap'] = 'round'
        path_tag['stroke-linejoin'] = 'round'

        g_tag.insert(0, path_tag)
        return g_tag

    @staticmethod
    def createGroup(objectID):
        soup = BeautifulSoup()
        g_tag = Tag(soup, name='g')
        g_tag['id'] = objectID
        g_tag['style'] = "opacity:0;"
        return g_tag

    @staticmethod
    def get_svg(xml,sketchID,version):

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
                tag = ksketchsvg.createGroup(objectID)
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
        SVGCache.addSVGData(sketchID,version,g_tag.prettify())
        return g_tag.prettify()

    @staticmethod
    def point_from_str(point):
        arr = [i for i in point.split(',')]
        if 'e' in arr[0]:
            arr[0] = "0"
        if 'e' in arr[1]:
            arr[1] = "0"
        return [float(i) for i in arr]

    @staticmethod
    def points_from_str(points):
        lst = []
        if points != '':
            for point in points.split():
                x, y, t = ksketchsvg.point_from_str(point)
                lst.append((x, y, t))
        return lst

    # Returns a list of all spatial key frames in a temporary structure:
    #   list of
    #       dict:    # Spatial Key Frame
    #           "time" : float
    #           "translate", "rotate", "scale", or "scale2": list of
    #               (float, float, float)   # (x, y, time)
    #   Example: [
    #               {
    #                   'time': 0
    #                   'translate': [(1, 1, 0), (2, 2, 1000)],
    #                   'rotate': [(3, 0, 0), (4, 0, 1000)],
    #                   'scale2': [(1, 0, 0), (5, 0, 1000)]
    #               },
    #               {
    #                   'time': 1000
    #                   'translate': [(7, 7, 0), (8, 8, 1000)],
    #                   'rotate': [(9, 0, 0), (1, 0, 1000)],
    #                   'scale2': [(1, 0, 0), (3, 0, 1000)]
    #               }
    #           ]
    @staticmethod
    def get_spatial_keys(kobject):
        keylist = []
        for spatial_key in kobject.findall('.//spatialkey'):
            d = {'time': float(spatial_key.attrib['time'])}

            for path in spatial_key.findall('path'):
                path_type = path.attrib['type']
                if path_type == 'translate':
                    d['translate'] = ksketchsvg.points_from_str(path.attrib['points'])
                elif path_type == 'rotate':
                    d['rotate'] = ksketchsvg.points_from_str(path.attrib['points'])
                elif path_type == 'scale':
                    d['scale'] = ksketchsvg.points_from_str(path.attrib['points'])
                elif path_type == 'scale2':
                    d['scale2'] = ksketchsvg.points_from_str(path.attrib['points'])
            keylist.append(d)
        return keylist

    # Returns a list of all visibility key frames in a temporary structure:
    #   list of
    #       dict:    # Visibility Key Frame
    #           "time" : float
    #           "v": float # 0 or 1
    #   Example: [
    #               {
    #                   'time': 0
    #                   'v': 0
    #               },
    #               {
    #                   'time': 1000
    #                   'v': 1
    #               }
    #           ]
    @staticmethod
    def get_visibility_keys(kobject):
        keylist = []
        for visibility_key in kobject.findall('.//visibilitykey'):   #List of ElementTree in document order
            d = {}
            d['time'] = float(visibility_key.attrib['time'])
            vis = visibility_key.attrib['visibility']
            if vis[0] == 't':
                d['v'] = 1
            elif vis[0] == 'f':
                d['v'] = 0
            else:
                raise Exception('Visibility %s is neither "true" nor "false".' % (vis))
            keylist.append(d)
        return keylist

    @staticmethod
    def find_index_at_or_before_proportion(proportion, path_list, start_idx=0):
        # case: the key frames path is empty
        # throws an error message
        if len(path_list) == 0:
            raise Exception('Empty path.')

        # calculate the total time duration
        duration = path_list[len(path_list)-1][2] - path_list[0][2]

        # calculate the proportional time
        proportion_duration = proportion * duration

        i = start_idx
        index_before_prop = -1

        # iterate through each point in the key frames path until the
        # current point's time exceeds the calculated proportional time
        while path_list[i][2] <= proportion_duration:
            index_before_prop = i
            i += 1

        # return the index of the point in the key frames path located
        # at or before the proportional time
        return index_before_prop;



    # Gets the next-last point from the previous key frame, if any.
    # The point is adjusted so that it
    # is positioned correctly relative to the current path.
    # returns the repositioned point (x, y, t), or None.
    @staticmethod
    def get_previous_point(skeys, key_idx, type, path_list):
        if key_idx <= 1:
            # The first key frame for an object should be instantaneous, and
            # the path is used for positioning only, so ignore it.
            return None

        prev_prev_key = skeys[key_idx-2]
        prev_key = skeys[key_idx-1]
        cur_key = skeys[key_idx]

        # In this case, there is no transition in the previous path, so the path should end.
        if not (type in prev_key):
            return None
        prev_path_list = prev_key[type]

        p_this_first = path_list[0]
        p_this_last = path_list[len(path_list)-1]
        p_prev_first = prev_path_list[0]
        p_prev_last = prev_path_list[len(prev_path_list)-1]
        p_prev_penultimate = prev_path_list[len(prev_path_list)-2]

        actual_time_diff = (p_prev_last[2] - p_prev_penultimate[2]) * \
                           ((prev_key['time'] - prev_prev_key['time']) / float(p_prev_last[2] - p_prev_first[2]))
        scaled_time_diff = actual_time_diff * ( (p_this_last[2] - p_this_first[2]) /
                                                float(cur_key['time'] - prev_key['time']) )

        previous_point = None
        if type != 'scale2':
            # Translates and Rotates are additive.
            previous_point = (p_this_first[0] - (p_prev_last[0] - p_prev_penultimate[0]),
                              p_this_first[1] - (p_prev_last[1] - p_prev_penultimate[1]),
                              p_this_first[2] - scaled_time_diff)
        else:
            # Scales are multiplicative
            previous_point = (p_this_first[0] * (p_prev_penultimate[0] / p_prev_last[0]), #i.e. p_this_first[0] / (p_prev_last[0] / p_prev_penultimate[0])
                              0,                                                          # Must do this. Otherwise divide by 0.
                              p_this_first[2] - scaled_time_diff)

        return previous_point

    # Gets the second point from the next key frame, if any.
    # The point is adjusted so that it
    # is positioned correctly relative to the current path.
    # returns the repositioned point (x, y, t), or None.
    @staticmethod
    def get_next_point(skeys, key_idx, type, path_list):
        if len(skeys)-1 <= key_idx:
            # There really is nothing else, so return null.
            return None

        prev_key = skeys[key_idx-1]
        cur_key = skeys[key_idx]
        next_key = skeys[key_idx+1]

        # In this case, there is no transition in the next path, so this path should end.
        if (not (type in next_key)) or (len(next_key[type]) < 2):
            return None
        next_path_list = next_key[type]

        p_this_first = path_list[0]
        p_this_last = path_list[len(path_list)-1]
        p_next_first = next_path_list[0]
        p_next_last = next_path_list[len(next_path_list)-1]
        p_next_second = next_path_list[1]

        actual_time_diff = (p_next_second[2] - p_next_first[2]) * \
                           ((next_key['time'] - cur_key['time']) / float(p_next_last[2] - p_next_first[2]))
        scaled_time_diff = actual_time_diff * ( (p_this_last[2] - p_this_first[2]) /
                                                float(cur_key['time'] - prev_key['time']) )

        next_point = None
        if type != 'scale2':
            # Translates and Rotates are additive.
            next_point = (p_this_last[0] + (p_next_second[0] - p_next_first[0]),
                          p_this_last[1] + (p_next_second[1] - p_next_first[1]),
                          p_this_last[2] + scaled_time_diff)
        else:
            # Scales are multiplicative
            next_point = (p_this_last[0] * (p_next_second[0] / p_next_first[0]),
                          0, # Must do this. Otherwise divide by 0.
                          p_this_last[2] + scaled_time_diff)

        return next_point

    # Returns the point on the path list at the given fraction.
    # If fraction < 0, returns the first point.
    # If 1 <= fraction, returns the last point.
    # Assumes skeys[key_idx][type] exists
    # returns (x, y, t), start_idx or None, start_idx
    @staticmethod
    def find_point(skeys, key_idx, type, proportion, start_idx=0):
        path_list = skeys[key_idx][type]

        # case: the path is empty
        # return no points (i.e., None)
        if len(path_list) == 0:
            return None, start_idx

        first_pt = path_list[0]
        last_pt = path_list[len(path_list)-1]


        # case: the proportion equal or greater than 1
        # return the last point
        if (1 <= proportion):
            return last_pt, len(path_list)-1

        # get the total time duration
        duration = float(last_pt[2] - first_pt[2])

        # case: there is no elapsed time in the duration
        # return the last point
        if duration == 0:
            return last_pt, len(path_list)-1

        base_idx = ksketchsvg.find_index_at_or_before_proportion(proportion, path_list, start_idx)
        next_idx = base_idx + 1

        # Get p0, p1, p2, p3
        if 0 < base_idx:
            p0 = path_list[base_idx-1]
        else:
            p0 = ksketchsvg.get_previous_point(skeys, key_idx, type, path_list)
        p1 = path_list[base_idx]
        p2 = path_list[next_idx]
        if next_idx < len(path_list)-1:
            p3 = path_list[next_idx+1]
        else:
            p3 = ksketchsvg.get_next_point(skeys, key_idx, type, path_list)

        base_proportion = p1[2]/duration
        numerator = proportion - base_proportion

        if numerator == 0:
            return p1, base_idx

        denominator = (p2[2] - p1[2]) / duration
        interpolation_factor = numerator / denominator

        # Linear interpolation
        new_point = ( (p2[0]-p1[0]) * interpolation_factor  +  p1[0],
                      (p2[1]-p1[1]) * interpolation_factor  +  p1[1],
                      (p2[2]-p1[2]) * interpolation_factor  +  p1[2] )

        return new_point, base_idx


    # Gets the target time's proportion within the time of the entire key frames.
    # Assumes skeys[skey_idx] exists
    @staticmethod
    def find_proportion(time, skeys, skey_idx):
        # Initialize start_time, end_time
        if 0 < skey_idx:
            start_time = skeys[skey_idx-1]['time']
        else:
            start_time = skeys[skey_idx]['time']
        end_time = skeys[skey_idx]['time']

        # case: the target time is at least equal to the final time
        if end_time <= time:
            return 1

        # case: the target time is at most equal to the beginning time
        if time <= start_time:
            return 0

        time_elapsed = float(time - start_time)     # calculate the elapsed time
        duration     = float(end_time - start_time) # calculate the duration time


        if duration == 0:
            # case: zero-length duration time
            proportion = 1
        else:
            # case: non-zero-length duration time
            proportion = time_elapsed/duration;

        # return the proportion value
        return proportion

    # Get the spatial frame at this time.
    # Successive calls to this method are assumed to have the same or increasing time
    # returns a new spatial frame for this tiem.
    @staticmethod
    def get_spatial_frame(time, skeys, skey_idx, prev_key_frame, mem):
        if (mem == None):
            mem = { 't_idx':0, 'r_idx':0, 's_idx':0 }
        sframe = {'x':prev_key_frame['x'], 'y':prev_key_frame['y'], 'r':prev_key_frame['r'], 's':prev_key_frame['s']}

        proportion = ksketchsvg.find_proportion(time, skeys, skey_idx)

        if 'translate' in skeys[skey_idx]:
            point, mem['t_idx'] = ksketchsvg.find_point(skeys, skey_idx, 'translate', proportion, mem['t_idx'])
            if point != None:
                sframe['x'] += point[0]
                sframe['y'] += point[1]
            
        if 'rotate' in skeys[skey_idx]:
            point, mem['r_idx'] = ksketchsvg.find_point(skeys, skey_idx, 'rotate', proportion, mem['r_idx'])
            if point != None:
                sframe['r'] += point[0]
            
        if 'scale' in skeys[skey_idx]:
            point, mem['s_idx'] = ksketchsvg.find_point(skeys, skey_idx, 'scale', proportion, mem['s_idx'])
            if point != None:
                sframe['s'] += point[0]
            
        if 'scale2' in skeys[skey_idx]:
            point, mem['s_idx'] = ksketchsvg.find_point(skeys, skey_idx, 'scale2', proportion, mem['s_idx'])
            if point != None:
                sframe['s'] *= point[0]
            
        return sframe, mem


    # Returns true if idx points to the key at the current time.
    # Assumes that keys[idx] points to a valid key (a dict with a 'time' property)
    @staticmethod
    def on_current_key(time, keys, idx):
        #print "on_current_key: time %f, idx %d" % (time, idx)
        after_last = idx == len(keys)-1 and keys[idx]['time'] < time
        after_prev = idx == 0 or keys[idx-1]['time'] < time
        on_or_before_cur = time <= keys[idx]['time']
        next_later = len(keys)-1 == idx or time < keys[idx+1]['time']
        return after_last or (after_prev and on_or_before_cur and next_later)


    # Returns a "frame" at the current time
    # dict: {
    #           'x': float   # x translation
    #           'y': float   # y translation
    #           'r': float   # rotation
    #           's': float   # scale2
    #           'v': int     # visibility (1 or 0)
    #        }
    @staticmethod
    def get_object_frame(time, skeys, vkeys, mem):
        if mem == None:
            mem = { 'skey_idx':0, 'vkey_idx':0, 'prev_key_frame':dict(ksketchsvg.default_frame), 'sf_memento':None }

        # While before current skey, move to next skey
        while not ksketchsvg.on_current_key(time, skeys, mem['skey_idx']):
            # set prev_key_x, etc. and clear sf_memento
            sframe, memento = ksketchsvg.get_spatial_frame(skeys[mem['skey_idx']]['time'], skeys, mem['skey_idx'], 
                                                           mem['prev_key_frame'], mem['sf_memento'])
            mem['prev_key_frame']['x'] = sframe['x']
            mem['prev_key_frame']['y'] = sframe['y']
            mem['prev_key_frame']['r'] = sframe['r']
            mem['prev_key_frame']['s'] = sframe['s']
            mem['sf_memento'] = None
            # point to the next spatial key frame
            mem['skey_idx'] += 1


        cur_frame, mem['sf_memento'] = ksketchsvg.get_spatial_frame(time, skeys, mem['skey_idx'],
                                                                    mem['prev_key_frame'], mem['sf_memento'])

        # While before current vkey, move to next vkey
        while not ksketchsvg.on_current_key(time, vkeys, mem['vkey_idx']):
            mem['prev_key_frame']['v'] = vkeys[mem['vkey_idx']]['v']
            # point to the next spatial key frame
            mem['vkey_idx'] += 1

        # get the current visibility and add it to cur_frame
        if vkeys[mem['vkey_idx']]['time'] <= time:
            cur_frame['v'] = vkeys[mem['vkey_idx']]['v']
        else:
            cur_frame['v'] = mem['prev_key_frame']['v']

        return cur_frame, mem

    # Computes a list of frames for a given object. The output is an
    # Object Timeline
    #   OrderedDict
    #       key: float                   # time in milliseconds
    #       val: TimelineFrame
    #   Example: {
    #               0 :     { 'id':154, 'x':0,   'y':0,   'r':0                 },
    #               1065.5: { 'id':154, 'x':100, 'y':100,          's':2, 'v':1 }
    #           }
    #
    # The second value is True iff this object ever rotates or scales
    @staticmethod
    def get_object_timeline(kobject):
        timeline = collections.OrderedDict()  # Output at the end
        id = int(kobject.attrib['id'])
        rot_or_scale = False

        spatial_keys = ksketchsvg.get_spatial_keys(kobject)
        visibility_keys = ksketchsvg.get_visibility_keys(kobject)

        # initialize cur_time to 0 and last_time to max(last spatial key time, last visibility key time)
        cur_time = 0;
        last_time = max(spatial_keys[len(spatial_keys)-1]['time'], visibility_keys[len(visibility_keys)-1]['time'])
        #print "get_object_timeline: last_time %.1f" % (last_time)

        # initialize prev_frame and memento to empty values
        prev_frame = dict(ksketchsvg.default_frame)
        memento = None

        # We do this while cur_time < last_time + 1, not while cur_time <= last_time,
        # because the fractional component of last_time may have been truncated.
        while cur_time < last_time + 1:
            cur_frame, memento = ksketchsvg.get_object_frame(cur_time, spatial_keys, visibility_keys, memento)

            # If anything (other than time) is different between prev_out and cur_out,
            # then add cur_out to timeline (timeline[cur_time] = cur_out)
            if cur_frame != prev_frame:
                d = collections.OrderedDict()
                d['id'] = id
                for k in ('x', 'y', 'r', 's', 'v'):
                    if prev_frame[k] != cur_frame[k]:
                        d[k] = cur_frame[k]
                timeline[int(cur_time)] = d
                if 'r' in d or 's' in d:
                    rot_or_scale = True

            # Close: prepare for next iteration step
            prev_frame = cur_frame
            cur_time += ksketchsvg.time_step

        return timeline, rot_or_scale

    # Transformations
    #    dict:
    #       'centers': dict
    #          key: int                    # object id
    #          val: Array of 2 floats      # center x, center y
    #       'timeline': OrderedDict
    #          key: float                  # time in milliseconds
    #          val: Array of TimelineFrame
    @staticmethod
    def get_transformations(xml,sketchId,version):
        root = ET.fromstring(xml)
        max_time = 0
        timelines = {}
        centers = {}
        for kobject in root.findall('.//KObject'):
            id = int(kobject.attrib['id'])
            cx, cy = ksketchsvg.point_from_str(kobject.attrib['centroid'])
            timelines[id], rot_or_scale = ksketchsvg.get_object_timeline(kobject)
            # if rot_or_scale:
            d = collections.OrderedDict()
            d['x'] = cx
            d['y'] = cy
            centers[id] = d

        timeline = {}
        for id in timelines:
            for time_int in timelines[id]:
                if time_int in timeline:
                    arr = timeline[time_int]
                else:
                    arr = []
                    timeline[time_int] = arr
                arr.append(timelines[id][time_int])
                max_time = max(max_time,time_int)

        output = collections.OrderedDict()
        output['time_step'] = ksketchsvg.time_step
        output['max_time'] = max_time
        output['default_frame'] = ksketchsvg.default_frame
        output['centers'] = centers
        output['timeline'] = timeline
        SVGCache.addAnimationData(sketchId,version,output)
        return output

    @staticmethod
    def check_permission(sketchId, userID):
        perm = Permissions.user_access_control(sketchId,userID)
        return perm['p_view']

import xml.etree.ElementTree as ET
from bs4 import BeautifulSoup, Tag
from svgcache import SVGCache
from permissions_groups import Permissions
# Test area
testxml = ""
#print ksketchsvg.get_svg(testxml)
#print "get_transformations " , ksketchsvg.get_transformations(testxml)
