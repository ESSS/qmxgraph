#!/usr/bin/env python
"""
This is a tool created to help developers convert SVGs to the shapes in XML
format used by mxGraph's stencils.

To learn details about mxGraph's stencils refer to its official docs:
https://jgraph.github.io/mxgraph/docs/js-api/files/shape/mxStencil-js.html#mxStencil

Basically this tool parses the SVG file contents and converts SVG commands to
their counterpart
for a stencil shape.

It dumps the stencil shape to standard output when done.

Pre-requirements
----------------

* Based on SVGs saved in Inkscape software (it can probably work for any SVGs,
 may need some refactoring first though);
* mxGraph's stencils ONLY work with absolute coordinates and this tool does
 NOT know how to convert relative coordinates to their absolute counterpart, so
 sure SVG is ONLY using absolute coordinates;
    * In Inkscape you can fix this by edit > preferenes > SVG output > set
        `Path String Format` to `Absolute`;
* It assumes just ONE shape by file, separate in different files before using
 this tool, if possible.

Known issues
------------

* Output generated in *mostly* ready, but still requires manual intervention,
 mainly because
    * it doesn't have an heuristic to infer which paths are part of background
     or foreground of stencil. By default, as drawing are placed in foreground;
    * shape name and dimensions are extracted automatically from SVG too, you
     may need to review them first;
* it isn't feature complete, as it is evolving according new SVGs are created
 and converted to stencils.
"""
import abc
import itertools
import os
import re
import sys
import xml.etree.ElementTree


class SvgParser:
    def __init__(self, svg_path):
        self.svg_path = svg_path

    def read(self):
        ident = " " * 4
        tree = xml.etree.ElementTree.parse(self.svg_path)
        root = tree.getroot()

        ns = {
            "default": "http://www.w3.org/2000/svg",
            "sodipodi": "http://sodipodi.sourceforge.net/DTD/sodipodi-0.dtd",
            "inkscape": "http://www.inkscape.org/namespaces/inkscape",
        }

        sodipodi_docname = "{{{}}}docname".format(ns["sodipodi"])
        if sodipodi_docname in root.attrib:
            name = root.attrib[sodipodi_docname].replace(".svg", "")
        else:
            name = os.path.basename(self.svg_path).replace(".svg", "")
        width = root.attrib["width"].replace("px", "")
        height = root.attrib["height"].replace("px", "")

        default_ns = "{{{}}}".format(ns["default"])
        svg_elements = (c for c in root if c.tag.startswith(default_ns))

        drawing_cmds = []
        for svg_element in svg_elements:
            tag = svg_element.tag.replace(default_ns, "")
            parser = None
            if tag == "path":
                parser = PathParser(ident)
            elif tag == "polygon":
                parser = PolygonParser(ident)
            elif tag == "rect":
                parser = RectParser(ident)

            if parser is not None:
                path = parser.parse(svg_element)
                drawing_cmds.append(path)
            else:
                no_parser_msg = '<!-- not known parser for tag "{}" -->'
                drawing_cmds.append([no_parser_msg.format(tag)])

        return _SHAPE_TEMPLATE.format(
            name=name,
            width=width,
            height=height,
            drawing="\n".join(
                "{}{}".format(ident * 2, c) for c in itertools.chain.from_iterable(drawing_cmds)
            ),
        )

    def _parse_size(self, value, unit):
        return value.replace(unit, "")


class DrawingParser:
    __metaclass__ = abc.ABCMeta

    def __init__(self, ident=""):
        self.ident = ident
        self.cmds = []
        self.styles = {}

    def parse(self, value):
        self._add_style_commands(value)
        self._add_drawing_commands(value)
        self._add_fill_stroke_command()
        return self.cmds

    @abc.abstractmethod
    def _add_drawing_commands(self, value):
        pass

    def _add_style_commands(self, value):
        added = self.styles

        tag_map = {
            "fill": ("fillcolor", "color"),
            "stroke": ("strokecolor", "color"),
            "stroke-width": ("strokewidth", "width"),
            "stroke-miterlimit": ("miterlimit", "limit"),
        }

        if "style" in value.attrib:
            style = value.attrib["style"]
            for style_attr in style.split(";"):
                style_tag, style_value = style_attr.split(":")

                if style_tag in tag_map:
                    el_name, attr = tag_map[style_tag]
                    added[style_tag] = self._add_if_not_none(el_name, attr, style_value)

        for style_tag, (el_name, attr) in tag_map.items():
            if added.get(style_tag):
                continue

            if style_tag in value.attrib:
                added[style_tag] = self._add_if_not_none(el_name, attr, value.attrib[style_tag])

    def _add_fill_stroke_command(self):
        has_stroke = self.styles.get("stroke")
        has_fill = self.styles.get("fill")
        if has_fill and has_stroke:
            self.cmds.append("<fillstroke/>")
        elif has_fill:
            self.cmds.append("<fill/>")
        elif has_stroke:
            self.cmds.append("<stroke/>")

    def _add_if_not_none(self, el_name, attr, value):
        added = False
        if value != "none":
            self.cmds.append('<{} {}="{}"/>'.format(el_name, attr, value))
            added = True
        return added


class PolygonParser(DrawingParser):
    def _add_drawing_commands(self, value):
        # https://www.w3.org/TR/SVG/shapes.html#PolygonElement
        # Mathematically, a 'polygon' element can be mapped to an equivalent
        # 'path' element as follows:
        # * perform an absolute `moveto` operation to the first coordinate
        # pair in the list of points
        # * for each subsequent coordinate pair, perform an absolute `lineto`
        # operation to that coordinate pair
        # * perform a `closepath` command
        points = value.attrib["points"]
        pos = 0

        self.cmds.append("<path>")
        m = re.match(r"(\d+(?:\.\d+)?),(\d+(?:\.\d+)?) +", points[pos:])
        x0 = m.group(1)
        y0 = m.group(2)
        self.cmds.append('{}<move x="{}" y="{}"/>'.format(self.ident, x0, y0))
        pos += len(m.group(0))

        while True:
            m = re.match(r"(\d+(?:\.\d+)?),(\d+(?:\.\d+)?) +", points[pos:])
            if m is None:
                break

            self.cmds.append('{}<line x="{}" y="{}"/>'.format(self.ident, m.group(1), m.group(2)))
            pos += len(m.group(0))

        # Close polygon
        self.cmds.append('{}<line x="{}" y="{}"/>'.format(self.ident, x0, y0))
        self.cmds.append("</path>")


class PathParser(DrawingParser):
    def _add_drawing_commands(self, value):
        drawing = value.attrib["d"]
        state = self.wait_command_state
        pos = 0

        cmds_offset = len(self.cmds)
        while state is not None:
            state, pos = state(drawing, pos)

        self.cmds.insert(cmds_offset, "<path>")
        self.cmds.append("</path>")

    def wait_command_state(self, value, pos):
        if pos >= len(value):
            return None, pos
        elif value[pos] == "M":
            return self.move_state, pos + 1
        elif value[pos] == "C":
            return self.curve_state, pos + 1
        elif value[pos] == " ":
            return self.wait_command_state, pos + 1

        raise ValueError("Could not parse {}".format(value[pos]))

    def move_state(self, value, pos):
        m = re.match(r" +(\d+(\.\d+)?),(\d+(\.\d+)?) +", value[pos:])
        if m is None:
            raise ValueError("Could not parse {}".format(value[pos]))

        self.cmds.append('{}<move x="{}" y="{}"/>'.format(self.ident, m.group(1), m.group(3)))
        return self.wait_command_state, pos + len(m.group(0))

    def curve_state(self, svg, pos):
        index = 1

        cmd = ""
        while True:
            m = re.match(r" *(\d+(\.\d+)?),(\d+(\.\d+)?) *(Z)?", svg[pos:])
            if m is None:
                raise ValueError("Could not parse {}".format(svg[pos]))

            pos += len(m.group(0))

            if index == 1:
                cmd = "{}<curve".format(self.ident)

            cmd += ' x{index}="{x}" y{index}="{y}"'.format(index=index, x=m.group(1), y=m.group(3))
            index += 1
            if index > 3:
                index = 1
                cmd += "/>"
                self.cmds.append(cmd)

            if m.group(5) is not None:
                break

        assert index == 1, "should have had 3 coordinates for each curve"

        return self.wait_command_state, pos


class RectParser(DrawingParser):
    def _add_drawing_commands(self, value):
        svg_to_stencil_attr_map = {
            "x": "x",
            "y": "y",
            "width": "w",
            "height": "h",
        }
        rect_stencil_tag = "<rect"
        for svg, stencil in svg_to_stencil_attr_map.items():
            rect_stencil_tag += ' {}="{}"'.format(stencil, value.attrib[svg])

        rect_stencil_tag += "/>"
        self.cmds.append(rect_stencil_tag)


_SHAPE_TEMPLATE = """\
<shape aspect="fixed" h="{width}" name="{name}" w="{height}">
    <connections>
        <constraint name="N" perimeter="0" x="0.5" y="0"/>
        <constraint name="S" perimeter="0" x="0.5" y="1"/>
        <constraint name="W" perimeter="0" x="0" y="0.5"/>
        <constraint name="E" perimeter="0" x="1" y="0.5"/>
        <constraint name="NW" perimeter="0" x="0.145" y="0.145"/>
        <constraint name="SW" perimeter="0" x="0.145" y="0.855"/>
        <constraint name="NE" perimeter="0" x="0.855" y="0.145"/>
        <constraint name="SE" perimeter="0" x="0.855" y="0.855"/>
    </connections>
    <foreground>
{drawing}
    </foreground>
    <background>
    </background>
</shape>
"""


if __name__ == "__main__":
    import argparse

    arg_parser = argparse.ArgumentParser(
        description="Converts a SVG file to a stencil file " "compatible with mxGraph."
    )
    arg_parser.add_argument(
        "svg",
        metavar="SVG_FILE",
        nargs=1,
        help="A SVG file",
    )
    args = sys.argv[1:]
    args = arg_parser.parse_args(args=args)

    parser = SvgParser(args.svg[0])
    print(parser.read())
