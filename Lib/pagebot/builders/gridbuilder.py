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
#     gridbuilder.py
#
#     Model after alistapart.com/article/practical-grid
#
from pagebot.builders.basebuilder import BaseBuilder

class GridBuilder(BaseBuilder):

    def build(self, path, format=None, pageSelection=None, multiPage=True, buildHead=True, buildBody=True, buildCss=True):
        u"""Build simple HTML/CSS site of static code, interpreting the content of self.document."""
        if buildCss:
            self.buildCss()
        if buildHead:
            self.buildHead()
        if buildBody:
            self.buildBody()

    def buildCss(self):
        pass

    def buildHead(self):
        pass

    def buildBody(self):
        pass

