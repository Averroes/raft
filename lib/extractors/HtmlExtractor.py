#
# Author: Gregory Fleischer (gfleischer@gmail.com)
#
# Copyright (c) 2011 RAFT Team
#
# This file is part of RAFT.
#
# RAFT is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
# 
# RAFT is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with RAFT.  If not, see <http://www.gnu.org/licenses/>.
#

from BaseExtractor import BaseExtractor
from JSLiteParser import JSLiteParser
from lxml import etree
from cStringIO import StringIO
from urllib2 import urlparse
import urllib2
import hashlib
import re

class HtmlInput():
    def __init__(self):
        self.name = ''
        self.Id = ''
        self.value = ''
        self.src = ''
        self.Type = ''
        self.Class = ''
        self.required = ''
        self.maxlength = ''
        self.accept = ''
        self.label = ''

    def __eq__(self, other):
        return self.make_input_string() ==  other.make_input_string()

    def __str__(self):
        return self.make_input_string()

    def make_input_string(self):
        # TODO: finish
        s = '<input name="%s" id="%s" type="%s" value="%s">' % (self.name, self.Id, self.Type, self.value)
        if self.label:
            s = '<label>%s%s</label>\n' % (self.label, s)
        else:
            s += '\n'
        return s

class HtmlForm():
    def __init__(self, baseurl):
        self.inputs = []
        self.Id = ''
        self.Class = ''
        self.action = baseurl
        self.method = 'GET'
        self.enctype = 'application/x-www-form-urlencoded'
        self.target = ''
        self.onsubmit = ''
        self.onreset = ''

    def add_input(self, input):
        if not input in self.inputs:
            self.inputs.append(input)

    def __eq__(self, other):
        return self.make_form_string_start() == other.make_form_string_start()

    def make_form_string_start(self):
        return '<form id="%s" class="%s" action="%s" method="%s" enctype="%s" onsubmit="%s" onreset="%s" target="%s">\n' % (
            self.Id, self.Class, self.action, self.method, self.enctype, self.onsubmit, self.onreset, self.target)
    
    def __str__(self):
        s = StringIO()
        s.write(self.make_form_string_start())
        for input in self.inputs:
            s.write(str(input))
        s.write('</form>\n')
        return s.getvalue()
        
class HtmlParseResults():

    def __init__(self, baseurl, encoding):
        self.baseurl = baseurl
        self.encoding = encoding
        self.__re_url_encoded = re.compile(r'%[a-fA-F0-9]{2}')
        self.comments = []
        self.relative_links = []
        self.links = []
        self.anchors = []
        # TODO: really any need to distinguish between inline in this way?
        self.inline_scripts = []
        self.all_scripts = []
        self.scripts = []
        self.script_links = []
        self.inline_styles = []
        self.styles = []
        self.labels_by_id = {}
        self.labels_by_name = {}
        self.forms = []
        self.other_inputs = []
        self.baseurl_set = False
        self.contextual_fingerprint = ''
        self.structural_fingerprint = ''

    def resolve_url(self, uri):
        splitted = urlparse.urlsplit(uri)
        if self.__re_url_encoded.search(splitted.path):
            # url-encoded
            uri = urllib2.unquote(uri)
            splitted = urlparse.urlsplit(uri)
        if not splitted.scheme and splitted.path and not splitted.path.startswith('/'):
            if splitted.path not in self.relative_links:
                self.relative_links.append(splitted.path)
        # TODO: urljoin doesn't understand example.com/foo relative links
        resolved = urlparse.urljoin(self.baseurl, uri)
        return resolved

    def add_relative_uri(self, uri):
        if not uri in self.relative_links:
            self.relative_links.append(uri)

    def add_comment(self, text):
        if text not in self.comments:
            self.comments.append(text)

    def add_uri(self, uri):
        resolved = self.resolve_url(uri)
        if not resolved in self.links:
            self.links.append(resolved)

    def add_anchor_uri(self, uri, anchor_text, Id, classname, title):
        resolved = self.resolve_url(uri)
        if not resolved in self.links:
            self.links.append(resolved)

        anchor = (resolved, anchor_text, Id, classname, title)
        if not anchor in self.anchors:
            self.anchors.append(anchor)
        
    def add_meta_redirect_uri(self, uri):
        resolved = self.resolve_url(uri)
        if not resolved in self.links:
            self.links.append(resolved)

    def add_script_uri(self, uri):
        resolved = self.resolve_url(uri)
        self.all_scripts.append(resolved)
        if not resolved in self.script_links:
            self.script_links.append(resolved)
        if not resolved in self.links:
            self.links.append(resolved)

    def add_inline_script(self, script):
        self.all_scripts.append(script)
        if not script in self.inline_scripts:
            self.inline_scripts.append(script)
            return True
        else:
            return False

    def add_script_block(self, script):
        if not script in self.scripts:
            self.all_scripts.append(script)
            self.scripts.append(script)
            return True
        else:
            return False

    def add_inline_style(self, style):
        if not style in self.inline_styles:
            self.inline_styles.append(style)

    def add_style_block(self, style):
        self.styles.append(style)

    def add_form(self, form):
        try:
            index = self.forms.index(form)
            return self.forms[index]
        except ValueError:
            self.forms.append(form)
            return form

    def add_other_input(self, input):
        self.other_inputs.append(input)

    def add_label_info(self, forId, forName, text):
        if forId:
            self.labels_by_id[forId] = text
        if forName:
            self.labels_by_name[forName] = text

    def attach_input_label(self, input):
        name = input.name
        Id = input.Id
        if name and self.labels_by_name.has_key(name):
            input.label = self.labels_by_name[name]
        if Id and self.labels_by_id.has_key(Id):
            input.label = self.labels_by_id[Id]

    def set_baseurl(self, baseurl):
        if not self.baseurl_set:
            self.baseurl = baseurl
            self.baseurl_set = True
        else:
            # TODO: warn
            pass

    def set_contextual_fingerprint(self, data):
        sha256 = hashlib.sha256()
        sha256.update(data)
        self.contextual_fingerprint = sha256.hexdigest()

    def set_structural_fingerprint(self, data):
        sha256 = hashlib.sha256()
        sha256.update(data)
        self.structural_fingerprint = sha256.hexdigest()

class HtmlExtractor(BaseExtractor):

    T_SCRIPT = 1
    T_URI = 2
    T_URI_LIST = 3
    T_BASE_URI = 4
    T_STYLE = 5
    T_META_CONTENT = 6
    T_PARAM_CONTENT = 7
    T_SCRIPT_URI = 8
    T_ANCHOR_URI = 9

    DEFAULT_TAG_ATTRS = {
        # TODO: id, class, text
        'style' : T_STYLE,
        'datasrc' : T_URI,
        'onclick' : T_SCRIPT, 
        'ondblclick' : T_SCRIPT, 
        'onmousedown' : T_SCRIPT, 
        'onmouseup' : T_SCRIPT, 
        'onmouseover' : T_SCRIPT, 
        'onmousemove' : T_SCRIPT, 
        'onmouseout' : T_SCRIPT, 
        'onkeypress' : T_SCRIPT, 
        'onkeydown' : T_SCRIPT, 
        'onkeyup' : T_SCRIPT, 
        }

    # Add HTML5
    HTML_TAG_ATTRS = {
        'body' : {
            'onload' : T_SCRIPT,
            'onunload' : T_SCRIPT,
            'background' : T_URI,
            },
        'a' : {
            'href' : T_ANCHOR_URI,
            'onfocus' : T_SCRIPT,
            'onblur' : T_SCRIPT,
            },
        'applet' : {
            'codebase' : T_URI,
            'code' : T_URI,
            'archive' : T_URI,
            },
        'area' : {
            'href' : T_URI,
            'onfocus' : T_SCRIPT,
            'onblur' : T_SCRIPT,
            }, 
        'link' : {
            'href' : T_URI,
            },
        'img' : {
            'src' : T_ANCHOR_URI,
            'usemap' : T_URI,
            'onerror' : T_SCRIPT,
            },
        'object': { 
            'classid' : T_URI,
            'codebase' : T_URI,
            'data' : T_URI,
            'archive' : T_URI_LIST,
            'usemap' : T_URI,
            },
        'q' : {
            'cite' : T_URI,
            },
        'ins' : {
            'cite' : T_URI,
            },
        'del' : {
            'cite' : T_URI,
            },
        'form' : {
            'action' : T_URI,
            'onsubmit' : T_SCRIPT,
            'onreset' : T_SCRIPT,
            },
        'label' : {
            'onfocus' : T_SCRIPT,
            'onblur' : T_SCRIPT,
            },
        'input' : {
            'src' : T_URI,
            'usemap' : T_URI,
            'onfocus' : T_SCRIPT,
            'onblur' : T_SCRIPT,
            'onselect' : T_SCRIPT,
            'onchange' : T_SCRIPT,
            'onerror' : T_SCRIPT,
            },
        'select' : {
            'onfocus' : T_SCRIPT,
            'onblur' : T_SCRIPT,
            'onchange' : T_SCRIPT,
            },
        'option' : {
            },
        'textarea' : {
            'onfocus' : T_SCRIPT,
            'onblur' : T_SCRIPT,
            'onselect' : T_SCRIPT,
            'onchange' : T_SCRIPT,
            },
        'button' : {
            'onfocus' : T_SCRIPT,
            'onblur' : T_SCRIPT,
            },
        'head' : {
            'profile' : T_URI,
            },
        'base' : {
            'href' : T_BASE_URI,
            },
        'meta' : {
            'http-equiv' : T_META_CONTENT,
            },
        'script' : {
            'src' : T_SCRIPT_URI,
            'for' : T_URI,
            'onload' : T_SCRIPT,
            'onerror' : T_SCRIPT,
            },
        'frameset' : {
            'onload' : T_SCRIPT,
            'onunload' : T_SCRIPT,
            },
        'frame' : {
            'src' : T_URI,
            'longdesc' : T_URI,
            'onload' : T_SCRIPT,
            'onerror' : T_SCRIPT,
            },
        'iframe' : {
            'src' : T_URI,
            'onload' : T_SCRIPT,
            'onerror' : T_SCRIPT,
            },
        'param' : {
            'name' : T_PARAM_CONTENT,
            }
        }

    def __init__(self):
        BaseExtractor.__init__(self)

        self.re_meta_refresh = re.compile(r'(?:\d|\s|[,;])*(?:url\s*=\s*)?(\S+)', re.I)
        self.re_meta_content_type = re.compile(r'([^/;]+/[^/;]+)\s*(?:;\s*charset\s*=\s*(\S+)\s*)?', re.I)
        self.re_quoted_http = re.compile(r'(\"\s*%s[^\"]+?\s*\"|\'\s*%s[^\']+?\s*\'|\`\s*%s[^\`]+?\s*\`)' % (self.host_spec, self.host_spec, self.host_spec), re.I)
        self.re_quoted_relative = re.compile(r'(\"\s*%s[^\"]+?\s*\"|\'\s*%s[^\']+?\s*\'|\`\s*%s[^\`]+?\s*\`)' % (self.relative_spec, self.relative_spec, self.relative_spec), re.I)
        self.re_naked_uri = re.compile(r'\b((?:%s/%s)|%s[^/])\b' % (self.host_spec, self.path_spec, self.host_spec), re.I)

        # merge default attribute types
        for tag in self.HTML_TAG_ATTRS:
            for attr_name in self.DEFAULT_TAG_ATTRS.keys():
                if not self.HTML_TAG_ATTRS[tag].has_key(attr_name):
                    self.HTML_TAG_ATTRS[tag][attr_name] = self.DEFAULT_TAG_ATTRS[attr_name]
        
    def process_tag(self, results, jsParser, elem):
        tag = elem.tag.lower()
        if 'script' == tag:
            self.process_script_block(results, jsParser, elem)
        elif 'style' == tag:
            self.process_style_block(results, elem)
        elif 'label' == tag:
            self.process_label(results, elem)
        elif 'form' == tag:
            self.process_form(results, elem)
        elif 'input' == tag:
            self.process_input(results, elem)
        else:
            # TODO: forms, a, etc
            text = self.get_text_string(results, elem.text)
            if text:
                self.match_uri_contents(results, text)

    def get_text_string(self, results, text):
        if text is None:
            return ''
        try:
            ret = None
            try:
                ret = text.decode(results.encoding)
            except UnicodeDecodeError:
                pass
            except UnicodeEncodeError:
                pass
            except LookupError:
                pass
            if ret is None:
                ret = text.decode('utf-8')
        except UnicodeDecodeError:
            ret = repr(text)[1:-1]
        except UnicodeEncodeError:
            ret = repr(text)[1:-1]

        return ret

    def process_script_block(self, results, jsParser, elem):
        script = self.get_text_string(results, elem.text)
        if script:
            if results.add_script_block(script):
                jsParser.parse(script)

    def process_style_block(self, results, elem):
        style = self.get_text_string(results, elem.text)
        if style:
            results.add_style_block(style)

    def process_input(self, results, elem):
        # find inputs not associated with forms
        found = False
        parent = elem.getparent()
        while parent is not None:
            if parent.tag.lower() == 'form':
                found = True
                break
            parent = parent.getparent()

        if not found:
            results.add_other_input(self.process_input_element(results, elem))

    def process_form(self, results, elem):
        form = HtmlForm(results.baseurl)
        for name, value in elem.attrib.iteritems():
            if value:
                lname = name.lower()
                if 'method' == lname:
                    form.method = value
                elif 'action' == lname:
                    form.action = results.resolve_url(value)
                elif 'enctype' == lname:
                    form.enctype = value
                elif 'target' == lname:
                    form.target = value
                elif 'id' == lname:
                    form.Id = value
                elif 'class' == lname:
                    form.Class = value
        form = results.add_form(form)

        input_elems = elem.findall('.//input')
        for input_elem in input_elems:
            form.add_input(self.process_input_element(results, input_elem))

    def process_input_element(self, results, elem):
        input = HtmlInput()
        for name, value in elem.attrib.iteritems():
            if value:
                lname = name.lower()
                if 'name' == lname:
                    input.name = value
                elif 'id' == lname:
                    input.Id = value
                elif 'src' == lname:
                    input.src = value
                elif 'value' == lname:
                    input.value = value
                elif 'type' == lname:
                    input.Type = value
                elif 'class' == lname:
                    input.Class = value
                elif 'required' == lname:
                    input.required = value
                elif 'maxlength' == lname:
                    input.maxlength = value
                elif 'accept' == lname:
                    input.accept = value

        results.attach_input_label(input)
        return input
        
    def process_label(self, results, elem):
        forId, forName = '', ''
        text = self.get_text_string(results, elem.text)
        for name, value in elem.attrib.iteritems():
            if value:
                lname = name.lower()
                if 'for' == lname:
                    forId = value
        if '' == forId:
            input_elem = elem.find('.//input')
            if input_elem is not None:
                if not text:
                    text == self.get_text_string(results, input_elem.text)
                for name, value in input_elem.attrib.iteritems():
                    if value:
                        lname = name.lower()
                        if 'id' == lname:
                            forId = value
                        elif 'name' == lname:
                            forName = value

                # TODO: doesn't properly handle <label><input>xxxx</label>

        results.add_label_info(forId, forName, text)
        
    def process_inline_script(self, results, jsParser, script):
        if results.add_inline_script(script):
            # TODO: fixme better ....
            jsParser.parse('(function (){'+script+'})')

    def process_script_uri(self, results, uri):
        results.add_script_uri(uri)

    def process_uri(self, results, uri):
        results.add_uri(uri)

    def process_uri_list(self, results, uri_list):
        for uri in uri_list.split():
            self.process_uri(uri)

    def process_inline_style(self, results, style):
        results.add_inline_style(style)

    def process_attributes(self, results, jsParser, elem):
        tag = elem.tag.lower()
        if self.HTML_TAG_ATTRS.has_key(tag):
            tag_attrs = self.HTML_TAG_ATTRS[tag]
        else:
            tag_attrs = self.DEFAULT_TAG_ATTRS
        for name, value in elem.attrib.iteritems():
            if value:
                lname = name.lower()
                if tag_attrs.has_key(lname):
                    attr_type = tag_attrs[lname]
                    if self.T_SCRIPT == attr_type:
                        self.process_inline_script(results, jsParser, value)
                    elif self.T_URI == attr_type:
                        self.process_uri(results, value)
                    elif self.T_ANCHOR_URI == attr_type:
                        self.process_anchor_uri(results, elem, value)
                    elif self.T_SCRIPT_URI == attr_type:
                        self.process_script_uri(results, value)
                    elif self.T_BASE_URI == attr_type:
                        results.set_baseurl(str(value).strip())
                    elif self.T_URI_LIST == attr_type:
                        self.process_uri_list(results, value)
                    elif self.T_STYLE == attr_type:
                        self.process_inline_style(results, value)
                    elif self.T_META_CONTENT == attr_type:
                        self.process_meta_content(results, elem)
                    elif self.T_PARAM_CONTENT == attr_type:
                        self.process_param_content(results, elem)
                    else:
                        raise Exception('unexpected type: %s' % attr_type)

    def normalize_attributes(self, attrib):
        normalized = {}
        for name, value in elem.attrib.iteritems():
            lname = name.lower()
            if lname and value:
                # TODO: should use a multi-map?
                normalized[lname] = value

        return normalized

    def process_comment(self, results, elem):
        comment = self.get_text_string(results, elem.text)
        if comment:
            results.add_comment(comment)
            self.match_uri_contents(results, comment)

    def process_anchor_uri(self, results, elem, uri):
        anchor_text = self.get_text_string(results, elem.text)
        Id, classname, title = '', '', ''
        for name, value in elem.attrib.iteritems():
            lname = name.lower()
            if value:
                if 'id' == lname:
                    Id = value
                elif 'class' == lname:
                    classname = value
                elif 'title' == lname:
                    title = value

        results.add_anchor_uri(uri, anchor_text, Id, classname, title)
        
    def process_meta_content(self, results, elem):
        http_equiv, content = '', ''
        for name, value in elem.attrib.iteritems():
            lname = name.lower()
            if lname and value:
                if 'http-equiv' == lname:
                    http_equiv = value
                elif 'content' == lname:
                    content = value

            if content and http_equiv:
                http_equiv = http_equiv.lower()
                if  http_equiv in ('redirect', 'refresh') and content:
                    m = self.re_meta_refresh.match(content.strip())
                    if m:
                        results.add_meta_redirect_uri(m.group(1))
                elif 'content-type' == http_equiv:
                    m = self.re_meta_content_type.match(content.strip())
                    if m:
                        # TODO: if this isn't HTML, what do then?
                        content_type = m.group(1)
                        encoding = m.group(2)
                        if encoding:
                            results.encoding = encoding
                    

    def match_uri_contents(self, results, value):
        # TODO: implement using content_type dependent processing ?
        #       or just use regex for now?
        self.match_uri_quote_delimited(results, value)
        self.match_uri_nonquote_delimited(results, value)

    def match_uri_quote_delimited(self, results, value):
        matches = self.re_quoted_http.findall(value)
        for m in matches:
            results.add_uri(m[1:-1].strip())
        matches = self.re_quoted_relative.findall(value)
        for m in matches:
            results.add_uri(m[1:-1].strip())

    def match_uri_nonquote_delimited(self, results, value):
        matches = self.re_naked_uri.findall(value)
        for m in matches:
            results.add_uri(m.strip())

    def process_param_content(self, results, elem):
        for name, value in elem.attrib.iteritems():
            lname = name.lower()
            if lname and value:
                if 'value' == lname:
                    self.match_uri_contents(results, value)

    def process_etree(self, results, jsParser, htmlbuf, html):

        # TODO: decide if XHTML needs different parsing
        parser = etree.HTMLParser()
        dom = etree.parse(htmlbuf, parser)
        root = dom.getroot()

        contextual_io = StringIO()
        structural_io = StringIO()

        if root is None:
            # okay, maybe not real HTML
            if html.startswith('<!--') and html.endswith('-->'):
                htmlbuf = StringIO(html[4:-3])
                dom = etree.parse(htmlbuf, parser)
                root = dom.getroot()
            else:
                # something else or totallly invalid
                raise Exception('invalid content for now: %s' % html)
                self.match_uri_contents(results, self.get_text_string(results, html))

        if root is not None:
            for elem in root.itersiblings(tag=etree.Comment, preceding=True):
                self.process_comment(results, elem)
            
            events = ('start', 'end', 'comment', 'pi')
            context = etree.iterwalk(root, events = events)
            for action, elem in context:
#                print(action, elem)
                if 'start' == action:
                    if elem.tag == etree.Comment:
                        pass
                    elif elem.tag == etree.ProcessingInstruction:
                        pass
                    else:
                        contextual_io.write('<')
                        structural_io.write('<')
                        contextual_io.write(str(elem.tag))
                        for k in elem.attrib.keys():
                            contextual_io.write(' ')
                            contextual_io.write(k)
                            structural_io.write('@')
                        contextual_io.write('>')
                        structural_io.write('>')
                elif 'end' == action:
                    if elem.tag == etree.Comment:
                        self.process_comment(results, elem)
                    elif elem.tag == etree.ProcessingInstruction:
                        # TODO
                        pass
                    else:
                        self.process_attributes(results, jsParser, elem)
                        self.process_tag(results, jsParser, elem)
                        contextual_io.write('</')
                        contextual_io.write(str(elem.tag))
                        contextual_io.write('>')
                        structural_io.write('</>')

            results.set_contextual_fingerprint(contextual_io.getvalue())
            results.set_structural_fingerprint(structural_io.getvalue())
            
            for elem in root.itersiblings(tag=etree.Comment, preceding=False):
                self.process_comment(results, elem)

    def process(self, html, baseurl, encoding = 'utf-8', results = None):
        parser = etree.HTMLParser()
        jsParser = JSLiteParser()

        if results is None:
            results = HtmlParseResults(baseurl, encoding)

        if html is not None:
            html = html.strip()
            if len(html) > 0:
                htmlbuf = StringIO(html)
                try:
                    self.process_etree(results, jsParser, htmlbuf, html)
                except etree.XMLSyntaxError, e:
                    # TODO: consider using beautiful soup
                    # TODO: real warning
                    print('Exception on html extraction: %s (%s)' % (e, html[0:128]))
                    pass

        js_comments =jsParser.comments()
        js_strings = jsParser.strings()

        # TODO: basically duplicated for JSExtractor .. refactor
        for string in js_strings:
            for line in string.splitlines():
                match = self.re_full_url.search(line)
                if match:
                    results.add_uri(match.group(0))
                match = self.re_relative_url.search(line)
                if match:
                    results.add_relative_uri(match.group(0))

        for comment in js_comments:
            results.add_comment(comment)
            for line in comment.splitlines():
                match = self.re_full_url.search(line)
                if match:
                    results.add_uri(match.group(0))
                match = self.re_relative_url.search(line)
                if match:
                    results.add_relative_uri(match.group(0))

        return results

if '__main__' == __name__:

    import sys
    filename = sys.argv[1]
    url = sys.argv[2]
    contents = open(filename).read()
    
    extractor = HtmlExtractor()
    results = extractor.process(contents, url)

    print('contextual fingerprint: %s' % (results.contextual_fingerprint))
    print('structural fingerprint: %s' % (results.structural_fingerprint))

    for form in results.forms:
        print('form:\n%s' % (form))

    for input in results.other_inputs:
        print('input:\n%s' % (input))

    if True:
        for comment in results.comments:
            print('comment: %s' % comment)

        for link in results.links:
            print('link: %s' % link)

        for link in results.relative_links:
            print('relative link: %s' % link)

        for anchor in results.anchors:
            print('anchor: %s' % repr(anchor))

        for script in results.inline_scripts:
            print('inline script: %s' % script)

        for script in results.scripts:
            print('script: %s' % script)

        for style in results.inline_styles:
            print('inline style: %s' % style)

        for style in results.styles:
            print('style: %s' % style)

