# -----------------------------------------------------------------------------
#     Copyright (c) 2016+ Type Network, www.typenetwork.com, www.pagebot.io
#
#     P A G E B O T
#
#     Licensed under MIT conditions
#     Made for usage in DrawBot, www.drawbot.com
# -----------------------------------------------------------------------------
#
#     ConditionalElements.py
#
#     This script generates a fake article on a single page, using Filibuster text,
#     automatic layout template, Galley, Typesetter and Composer classes.
#     Its purpose is to show the use of Validator
#
import pagebot # Import to know the path of non-Python resources.
from pagebot import getFormattedString, textBoxBaseLines
from pagebot.contributions.filibuster.blurb import blurb

# Creation of the RootStyle (dictionary) with all available default style parameters filled.
from pagebot.style import getRootStyle, LEFT_ALIGN, A4, A1, CENTER, RIGHT_ALIGN, BOTTOM_ALIGN
# Document is the main instance holding all information about the document togethers (pages, styles, etc.)
from pagebot.elements.document import Document
from pagebot.elements.galley import Galley
# The Typesetter instance takes content from a file (typically MarkDown text) and converts that 
# into Galley list of elements.
from pagebot.typesetter import Typesetter
# The Composer instance distributes the Galley content of the pages, according to the defined Templates.
from pagebot.composer import Composer 
from pagebot.conditions import Condition, Fit, Center2Center, Center2CenterSides, Left2Left, Left2LeftSide, Right2Right, Right2RightSide, Center2VerticalCenter, Top2Top, Top2TopSide, Origin2Top, Bottom2Bottom, Bottom2BottomSide
#, MaxWidthByFontSize

class FontSizeWidthRatio(Condition):
    def evaluate(self, e):
        if abs(e.x) <= self.tolerance and e.css('fontSize') < 20:
            return self.value
        return self.value * self.errorFactor
		
    def solve(self, e):
        if self.evaluate(e) < 0:
            e.style['fontSize'] = 19
            return self.value
        return self.value * self.errorFactor
	    
# For clarity, most of the OneValidatingPage.py example documenet is setup as a sequential excecution of
# Python functions. For complex documents this is not the best method. More functions and classes
# will be used in the real templates, which are available from the OpenSource PageBotTemplates repository.
    
W, H = A4 # or A1
H = W

# The standard PageBot function getRootStyle() answers a standard Python dictionary, 
# where all PageBot values are filled by their default values. The root style is kept in RS
# as reference to for all ininitialzaiton of elements. 
# Each element uses the root style as copy and then modifies the values it needs. 
# Note that the use of style dictionaries is fully recursive in PageBot, implementing a cascading structure
# that is very similar to what happens in CSS.

RS = getRootStyle(
    w = W,
    h = H,
    ml = 10,
    mt = 10,
    mr = 100,
    mb = 100,
    conditions = [],
    fontSize = 10,
    rLeading = 0,
    showElementInfo = True,
)

EXPORT_PATH = '_export/ConditionalElements.pdf' # Export in folder that does not commit un Git. Force to export PDF.

def makeDocument(rootStyle):
    u"""Demo page composer."""
    
    # Create new document with (w,h) and fixed amount of pages.
    # Make number of pages with default document size.
    # Initially make all pages default with template
    doc = Document(rootStyle, pages=1) 
 
    w = 300

    colorCondition1 = [ # Placement condition(s) for the color rectangle elements.
        # = Horizontal
        Fit(),
        #Center2Center(), 
        #Center2CenterSides(),
        #Left2Left(), 
        #Left2LeftSide(), 
        #Right2Right(), 
        #Right2RightSide(), 
        # = Vertical
        #Center2VerticalCenter(), 
        #Top2Top(), 
        #Top2TopSide(), 
        #Origin2Top(), 
        #Bottom2Bottom(), 
        #Bottom2BottomSide()
    ]
    colorCondition2 = [ # Placement condition(s) for the color rectangle elements.
        Center2Center(), 
        #Left2Left(), 
        #Left2LeftSide(), 
        #Right2Right(), 
        #Right2RightSide(), 
        #Center2VerticalCenter(), 
        Top2Top(), 
        #Top2TopSide(), 
        #Origin2Top(), 
        #Bottom2Bottom(), 
        #Bottom2BottomSide()
    ]
    textCondition = [ # Placement condition(s) for the text element..
        Center2Center(), 
        #Left2Left(), 
        #Left2LeftSide(), 
        #Right2Right(), 
        #Right2RightSide(), 
        #Center2VerticalCenter(), 
        Top2Top(), 
        #Top2TopSide(), 
        #Origin2Top(), 
        #Bottom2Bottom(), 
        #Bottom2BottomSide()
    ]
    # Obvious wrong placement of all elements, to be corrected by solving conditions.
    # In this example the wrongOrigin still shows the elements in the bottom left corner,
    # so it is obvious where they are, of not corrected.
    wrongOrigin = (-300, -300)
    
    page = doc[1] # Get the first/single page of the document.
    if page.originTop:
        p = (page.css('ml'), page.css('mt'))
    else:
        p = (page.css('ml'), page.css('mb'))
    page.rect(point=p, style=rootStyle, w=page.w - page.css('ml') - page.css('mr'),
    h = page.h - page.css('mt') - page.css('mb'),
    fill=0.9)
    # Add some color elements (same width, different height) at the “wrongOrigin” position.
    # They will be repositioned by solving the colorConditions.
    e1 = page.rect(point=wrongOrigin, style=rootStyle, w=w*2/3, h=300, conditions=colorCondition1, 
        fill=(1, 0.5, 0.5), align=LEFT_ALIGN, vAlign=BOTTOM_ALIGN)
    #e2 = page.rect(point=wrongOrigin, style=rootStyle, w=w, h=100, conditions=colorCondition2, 
    #    fill=(1, 1, 0), align=CENTER, vAlign=CENTER)
    # Make text box at wrong origin. Apply same width a the color rect, which may
    # be too wide from typographic point ogf view. The MaxWidthByFontSize will set the 
    # self.w to the maximum width for this pointSize.
    blurbText = getFormattedString(blurb.getBlurb('article', noTags=True), page,
        style=dict(font='Georgia', fontSize=9, rLeading=0.2, textColor=0))
    #eTextBox = page.textBox(blurbText, point=wrongOrigin, style=rootStyle, w=w, 
    #    vacuumH=True, conditions=textCondition, align=CENTER, vAlign=CENTER)

    score = page.evaluate()
    print 'Page value on evaluation:', score
    print score.fails
    # Try to solve the problems if evaluation < 0
    if score.result < 0:
        print 'Solving', score
        page.solve()
    print score.fails
    # Evaluate again, result should now be >= 0
    print 'Page value after solving the problems:', page.evaluate()
    
    return doc
        
d = makeDocument(RS)
d.export(EXPORT_PATH) 

    
