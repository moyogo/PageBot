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
#     BitcountReference.py
#
#     This script the PDF document with Bitcount refernce information.
#
import pagebot
from pagebot import newFS, findMarkers, textBoxBaseLines
from pagebot.style import getRootStyle, LEFT, NO_COLOR, RIGHT
from pagebot.document import Document
from pagebot.elements.pbpage import Page, Template
from pagebot.composer import Composer
from pagebot.typesetter import Typesetter
from pagebot.elements import Galley
from pagebot.fonttoolbox.objects.family import getFamilyFontPaths

DEBUG = False

SHOW_GRID = True
SHOW_GRID_COLUMNS = True
SHOW_BASELINE_GRID = DEBUG
SHOW_FLOW_CONNECTIONS = DEBUG

if SHOW_GRID:
    BOX_COLOR = (0.8, 0.8, 0.8, 0.4)
else:
    BOX_COLOR = None
    
# Get the default root style and overwrite values for this document.
U = 7
baselineGrid = 2*U
listIndent = 1.5*U

RS = getRootStyle(
    u = U, # Page base unit
    # Basic layout measures altering the default rooT STYLE.
    w = 595, # Om root level the "w" is the page width 210mm, international generic fit.
    h = 842, # 842 = A4 height. Other example: page height 11", international generic fit.
    pl = 8*U, # Padding left rs.mt = 7*U # Padding top
    baselineGrid = 14,#baselineGrid,
    gw = 2*U, # Generic gutter, equal for width and height
    gh = 2*U,
    # Column width. Uneven means possible split in 5+1+5 or even 2+1+2 +1+ 2+1+2
    # Uneven a the best in that respect for column calculation,
    # as it is possible to make micro columsn with the same gutter.
    cw = 8*U, 
    ch = 5*baselineGrid - U, # Approx. square and fitting with baseline.
    listIndent = listIndent, # Indent for bullet lists
    listTabs = [(listIndent, LEFT)], # Match bullet+tab with left indent.
    # Display option during design and testing
    showGrid = SHOW_GRID,
    showGridColumns = SHOW_GRID_COLUMNS,
    showBaselineGrid = SHOW_BASELINE_GRID,
    showFlowConnections = SHOW_FLOW_CONNECTIONS,
    BOX_COLOR = BOX_COLOR,
    # Text measures
    leading = 14,
    rLeading = 0,
    rTracking = 0,
    fontSize = 9
)
# LANGUAGE-SWITCH Language settings
RS['language'] = 'en'

Slashed_Zero = False
Smallcaps = False
Caps_As_Smallcaps = False
Italic_Shapes = False
Condensed = False
Extended_Ascenders = False
Extended_Capitals = False
Extended_Descenders = True
Contrast_Pixel = True
Alternative_g = False
LC_Figures = True

RS['openTypeFeatures'] = dict(zero=Slashed_Zero, smcp=Smallcaps, c2sc=Caps_As_Smallcaps, ss08=Italic_Shapes,
        ss07=Condensed, ss01=Extended_Ascenders, ss02=Extended_Capitals, ss03=Extended_Descenders,
        ss04=Contrast_Pixel, ss09=Alternative_g, onum=LC_Figures)

MD_PATH = 'BitcountReference.md'
EXPORT_PATH = '_export/BitcountReference.pdf'

MAIN_FLOW = 'main' # ELement id of the text box on pages the hold the main text flow.

# Tracking presets
H1_TRACK = H2_TRACK = 10 # 1/1000 of fontSize, multiplier factor.
H3_TRACK = 0 # Tracking as relative factor to font size.
P_TRACK = 0

familyName = 'Bitcount'
BitcountPaths = getFamilyFontPaths(familyName) 

BOOK = 'BitcountPropSingle-BookCircle'
MEDIUM = 'BitcountPropSingle-MediumCircle'
BOOK_ITALIC = 'BitcountPropSingle-BookCircleItalic'
BOLD = 'BitcountPropSingle-BoldCircleItalic'
BOLD = SEMIBOLD = 'BitcountPropSingle-BoldCircleItalic'

SEMIBOLD_CONDENSED = BOOK

RS['font'] = BOOK

# -----------------------------------------------------------------         
def makeDocument(rs):
    u"""Demo Bitcount Reference composer."""

    # Set some values of the default template (as already generated by the document).
    # Make squential unique names for the flow boxes inside the templates
    coverTitleId = 'coverTitleId' # To find the placement of the cover title.
    coverAuthorId = 'coverAuthorId' # Find the placement for the author name.
    tocId = 'toc' # Id of target textBox, containing the table of content.
    flowId1 = MAIN_FLOW+'1' 
    flowIds = [flowId1] # Names of boxes that contain footnote text in flow.
    footnotesId = 'footnotes' # Id of target textBox containing footnotes per page. 
    literatureIndexId = 'literatureIndex'
    imageIndexId = 'imageIndex'
    pageNumberId = 'pageNumberId'
    
    # Template for Cover page
    templateCover = Template(rs) # Create new template
    templateCover.rect(0, 0, rs['w'], rs['h'], fill=(1, 0, 0))
    # Placement of first <h1> in the Galley, holding the Thesis title.
    templateCover.cTextBox(FS, 1, 1, 6, 5, rs, coverTitleId, fill=BOX_COLOR)
    # Placement of first <h4> in the Galley, holding the author name(s)
    templateCover.cTextBox(FS, 1, 8, 6, 5, rs, coverAuthorId, fill=BOX_COLOR)
    
    # Template for Table of Content
    templateToc = Template(rs) # Create template for Table of Content
    # Show grid columns and paddngs if rootStyle.showGrid or rootStyle.showGridColumns are True
    templateToc.grid(rs) 
    # Show baseline grid if rs.showBaselineGrid is True
    templateToc.baselineGrid(rs)
    templateToc.cTextBox('\nTable of Content', 3, 0, 4, 1, rs, fill=BOX_COLOR, fontSize=32)
    templateToc.cTextBox('', 3, 1, 4, 8, rs, tocId, fill=BOX_COLOR)
    
    # Template for literature reference index.
    templateLiteratureIndex = Template(rs) # Create template for Table of Content
    # Show grid columns and paddings if rootStyle.showGrid or rootStyle.showGridColumns are True
    templateLiteratureIndex.grid(rs) 
    # Show baseline grid if rs.showBaselineGrid is True
    templateLiteratureIndex.baselineGrid(rs)
    templateLiteratureIndex.cTextBox('\nLiterature index', 3, 0, 4, 1, rs, fill=BOX_COLOR, fontSize=32)
    templateLiteratureIndex.cTextBox('', 3, 1, 4, 8, rs, literatureIndexId, fill=BOX_COLOR)
    
    # Template for image reference index.
    templateImageIndex = Template(rs) # Create template for Table of Content
    # Show grid columns and padding if rootStyle.showGrid or rootStyle.showGridColumns are True
    templateImageIndex.grid(rs) 
    # Show baseline grid if rs.showBaselineGrid is True
    templateImageIndex.baselineGrid(rs)
    templateImageIndex.cTextBox('\nImage index', 3, 0, 4, 1, rs, fill=BOX_COLOR, fontSize=32)
    templateImageIndex.cTextBox('', 3, 1, 4, 8, rs, imageIndexId, fill=BOX_COLOR)
    
    # Template 1
    template1 = Template(rs) # Create template of main size. Front page only.
    # Show grid columns and paddings if rootStyle.showGrid or rootStyle.showGridColumns are True
    template1.grid(rs) 
    # Show baseline grid if rs.showBaselineGrid is True
    template1.baselineGrid(rs)
    # Create empty image place holders. To be filled by running content on the page.
    # In this templates the images fill the left column if there is a reference on the page.
    template1.cContainer(0, 0, 3, 3, rs)  # Empty image element, cx, cy, cw, ch
    template1.cContainer(0, 3, 3, 3, rs)
    template1.cContainer(0, 6, 3, 3, rs)
    # Create linked text boxes. Note the "nextPage" to keep on the same page or to next.
    template1.cTextBox(FS, 3, 0, 4, 9, rs, flowId1, nextBox=flowId1, nextPage=1, fill=BOX_COLOR)
    template1.cTextBox('', 3, 9, 3, 2, rs, footnotesId, fill=BOX_COLOR)
    # Create page number box. Pattern pageNumberMarker is replaced by FormattedString of actual page number.
    # Mark the text box, so we can find it back later.
    template1.cTextBox(rs['pageIdMarker'], 6, 9, 1, 1, eId=pageNumberId, style=rs, 
        font=BOOK, fontSize=12, fill=BOX_COLOR, xAlign=RIGHT)
   
    # Create new document with (w,h) and fixed amount of pages.
    # Make number of pages with default document size.
    # Initially make all pages default with template2
    doc = Document(rs, pages=5, template=template1) 
 
    # Cache some values from the root style that we need multiple time to create the tag styles.
    fontSize = rs['fontSize']
    leading = rs['leading']
    rLeading = rs['rLeading']
    listIndent = rs['listIndent']
    language = rs['language']

    # Add styles for whole document and text flows.  
    # Note that some values are defined here for clarity, even if their default root values
    # are the same.             
    doc.newStyle(name='chapter', font=BOOK)    
    doc.newStyle(name='title', fontSize=3*fontSize, font=BOLD)
    doc.newStyle(name='subtitle', fontSize=2.6*fontSize, font=BOOK_ITALIC)
    doc.newStyle(name='author', fontSize=2*fontSize, font=BOOK, fill=(1, 0, 0))
    doc.newStyle(name='h1', fontSize=7*fontSize, font=SEMIBOLD_CONDENSED, fill=(1, 0, 0), 
        leading=7.2*fontSize, tracking=H1_TRACK, prefix='', postfix='\n')
    doc.newStyle(name='h2', fontSize=1.5*fontSize, font=SEMIBOLD_CONDENSED, 
        fill=0, leading=1.6*fontSize, rLeading=0, rTracking=H2_TRACK, 
        prefix='\n', postfix='\n',  paragraphTopSpacing=U)
    doc.newStyle(name='h3', fontSize=1.1*fontSize, font=MEDIUM, fill=0, 
        paragraphTopSpacing=2*U, paragraphBottomSpacing=U,
        leading=leading, rLeading=0, rNeedsBelow=2*rLeading, rTracking=H3_TRACK,
        prefix='\n', postfix='\n')
    doc.newStyle(name='h4', fontSize=1.1*fontSize, font=BOOK, fill=0, 
        leading=leading, rLeading=0, rNeedsBelow=2*rLeading, rTracking=H3_TRACK,
        paragraphTopSpacing=U, paragraphBottomSpacing=U, prefix='\n', postfix='\n')
    
    # Spaced paragraphs.
    doc.newStyle(name='p', fontSize=fontSize, font=BOOK, fill=0.1, 
        prefix='', postfix='\n', rTracking=P_TRACK, leading=14, 
        rLeading=0, xAlign=LEFT, hyphenation=True, indent=0,
        firstLineIndent=2*U, 
        firstParagraphIndent=0) # TODO: Make firstParagraphIndent to work.
    # Inline tags need to refined prefix and postfix as non-\n, otherwise they
    # will inherit these attributes from the parent <p>
    doc.newStyle(name='b', font=SEMIBOLD, prefix='', postfix='')
    doc.newStyle(name='em', font=BOOK_ITALIC, textFill=(1, 0, 0),
        prefix='', postfix='')
    doc.newStyle(name='hr', stroke=(1, 0, 0), strokeWidth=4)
    doc.newStyle(name='br', postfix='\n') # Simplest way to make <br/> show newline
    doc.newStyle(name='a', prefix='', postfix='')

    # Literature reference.
    doc.newStyle(name='literatureref', textFill=0.3, fontSize=fontSize-1)
    
    # Footnote reference index.
    doc.newStyle(name='sup', font=MEDIUM, baselineShift=2, prefix='', postfix=' ',
        fontSize=fontSize-2)
    doc.newStyle(name='li', fontSize=fontSize, font=BOOK, 
        rTracking=P_TRACK, leading=leading, hyphenation=True, 
        # Lists need to copy the listIndex over to the regalar style value.
        tabs=[(listIndent, LEFT)], indent=listIndent, 
        firstLineIndent=1, postfix='\n')
    doc.newStyle(name='ul', prefix='', postfix='')
    doc.newStyle(name='footnote', fill=0, fontSize=0.9*fontSize, font=BOOK,
        rTracking=P_TRACK,
        tabs=[(listIndent, LEFT)], indent=listIndent, 
        firstLineIndent=1, postfix='\n')
        
    # Image & captions
    doc.newStyle(name='img', stroke=0.3, fill=None, rTracking=P_TRACK,
        language=language, textFill=0.2, strokeWidth=1, 
        leading=leading*0.8, fontSize=0.8*fontSize, font=BOOK_ITALIC, 
        hyphenation=True, indent=0, firstLineIndent=0,
    # Use style['fill'] = transparant color as overlay on image.
    )
    
    # Generic document layout
    # Page 1    Cover
    # Page 2    Title
    # Page 3    Table of Content
    # Page 4+   Content  (footnotes are shown on the page of their reference)
    # Page -1   Alphabetical literature reference.

    # Change template of cover page.
    # Create filtered Galley for cover page.  
    # See https://docs.python.org/2/library/xml.etree.elementtree.html#xpath-support
    # for XPath filter syntax.  
    gTitle = Galley() 
    t = Typesetter(doc, gTitle)
    t.typesetFile(MD_PATH, rootStyle=dict(textFill=1, fontSize=80, font=MEDIUM,
        leading=84), 
        xPath='h1')

    gAuthor = Galley() 
    t = Typesetter(doc, gAuthor)
    t.typesetFile(MD_PATH, rootStyle=dict(textFill=1, fontSize=24, font=MEDIUM), 
        xPath='h4') # First one is the author

    coverPage = doc[1]
    coverPage.setTemplate(templateCover)
    c = Composer(doc)
    c.compose(gTitle, coverPage, coverTitleId)
    c.compose(gAuthor, coverPage, coverAuthorId)
    
    # Change template of Table of Content page
    tocPage = doc[2]
    tocPage.setTemplate(templateToc)

    mainPage = doc[3]

    # Create main Galley for this page, for pasting the sequence of elements.    
    g = Galley() 
    t = Typesetter(doc, g)
    t.typesetFile(MD_PATH)
                
    # Fill the main flow of text boxes with the ML-->XHTML formatted text. 
    c = Composer(doc)
    c.compose(g, mainPage, flowId1)
    
    # Now all text is composed on pages, scan for the pages that contain footnotes.
    # TODO: This will be implemented a function inside Composer in a later version.
    # Assume the tocBox (Table of Content) to be available on the first page.
    literatureRefs = {}
    tocBox, (_, _) = tocPage[tocId]
    for pageId, page in sorted(doc.pages.items()):
        if page in (tocPage, coverPage): # Skip these for toc collect and footnotes.
            continue
        # Get page box for footnotes
        fnBox, (_, _) = page[footnotesId]
        assert fnBox is not None # Otherwise there is a template error. Footnote box needs to exist.
        for flowId in flowIds:
            # BUG: Need to check if the marker was really found in the textbox area. 
            # If it is part of the overflow, then it should not be found here.
            flow, _ = page[flowId]
            for marker, arguments in findMarkers(flow.fs):
                if marker == 'footnote': 
                    footNoteIsInOverflow = False
                    # Process the foot note.
                    footnoteId = int(arguments) # Footnode ids are numbers. 
                    # @@@ Hack to check if the marker is in the overflow text. 
                    # In that case, ignore it.
                    for overFlowMarker, overFlowArguments in findMarkers(flow.getOverflow()):
                        # If this marker is a footnote and one that we are looking for,
                        # we can ignore it, because it is in the overflow part of the flow.fs
                        if overFlowMarker == 'footnote' and footnoteId == int(overFlowArguments):
                            footNoteIsInOverflow = True
                            break 
                    if not footNoteIsInOverflow:
                        # We found a footnote that is visible on this page and 
                        # not in one of the overflow texts.
                        # Process the footnote id and content, usng the “footnote“ content style.
                        # We are re-using the typesetter here. This may become a separate typesetter, if this code
                        # becomes a method of the composer.
                        # TODO: Make this into Galley, in case footnote <p> has child nodes. 
                        footnoteText = newFS('%d\t%s\n' % (footnoteId, doc.footnotes[footnoteId]['p'].text),
                            page, t.getCascadedStyle(doc.getStyle('footnote')))
                        # Add the footnote content to the box (it may not be the first to be added.
                        fnBox.append(footnoteText)
                elif marker in ('h1', 'h2', 'h3', 'h4'): # For now we want them all in the TOC
                    #doc.addToc(marker)
                    pass
                elif marker == 'literature':
                    # The "arguments" contains the refId, so we can find it in the collected literature references
                    # and then add this page number.
                    # @@@ TODO: check if reference marker is in overflow. Then ignore processing it.
                    doc.literatureRefs[int(arguments)]['pageIds'].append(pageId)
                    
    # Build the alphabetical literature reference page.
    # Scan the created pages for literature references and build an index on a new page.
    literatureIndexPage = doc.newPage(template=templateLiteratureIndex)
    # Make an alfabetic sorted list of name-->(reference, (pageNumber, ...))
    references = {}  
    for refIndex, item in doc.literatureRefs.items():
        references[item['nodeId']] = item
    literatureRefBox = literatureIndexPage.getElement(literatureIndexId)    
    for refId, item in sorted(references.items()):
        # Now we have a sorted list of reference items, we need to make it into a galley.
        # Several ways of doing it: Create MarkDown, HTML/XML or directly writing FormattedText.
        pageNumbers = []
        for pageNumber in item['pageIds']:
            pageNumbers.append(`pageNumber`)
        literatureRefBox.append(u'%s – %s\n' % (refId, ', '.join(pageNumbers)))
        
        print refId, item['nodeId'], item['node'], item['p'], item['pageIds']

    # Build the alphabetical image reference page.
    # Scan the created pages for image references and build an index on a new page.
    imageIndexPage = doc.newPage(template=templateImageIndex)
    # Make an alfabetic sorted list of name-->(reference, (pageNumber, ...))
    references = {}  
    for refIndex, item in doc.imageRefs.items():
        references[item['nodeId']] = item
    for imageRefId, item in sorted(references.items()):
        print imageRefId, item['nodeId'], item['node'], item['p'], item['pageIds']

    # Set all pagenumbers and other page-based info
    for pageId, page in sorted(doc.pages.items()):
        for e in page.elements:
            if e.eId == pageNumberId:
                e.setText('%s' % pageId)
                break
    
    return doc

if __name__ == '__main__':
    
    print BitcountPaths.keys()

    d = makeDocument(RS)
    d.export(EXPORT_PATH) 

