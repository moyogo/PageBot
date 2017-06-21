
# Demo Spreadsheet Element
     
from pagebot.document import Document
from pagebot.elements import *
from pagebot.conditions import *
from pagebot.style import A5, TOP
from pagebot.contributions.filibuster.blurb import Blurb

class DemoSpreadSheet(Element):
    pass
    
W, H = A5

doc = Document(w=W, h=H, originTop=False, autoPages=1)

view = doc.getView()
view.showPagePadding = True
view.showElementOrigin = True
view.showFlowConnections = True

page = doc[0]
page.padding = int(page.h/12), int(page.w/12)

DemoSpreadSheet(parent=page, width=200, height=200, fill=0.8,
    conditions=[Left2Left(), Fit2Width(), Top2Top()]
)
#print he.x, he.y 
print page.solve()
#print he.x, he.y 

doc.export('_export/DemoSpreadSheetElement.pdf')