# -*- coding: UTF-8 -*-

import copy
import codecs
import xml.etree.ElementTree as ET

import pagebot
reload(pagebot)
from pagebot import getFormattedString, getMarker

import markdown
from markdown.extensions.nl2br import Nl2BrExtension
from markdown.extensions.footnotes import FootnoteExtension

import literature
reload(literature)
from literature import LiteratureExtension

import elements
reload(elements)
from elements import Galley, Image

class Typesetter(object):
    
    def __init__(self, document, galley):
        self.document = document
        self.galley = galley
        self.gState = [document.getRootStyle()] # Stack of graphic state as cascading styles.
     
    def getTextBox(self, style):
        return self.galley.getTextBox(style)
                        
    def node_h1(self, node, style):
        u"""Collect the page-node-pageNumber connection."""
        # Add line break to whatever style/content there was before. 
        # Add invisible h2-marker in the string, to be retrieved by the composer.
        tb = self.getTextBox(style)
        tb.append('\n')# + getMarker(node.tag) 
        self.typesetNode(node, style)

    def node_h2(self, node, style):
        u"""Collect the page-node-pageNumber connection."""
        # Add line break to whatever style/content there was before. 
        # Add invisible h2-marker in the string, to be retrieved by the composer.
        tb = self.getTextBox(style)
        tb.append('\n')# + getMarker(node.tag) 
        self.typesetNode(node, style)
        

    def node_h3(self, node, style):
        u"""Collect the page-node-pageNumber connection."""
        # Add line break to whatever style/content there was before. 
        # Add invisible h3-marker in the string, to be retrieved by the composer.
        tb = self.getTextBox(style)
        tb.append('\n')# + getMarker(node.tag) 
        self.typesetNode(node, style)
        
    def node_h4(self, node, style):
        u"""Collect the page-node-pageNumber connection."""
        # Add line break to whatever style/content there was before. 
        # Add invisible h3-marker in the string, to be retrieved by the composer.
        tb = self.getTextBox(style)
        tb.append('\n')# + getMarker(node.tag) 
        self.typesetNode(node, style)

    def node_br(self, node, style):
        u"""Add line break to the formatted string."""
        tb = self.getTextBox(style)
        tb.append('\n')# + getMarker(node.tag) 

    def node_a(self, node, style):
        u"""Ignore links, but process the block"""
        return self.typesetNode(node, style)
        
    def node_sup(self, node, style):
        u"""Collect footnote refereneces on their page number. 
        And typeset the superior footnote index reference."""
        nodeId = node.attrib.get('id')
        if nodeId.startswith('fnref'): # This is a footnote reference.
            footnotes = self.document.footnotes
            footnotes[len(footnotes)+1] = [node, style]      
        return self.typesetNode(node, style)
 
    def node_literatureref(self, node, style):
        u"""Collect literature references."""
        return self.typesetNode(node, style)
         
    def node_div(self, node, style):
        u"""MarkDown generates <div class="footnote">...</div> and <div class="literature">...</div>
        as output, but we will handle them separetely by looking them up in the XML-tree.
        So we'll skip them in the regular flow process."""
        # TODO: Check specific on the class name. Process otherwise.
        tb = self.getTextBox(style)
        if node.attrib.get('class') == 'literature':
            return
        elif node.attrib.get('class') == 'footnote':
            # Find the content of the footnotes.
            #node.findall('./ol/li/p')
            #for index, p in enumerate(node.findall('./ol/li/p')):
            #    self.document.footnotes[index+1].append(p)
            return
        return self.typesetNode(node, style)
                    
    def node_li(self, node, style):
        # Bullet/Numbered list item
        tb = self.getTextBox(style)
        tb.append(getFormattedString(u'\n•\t', style))
        self.typesetNode(node, style)
                  
    def node_img(self, node, style):
        u"""Process the image. Find empty space on the page to place it,
        closest related to the w/h ration of the image."""
        src = node.attrib.get('src')
        g = Galley()
        imageElement = Image(src) # Set path, image w/h and image scale.
        imgStyle = self.pushStyle(self.document.getStyle(node.tag))
        imageElement.fill = imgStyle.fill
        imageElement.stroke = imgStyle.stroke
        imageElement.strokeWidth = imgStyle.strokeWidth
        imageElement.hyphenation = imgStyle.hyphenation
        g.append(imageElement)
        caption = node.attrib.get('title')
        if caption is not None:
            captionStyle = self.pushStyle(self.document.getStyle('caption'))
            tb = g.getTextBox(captionStyle)
            caption = node.attrib.get('title')
            # Add invisible marker to the FormattedString, to indicate where the image
            # reference went in a textBox after slicing the string.
            print tb
            tb.append(getFormattedString(caption+'\n', captionStyle))
            tb.append(getMarker(node.tag, src))
            self.popStyle() # captionStyle
        self.galley.append(g)
                                    
    def pushStyle(self, style):
        u"""As we want cascading font and fontSize in the page elements, we need to keep track
        of the stacking of XML-hiearchy of the tag styles.
        The styles can omit the font or fontSize, and still we need to be able to set the element
        attributes. Copy the current style and add overwrite the attributes in style. This way
        the current style always contains all attributes of the root style."""
        nextStyle = copy.copy(self.gState[-1])
        if style is not None:
            for name, value in style.__dict__.items():
                if name.startswith('_'):
                    continue
                setattr(nextStyle, name, value)
        self.gState.append(nextStyle)
        return nextStyle
        
    def popStyle(self):
        self.gState.pop()
        return self.gState[-1]

    def typesetNode(self, node, style):

        style = self.pushStyle(style)        
        tb = self.getTextBox(style)
        
        nodeText = node.text
        if nodeText is not None:
            if style.stripWhiteSpace:
                nodeText = nodeText.strip() #+ style.stripWhiteSpace
            if nodeText: # Anythong left to add?
                #print node.tag, `node.text`
                tb.append(getFormattedString(nodeText, style))
            
        # Type set all child node in the current node, by recursive call.
        for child in node:
            hook = 'node_'+child.tag
            # Method will handle the styled body of the element, but not the tail.
            if hasattr(self, hook): 
                getattr(self, hook)(child, style)
                childTail = child.tail
                if childTail is not None:
                    if style.stripWhiteSpace:
                        childTail = childTail.strip() #+ style.stripWhiteSpace
                    if childTail: # Anything left to add?
                        #print child.tag, `child.tail`
                        tb.append(getFormattedString(childTail, style))
                
            else: # If no method hook defined, then just solve recursively.
                self.typesetNode(child, style)

        # XML-nodes are organized as: node - node.text - node.children - node.tail
        # If there is no text or if the node does not have tail text, these are None.
        # Restore the graphic state at the end of the element content processing to the 
        # style of the parent in order to process the tail text.
        style = self.popStyle()
        nodeTail = node.tail
        if nodeTail is not None:
            if style.stripWhiteSpace:
                nodeTail = nodeTail.strip() + style.stripWhiteSpace
            if nodeTail: # Anython left to add?
                #print node.tag, `node.tail`
                tb.append(getFormattedString(nodeTail, style))
                         
    def typesetFile(self, fileName):
        u"""Read the XML document and parse it into a tree of document-chapter nodes. Make the typesetter
        start at page pageNumber and find the name of the flow in the page template."""

        fileExtension = fileName.split('.')[-1]
        if fileExtension == 'md':
            # If we have MarkDown content, conver to HTNK/XML
            f = codecs.open(fileName, mode="r", encoding="utf-8")
            mdText = f.read()
            f.close()
            mdExtensions = [FootnoteExtension(), LiteratureExtension(), Nl2BrExtension()]
            xml = '<document>%s</document>' % markdown.markdown(mdText, extensions=mdExtensions)
            xmlName = fileName + '.xml'
            f = codecs.open(xmlName, mode="w", encoding="utf-8")
            f.write(xml)
            f.close()
            fileName = xmlName

        tree = ET.parse(fileName)
        root = tree.getroot() # Get the root element of the tree.
        # Get the root style that all other styles will be merged with.
        rootStyle = self.document.getRootStyle()
        # Collect all flowing text in one formatted string, while simulating the page/flow, because
        # we need to keep track on which page/flow nodes results get positioned (e.g. for toc-head
        # reference, image index and footnote placement.   
        self.typesetNode(root, rootStyle)
        
    def typesetFootnotes(self):
        footnotes = self.document.footnotes
        for index, (page, e, p) in footnotes.items():
            style = page.getStyle('footnote')
            fs = getFormattedString('%d ' % index, style)
            tb = page.findElement('footnote')
            if tb is not None:
                self.typesetNode(p, page, style)
