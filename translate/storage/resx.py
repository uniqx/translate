# -*- coding: utf-8 -*-
#
# Copyright 2015 Zuza Software Foundation
# Copyright 2015 Sarah Hale
#
# This file is part of translate.
#
# translate is free software; you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation; either version 2 of the License, or
# (at your option) any later version.
#
# translate is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program; if not, see <http://www.gnu.org/licenses/>.

"""Module for handling .Net Resource (.resx) files."""

from lxml import etree

from translate.lang import data
from translate.misc.deprecation import deprecated
from translate.misc.xml_helpers import setXMLspace, reindent
from translate.storage import lisa
from translate.storage.placeables import general


class RESXUnit(lisa.LISAunit):
    """A single term in the RESX file."""

    rootNode = "data"
    languageNode = "value"
    textNode = ""
    namespace = ""
    rich_parsers = general.parsers

    def createlanguageNode(self, lang, text, purpose):
        """Returns an xml Element setup with given parameters."""

        langset = etree.Element(self.namespaced(self.languageNode))

        langset.text = text
        return langset

    def _gettargetnode(self):
        return self.xmlelement.find(self.namespaced(self.languageNode))

    @lisa.LISAunit.source.getter
    def source(self):
        return self.target

    # Deprecated on 2.3.1
    @deprecated("Use `source` property instead")
    def getsource(self):
        return self.source

    @property
    def target(self):
        targetnode = self._gettargetnode()
        if targetnode is None:
            etree.SubElement(self.xmlelement, self.namespaced("value"))
            return None
        return data.forceunicode(targetnode.text) or u""

    @target.setter
    def target(self, target):
        # Firstly deal with reinitialising to None or setting to identical
        # string.
        self._rich_target = None
        if self.target == target:
            return
        targetnode = self._gettargetnode()
        targetnode.clear()
        targetnode.text = data.forceunicode(target) or u""

    # Deprecated on 2.3.1
    @deprecated("Use `target` property instead")
    def gettarget(self):
        return self.target

    # Deprecated on 2.3.1
    @deprecated("Use `target` property instead")
    def settarget(self, target):
        self.target = target

    def addnote(self, text, origin=None, position="append"):
        """Add a note specifically in the appropriate "comment" tag"""
        if isinstance(text, bytes):
            text = text.decode("utf-8")
        current_notes = self.getnotes(origin)
        self.removenotes(origin)
        note = etree.SubElement(self.xmlelement, self.namespaced("comment"))
        text_stripped = text.strip()
        if position == "append":
            if current_notes.strip() in text_stripped:
                # Don't add duplicate comments
                note.text = text_stripped
            else:
                note.text = "\n".join(filter(None, [current_notes, text_stripped]))
        else:
            note.text = text_stripped
        if note.text:
            # Correct the indent of <comment> by updating the tail of
            # the preceding <value> element
            targetnode = self._gettargetnode()

    def getnotes(self, origin=None):
        comments = []
        notenode = self.xmlelement.find(self.namespaced("comment"))
        if notenode is not None and notenode.text is not None:
            comments.append(notenode.text)
        return '\n'.join(comments)

    def removenotes(self, origin=None):
        note = self.xmlelement.find(self.namespaced("comment"))
        if note is not None:
            self.xmlelement.remove(note)

    def setid(self, value):
        if id is None:
            return False
        else:
            self.xmlelement.set("name", value)

    def getid(self):
        return self.xmlelement.get("name")

    def getlocations(self):
        return [self.getid()]

    def merge(self, otherunit, overwrite=False, comments=True, authoritative=False):
        super().merge(otherunit, overwrite, comments)
        if otherunit.isfuzzy():
            self.markfuzzy()


class RESXFile(lisa.LISAfile):
    """Class representing a RESX file store."""

    UnitClass = RESXUnit
    Name = ".NET RESX File"
    Mimetypes = ["text/microsoft-resx"]
    Extensions = ["resx"]
    rootNode = "root"
    # We will switch out .body to fit with the context we are working on
    bodyNode = ""
    XMLskeleton = '''<?xml version="1.0" encoding="utf-8"?>
<root>
  <xsd:schema id="root" xmlns="" xmlns:xsd="http://www.w3.org/2001/XMLSchema" xmlns:msdata="urn:schemas-microsoft-com:xml-msdata">
    <xsd:import namespace="http://www.w3.org/XML/1998/namespace" />
    <xsd:element name="root" msdata:IsDataSet="true">
      <xsd:complexType>
        <xsd:choice maxOccurs="unbounded">
          <xsd:element name="metadata">
            <xsd:complexType>
              <xsd:sequence>
                <xsd:element name="value" type="xsd:string" minOccurs="0" />
              </xsd:sequence>
              <xsd:attribute name="name" use="required" type="xsd:string" />
              <xsd:attribute name="type" type="xsd:string" />
              <xsd:attribute name="mimetype" type="xsd:string" />
              <xsd:attribute ref="xml:space" />
            </xsd:complexType>
          </xsd:element>
          <xsd:element name="assembly">
            <xsd:complexType>
              <xsd:attribute name="alias" type="xsd:string" />
              <xsd:attribute name="name" type="xsd:string" />
            </xsd:complexType>
          </xsd:element>
          <xsd:element name="data">
            <xsd:complexType>
              <xsd:sequence>
                <xsd:element name="value" type="xsd:string" minOccurs="0" msdata:Ordinal="1" />
                <xsd:element name="comment" type="xsd:string" minOccurs="0" msdata:Ordinal="2" />
              </xsd:sequence>
              <xsd:attribute name="name" type="xsd:string" use="required" msdata:Ordinal="1" />
              <xsd:attribute name="type" type="xsd:string" msdata:Ordinal="3" />
              <xsd:attribute name="mimetype" type="xsd:string" msdata:Ordinal="4" />
              <xsd:attribute ref="xml:space" />
            </xsd:complexType>
          </xsd:element>
          <xsd:element name="resheader">
            <xsd:complexType>
              <xsd:sequence>
                <xsd:element name="value" type="xsd:string" minOccurs="0" msdata:Ordinal="1" />
              </xsd:sequence>
              <xsd:attribute name="name" type="xsd:string" use="required" />
            </xsd:complexType>
          </xsd:element>
        </xsd:choice>
      </xsd:complexType>
    </xsd:element>
  </xsd:schema>
  <resheader name="resmimetype">
    <value>text/microsoft-resx</value>
  </resheader>
  <resheader name="version">
    <value>2.0</value>
  </resheader>
  <resheader name="reader">
    <value>System.Resources.ResXResourceReader, System.Windows.Forms, Version=4.0.0.0, Culture=neutral, PublicKeyToken=b77a5c561934e089</value>
  </resheader>
  <resheader name="writer">
    <value>System.Resources.ResXResourceWriter, System.Windows.Forms, Version=4.0.0.0, Culture=neutral, PublicKeyToken=b77a5c561934e089</value>
  </resheader>
</root>
'''
    namespace = ''

    def __init__(self, *args, **kwargs):
        lisa.LISAfile.__init__(self, *args, **kwargs)
        self._messagenum = 0

    def initbody(self):
        """Initialises self.body."""
        self.namespace = self.document.getroot().nsmap.get(None, None)
        self.header = self.document.getroot()
        self.body = self.document.getroot()

    def addunit(self, unit, new=True):
        """Adds the given unit to the body node."""
        super().addunit(unit, new)
        setXMLspace(unit.xmlelement, "preserve")
        if unit.getid() is None:
            self._messagenum += 1
            unit.setid(u"%s" % unit.source.strip(' '))
        # adjust the current and previous elements for new ones;
        # otherwise they will not be indented correctly.
        if new:
            previous_node = unit.xmlelement.getprevious()
            if previous_node is None:
                # this is the first element; adjust root.
                # should not happen in a ResX file prepared by Visual Studio
                # since it includes an inline XSD plus resheader at all times.
                self.body.text = u"\n  "
            # adjust the indent of the following <value> element
            unit.xmlelement.text = u"\n    "
        return unit

    def serialize(self, out=None):
        root = self.document.getroot()
        reindent(root, indent="  ", max_level=4)
        # Use same header as Visual Studio
        out.write(b'<?xml version="1.0" encoding="utf-8"?>\n')
        content = etree.tostring(root, pretty_print=False, xml_declaration=False,
                                 encoding='utf-8')
        # Additional space on empty tags same as Visual Studio
        out.write(content.replace(b'/>', b' />'))
