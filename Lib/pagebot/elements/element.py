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
#     element.py
#
from __future__ import division

import weakref
import copy

from drawBot import rect, oval, line, newPath, moveTo, lineTo, lineDash, drawPath, \
    save, restore, scale, textSize, fill, text, stroke, strokeWidth, shadow

from pagebot.conditions.score import Score
from pagebot import newFS, setFillColor, setStrokeColor, setGradient, setShadow,\
    x2cx, cx2x, y2cy, cy2y, z2cz, cz2z, w2cw, cw2w, h2ch, ch2h, d2cd, cd2d
from pagebot.toolbox.transformer import point3D, pointOffset, uniqueID, point2D
from pagebot.style import makeStyle, ORIGIN_POINT, MIDDLE, CENTER, RIGHT, TOP, BOTTOM, LEFT, FRONT, BACK, NO_COLOR, XALIGNS, YALIGNS, ZALIGNS, \
    MIN_WIDTH, MAX_WIDTH, MIN_HEIGHT, MAX_HEIGHT, MIN_DEPTH, MAX_DEPTH, DEFAULT_WIDTH, DEFAULT_HEIGHT, DEFAULT_DEPTH, XXXL, INTERPOLATING_TIME_KEYS,\
    ONLINE, INLINE, OUTLINE
from pagebot.toolbox.transformer import asFormatted, uniqueID
from pagebot.toolbox.timemark import TimeMark


class Element(object):

    # Initialize the default Element behavior flags.
    # These flags can be overwritten by inheriting classes, or dynamically in instances,
    # e.g. where the settings of TextBox.nextBox and TextBox.nextPage define if a TextBox
    # instance can operate as a flow.
    isText = False
    isTextBox = False
    isFlow = False # Value is True if self.next if defined.
    isPage = False # Set to True by Page-like elements.
    isView = False 
    
    def __init__(self, point=None, x=0, y=0, z=0, w=DEFAULT_WIDTH, h=DEFAULT_HEIGHT, d=DEFAULT_DEPTH, 
            t=0, parent=None, name=None, title=None, style=None, conditions=None, elements=None, 
            template=None, nextElement=None, prevElement=None, nextPage=None, prevPage=None, padding=None, 
            margin=None, pt=0, pr=0, pb=0, pl=0, pzf=0, pzb=0, mt=0, mr=0, mb=0, ml=0, mzf=0, mzb=0, 
            borders=None, borderTop=None, borderRight=None, borderBottom=None, borderLeft=None, 
            shadow=None, gradient=None, drawBefore=None, drawAfter=None, framePath=None, **kwargs):  
        u"""Basic initialize for every Element constructor. Element always have a location, even if not defined here.
        If values are added to the contructor parameter, instead of part in **kwargs, this forces them to have values,
        not inheriting from one of the parent styles.
        Ignore setting of setting eId as attribute, guaranteed to be unique.
        """  
        assert point is None or isinstance(point, (tuple, list))
        
        self.style = makeStyle(style, **kwargs) # Make default style for t == 0
        # Initialize style values that are not supposed to inherite from parent styles.
        # Always store point in style as separate (x, y, z) values. Missing values are 0
        self.point3D = point or (x, y, z)
        self.w = w
        self.h = h
        self.d = d
        self.padding = padding or (pt, pr, pb, pl, pzf, pzb)
        self.margin = margin or (mt, mr, mb, ml, mzf, mzb)
        # Border info dict have format: 
        # dict(line=ONLINE, dash=None, stroke=0, strokeWidth=borderData)
        # If not borders defined, then drawing will use the stroke and strokeWidth (if defined)
        # for intuitive compatibility with DrawBot.
        self.borders = borders or (borderTop, borderRight, borderBottom, borderLeft)

        # Drawing hooks
        self.drawBefore = drawBefore # Optional method to draw before child elements are drawn.
        self.drawAfter = drawAfter # Optional method to draw after child elements are drawn.

        # Shadow and gradient, if defined
        self.shadow = shadow
        self.gradient = gradient
        self.framePath = framePath # Optiona frame path to draw instead of bounding box element rectangle.

        # Set timer of this element.
        self.timeMarks = [TimeMark(0, self.style), TimeMark(XXXL, self.style)] # Default TimeMarks from t == 0 until infinite of time.
        self._t = 0 # Initialize self.style from t = 0
        self._tm0 = self._tm1 = None # Boundary timemarks, where self._tm0.t <= t <= self._tm1.t, with expanded styles.
        self.timeKeys = INTERPOLATING_TIME_KEYS # List of names of style entries that can interpolate in time.

        if padding is not None:
            self.padding = padding # Expand by property
        if margin is not None:
            self.margin = margin

        self.name = name
        self.title = title or name # Optional to make difference between title name, style property
        self._eId = uniqueID(self) # Direct set property with guaranteed unique persistent value. 
        self._parent = None # Preset, so it exists for checking when appending parent.
        if parent is not None:
            # Add and set weakref to parent element or None, if it is the root. Caller must add self to its elements separately.
            self.parent = parent # Set referecnes in both directions. Remove any previous parent links
        # Conditional placement stuff
        if not conditions is None and not isinstance(conditions, (list, tuple)): # Allow singles
            conditions = [conditions]
        self.conditions = conditions # Explicitedly stored local in element, not inheriting from ancesters. Can be None.
        self.report = [] # Area for conditions and drawing methods to report errors and warnings.
        # Save flow reference names
        self.prevElement = prevElement # Name of the prev flow element
        self.nextElement = nextElement # Name of the next flow element
        self.nextPage = nextPage # Name ot identifier of the next page that nextElement refers to.
        self.prevPage = prevPage
        # Copy relevant info from template: w, h, elements, style, conditions, next, prev, nextPage
        # Initialze self.elements, add template elements and values, copy elements if defined.
        self.applyTemplate(template, elements) 
        # Initialize the default Element behavior tags, in case this is a flow.
        self.isFlow = not None in (prevElement, nextElement, nextPage)

    def __repr__(self):
        if self.title:
            name = ':'+self.title
        elif self.name:
            name = ':'+self.name
        else: # No naming, show unique self.eId:
            name = ':'+self.eId

        if self.elements:
            elements = ' E(%d)' % len(self.elements)
        else:
            elements = ''
        return '%s%s (%d, %d)%s' % (self.__class__.__name__, name, int(round(self.point[0])), int(round(self.point[1])), elements)

    def __len__(self):
        u"""Answer total amount of elements, placed or not."""
        return len(self.elements) 

    #   T E M P L A T E

    def applyTemplate(self, template, elements=None):
        u"""Copy relevant info from template: w, h, elements, style, conditions when element is created.
        Don't call later."""
        self.template = template # Set template by property
        if elements is not None:
            # Add optional list of elements.
            for e in elements or []: 
                self.appendElement(e) # Add cross reference searching for eId of elements.
            
    def _get_template(self):
        return self._template
    def _set_template(self, template):
        self.clearElements()
        self._template = template # Keep in order to clone pages or if addition info is needed.
        # Copy optional template stuff
        if template is not None:
            # Copy elements from the template and put them in the designated positions.
            self.w = template.w
            self.h = template.h
            self.prevElement = template.prevElement
            self.nextElement = template.nextElement
            self.nextPage = template.nextPage
            # Copy style items
            for  name, value in template.style.items():
                self.style[name] = value
            # Copy condition list. Does not have to be deepCopy, condition instances are multi-purpose.
            self.conditions = copy.copy(template.conditions)
            for e in template.elements:
                self.appendElement(e.deepCopy())
    template = property(_get_template, _set_template)

    #   E L E M E N T S
    #   Every element is potentioally a container of other elements.

    def __getitem__(self, eId):
        u"""Answer the element with eId. Raise a KeyError if the element does not exist."""
        return self._eIds[eId]

    def __setitem__(self, eId, e):
        if not e in self.elements:
            self.elements.append(e)
        self._eIds[eId] = e

    def _get_eId(self):
        return self._eId
        # Cannot set self._eId through self.eId property. Set self._eId if necessary.
    eId = property(_get_eId)

    def _get_elements(self):
        return self._elements
    def _set_elements(self, elements):
        self.clearElements()
        for e in elements:
            self.appendElement(e) # Make sure to set all references.
    elements = property(_get_elements, _set_elements)

    def _get_elementIds(self): # Answer the x-ref dictionary with elements by their e.eIds
        return self._eIds
    elementIds = property(_get_elementIds)

    def getElement(self, eId):
        u"""Answer the page element, if it has a unique element Id. Answer None if the eId does not exist as child."""
        return self._eIds.get(eId)

    def getElementPage(self):
        u"""Recursively answer the page of this element. This can be several layers above self."""
        if self.isPage:
            return self
        return self.parent.getElementPage()

    def getElementByName(self, name):
        u"""Answer the first element in the offspring list that fits the name. Answer None if it cannot be found"""
        if self.name == name:
            return self
        for e in self.elements:
            found = e.getElementByName(name) # Don't search on next page yet.
            if found is not None:
                return found
        return None

    def clearElements(self):
        u"""Properly initializes self._elements and self._eIds. 
        Any existing elements get their parent weakrefs become None and will garbage collect."""
        self._elements = [] 
        self._eIds = {}

    def deepCopy(self):
        u"""Answer a copy of self, where the "unique" fields are set to default. Also perform a deep copy
        on all child elements."""
        e = copy.copy(self)
        e._eId = uniqueID(e) # Guaranteed unique Id for every element.
        e.nextElement = None
        e.prevElement = None
        e.style = copy.copy(self.style)
        e.clearElements()
        for child in self.elements:
            e.appendElement(child.deepCopy())
        return e

    copy = deepCopy # Make the same as default.

    def setElementByIndex(self, e, index):
        u"""Replace the element, if there is already one at index. Otherwise append it to self.elements
        and answer the index number that it got."""
        if index < len(self.elements):
            self.elements[index] = e
            if self.eId:
                self._eIds[e.eId] = e
            return index
        return self.appendElement(e)

    def appendElement(self, e):
        u"""Add element to the list of child elements. Note that elements can be added multiple times.
        If the element is alread placed in another container, then remove it from its current parent.
        This relation and position is lost. The position e is supposed to be filled already in local position."""
        eParent = e.parent
        if not eParent is None: 
            eParent.removeElement(e) # Remove from current parent, if there is one.
        self._elements.append(e) # Possibly add to self again, will move it to the top of the element stack.
        e.setParent(self) # Set parent of element without calling this method again.
        if e.eId: # Store the element by unique element id, if it is defined.
            self._eIds[e.eId] = e
        return len(self._elements)-1 # Answer the element index for e.

    def removeElement(self, e):
        u"""If the element is placed in self, then remove it. Don't touch the position."""
        assert e.parent is self
        e.setParent(None) # Unlink the parent reference of e
        if e.eId in self._eIds:
            del self._eIds[e.eId]
        if e in self._elements:
            self._elements.remove(e)
        return e # Answer the unlinked elements for convenience of the caller.

    def _get_show(self): # Set flag for drawing or interpreation with conditional.
        return self.css('show')
    def _set_show(self, showFlag):
        self.style['show'] = showFlag # Hiding rest of css for this value.
    show = property(_get_show, _set_show)

    #   C H I L D  E L E M E N T  P O S I T I O N S

    def getElementsAtPoint(self, point):
        u"""Answer the list with elements that fit the point. Note None in the point will match any
        value in the element position. Where None in the element position with not fit any xyz of the point."""
        elements = []
        px, py, pz = point3D(point) 
        for e in self.elements:
            ex, ey, ez = point3D(e.point)
            if (ex == px or px is None) and (ey == py or py is None) and (ez == pz or pz is None):
                elements.append(e)
        return elements

    def getElementsPosition(self):
        u"""Answer the dictionary of elements that have eIds and their positions."""
        elements = {}
        for e in self.elements:
            if e.eId:
                elements[e.eId] = e.point
        return elements

    def getPositions(self):
        u""""Answer the dictionary of positions of elements. 
        Key is the local point of the child element. Value is list of elements."""
        positions = {}
        for e in self.elements:
            point = tuple(e.point) # Point needs to be tuple to be used a key.
            if not point in positions:
                positions[point] = []
            positions[point].append(e)
        return positions

    #   F L O W

    # If the element is part of a flow, then answer the squence.
    
    def NOTNOW_getFlows(self):
        u"""Answer the set of flow element sequences on the page."""
        flows = {} # Key is nextBox of first textBox. Values is list of TextBox instances.
        for e in self.elements:
            if not e.isFlow:
                continue
            # Now we know that this element has a e.nextBox and e.nextPage
            # There should be a flow with that name in our flows yet
            found = False
            for nextId, seq in flows.items():
                if seq[-1].nextElement == e.name: # Glue to the end of the sequence.
                    seq.append(e)
                    found = True
                elif e.nextElement == seq[0].name: # Add at the start of the list.
                    seq.insert(0, e)
                    found = True
            if not found: # New entry
                flows[e.next] = [e]
        return flows

    def NOTNOW_getNextFlowBox(self, tb, makeNew=True):
        u"""Answer the next textBox that tb is pointing to. This can be on the same page or a next
        page, depending how the page (and probably its template) is defined."""
        if tb.nextPage: # Page number or name
            # The flow textBox is pointing to another page. Try to get it, and otherwise create one,
            # if makeNew is set to True.
            page = self.doc.getPage(tb.nextPage)
            if page is None and makeNew:
                page = self.doc.newPage(name=tb.nextPage)
            # Hard check. Otherwise something must be wrong in the template flow definition.
            # or there is more content than we can handle, while not allowing to create new pages.
            assert page is not None
            assert not page is self # Make sure that we got a another page than self.
            # Get the element on the next page that
            tb = page.getElementByName(tb.nextElement)
            # Hard check. Otherwise something must be wrong in the template flow definition.
            assert tb is not None and not len(tb)
        else:
            page = self # Staying on the same page, flowing into another column.
            tb = self.getElementByName(tb.nextElement)
            # Hard check. Make sure that this one is empty, otherwise mistake in template
            assert not len(tb)
        return page, tb

    #   If self.nextElement is defined, then check the condition if there is overflow.

    def isOverflow(self, tolerance):
        return True

    def overflow2Next(self):
        u"""Try to fix if there is overflow. Default behavior is to do nothing. This method
        is redefined by inheriting classed, such as TextBox, that can have overflow of text."""
        return True

    def _get_baselineGrid(self):
        return self.css('baselineGrid')
    def _set_baselineGrid(self, baselineGrid):
        self.style['baselineGrid'] = baselineGrid
    baselineGrid = property(_get_baselineGrid, _set_baselineGrid)

    def _get_baselineGridStart(self):
        return self.css('baselineGridStart')
    def _set_baselineGridStart(self, baselineGridStart):
        self.style['baselineGridStart'] = baselineGridStart
    baselineGridStart = property(_get_baselineGridStart, _set_baselineGridStart)

    # Text conditions, always True for non-text elements.

    def isBaselineOnTop(self, tolerance):
        return True

    def isBaselineOnBottom(self, tolerance):
        return True

    def isBaselineOnTop(self, tolerance):
        return True

    def isAscenderOnTop(self, tolerance):
        return True

    def isCapHeightOnTop(self, tolerance):
        return True

    def isXHeightOnTop(self, tolerance):
        return True

    #   S T Y L E

    # Answer the cascaded style value, looking up the chain of ancestors, until style value is defined.

    def css(self, name, default=None):
        u"""In case we are looking for a plain css value, cascading from the main ancestor styles
        of self, then follow the parent links until document or root, if self does not contain
        the requested value."""
        if name in self.style:
            return self.style[name]
        if self.parent is not None:
            return self.parent.css(name, default)
        return default

    def getNamedStyle(self, styleName):
        u"""In case we are looking for a named style (e.g. used by the Typesetter to build a stack
        of cascading tag style, then query the ancestors for the named style. Default behavior
        of all elements is that they pass the request on to the root, which is nornally the document."""
        if self.parent:
            return self.parent.getNamedStyle(styleName)
        return None

    #   L I B --> Document.lib

    def _get_lib(self):
        u"""Answer the shared document.lib dictionary by property, used for share global entry by elements.
        Elements query their self.parent.lib until the root document is reached."""
        parent = self.parent
        if parent is not None:
            return parent.lib # Either parent element or document.lib.
        return None # Document cannot be found, or there is there is no parent defined in the element.
    lib = property(_get_lib)

    def _get_doc(self):
        u"""Answer the root Document of this element by property, looking upward in the ancestor tree."""
        if self.parent is not None:
            return self.parent.doc
        return None
    doc = property(_get_doc)

    # Most common properties

    def setParent(self, parent):
        u"""Set the parent of self as weakref if it is not None. Don't call self.appendElement()."""
        if parent is not None:
            parent = weakref.ref(parent)
        self._parent = parent # Can be None if self needs to be unlinked from a parent tree. E.g. when moving it.

    def _get_parent(self):
        u"""Answer the parent of the element, if it exists, by weakref reference. Answer None of there
        is not parent defined or if the parent not longer exists."""
        if self._parent is not None:
            return self._parent()
        return None
    def _set_parent(self, parent):
        # Note that the caller must add self to its elements.
        if parent is not None:
            #assert not self in parent.ancestors, '[%s.%s] Cannot set one of the children "%s" as parent.' % (self.__class__.__name__, self.name, parent)
            parent.appendElement(self)
        else:
            self._parent = None
    parent = property(_get_parent, _set_parent)

    def _get_siblings(self):
        u"""Answer all elements that share self.parent, not including self in the list."""
        siblings = []
        for e in self.parent.elements:
            if not e is self:
                siblings.append(e)
        return siblings
    siblings = property(_get_siblings)

    def _get_ancestors(self):
        u"""Answer the list of anscestors of self, including the document root. Self is not included."""
        ancestors = []
        parent = self.parent
        while parent is not None:
            assert not parent in ancestors, '[%s.%s] Illegal loop in parent->ancestors reference.' % (self.__class__.__name__, self.name)
            ancestors.append(parent)
            parent = parent.parent
        return ancestors
    ancestors = property(_get_ancestors)

    def _get_point(self):
        u"""Answer the 2D point tuple of the relative local position of self."""
        return self.x, self.y # Answer as 2D
    def _set_point(self, point):
        self.x = point[0]
        self.y = point[1]
    point = property(_get_point, _set_point)

    def _get_point3D(self):
        u"""Answer the 3D point tuple of the relative local position of self."""
        return self.x, self.y, self.z
    def _set_point3D(self, point):
        self.x, self.y, self.z = point3D(point) # Always store as 3D-point, z = 0 if missing.
    point3D = property(_get_point3D, _set_point3D)

    def _get_oPoint(self): 
        u"""Answer the self.point, where y can be flipped, depending on the self.originTop flag."""
        return self._applyOrigin(self.point)
    oPoint3D = oPoint = property(_get_oPoint)

    # Plain coordinates

    def _get_x(self):
        u"""Answer the x position of self."""
        return self.style['x'] # Direct from style. Not CSS lookup.
    def _set_x(self, x):
        self.style['x'] = x
    x = property(_get_x, _set_x)
    
    def _get_y(self):
        u"""Answer the y position of self."""
        return self.style['y'] # Direct from style. Not CSS lookup.
    def _set_y(self, y):
        self.style['y'] = y
    y = property(_get_y, _set_y)
    
    def _get_z(self):
        u"""Answer the z position of self."""
        return self.style['z'] # Direct from style. Not CSS lookup.
    def _set_z(self, z):
        self.style['z'] = z
    z = property(_get_z, _set_z)
    
    # Time management

    def _get_t(self):
        u"""The self._t status is the time status, interpolating between the values in 
        self.tStyles[t1] and self.tStyles[t2] where t1 <= t <= t2 and these styles contain
        the requested parameters."""
        return self._t
    def _set_t(self, t):
        self._t = t
        if self._tm0 is None or self._tm1 is None or t < self._tm0.t or self._tm1.t < t:
            # If not initialized or t outside cached time span, then create new expanded styles.
            self._tm0, self._tm1 = self.getExpandedTimeMarks(t)

    def appendTimeMark(self, tm):
        assert isinstance(tm, TimeMark)
        self.timeMarks.append(tm)
        self.timeMarks.sort() # Keep them in tm.t order.

    def NOTNOW_getExpandedTimeMarks(t):
        u"""Answer a new interpolated TimeState instance, from the enclosing time states for t."""
        timeValueNames = self.timeKeys
        rootStyleKeys = self.timeMarks[0].keys()
        for n in range(1, len(timers)):
            tm0 = self.timeMarks[timers[n-1]]
            if t < tm0.t:
                continue
            tm1 = self.timeMarks[timers[n]]
            futureTimers = timers[n:]
            pastTimers = timers[:n-1]
            for rootStyleKey in rootStyleKeys:
                if not rootStyleKey in tm1.style:
                    for futureTime in futureTimers:
                        futureTimeMark = self.timeMarks[futureTime]
                        if rootStyleKey in futureTimeMark.style:
                            tm1.style[rootStyleKey] = futureTimeMark.style[rootStyleKey]

            return tm0, tm1
        raise ValueError

    # Origin compensated by alignment. This is used for easy solving of conditions,
    # where the positioning can be compenssaring the element alignment type.

    def _get_left(self):
        xAlign = self.xAlign
        if xAlign == CENTER:
            return self.x - self.w/2
        if xAlign == RIGHT:
            return self.x - self.w
        return self.x
    def _set_left(self, x):
        xAlign = self.xAlign
        if xAlign == CENTER:
            self.x = x + self.w/2
        elif xAlign == RIGHT:
            self.x = x + self.w
        else:
            self.x = x
    left = property(_get_left, _set_left)

    def _get_mLeft(self): # Left, including left margin
        return self.left - self.css('ml')
    def _set_mLeft(self, x):
        self.left = x + self.css('ml')
    mLeft = property(_get_mLeft, _set_mLeft)

    def _get_center(self):
        xAlign = self.xAlign
        if xAlign == LEFT:
            return self.x + self.w/2
        if xAlign == RIGHT:
            return self.x + self.w
        return self.x
    def _set_center(self, x):
        xAlign = self.xAlign
        if xAlign == LEFT:
            self.x = x - self.w/2
        elif xAlign == RIGHT:
            self.x = x - self.w
        else:
            self.x = x
    center = property(_get_center, _set_center)

    def _get_right(self):
        xAlign = self.xAlign
        if xAlign == LEFT:
            return self.x + self.w
        if xAlign == CENTER:
            return self.x + self.w/2
        return self.x
    def _set_right(self, x):
        xAlign = self.xAlign
        if xAlign == LEFT:
            self.x = x - self.w
        elif xAlign == CENTER:
            self.x = x - self.w/2
        else:
            self.x = x
    right = property(_get_right, _set_right)

    def _get_mRight(self): # Right, including right margin
        return self.right - self.mr
    def _set_mRight(self, x):
        self.right = x + self.mr
    mRight = property(_get_mRight, _set_mRight)

    # Vertical

    def _get_top(self):
        u"""Answer the top position (relative to self.parent) of self."""
        yAlign = self.yAlign
        if yAlign == MIDDLE:
            return self.y - self.h/2
        if yAlign == BOTTOM:
            if self.originTop:
                return self.y - self.h
            return self.y + self.h
        return self.y
    def _set_top(self, y):
        u"""Shift the element so self.top == y."""
        yAlign = self.yAlign
        if yAlign == MIDDLE:
            self.y = y + self.h/2
        elif yAlign == BOTTOM:
            if self.originTop:
                self.y = y + self.h
            else:
                self.y = y - self.h
        else:
            self.y = y
    top = property(_get_top, _set_top)

    def _get_mTop(self): # Top, including top margin
        if self.originTop:
            return self.top - self.mt
        return self.top + self.mt
    def _set_mTop(self, y):
        if self.originTop:
            self.top = y + self.mt
        else:
            self.top = y - self.mt
    mTop = property(_get_mTop, _set_mTop)

    def _get_middle(self): # On bounding box, not including margins.
        yAlign = self.yAlign
        if yAlign == TOP:
            if self.originTop:
                return self.y + self.h/2
            return self.y - self.h/2
        if yAlign == BOTTOM:
            if self.originTop:
                return self.y - self.h/2
            return self.y + self.h/2
        return self.y
    def _set_middle(self, y):
        yAlign = self.yAlign
        if yAlign == TOP:
            if self.originTop:
                self.y = y - self.h/2
            else:
                self.y = y + self.h/2
        elif yAlign == BOTTOM:
            if self.originTop:
                self.y = y + self.h/2
            else:
                self.y = y - self.h/2
        else:
            self.y = y
    middle = property(_get_middle, _set_middle)

    def _get_bottom(self):
        yAlign = self.yAlign
        if yAlign == TOP:
            if self.originTop:
                return self.y + self.h
            return self.y - self.h
        if yAlign == MIDDLE:
            return self.y + self.h/2
        return self.y
    def _set_bottom(self, y):
        yAlign = self.yAlign
        if yAlign == TOP:
            if self.originTop:
                self.y = y - self.h
            else:
                self.y = y + self.h
        elif yAlign == MIDDLE:
            self.y = y - self.h/2
        else:
            self.y = y
    bottom = property(_get_bottom, _set_bottom)

    def _get_mBottom(self): # Bottom, including bottom margin
        if self.originTop:
            return self.bottom + self.mb
        return self.bottom - self.mb
    def _set_mBottom(self, y):
        if self.originTop:
            self.bottom = y - self.mb
        else:
            self.bottom = y + self.mb
    mBottom = property(_get_mBottom, _set_mBottom)

    # Depth, running  in vertical z-axis dirction. Viewer is origin, posistive value is perpendicular to the screen.
    # Besides future usage in real 3D rendering, the z-axis is used to compare conditional status in element layers.

    def _get_front(self):
        zAlign = self.css('zAlign')
        if zAlign == MIDDLE:
            return self.z - self.d/2
        if zAlign == BACK:
            return self.z - self.d
        return self.z
    def _set_front(self, z):
        zAlign = self.css('zAlign')
        if zAlign == MIDDLE:
            self.z = z + self.d/2
        elif zAlign == BACK:
            self.z = z + self.d
        else:
            self.z = z
    front = property(_get_front, _set_front)

    def _get_mFront(self): # Front, including front margin
        return self.front + self.css('mzf')
    def _set_mFront(self, z):
        self.front = z + self.css('mzf')
    mFront = property(_get_mFront, _set_mFront)

    def _get_back(self):
        zAlign = self.css('zAlign')
        if zAlign == MIDDLE:
            return self.z + self.d/2
        if zAlign == FRONT:
            return self.z + self.d
        return self.z
    def _set_back(self, z):
        zAlign = self.css('zAlign')
        if zAlign == MIDDLE:
            self.z = z - self.d/2
        elif zAlign == FRONT:
            self.z = z - self.d
        else:
            self.z = z
    back = property(_get_back, _set_back)

    def _get_mBack(self): # Front, including front margin
        return self.back - self.css('mzb')
    def _set_mBack(self, z):
        self.back = z - self.css('mzb')
    mBack = property(_get_mBack, _set_mBack)

    # Borders

    def _borderDict(self, borderData):
        u"""Internal method to create a dictionary with border info. If no valid border
        dictionary is defined, then use optional stroke and strokeWidth to create one.
        Otherwise answer *None*."""
        if isinstance(borderData, (int, long, float)):
            return dict(line=ONLINE, dash=None, stroke=0, strokeWidth=borderData)
        if isinstance(borderData, dict):
            if not 'line' in borderData: # (ONLINE, INLINE, OUTLINE):
                borderData['line'] = ONLINE
            if not 'dash' in borderData:
                borderData['dash'] = None
            if not 'strokeWidth' in borderData:
                borderData['strokeWidth'] = 1
            if not 'stroke' in borderData:
                borderData['stroke'] = 0
            return borderData
        # TODO: Solve this, error on initialize of element, _parent does not yet exist.
        #stroke = self.css('stroke')
        #strokeWidth = self.css('strokeWidht')
        #if stroke is not None and strokeWidth:
        #     return dict(line=ONLINE, dash=None, stroke=stroke, strokeWidth=strokeWidth)
        return None

    def _get_borders(self):
        return self.borderTop, self.borderRight, self.borderBottom, self.borderLeft
    def _set_borders(self, borders):
        if not isinstance(borders, (list, tuple)):
            # Make copy, in case it is a dict, otherwise changes will be made in all.
            borders = copy.copy(borders), copy.copy(borders), copy.copy(borders), copy.copy(borders)
        elif len(borders) == 2:
            borders = borders*2
        elif len(borders) == 1:
            borders = borders*4
        self.borderTop, self.borderRight, self.borderBottom, self.borderLeft = borders
    # Seems to be onfusing having only one of the two. So allow both property names for the same.
    border = borders = property(_get_borders, _set_borders)

    def _get_borderTop(self):
        return self.css('borderTop')
    def _set_borderTop(self, border):
        self.style['borderTop'] = self._borderDict(border)
    borderTop = property(_get_borderTop, _set_borderTop)

    def _get_borderRight(self):
        return self.css('borderRight')
    def _set_borderRight(self, border):
        self.style['borderRight'] = self._borderDict(border)
    borderRight = property(_get_borderRight, _set_borderRight)

    def _get_borderBottom(self):
        return self.css('borderBottom')
    def _set_borderBottom(self, border):
        self.style['borderBottom'] = self._borderDict(border)
    borderBottom = property(_get_borderBottom, _set_borderBottom)

    def _get_borderLeft(self):
        return self.css('borderLeft')
    def _set_borderLeft(self, border):
        self.style['borderLeft'] = self._borderDict(border)
    borderLeft = property(_get_borderLeft, _set_borderLeft)

    # Alignment types, defines where the origin of the element is located.

    def _validateXAlign(self, xAlign): # Check and answer value
        assert xAlign in XALIGNS, '[%s.xAlign] Alignment "%s" not valid in %s' % (self.__class__.__name__, xAlign, sorted(XALIGNS))
        return xAlign
    def _validateYAlign(self, yAlign): # Check and answer value
        assert yAlign in YALIGNS, '[%s.yAlign] Alignment "%s" not valid in %s' % (self.__class__.__name__, yAlign, sorted(YALIGNS))
        return yAlign
    def _validateZAlign(self, zAlign): # Check and answer value
        assert zAlign in ZALIGNS, '[%s.zAlign] Alignment "%s" not valid in %s' % (self.__class__.__name__, zAlign, sorted(ZALIGNS))
        return zAlign

    def _get_xAlign(self): # Answer the type of x-alignment. For compatibility allow align and xAlign as equivalents.
        return self._validateXAlign(self.css('xAlign'))
    def _set_xAlign(self, xAlign):
        self.style['xAlign'] = self._validateXAlign(xAlign) # Save locally, blocking CSS parent scope for this param.
    xAlign = property(_get_xAlign, _set_xAlign)
     
    def _get_yAlign(self): # Answer the type of x-alignment.
        return self._validateYAlign(self.css('yAlign'))
    def _set_yAlign(self, yAlign):
        self.style['yAlign'] = self._validateYAlign(yAlign) # Save locally, blocking CSS parent scope for this param.
    yAlign = property(_get_yAlign, _set_yAlign)
     
    def _get_zAlign(self): # Answer the type of x-alignment.
        return self._validateZAlign(self.css('zAlign'))
    def _set_zAlign(self, zAlign):
        self.style['zAlign'] = self._validateZAlign(zAlign) # Save locally, blocking CSS parent scope for this param.
    zAlign = property(_get_zAlign, _set_zAlign)
     
    # Position by column + gutter size index.

    def _get_cx(self): # Answer the x-position, defined in columns. Can be fractional for elements not on grid.
        return x2cx(self.x, self)
    def _set_cx(self, cx): # Set the x-position, defined in columns.
        x = cx2x(cx, self)
        if x is not None:
            self.x = x
    cx = property(_get_cx, _set_cx)

    def _get_cy(self): # Answer the y-position, defined in columns. Can be fractional for elements not on grid.
        return y2cy(self.y, self)
    def _set_cy(self, cy): # Set the x-position, defined in columns.
        y = cy2y(cy, self)
        if y is not None:
            self.y = y
    cy = property(_get_cy, _set_cy)

    def _get_cz(self): # Answer the z-position, defined in columns. Can be fractional for elements not on 3D-grid.
        return z2cz(self.y, self)
    def _set_cz(self, cz): # Set the z-position, defined in style['cz'] columns.
        z = cz2z(cz, self)
        if z is not None:
            self.z = z
    cz = property(_get_cz, _set_cz)

    # TODO: Make this work
    """
    def _get_cols(self): # Number of columns in the given self.w and self.colW
        return w2cols(self.w, self) # Using self.cw and self.gw
    def _set_cols(self, cols):
        w = cols2w(cw, self)
        if w is not None:
            self.w = w
    cols = property(_get_cols, _set_cols)

    def _get_rows(self): # Number of vertical rows, in the given self.h and self.colH
        return h2rows(self.h, self) # Using self.ch and self.gw
    def _set_rows(self, rows):
        h = rows2h(ch, self)
        if h is not None:
            self.h = h
    rows = property(_get_rows, _set_rows)

    def _get_lanes(self): # z-axis name for rows and cols.
        return d2lanes(self.d, self) # Using self.cd and self.gw
    def _set_lanes(self, cd):
        d = lanes2d(cd, self)
        if d is not None:
            self.d = d
    lanes = property(_get_lanes, _set_lanes)
    """

    def _get_cw(self): # Column width
        return self.css('cw')
    def _set_cw(self, cw):
        self.style['cw'] = cw
    cw = property(_get_cw, _set_cw)

    def _get_ch(self): # Column height (row height)
        return self.css('ch')
    def _set_ch(self, ch):
        self.style['ch'] = ch
    ch = property(_get_ch, _set_ch)

    def _get_cd(self): # Column depth (slice?)
        return self.css('cd')
    def _set_cd(self, cd):
        self.style['cd'] = cd
    cd = property(_get_cd, _set_cd)


    def _get_gw(self): # Gutter width
        return self.css('gw', 0)
    def _set_gw(self, gw):
        self.style['gw'] = gw # Set local.
    gw = property(_get_gw, _set_gw)

    def _get_gh(self): # Gutter height
        return self.css('gh', 0)
    def _set_gh(self, gh):
        self.style['gh'] = gh # Set local
    gh = property(_get_gh, _set_gh)

    def _get_gd(self): # Gutter depth
        return self.css('gd', 0)
    def _set_gd(self, gd):
        self.style['gd'] = gd
    gd = property(_get_gd, _set_gd)

    def _get_gutter(self): # Tuple of (w, h) gutters
        return self.gw, self.gh
    def _set_gutter(self, gutter):
        if isinstance(gutter, (long, int, float)):
            gutter = [gutter]
        if len(gutter) == 1:
            gutter = (gutter[0], gutter[0])
        elif len(margin) == 2:
            pass
        else:
            raise ValueError
        self.gw, self.gh = gutter
    gutter = property(_get_gutter, _set_gutter)

    def _get_gutter3D(self): # Tuple of (gw, gh, gd) gutters
        return self.gw, self.gh, self.gd
    def _set_gutter3D(self, gutter3D):
        if isinstance(gutter3D, (long, int, float)):
            gutter3D = [gutter3D]
        if len(gutter3D) == 1:
            gutter3D = (gutter3D[0], gutter3D[0], gutter3D[0])
        elif len(margin) == 3:
            pass
        else:
            raise ValueError
        self.gw, self.gh, self.gd = gutter3D
    gutter3D = property(_get_gutter3D, _set_gutter3D)

    # Absolute positions

    def _get_rootX(self): # Answer the root value of local self.x, from whole tree of ancestors.
        parent = self.parent
        if parent is not None:
            return self.x + parent.rootX # Add relative self to parents position.
        return self.x
    rootX = property(_get_rootX)

    def _get_rootY(self): # Answer the absolute value of local self.y, from whole tree of ancestors.
        parent = self.parent
        if parent is not None:
            return self.y + parent.rootY # Add relative self to parents position.
        return self.y
    rootY = property(_get_rootY)

    def _get_rootZ(self): # Answer the absolute value of local self.z, from whole tree of ancestors.
        parent = self.parent
        if parent is not None:
            return self.z + parent.rootZ # Add relative self to parents position.
        return self.z
    rootZ = property(_get_rootZ)

    # (w, h, d) size of the element.

    def _get_w(self): # Width
        return min(self.maxW, max(self.minW, self.style['w'], MIN_WIDTH)) # From self.style, don't inherit.
    def _set_w(self, w):
        self.style['w'] = w or DEFAULT_WIDTH # Overwrite element local style from here, parent css becomes inaccessable.
    w = property(_get_w, _set_w)

    def _get_mw(self): # Width, including margins
        return self.w + self.ml + self.mr # Add margins to width
    def _set_mw(self, w):
        self.style['w'] = max(0, w - self.ml - self.mr) # Cannot become < 0
    mw = property(_get_mw, _set_mw)

    def _get_h(self): # Height
        return min(self.maxH, max(self.minH, self.style['h'], MIN_HEIGHT)) # From self.style, don't inherit.
    def _set_h(self, h):
        self.style['h'] = h or MIN_HEIGHT # Overwrite element local style from here, parent css becomes inaccessable.
    h = property(_get_h, _set_h)

    def _get_mh(self): # Height, including margins
        return self.h + self.mt + self.mb # Add margins to height
    def _set_mh(self, h):
        self.style['h'] = max(0, h - self.mt - self.mb) # Cannot become < 0
        self.changedHeight()
    mh = property(_get_mh, _set_mh)

    def _get_d(self): # Depth
        return min(self.maxD, max(self.minD, self.style['d'], MIN_DEPTH)) # From self.style, don't inherit.
    def _set_d(self, d):
        self.style['d'] = d or MIN_DEPTH # Overwrite element local style from here, parent css becomes inaccessable.
    d = property(_get_d, _set_d)

    def _get_md(self): # Depth, including margin front and margin back in z-axis.
        return self.d + self.mzb + self.mzf # Add front and back margins to depth
    def _set_md(self, d):
        self.style['d'] = max(0, d - self.mzf - self.mzb) # Cannot become < 0, behind viewer?
    md = property(_get_md, _set_md)

    # Margin properties

    # TODO: Add support of "auto" values, doing live centering.

    def _get_margin(self): # Tuple of paddings in CSS order, direction of clock
        return self.mt, self.mr, self.mb, self.ml
    def _set_margin(self, margin):
        # Can be 123, [123], [123, 234] or [123, 234, 345, 4565, ]
        if isinstance(margin, (long, int, float)):
            margin = [margin]
        if len(margin) == 1: # All same value
            margin = (margin[0], margin[0], margin[0], margin[0], margin[0], margin[0])
        elif len(margin) == 2: # mt == mb, ml == mr, mzf == mzb
            margin = (margin[0], margin[1], margin[0], margin[1], margin[0], margin[1])
        elif len(margin) == 3: # mt == ml == mzf, mb == mr == mzb
            margin = (margin[0], margin[1], margin[2], margin[0], margin[1], margin[2])
        elif len(margin) == 4: # mt, mr, mb, ml, 0, 0
            margin = (margin[0], margin[1], margin[2], margin[3], 0, 0)
        elif len(margin) == 6:
            pass
        else:
            raise ValueError
        self.mt, self.mr, self.mb, self.ml, self.mzf, self.mzb = margin
    margin = property(_get_margin, _set_margin)

    def _get_margin3D(self): # Tuple of margin in CSS order + (front, back), direction of clock
        return self.mt, self.mr, self.mb, self.ml, self.mzf, self.mzb
    margin3D = property(_get_margin3D, _set_margin)

    def _get_mt(self): # Margin top
        return self.style['mt'] # Don't inherit
    def _set_mt(self, mt):
        self.style['mt'] = mt  # Overwrite element local style from here, parent css becomes inaccessable.
    mt = property(_get_mt, _set_mt)
    
    def _get_mb(self): # Margin bottom
        return self.style['mb'] # Don't inherit
    def _set_mb(self, mb):
        self.style['mb'] = mb  # Overwrite element local style from here, parent css becomes inaccessable.
    mb = property(_get_mb, _set_mb)
    
    def _get_ml(self): # Margin left
        return self.style['ml'] # Don't inherit
    def _set_ml(self, ml):
        self.style['ml'] = ml # Overwrite element local style from here, parent css becomes inaccessable.
    ml = property(_get_ml, _set_ml)
    
    def _get_mr(self): # Margin right
        return self.style['mr'] # Don't inherit
    def _set_mr(self, mr):
        self.style['mr'] = mr  # Overwrite element local style from here, parent css becomes inaccessable.
    mr = property(_get_mr, _set_mr)

    def _get_mzf(self): # Margin z-axis front
        return self.style['mzf'] # Don't inherit
    def _set_mzf(self, mzf):
        self.style['mzf'] = mzf  # Overwrite element local style from here, parent css becomes inaccessable.
    mzf = property(_get_mzf, _set_mzf)
    
    def _get_mzb(self): # Margin z-axis back
        return self.style['mzb'] # Don't inherit
    def _set_mzb(self, mzb):
        self.style['mzb'] = mzb  # Overwrite element local style from here, parent css becomes inaccessable.
    mzb = property(_get_mzb, _set_mzb)
    
    def _get_mw(self): # Width including margins
        return self.w + self.ml + self.mr
    mw = property(_get_mw)
    
    def _get_mh(self): # Height including margins
        return self.h + self.mb + self.mt
    mh = property(_get_mh)
    
    def _get_md(self): # Depth including margins
        return self.d + self.mzf + self.mzb
    md = property(_get_md)
    
    # Padding properties

    # TODO: Add support of "auto" values, doing live centering.
    
    def _get_padding(self): # Tuple of paddings in CSS order, direction of clock
        return self.pt, self.pr, self.pb, self.pl
    def _set_padding(self, padding):
        # Can be 123, [123], [123, 234] or [123, 234, 345, 4565, ]
        if isinstance(padding, (long, int, float)):
            padding = [padding]
        if len(padding) == 1: # All same value
            padding = (padding[0], padding[0], padding[0], padding[0], padding[0], padding[0])
        elif len(padding) == 2: # pt == pb, pl == pr, pzf == pzb
            padding = (padding[0], padding[1], padding[0], padding[1], padding[0], padding[1])
        elif len(padding) == 3: # pt == pl == pzf, pb == pr == pzb
            padding = (padding[0], padding[1], padding[2], padding[0], padding[1], padding[2])
        elif len(padding) == 4: # pt, pr, pb, pl, 0, 0
            padding = (padding[0], padding[1], padding[2], padding[3], 0, 0)
        elif len(padding) == 6:
            pass
        else:
            raise ValueError
        self.pt, self.pr, self.pb, self.pl, self.pzf, self.pzb = padding
    padding = property(_get_padding, _set_padding)

    def _get_padding3D(self): # Tuple of padding in CSS order + (front, back), direction of clock
        return self.pt, self.pr, self.pb, self.pl, self.pzf, self.pzb
    padding3D = property(_get_padding3D, _set_padding)

    def _get_pt(self): # Padding top
        return self.css('pt', 0)
    def _set_pt(self, pt):
        self.style['pt'] = pt  # Overwrite element local style from here, parent css becomes inaccessable.
    pt = property(_get_pt, _set_pt)

    def _get_pb(self): # Padding bottom
        return self.css('pb', 0)
    def _set_pb(self, pb):
        self.style['pb'] = pb  # Overwrite element local style from here, parent css becomes inaccessable.
    pb = property(_get_pb, _set_pb)
    
    def _get_pl(self): # Padding left
        return self.css('pl', 0)
    def _set_pl(self, pl):
        self.style['pl'] = pl # Overwrite element local style from here, parent css becomes inaccessable.
    pl = property(_get_pl, _set_pl)
    
    def _get_pr(self): # Margin right
        return self.css('pr', 0)
    def _set_pr(self, pr):
        self.style['pr'] = pr  # Overwrite element local style from here, parent css becomes inaccessable.
    pr = property(_get_pr, _set_pr)

    def _get_pzf(self): # Padding z-axis front
        return self.css('pzf', 0)
    def _set_pzf(self, pzf):
        self.style['pzf'] = pzf  # Overwrite element local style from here, parent css becomes inaccessable.
    pzf = property(_get_pzf, _set_pzf)
    
    def _get_pzb(self): # Padding z-axis back
        return self.css('pzb', 0)
    def _set_pzb(self, pzb):
        self.style['pzb'] = pzb  # Overwrite element local style from here, parent css becomes inaccessable.
    pzb = property(_get_pzb, _set_pzb)

    def _get_originTop(self):
        u"""Answer the style flag if all point y values should measure top-down (typographic page
        orientation), instead of bottom-up (mathematical orientation). For Y-axis only. 
        The axes in X and Z directions are fixed."""
        return self.css('originTop')
    def _set_originTop(self, flag):
        if flag:
            self.style['originTop'] = True # Overwrite element local style from here, parent css becomes inaccessable.
            self.style['yAlign'] = TOP
        else:
            self.style['originTop'] = False
            self.style['yAlign'] = BOTTOM
    originTop = property(_get_originTop, _set_originTop)

    def _get_size(self):
        return self.getSize3D()  
    def _set_size(self, size):
        self.setSize(size)
    size = property(_get_size, _set_size)

    def getSize(self):
        u"""Answer the size of the element by calling properties self.w and self.h.
        This allows element to dynamically calculate the size if necessary, by redefining the
        self.w and/or self.h properties."""
        return self.w, self.h

    def getSize3D(self):
        u"""Answer the 3D size of the element."""
        return self.w, self.h, self.d

    def setSize(self, w, h=0, d=0):
        u"""Set the size of the element by calling by properties self.w and self.h. 
        If set, then overwrite access from style width and height. self.d is optional attribute."""
        if isinstance(w, (list, tuple)):
            if len(w) == 2:
                w, h = w
            elif len(w) == 3:
                w, h, d = w
            else:
                raise ValueError
        self.w = w # Set by property
        self.h = h 
        self.d = d # By default elements have 0 depth.

    def _get_pw(self): # Padded width
        return self.w - self.pl - self.pr
    pw = property(_get_pw)
    
    def _get_ph(self): # Padded height
        return self.h - self.pb - self.pt
    ph = property(_get_ph)
    
    def _get_pd(self): # Padded depth
        return self.d - self.pzf - self.pzb
    pd = property(_get_pd)
    
    def _get_shadow(self):
        return self.css('shadow')
    def _set_shadow(self, shadow):
        self.style['shadow'] = shadow
    shadow = property(_get_shadow, _set_shadow)

    def _get_textShadow(self):
        return self.css('textShadow')
    def _set_textShadow(self, textShadow):
        self.style['textShadow'] = textShadow
    textShadow = property(_get_textShadow, _set_textShadow)

    def _get_gradient(self):
        return self.css('gradient')
    def _set_gradient(self, gradient):
        self.style['gradient'] = gradient
    gradient = property(_get_gradient, _set_gradient)

    def _get_textGradient(self):
        return self.css('textGradient')
    def _set_textGradient(self, textGradient):
        self.style['textGradient'] = textGradient
    textGradient = property(_get_textGradient, _set_textGradient)

    def _get_box3D(self):
        u"""Answer the 3D bounding box of self from (self.x, self.y, self.w, self.h) properties."""
        return self.x or 0, self.y or 0, self.z or 0, self.w or 0, self.h or 0, self.d or 0
    box3D = property(_get_box3D)

    def _get_box(self):
        u"""Construct the bounding box from (self.x, self.y, self.w, self.h) properties."""
        return self.x or 0, self.y or 0, self.w or 0, self.h or 0
    box = property(_get_box)

    def _get_marginBox(self):
        u"""Calculate the margin position and margin resized box of the element, after applying the
        option style margin."""
        mt = self.mt
        mb = self.mb
        ml = self.ml
        if self.originTop:
            y = self.y - mt
        else:
            y = self.y - mb
        return (self.x - ml, y,
            self.w + ml + self.mr, 
            self.h + mt - mb)
    marginBox = property(_get_marginBox)

    def _get_paddedBox(self):
        u"""Calculate the padded position and padded resized box of the element, after applying the
        style padding. Answered format (x, y, w, h)."""
        pl = self.pl
        pt = self.pt
        pb = self.pb
        if self.originTop:
            y = self.y + pt
        else:
            y = self.y + pb
        return (self.x + pl, y, self.w - pl - self.pr, self.h - pt - pb)
    paddedBox = property(_get_paddedBox)

    def _get_paddedBox3D(self):
        u"""Calculate the padded position and padded resized box in 3D of the lement, after applying
        the style padding. Answered format (x, y, z, w, h, d)."""
        x, y, w, h = self.paddedBox
        pzf = self.pzf
        return x, y, self.z + pzf, w, h, self.d - pzf - self.pzb
    paddedBox3D = property(_get_paddedBox3D)

    # PDF naming: MediaBox is highlighted with a magenta rectangle, the BleedBox with a cyan 
    # one while dark blue is used for the TrimBox.
    # https://www.prepressure.com/pdf/basics/page-boxes

    # "Box" is bounding box on a single element.
    # "Block" is here used as bounding box of a group of elements.

    def _get_block3D(self):
        u"""Answer the vacuum 3D bounding box around all child elements."""
        x1 = y1 = z1 = XXXL
        x2 = y2 = z2 = -XXXL
        if not self.elements:
            return 0, 0, 0, 0, 0, 0
        for e in self.elements:
            x1 = min(x1, e.left)
            x2 = max(x2, e.right)
            if e.originTop:
                y1 = min(y1, e.top)
                y2 = max(y2, e.bottom)
            else:
                y1 = min(y1, e.bottom)
                y2 = max(y2, e.top)
            z1 = min(z1, e.front)
            z2 = max(z2, e.back)

        return x1, y1, z1, x2 - x1, y2 - y1, z2 - z1
    block3D = property(_get_block3D)

    def _get_block(self):
        u"""Answer the vacuum bounding box around all child elements in 2D"""
        x, y, _, w, h, _ = self.getVacuumElementsBox3D()
        return x, y, w, h
    block = property(_get_block)

    def _get_marginBlock3D(self):
        u"""Answer the vacuum 3D bounding box around all child elements."""
        x1 = y1 = z1 = XXXL
        x2 = y2 = z2 = -XXXL
        if not self.elements:
            return 0, 0, 0, 0, 0, 0
        for e in self.elements:
            x1 = min(x1, e.left - e.ml)
            x2 = max(x2, e.right + e.mr)
            if e.originTop:
                y1 = min(y1, e.top - e.mt)
                y2 = max(y2, e.bottom + e.mb)
            else:
                y1 = min(y1, e.bottom - e.mb)
                y2 = max(y2, e.top + e.mt)
            z1 = min(z1, e.front - e.zmf)
            z2 = max(z2, e.back - e.zmb)

        return x1, y1, z1, x2 - x1, y2 - y1, z2 - z1
    marginBlock3D = property(_get_marginBlock3D)

    def _get_block(self):
        u"""Answer the vacuum bounding box around all child elements in 2D"""
        x, y, _, w, h, _ = self._get_block()
        return x, y, w, h
    block = property(_get_block)

    def _get_paddedBlock3D(self):
        u"""Answer the vacuum 3D bounding box around all child elements, 
        subtracting their paddings. Sizes cannot become nextive."""
        x1 = y1 = z1 = XXXL
        x2 = y2 = z2 = -XXXL
        if not self.elements:
            return 0, 0, 0, 0, 0, 0
        for e in self.elements:
            x1 = max(x1, e.left + e.pl)
            x2 = min(x2, e.right - e.pl)
            if e.originTop:
                y1 = max(y1, e.top + e.pt)
                y2 = min(y2, e.bottom - e.pb)
            else:
                y1 = max(y1, e.bottom + e.pb)
                y2 = min(y2, e.top - e.pt)
            z1 = max(z1, e.front + e.zpf)
            z2 = min(z2, e.back - e.zpb)

        # Make sure that the values cannot overlap.
        if x2 < x1: # If overlap
            x1 = x2 = (x1 + x2)/2 # Middle the x position
        if y2 < y1: # If overlap
            y1 = y2 = (y1 + y2)/2 # Middle the y position
        if z2 < z1: # If overlap
            z1 = z2 = (z1 + z2)/2 # Middle the z position
        return x1, y1, z1, x2 - x1, y2 - y1, z2 - z1
    paddedBlock3D = property(_get_paddedBlock3D)

    def _get_block(self):
        u"""Answer the vacuum bounding box around all child elements in 2D"""
        x, y, _, w, h, _ = self._get_paddedBlock3D()
        return x, y, w, h
    block = property(_get_block)

    def _get_originsBlock3D(self):
        u"""Answer (minX, minY, maxX, maxY, minZ, maxZ) for all element origins."""
        minX = minY = XXXL
        maxX = maxY = -XXXL
        for e in self.elements:
            minX = min(minX, e.x)
            maxX = max(maxX, e.x)
            minY = min(minY, e.y)
            maxY = max(maxY, e.y)
            minZ = min(minZ, e.z)
            maxZ = max(maxZ, e.z)
        return minX, minY, minZ, maxX, maxY, maxZ
    originsBlock3D = property(_get_originsBlock3D)

    def _get_originsBlock(self):
        minX, minY, _, maxX, maxY, _ = self._get_originsBlock3D()
        return minX, minY, maxX, maxY
    originsBlock = property(_get_originsBlock)

    # Size limits

    def _get_minW(self):
        return self.css('minW') or MIN_WIDTH
    def _set_minW(self, minW): # Clip values
        self.style['minW'] = max(MIN_WIDTH, min(MAX_WIDTH, minW)) # Set on local style, shielding parent self.css value.
    minW = property(_get_minW, _set_minW)

    def _get_minH(self):
        return self.css('minH') or MIN_HEIGHT
    def _set_minH(self, minH):
        self.style['minH'] = max(MIN_HEIGHT, min(MAX_HEIGHT, minH)) # Set on local style, shielding parent self.css value.
    minH = property(_get_minH, _set_minH)

    def _get_minD(self): # Set/get the minimal depth, in case the element has 3D dimensions.
        return self.css('minD') or MIN_DEPTH
    def _set_minD(self, minD):
        self.style['minD'] = max(MIN_DEPTH, min(MAX_DEPTH, minD)) # Set on local style, shielding parent self.css value.
    minD = property(_get_minD, _set_minD)

    def getMinSize(self):
        u"""Answer the (minW, minH) of this element."""
        return self.minW, self.minH, self.minD

    def getMinSize3D(self):
        u"""Answer the (minW, minH, minD) of this element."""
        return self.minW, self.minH, self.minD

    def setMinSize(self, minW, minH=None, minD=None):
        if minW and minH is None and minD is None:
            if isinstance(minW, (int, float, long)):
                self.minW = self.minH = self.minD = minW
            elif isinstance(minH, (tuple, list)):
                if len(minH) == 1:
                    self.minW = self.minH = self.minD = minW
                elif len(minH) == 2:
                    self.minW = self.minH = minW
                    self.minD = 0
                elif len(minH) == 3:
                    self.minW, self.minH, self.minD = minW
        else:
            self.minW = minW
            self.minH = minH
            self.minD = minD or 0 # Optional minimum depth of the element.

    def _get_maxW(self):
        maxW = self.style.get('maxW')
        if self.parent:
            maxW = maxW or self.parent.w
        return maxW or MIN_WIDTH # Unless defined local, take current parent.w as maxW
    def _set_maxW(self, maxW):
        self.style['maxW'] = max(MIN_WIDTH, min(MAX_WIDTH, maxW)) # Set on local style, shielding parent self.css value.
    maxW = property(_get_maxW, _set_maxW)

    def _get_maxH(self):
        maxH = self.style.get('maxH')
        if self.parent:
            maxH = maxH or self.parent.h
        return maxH or MIN_HEIGHT # Unless defined local, take current parent.w as maxW
    def _set_maxH(self, maxH):
        self.style['maxH'] = max(MIN_HEIGHT, min(MAX_HEIGHT, maxH)) # Set on local style, shielding parent self.css value.
    maxH = property(_get_maxH, _set_maxH)

    def _get_maxD(self):
        maxD = self.style.get('maxD')
        if self.parent:
            maxD = maxD or self.parent.d
        return maxD or MIN_HEIGHT # Unless defined local, take current parent.w as maxW
    def _set_maxD(self, maxD):
        self.style['maxD'] = max(MIN_DEPTH, min(MAX_DEPTH, maxD)) # Set on local style, shielding parent self.css value.
    maxD = property(_get_maxD, _set_maxD)

    def getMaxSize(self):
        return self.maxW, self.maxH, self.maxD # No limit if value is None

    def setMaxSize(self, maxW, maxH=None, maxD=None):
        if maxW and maxH is None and maxD is None:
            if isinstance(maxW, (int, float, long)):
                self.maxW = self.maxH = self.maxD = maxW
            elif isinstance(maxH, (tuple, list)):
                if len(maxH) == 1:
                    self.maxW = self.maxH = self.maxD = maxW
                elif len(maxH) == 2:
                    self.maxW = self.maxH = maxW
                    self.maxD = 0
                elif len(maxH) == 3:
                    self.maxW, self.maxH, self.maxD = maxW
        else:
            self.maxW = maxW
            self.maxH = maxH
            self.maxD = maxD or 0 # Optional maximum depth of the element.

    def _get_scaleX(self):
        return self.css('scaleX', 1)
    def _set_scaleX(self, scaleX):
        assert scaleX != 0
        self.style['scaleX'] = scaleX # Set on local style, shielding parent self.css value.
    scaleX = property(_get_scaleX, _set_scaleX)

    def _get_scaleY(self):
        return self.css('scaleX', 1)
    def _set_scaleY(self, scaleY):
        assert scaleY != 0
        self.style['scaleY'] = scaleY # Set on local style, shielding parent self.css value.
    scaleY = property(_get_scaleY, _set_scaleY)

    def _get_scaleZ(self):
        return self.css('scaleZ', 1)
    def _set_scaleZ(self, scaleY):
        assert scaleZ != 0
        self.style['scaleZ'] = scaleZ # Set on local style, shielding parent self.css value.
    scaleZ = property(_get_scaleZ, _set_scaleZ)

    def getFloatTopSide(self, previousOnly=True, tolerance=0):
        u"""Answer the max y that can float to top, without overlapping previous sibling elements.
        This means we are just looking at the vertical projection between (self.left, self.right).
        Note that the y may be outside the parent box. Only elements with identical z-value are compared.
        Comparison of available spave, includes the margins of the elements."""
        if self.originTop:
            y = 0
        else:
            y = self.parent.h
        for e in self.parent.elements: 
            if previousOnly and e is self: # Only look at siblings that are previous in the list.
                break 
            if abs(e.z - self.z) > tolerance or e.mRight < self.mLeft or self.mRight < e.mLeft:
                continue # Not equal z-layer or not in window of vertical projection.
            if self.originTop:
                y = max(y, e.mBottom)
            else:
                y = min(y, e.mBottom)
        return y

    def getFloatBottomSide(self, previousOnly=True, tolerance=0):
        u"""Answer the max y that can float to bottom, without overlapping previous sibling elements.
        This means we are just looking at the vertical projection of (self.left, self.right).
        Note that the y may be outside the parent box. Only elements with identical z-value are compared.
        Comparison of available spave, includes the margins of the elements."""
        if self.originTop:
            y = self.parent.h
        else:
            y = 0
        for e in self.parent.elements: # All elements that share self.parent, except self.
            if previousOnly and e is self: # Only look at siblings that are previous in the list.
                break 
            if abs(e.z - self.z) > tolerance or e.mRight < self.mLeft or self.mRight < e.mLeft:
                continue # Not equal z-layer or not in window of vertical projection.
            if self.originTop:
                y = min(y, e.mTop)
            else:
                y = max(y, e.mTop)
        return y

    def getFloatLeftSide(self, previousOnly=True, tolerance=0):
        u"""Answer the max x that can float to the left, without overlapping previous sibling elements.
        This means we are just looking at the horizontal projection of (self.top, self.bottom).
        Note that the x may be outside the parent box. Only elements with identical z-value are compared.
        Comparison of available spave, includes the margins of the elements."""
        x = 0
        for e in self.parent.elements: # All elements that share self.parent, except self.
            if previousOnly and e is self: # Only look at siblings that are previous in the list.
                break 
            if abs(e.z - self.z) > tolerance:
                continue # Not equal z-layer
            if self.originTop: # not in window of horizontal projection.
                if e.mBottom <= self.mTop or self.mBottom <= e.mTop:
                    continue
            else:
                if e.mBottom >= self.mTop or self.mBottom >= e.mTop:
                    continue 
            x = max(e.mRight, x)
        return x

    def getFloatRightSide(self, previousOnly=True, tolerance=0):
        u"""Answer the max Y that can float to the right, without overlapping previous sibling elements.
        This means we are just looking at the vertical projection of (self.left, self.right).
        Note that the y may be outside the parent box. Only elements with identical z-value are compared.
        Comparison of available spave, includes the margins of the elements."""
        x = self.parent.w
        for e in self.parent.elements: # All elements that share self.parent, except self.
            if previousOnly and e is self: # Only look at siblings that are previous in the list.
                break 
            if abs(e.z - self.z) > tolerance or e.mBottom < self.mTop or self.mBottom < e.mTop:
                continue # Not equal z-layer or not in window of horizontal projection.
            x = min(e.mLeft, x)
        return x

    def _applyAlignment(self, p):
        u"""Answer the p according to the alignment status in the css.""" 
        px, py, pz = point3D(p)
        # Horizontal
        xAlign = self.xAlign
        if xAlign == CENTER:
            px -= self.w/2/self.scaleX
        elif xAlign == RIGHT:
            px -= self.w/self.scaleX
        # Vertical
        yAlign = self.yAlign
        if yAlign == MIDDLE:
            py -= self.h/2/self.scaleY
        elif yAlign == TOP:
            py -= self.h/self.scaleY
        # Currently no alignment in z-axis implemented
        return px, py, pz

    def _applyOrigin(self, p):
        u"""If self.originTop is False, then the y-value is interpreted as mathematics, 
        starting at the bottom of the parent element, moving up.
        If the flag is True, then move from top down, where the origin of the element becomes
        top-left of the parent."""
        px, py, pz = point3D(p)
        if self.originTop and self.parent:
            py = self.parent.h - py
        return px, py, pz

    def _applyRotation(self, mx, my, angle):
        u"""Apply the rotation for angle, where (mx, my) is the rotation center."""
        save()
        # TODO: Working on this.

    def _restoreRotation(self):
        u"""Reset graphics state from rotation mode."""
        if self.css('rotationX') and self.css('rotationY') and self.css('rotationAngle'):
            restore()

    def _applyScale(self, p):
        u"""Internal method to apply the scale, if both *self.scaleX* and *self.scaleY* are set. Use this
        method paired with self._restoreScale(). The (x, y) answered as reversed scaled tuple,
        so drawing elements can still draw on "real size", while the other element is in scaled mode."""
        sx = self.scaleX
        sy = self.scaleY
        sz = self.scaleZ
        p = point3D(p)
        if sx and sy and sz and (sx != 1 or sy != 1 or sz != 1): # Make sure these are value scale values.
            save()
            scale(sx, sy)
            p = (p[0] / sx, p[1] / sy, p[2] / sz) # Scale point in 3 dimensions.
        return p

    def _restoreScale(self):
        u"""Reset graphics state from svaed scale mode. Make sure to match the call of self._applyScale.
        If one of (self.scaleX, self.scaleY, self.scaleZ) is not 0 or 1, then do the restore."""
        sx = self.scaleX
        sy = self.scaleY
        sz = self.scaleZ
        if sx and sy and sz and (sx != 1 or sy != 1 or sz != 1): # Make sure these are value scale values.
            restore()

    #   D R A W I N G  S U P P O R T 

    def _drawElements(self, origin, view):
        u"""Recursively draw all elements of self on their own relative position in the main canvas, """
        #p = pointOffset(self.point, origin)
        # Draw all elements relative to this point
        for e in self.elements:
            if e.show:
                e.draw(origin, view)

    def getElementInfoString(self):
        u"""Answer a single string with info about the element. Default is to show the posiiton
        and size (in points and columns). This method can be redefined by inheriting elements
        that want to show additional information."""
        s = '%s\nPosition: %s, %s, %s\nSize: %s, %s\nColumn point: %s, %s\nColumn size: %s, %s' % \
            (self.__class__.__name__ + ' ' + (self.name or ''), asFormatted(self.x), asFormatted(self.y), asFormatted(self.z), 
             asFormatted(self.w), asFormatted(self.h), 
             asFormatted(self.cx), asFormatted(self.cy), asFormatted(self.cw), asFormatted(self.ch),
            )
        if self.xAlign or self.yAlign:
            s += '\nAlign: %s, %s' % (self.xAlign, self.yAlign)
        if self.conditions:
            score = self.evaluate()
            s += '\nConditions: %d | Evaluate %d' % (len(self.conditions), score.result)
            if score.fails:
                s += ' Fails: %d' % len(score.fails)
                for eFail in score.fails:
                    s += '\n%s %s' % eFail
        return s

    def drawFrame(self, p, view):
        u"""Draw fill of the rectangular element space.
        The self.css('fill') defines the color of the element background.
        Instead of the DrawBot stroke and strokeWidth attributes, use
        borders or (borderTop, borderRight, borderBottom, borderLeft) attributes.
        """
        eShadow = self.shadow
        if eShadow:
            save()
            setShadow(eShadow)
            rect(p[0], p[1], self.w, self.h)
            restore()

        eFill = self.css('fill', None)
        eGradient = self.gradient
        if eFill or eGradient:
            save()
            # Drawing element fill and/or frame
            if eGradient: # Gradient overwrites setting of fill.
                setGradient(eGradient, p, self) # Add self to define start/end from relative size.
            else:
                setFillColor(eFill)
            #setStrokeColor(eStroke, eStrokeWidth)
            if self.framePath is not None: # In case defined, use instead of bounding box. 
                drawPath(self.framePath)
            else:
                rect(p[0], p[1], self.w, self.h)
            restore()

        # Instead of full frame drawing, check on separate border settings.
        borderTop = self.borderTop
        borderBottom = self.borderBottom
        borderRight = self.borderRight
        borderLeft = self.borderLeft

        if borderTop is not None:
            save()
            if borderTop['dash']:
                lineDash(*borderTop['dash'])
            setStrokeColor(borderTop['stroke'], borderTop['strokeWidth'])

            oLeft = 0 # Extra offset on left, if there is a left border.
            if borderLeft and (borderLeft['strokeWidth'] or 0) > 1:
                if borderLeft['line'] == ONLINE:
                    oLeft = borderLeft['strokeWidth']/2
                elif borderLeft['line'] == OUTLINE:
                    oLeft = borderLeft['strokeWidth']

            oRight = 0 # Extra offset on right, if there is a right border.
            if borderRight and (borderRight['strokeWidth'] or 0) > 1:
                if borderRight['line'] == ONLINE:
                    oRight = borderRight['strokeWidth']/2
                elif borderRight['line'] == OUTLINE:
                    oRight = borderRight['strokeWidth']

            if borderTop['line'] == OUTLINE:
                oTop = borderTop['strokeWidth']/2
            elif borderTop['line'] == INLINE:
                oTop = -borderTop['strokeWidth']/2
            else:
                oTop = 0

            if self.originTop:
                line((p[0]-oLeft, p[1]-oTop), (p[0]+self.w+oRight, p[1]-oTop))
            else:
                line((p[0]-oLeft, p[1]+self.h+oTop), (p[0]+self.w+oRight, p[1]+self.h+oTop))
            restore()

        if borderBottom is not None:
            save()
            if borderBottom['dash']:
                lineDash(*borderBottom['dash'])
            setStrokeColor(borderBottom['stroke'], borderBottom['strokeWidth'])

            oLeft = 0 # Extra offset on left, if there is a left border.
            if borderLeft and (borderLeft['strokeWidth'] or 0) > 1:
                if borderLeft['line'] == ONLINE:
                    oLeft = borderLeft['strokeWidth']/2
                elif borderLeft['line'] == OUTLINE:
                    oLeft = borderLeft['strokeWidth']

            oRight = 0 # Extra offset on right, if there is a right border.
            if borderRight and (borderRight['strokeWidth'] or 0) > 1:
                if borderRight['line'] == ONLINE:
                    oRight = borderRight['strokeWidth']/2
                elif borderRight['line'] == OUTLINE:
                    oRight = borderRight['strokeWidth']

            if borderBottom['line'] == OUTLINE:
                oBottom = borderBottom['strokeWidth']/2
            elif borderBottom['line'] == INLINE:
                oBottom = -borderBottom['strokeWidth']/2
            else:
                oBottom = 0

            if self.originTop:
                line((p[0]-oLeft, p[1]+self.h+oBottom), (p[0]+self.w+oRight, p[1]+self.h+oBottom))
            else:
                line((p[0]-oLeft, p[1]-oBottom), (p[0]+self.w+oRight, p[1]-oBottom))
            restore()
        
        if borderRight is not None:
            save()
            if borderRight['dash']:
                lineDash(*borderRight['dash'])
            setStrokeColor(borderRight['stroke'], borderRight['strokeWidth'])

            oTop = 0 # Extra offset on top, if there is a top border.
            if borderTop and (borderTop['strokeWidth'] or 0) > 1:
                if borderTop['line'] == ONLINE:
                    oTop = borderTop['strokeWidth']/2
                elif borderLeft['line'] == OUTLINE:
                    oTop = borderTop['strokeWidth']

            oBottom = 0 # Extra offset on bottom, if there is a bottom border.
            if borderBottom and (borderBottom['strokeWidth'] or 0) > 1:
                if borderBottom['line'] == ONLINE:
                    oBottom = borderBottom['strokeWidth']/2
                elif borderBottom['line'] == OUTLINE:
                    oBottom = borderBottom['strokeWidth']

            if borderRight['line'] == OUTLINE:
                oRight = borderRight['strokeWidth']/2
            elif borderLeft['line'] == INLINE:
                oRight = -borderRight['strokeWidth']/2
            else:
                oRight = 0

            if self.originTop:
                line((p[0]+self.w+oRight, p[1]-oTop), (p[0]+self.w+oRight, p[1]+self.h+oBottom))
            else:
                line((p[0]+self.w+oRight, p[1]-oBottom), (p[0]+self.w+oRight, p[1]+self.h+oTop))
            restore()

        if borderLeft is not None:
            save()
            if borderLeft['dash']:
                lineDash(*borderLeft['dash'])
            setStrokeColor(borderLeft['stroke'], borderLeft['strokeWidth'])

            oTop = 0 # Extra offset on top, if there is a top border.
            if borderTop and (borderTop['strokeWidth'] or 0) > 1:
                if borderTop['line'] == ONLINE:
                    oTop = borderTop['strokeWidth']/2
                elif borderLeft['line'] == OUTLINE:
                    oTop = borderTop['strokeWidth']

            oBottom = 0 # Extra offset on bottom, if there is a bottom border.
            if borderBottom and (borderBottom['strokeWidth'] or 0) > 1:
                if borderBottom['line'] == ONLINE:
                    oBottom = borderBottom['strokeWidth']/2
                elif borderBottom['line'] == OUTLINE:
                    oBottom = borderBottom['strokeWidth']

            if borderLeft['line'] == OUTLINE:
                oLeft = borderLeft['strokeWidth']/2
            elif borderLeft['line'] == INLINE:
                oLeft = -borderLeft['strokeWidth']/2
            else:
                oLeft = 0

            if self.originTop:
                line((p[0]-oLeft, p[1]-oTop), (p[0]-oLeft, p[1]+self.h+oBottom))
            else:
                line((p[0]-oLeft, p[1]-oBottom), (p[0]-oLeft, p[1]+self.h+oTop))
            restore()

    def draw(self, origin, view, drawElements=True):
        u"""Default drawing method just drawing the frame. 
        Probably will be redefined by inheriting element classes."""
        p = pointOffset(self.oPoint, origin)
        p = self._applyScale(p)    
        px, py, _ = p = self._applyAlignment(p) # Ignore z-axis for now.

        self.drawFrame(p, view) # Draw optional frame or borders.

        if self.drawBefore is not None: # Call if defined
            self.drawBefore(self, p, view)

        if drawElements:
            # If there are child elements, draw them over the pixel image.
            self._drawElements(p, view)

        if self.drawAfter is not None: # Call if defined
            self.drawAfter(self, p, view)

        self._restoreScale()
        view.drawElementMetaInfo(self, origin) # Depends on flag 'view.showElementInfo'

    #   V A L I D A T I O N

    def evaluate(self, score=None):
        u"""Evaluate the content of element e with the total sum of conditions."""
        if score is None:
            score = Score()
        if self.conditions: # Can be None or empty
            for condition in self.conditions: # Skip in case there are no conditions in the style.
             condition.evaluate(self, score)
        for e in self.elements: # Also works if showing element is not a container.
            if e.show:
                e.evaluate(score)
        return score
         
    def solve(self, score=None):
        u"""Evaluate the content of element e with the total sum of conditions."""
        if score is None:
            score = Score()
        if self.conditions: # Can be None or empty
            for condition in self.conditions: # Skip in case there are no conditions in the style.
                condition.solve(self, score)
        for e in self.elements: # Also works if showing element is not a container.
            if e.show:
                e.solve(score)
        return score
         
    #   C O N D I T I O N S

    def isBottomOnBottom(self, tolerance=0):
        if self.originTop:
            return abs(self.parent.h - self.parent.pb - self.bottom) <= tolerance
        return abs(self.parent.pb - self.bottom) <= tolerance

    def isBottomOnBottomSide(self, tolerance=0):
        if self.originTop:
            return abs(self.parent.h - self.bottom) <= tolerance
        return abs(self.bottom) <= tolerance
        
    def isBottomOnTop(self, tolerance=0):
        if self.originTop:
            return abs(self.parent.pt - self.bottom) <= tolerance
        return abs(self.parent.h - self.parent.pt - self.bottom) <= tolerance

    def isCenterOnCenter(self, tolerance=0):
        pl = self.parent.pl # Get parent padding left
        center = (self.parent.w - self.parent.pr - pl)/2
        return abs(pl + center - self.center) <= tolerance

    def isCenterOnCenterSides(self, tolerance=0):
        return abs(self.parent.w/2 - self.center) <= tolerance
  
    def isCenterOnLeft(self, tolerance=0):
        return abs(self.parent.pl - self.center) <= tolerance

    def isCenterOnRight(self, tolerance=0):
        return abs(self.parent.w - self.parent.pr - self.center) <= tolerance
   
    def isCenterOnRightSide(self, tolerance=0):
        return abs(self.parent.w - self.center) <= tolerance

    def isMiddleOnBottom(self, tolerance=0):
        if self.originTop:
            return abs(self.parent.h - self.parent.pb - self.middle) <= tolerance
        return abs(self.parent.pb - self.middle) <= tolerance

    def isMiddleOnBottomSide(self, tolerance=0):
        if self.originTop:
            return abs(self.parent.h - self.middle) <= tolerance
        return abs(self.middle) <= tolerance

    def isMiddleOnTop(self, tolerance=0):
        if self.originTop:
            return abs(self.parent.pt - self.middle) <= tolerance
        return abs(self.parent.h - self.parent.pt - self.middle) <= tolerance

    def isMiddleOnTopSide(self, tolerance=0):
        if self.originTop:
            return abs(self.middle) <= tolerance
        return abs(self.parent.h - self.middle) <= tolerance

    def isMiddleOnMiddle(self, tolerance=0):
        pt = self.parent.pt # Get parent padding top
        pb = self.parent.pb 
        middle = (self.parent.h - pt - pb)/2
        if self.originTop:
            return abs(pt + middle - self.middle) <= tolerance
        return abs(pb + middle - self.middle) <= tolerance

    def isMiddleOnMiddleSides(self, tolerance=0):
        if self.originTop:
            return abs(self.middle) <= tolerance
        return abs(self.parent.h - self.middle) <= tolerance
  
    def isLeftOnCenter(self, tolerance=0):
        pl = self.parent.pl # Get parent padding left
        center = (self.parent.w - self.parent.pr - pl)/2
        return abs(pl + center - self.left) <= tolerance

    def isLeftOnCenterSides(self, tolerance=0):
        return abs(self.parent.w/2 - self.left) <= tolerance

    def isLeftOnLeft(self, tolerance=0):
        return abs(self.parent.pl - self.left) <= tolerance

    def isLeftOnLeftSide(self, tolerance=0):
        return abs(self.left) <= tolerance

    def isLeftOnRight(self, tolerance=0):
        return abs(self.parent.w - self.parent.pr - self.left) <= tolerance

    def isCenterOnLeftSide(self, tolerance=0):
        return abs(self.parent.left - self.center) <= tolerance

    def isTopOnMiddle(self, tolerance=0):
        pt = self.parent.pt # Get parent padding top
        pb = self.parent.pb 
        middle = (self.parent.h - pb - pt)/2
        if self.originTop:
            return abs(pt + middle - self.top) <= tolerance
        return abs(pb + middle - self.top) <= tolerance

    def isTopOnMiddleSides(self, tolerance=0):
        return abs(self.parent.h/2 - self.top) <= tolerance

    def isOriginOnBottom(self, tolerance=0):
        pb = self.parent.pb # Get parent padding left
        if self.originTop:
            return abs(self.parent.h - pb - self.y) <= tolerance
        return abs(pb - self.y) <= tolerance

    def isOriginOnBottomSide(self, tolerance=0):
        if self.originTop:
            return abs(self.parent.h - self.y) <= tolerance
        return abs(self.y) <= tolerance

    def isOriginOnCenter(self, tolerance=0):
        pl = self.parent.pl # Get parent padding left
        center = (self.parent.w - self.parent.pr - pl)/2
        return abs(pl + center - self.x) <= tolerance

    def isOriginOnCenterSides(self, tolerance=0):
        return abs(self.parent.w/2 - self.x) <= tolerance

    def isOriginOnLeft(self, tolerance=0):
        return abs(self.parent.pl - self.x) <= tolerance

    def isOriginOnLeftSide(self, tolerance=0):
        return abs(self.x) <= tolerance

    def isOriginOnRight(self, tolerance=0):
        return abs(self.parent.w - self.parent.pr - self.x) <= tolerance

    def isOriginOnRightSide(self, tolerance=0):
        return abs(self.parent.w - self.x) <= tolerance

    def isOriginOnTop(self, tolerance=0):
        if self.originTop:
            return abs(self.parent.pt - self.y) <= tolerance
        return abs(self.parent.h - self.parent.pt - self.y) <= tolerance

    def isOriginOnTopSide(self, tolerance=0):
        if self.originTop:
            return abs(self.y) <= tolerance
        return abs(self.parent.h - self.y) <= tolerance

    def isOriginOnMiddle(self, tolerance=0):
        if self.originTop:
            return abs(mt + (self.parent.h - self.parent.pb - self.parent.pt)/2 - self.y) <= tolerance
        return abs(mb + (self.parent.h - self.parent.pb - self.parent.pt)/2 - self.y) <= tolerance
 
    def isOriginOnMiddleSides(self, tolerance=0):
        if self.originTop:
            return abs(self.parent.h/2 - self.y) <= tolerance
        return abs(self.parent.h/2 - self.y) <= tolerance
 
    def isRightOnCenter(self, tolerance=0):
        return abs(self.parent.w - self.x) <= tolerance

    def isRightOnCenterSides(self, tolerance=0):
        return abs(self.parent.w/2 - self.right) <= tolerance

    def isRightOnLeft(self, tolerance=0):
        return abs(self.parent.pl - self.right) <= tolerance

    def isRightOnRight(self, tolerance=0):
        return abs(self.parent.w - self.parent.pr - self.right) <= tolerance

    def isRightOnRightSide(self, tolerance=0):
        return abs(self.parent.w - self.right) <= tolerance

    def isBottomOnMiddle(self, tolerance=0):
        pt = self.parent.pt # Get parent padding top
        pb = self.parent.pb
        middle = (self.parent.h - pb - pt)/2
        if self.originTop:
            return abs(pt + middle - self.bottom) <= tolerance
        return abs(pb + middle - self.bottom) <= tolerance

    def isBottomOnMiddleSides(self, tolerance=0):
        return abs(self.parent.h/2 - self.bottom) <= tolerance

    def isTopOnBottom(self, tolerance=0):
        if self.originTop:
            return abs(self.parent.h - self.parent.pb - self.top) <= tolerance
        return abs(self.parent.pb - self.top) <= tolerance

    def isTopOnTop(self, tolerance=0):
        if self.originTop:
            return abs(self.parent.pt - self.top) <= tolerance
        return abs(self.parent.h - self.parent.pt - self.top) <= tolerance

    def isTopOnTopSide(self, tolerance=0):
        if self.originTop:
            return abs(self.top) <= tolerance
        return abs(self.parent.h - self.top) <= tolerance

    # Shrink block conditions

    def isSchrunkOnBlockLeft(self, tolerance):
        boxX, _, _, _ = self.marginBox
        return abs(self.left + self.pl - boxX) <= tolerance

    def isShrunkOnBlockRight(self, tolerance):
        boxX, _, boxW, _ = self.marginBox
        return abs(self.right - self.pr - (boxX + boxW)) <= tolerance
     
    def isShrunkOnBlockTop(self, tolerance):
        _, boxY, _, boxH = self.marginBox
        if self.originTop:
            return abs(self.top + self.pt - boxY) <= tolerance
        return self.top - self.pt - (boxY + boxH) <= tolerance

    def isShrunkOnBlockBottom(self, tolerance):
        u"""Test if the bottom of self is shrunk to the bottom position of the block."""
        _, boxY, _, boxH = self.marginBox
        if self.originTop:
            return abs(self.h - self.pb - (boxY + boxH)) <= tolerance
        return abs(self.pb - boxY) <= tolerance

    def isShrunkOnBlockLeftSide(self, tolerance):
        boxX, _, _, _ = self.box
        return abs(self.left - boxX) <= tolerance

    def isShrunkOnBlockRightSide(self, tolerance):
        boxX, _, boxW, _ = self.mbox
        return abs(self.right - (boxX + boxW)) <= tolerance
     
    def isShrunkOnBlockTopSide(self, tolerance):
        _, boxY, _, boxH = self.box
        if self.originTop:
            return abs(self.top - boxY) <= tolerance
        return self.top - (boxY + boxH) <= tolerance

    def isShrunkOnBlockBottomSide(self, tolerance):
        _, boxY, _, boxH = self.marginBox
        if self.originTop:
            return abs(self.bottom - (boxY + boxH)) <= tolerance
        return abs(self.bottom - boxY) <= tolerance

    # Float conditions

    def isFloatOnTop(self, tolerance=0):
        if self.originTop:
            return abs(max(self.getFloatTopSide(), self.parent.pt) - self.mTop) <= tolerance
        return abs(min(self.getFloatTopSide(), self.parent.h - self.parent.pt) - self.mTop) <= tolerance

    def isFloatOnTopSide(self, tolerance=0):
        return abs(self.getFloatTopSide() - self.mTop) <= tolerance

    def isFloatOnBottom(self, tolerance=0):
        if self.originTop:
            return abs(min(self.getFloatBottomSide(), self.parent.h - self.parent.pb) - self.mBottom) <= tolerance
        return abs(max(self.getFloatBottomSide(), self.parent.pb) - self.mBottom) <= tolerance

    def isFloatOnBottomSide(self, tolerance=0):
        return abs(self.getFloatBottomSide() - self.mBottom) <= tolerance

    def isFloatOnLeft(self, tolerance=0):
        return abs(max(self.getFloatLeftSide(), self.parent.pl) - self.mLeft) <= tolerance

    def isFloatOnLeftSide(self, tolerance=0):
        return abs(self.getFloatLeftSide() - self.mLeft) <= tolerance

    def isFloatOnRight(self, tolerance=0):
        return abs(min(self.getFloatRightSide(), self.parent.w - self.parent.pr) - self.mRight) <= tolerance

    def isFloatOnRightSide(self, tolerance=0):
        return abs(self.getFloatRightSide() - self.mRight) <= tolerance

    #   T R A N S F O R M A T I O N S 

    def bottom2Bottom(self):
        if self.originTop:
            self.bottom = self.parent.h - self.parent.pb
        else:
            self.bottom = self.parent.pb
        return True

    def bottom2BottomSide(self):
        if self.originTop:
            self.bottom = self.parent.h
        else:
            self.bottom = 0
        return True

    def bottom2Top(self):
        if self.originTop:
            self.bottom = self.parent.pt 
        else:
            self.bottom = self.parent.h - self.parent.pt
        return True
    
    def middle2Bottom(self):
        if self.originTop:
            self.middle = self.parent.h - self.parent.pb
        else:
            self.middle = self.parent.pb
        return True
    
    def middle2BottomSide(self):
        if self.originTop:
            self.middle = self.parent.h
        else:
            self.middle = 0
        return True

    def center2Center(self):
        pl = self.parent.pl # Get parent padding left
        self.center = pl + (self.parent.w - self.parent.pr - pl)/2
        return True
    
    def center2CenterSides(self):
        self.center = self.parent.w/2
        return True

    def center2Left(self):
        self.center = self.parent.pl # Padding left
        return True

    def center2LeftSide(self):
        self.center = 0
        return True

    def center2Right(self):
        self.center = self.parent.w - self.parent.pr
        return True

    def center2RightSide(self):
        self.center = self.parent.w
        return True

    def middle2Top(self):
        if self.originTop:
            self.middle = self.parent.pt
        else:
            self.middle = self.parent.h - self.parent.pt
        return True       

    def middle2TopSide(self):
        if self.originTop:
            self.middle = 0
        else:
            self.middle = self.parent.h
        return True       

    def middle2Middle(self): # Vertical center, following CSS naming.
        pt = self.parent.pt # Get parent padding top
        pb = self.parent.pb
        middle = (self.parent.h - pb - pt)/2
        if self.originTop:
            self.middle = pt + middle
        else:
            self.middle = pb + middle
        return True

    def middle2MiddleSides(self):
        self.middle = self.parent.h/2

    def left2Center(self):
        pl = self.parent.pl # Get parent padding left
        self.left = pl + (self.parent.w - self.parent.pr - pl)/2
        return True       

    def left2CenterSides(self):
        self.left = self.parent.w/2
        return True       

    def left2Left(self):
        self.left = self.parent.pl # Padding left
        return True       

    def left2Right(self):
        self.left = self.parent.w - self.parent.pr
        return True       

    def left2LeftSide(self):
        self.left = 0
        return True       

    def top2Middle(self):
        pt = self.parent.pt # Get parent padding left
        pb = self.parent.pb
        middle = (self.parent.h - pb - pt)/2
        if self.originTop:
            self.top = pt + middle
        else:
            self.top = pb + middle
        return True       

    def top2MiddleSides(self):
        self.top = self.parent.h/2
        return True       

    def origin2Bottom(self):
        if self.originTop:
            self.y = self.parent.h - self.parent.pb
        else:
            self.y = self.parent.pb
        return True

    def origin2BottomSide(self):
        if self.originTop:
            self.y = self.parent.h
        else:
            self.y = 0
        return True       

    def origin2Center(self):
        self.x = ml + (self.parent.w - self.parent.pr - sepf.parent.pl)/2
        return True       

    def origin2CenterSides(self):
        self.x = self.parent.w/2
        return True       

    def origin2Left(self):
        self.x = self.parent.pl # Padding left
        return True       

    def origin2LeftSide(self):
        self.x = 0
        return True       

    def origin2Right(self):
        self.x = self.parent.w - self.parent.pr
        return True

    def origin2RightSide(self):
        self.x = self.parent.w
        return True

    def origin2Top(self):
        if self.originTop:
            self.y = self.parent.pt
        else:
            self.y = self.parent.h - self.parent.pt
        return True

    def origin2TopSide(self):
        if self.originTop:
            self.y = 0
        else:
            self.y = self.parent.h
        return True

    def origin2Middle(self):
        pt = self.parent.pt # Get parent padding top
        pb = self.parent.pb
        middle = (self.parent.h - pb - pt)/2
        if self.originTop:
            self.y = pt + middle
        else:
            self.y = pb + middle
        return True
 
    def origin2MiddleSides(self):
        self.y = self.parent.h/2
        return True

    def right2Center(self):
        pl = self.parent.pl # Get parent padding left
        self.right = pl + (self.parent.w - self.parent.pr - pl)/2
        return True

    def right2CenterSides(self):
        self.right = self.parent.w/2
        return True

    def right2Left(self):
        self.right = self.parent.pl # Padding left
        return True

    def right2Right(self):
        self.right = self.parent.w - self.parent.pr
        return True
    
    def right2RightSide(self):        
        self.right = self.parent.w
        return True

    def bottom2Middle(self):
        pt = self.parent.pt # Get parent padding top
        pb = self.parent.pb
        middle = (self.parent.h - pb - pt)/2
        if self.originTop:
            self.bottom = pt + middle
        else:
            self.bottom = pb + middle
        return True

    def bottom2MiddleSides(self):
        self.bottom = self.parent.h/2
        return True

    def top2Bottom(self):
        if self.originTop:
            self.top = self.parent.h - self.parent.pb
        else:
            self.top = self.parent.pb
        return True
    
    def top2Top(self):
        if self.originTop:
            self.top = self.parent.pt
        else:
            self.top = self.parent.h - self.parent.pt
        return True
    
    def top2TopSide(self):
        if self.originTop:
            self.mTop = 0
        else:
            self.mTop = self.parent.h
        return True

    def float2Top(self):
        u"""Float the element upward, until top hits the parent top padding.
        Include margin to decide if it fits."""
        if self.originTop:
            self.mTop = min(self.getFloatTopSide(), self.parent.pt)
        else:
            self.mTop = min(self.getFloatTopSide(), self.parent.h - self.parent.pt)
        return True

    def float2TopSide(self):
        self.mTop = self.getFloatTopSide()
        return True

    def float2Bottom(self):
        if self.originTop:
            self.mBottom = min(self.getFloatBottomSide(), self.parent.h - self.parent.pb)
        else:
            self.mBottom = min(self.getFloatBottomSide(), self.parent.pb)
        return True

    def float2BottomSide(self):
        self.mBottom = self.getFloatBottomSide()
        return True

    def float2Left(self):
        self.mLeft = max(self.getFloatLeftSide(), self.parent.pl) # padding left
        return True

    def float2LeftSide(self):
        self.mLeft = self.getFloatLeftSide()
        return True

    def float2Right(self):
        self.mRight = min(self.getFloatRightSide(), self.parent.w - self.parent.pr)
        return True

    def float2RightSide(self):
        self.mRight = self.getFloatRightSide()
        return True

    # WIth fitting (and shrinking) we need to change the actual size of the element.
    # This can have implications on it's content, and we need to take the min/max
    # sizes into conderantion: setting the self.w and self.h to a value, does not mean
    # that the size really got that value, if exceeding a min/max limit.
    
    def fit2Bottom(self):
        if self.originTop:
            self.h += self.parent.h - self.parent.pb - self.bottom
        else:
            self.h = self.top - self.parent.pb
            self.bottom = self.parent.pb
        return True

    def fit2BottomSide(self):
        if self.originTop:
            self.h += self.parent.h - self.bottom
        else:
            top = self.top
            self.bottom = 0
            self.h += top - self.top
        return True

    def fit2Left(self):
        right = self.right
        self.left = self.parent.pl # Padding left
        self.w += right - self.right
        return True

    def fit2LeftSide(self):
        right = self.right
        self.left = 0
        self.w += right - self.right
        return True

    def fit2Right(self):
        self.w += self.parent.w - self.parent.pr - self.right
        return True

    def fit2RightSide(self):
        self.w += self.parent.w - self.right
        return True

    def fit2Top(self):
        if self.originTop:
            bottom = self.bottom
            self.top = self.parent.pt
            self.h += bottom - self.bottom
        else:
            self.h += self.parent.h - self.parent.pt - self.top
        return True

    def fit2TopSide(self):
        if self.originTop:
            bottom = self.bottom
            self.top = 0
            self.h += bottom - self.bottom
        else:
            self.h += self.parent.h - self.top
        return True

    # Shrinking
    
    def shrink2BlockBottom(self):
        _, boxY, _, boxH = self.box
        if self.originTop:
            self.h = boxH
        else:
            top = self.top
            self.bottom = boxY
            self.h += top - self.top
        return True

    def shrink2BlockBottomSide(self):
        if self.originTop:
            self.h += self.parent.h - self.bottom
        else:
            top = self.top
            self.bottom = 0 # Parent botom 
            self.h += top - self.top
        return True

    def shrink2BlockLeft(self):
        right = self.right
        self.left = self.parent.pl # Padding left
        self.w += right - self.right
        return True

    def shrink2BlockLeftSide(self):
        right = self.right
        self.left = 0
        self.w += right - self.right
        return True

    def shrink2BlockRight(self):
        self.w += self.parent.w - self.parent.pr - self.right
        return True

    def shrink2BlockRightSide(self):
        self.w += self.parent.w - self.right
        return True

    def shrink2BlockTop(self):
        if self.originTop:
            bottom = self.bottom
            self.top = self.parent.pt
            self.h += bottom - self.bottom
        else:
            self.h += self.parent.h - self.parent.pt - self.top
        return True

    def shrink2BlockTopSide(self):
        if self.originTop:
            bottom = self.bottom
            self.top = 0
            self.h += bottom - self.bottom
        else:
            self.h += self.parent.h - self.top
        return True

    #    Text conditions

    def baseline2Top(self):
        # ...
        return True
        
    def baseline2Bottom(self):
        # ...
        return True

    def floatBaseline2Top(self):
        # ...
        return True

    def floatAscender2Top(self):
        # ...
        return True

    def floatCapHeight2Top(self):
        # ...
        return True

    def floatXHeight2Top(self):
        # ...
        return True


if __name__ == '__main__':
    import doctest
    doctest.testmod()
