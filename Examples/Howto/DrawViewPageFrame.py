# -----------------------------------------------------------------------------
#     Copyright (c) 2016+ Buro Petr van Blokland + Claudia Mens & Font Bureau
#     www.pagebot.io
#
#     P A G E B O T
#
#     Licensed under MIT conditions
#     Made for usage in DrawBot, www.drawbot.com
# -----------------------------------------------------------------------------
#
#     DrawViewPageFrame.py
#
#     Needs debug in view dimension showing.
#
from pagebot import newFS
from pagebot.style import getRootStyle, A5, BOTTOM, CENTER
# Document is the main instance holding all information about the document togethers (pages, styles, etc.)
from pagebot.document import Document
from pagebot.elements import *
from pagebot.conditions import *
    
W, H = 500, 500 #A5 

OriginTop = False

def makeDocument():
    # Create new document with (w,h) and fixed amount of pages.
    # Make number of pages with default document size.
    # Initially make all pages default with template
    rootStyle = getRootStyle()
    
    doc = Document(rootStyle, originTop=OriginTop, w=W, h=H, pages=1) 
    
    page = doc[0] # Get the first/single page of the document.
    page.size = W, H
    print page.originTop
    if OriginTop:
        s = 'Origin on top'
        conditions = (Center2Center(), Top2Top())
    else:
        s = 'Origin on bottom'
        conditions = (Center2Center(), Bottom2Bottom())
    
    fs = newFS(s, style=dict(fontSize=30, textFill=(1, 0, 0), xTextAlign=CENTER)) 
    nt = newText(fs, y=100, xxconditions=conditions, parent=page, fill=(1, 1, 0))
    print nt.x, nt.y, nt.w, nt.h
    score = page.solve()
    if score.fails:
        print score.fails
    print nt.x, nt.y, nt.w, nt.h
    
    # Set the view parameters for the required output.
    view = doc.getView()
    view.w = view.h = W, H
    view.padding = 100 # Make view padding to show crop marks and frame
    view.showPageFrame = True
    view.showPageCropMarks = True
    view.showElementOrigin = False
    view.showElementDimensions = True
    
    return doc
  
if __name__ == '__main__':

    Variable([
        #dict(name='ElementOrigin', ui='CheckBox', args=dict(value=False)),
        dict(name='OriginTop', ui='CheckBox', args=dict(value=False)),
    ], globals())

    d = makeDocument()
    d.export('_export/DrawViewPageFrame.pdf')
    
