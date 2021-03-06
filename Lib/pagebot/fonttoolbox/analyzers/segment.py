# -*- coding: UTF-8 -*-
# -----------------------------------------------------------------------------
#
#     P A G E B O T
#
#     Copyright (c) 2016+ Buro Petr van Blokland + Claudia Mens & Font Bureau
#     www.pagebot.io
#     Licensed under MIT conditions
#     Made for usage in DrawBot, www.drawbot.com
# -----------------------------------------------------------------------------
#
#     segment.py
#
class Segment(object):
    def __init__(self, points=None):
        if points is None:
            points = []
        self.points = points

    def __len__(self):
        return len(self.points)

    def __repr__(self):
        return 'Sg(%s)' % self.points

    def append(self, p):
        self.points.append(p)

