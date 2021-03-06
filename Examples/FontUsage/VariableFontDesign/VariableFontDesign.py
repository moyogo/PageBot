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
#     AutomaticPageComposition.py
#
#     This script generates an article (in Dutch) of 2009 about the approach to
#     generate automatic layouts, using Style, Galley, Typesetter and Composer classes.
#
import pagebot
from pagebot import textBoxBaseLines

from pagebot.style import getRootStyle, LEFT
from pagebot.document import Document
from pagebot.elements.pbpage import Page, Template
from pagebot.composer import Composer
from pagebot.typesetter import Typesetter
from pagebot.elements import Galley, Rect
#from pagebot.elements.variablefonts.variablecube import VariableCube
#from pagebot.fonttoolbox.variablebuilder import generateInstance
    
DEBUG = False

SHOW_GRID = DEBUG
SHOW_GRID_COLUMNS = DEBUG
SHOW_BASELINE_GRID = DEBUG
SHOW_FLOW_CONNECTIONS = DEBUG
  
# Get the default root style and overwrite values for this document.
U = 7
baselineGrid = 2*U
listIndent = 1.5*U

RS = getRootStyle(
    u = U, # Page base unit
    # Basic layout measures altering the default rooT STYLE.
    w = 595, # Om root level the "w" is the page width 210mm, international generic fit.
    h = 11 * 72, # Page height 11", international generic fit.
    pl = 7*U, # Padding left rs.pt = 7*U # Padding top
    baselineGrid = baselineGrid,
    g = U, # Generic gutter.
    # Column width. Uneven means possible split in 5+1+5 or even 2+1+2 +1+ 2+1+2
    # 11 is a the best in that respect for column calculation.
    cw = 11*U, 
    ch = 6*baselineGrid - U, # Approx. square and fitting with baseline.
    listIndent = listIndent, # Indent for bullet lists
    listTabs = [(listIndent, LEFT)], # Match bullet+tab with left indent.
    # Display option during design and testing
    showGrid = SHOW_GRID,
    showGridColumns = SHOW_GRID_COLUMNS,
    showBaselineGrid = SHOW_BASELINE_GRID,
    showFlowConnections = SHOW_FLOW_CONNECTIONS,
    # Text measures
    leading = baselineGrid,
    rLeading = 0,
    fontSize = 9
)
# Tracking presets
H1_TRACK = H2_TRACK = 0.015 # 1/1000 of fontSize, multiplier factor.
H3_TRACK = 0.030 # Tracking as relative factor to font size.
P_TRACK = 0.030

FONT_PATH = pagebot.getFontPath()
VAR_FONT_PATH = FONT_PATH + 'fontbureau/AmstelvarAlpha-Variables.ttf'
EXPORT_PATH = '_export/AmstelvarAlphaSpecimen.pdf'


# -----------------------------------------------------------------         
if __name__ == '__main__':
    def makeSpecimen(rs):
            
        # Template 1
        template1 = Template(rs) # Create template of main size. Front page only.
        # Show grid columns and paddings if rootStyle.showGrid or rootStyle.showGridColumns are True
        template1.grid(rs) 
        # Show baseline grid if rs.showBaselineGrid is True
        template1.baselineGrid(rs)
        vCube = VariableCube(path=VAR_FONT_PATH, point=(50, 100), w=500, h=500, s='a', fontSize=86, dimensions=dict(wght=5, wdth=5))
        template1.append(vCube)
       
        # Create new document with (w,h) and fixed amount of pages.
        # Make number of pages with default document size.
        # Initially make all pages default with template2
        doc = Document(rs, pages=1, template=template1) 

        return doc
            
    d = makeSpecimen(RS)
    d.export(EXPORT_PATH) 

