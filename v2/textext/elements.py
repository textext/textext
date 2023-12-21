"""
This file is part of TexText, an extension for the vector
illustration program Inkscape.

Copyright (c) 2006-2023 TexText developers.

TexText is released under the 3-Clause BSD license. See
file LICENSE.txt or go to https://github.com/textext/textext
for full license details.
"""
from copy import deepcopy
from dataclasses import dataclass
from lxml import etree
from typing import Any, Callable, List
import math
import re
import uuid
import inkex


@dataclass
class TexTextEleMetaData:
    """ A data class just holding the metadata of a TexText node

    Also holds the default values for several metadata keys.
    """
    DEFAULT_TEXCMD = "pdflatex"
    DEFAULT_PREAMBLE = "default_packages.tex"
    DEFAULT_SCALE = 1.0
    DEFAULT_FONTSIZE_PT = 10
    DEFAULT_ALIGNMENT = "middle center"
    DEFAULT_STROKE_TO_PATH = False
    DEFAULT_JACOBIAN_SQRT = 1.0
    DEFAULT_TEXTEXT_VERSION = "<=0.7"
    DEFAULT_INKSCAPE_VERSION = "0.0"
    DEFAULT_INKEX_VERSION = "0.0"

    text: str = ""
    tex_command: str = DEFAULT_TEXCMD
    preamble: str = DEFAULT_PREAMBLE
    scale_factor: float = DEFAULT_SCALE
    font_size_pt: float = DEFAULT_FONTSIZE_PT
    alignment: str = DEFAULT_ALIGNMENT
    stroke_to_path: bool = DEFAULT_STROKE_TO_PATH
    jacobian_sqrt: float = DEFAULT_JACOBIAN_SQRT
    textext_version: str = DEFAULT_TEXTEXT_VERSION  # Introduced in 0.7.1
    inkscape_version: str = DEFAULT_INKSCAPE_VERSION
    inkex_version: str = DEFAULT_INKEX_VERSION  # Introduced in 2.0.0


class TexTextSvgEle(inkex.Group):
    """ A xml Group-element holding the rendered content.

    The temporary svg file created by the converters is passed to this class.
    It is read in, and converted into a properly scaled svg group element.
    This element can later be used to insert it into the target svg
    document.

    The metadata used to generate this node can be added by set_meta_data.

    Several methods can be used to properly align this node to a reference
    node and to manage its color.
    """
    tag_name = "g"

    # For addressing the SVG elements
    TEXTEXT_NS = "http://www.iki.fi/pav/software/textext/"
    SVG_NS = "http://www.w3.org/2000/svg"
    XLINK_NS = "http://www.w3.org/1999/xlink"
    ID_PREFIX = "textext-"
    NSS = {
        "textext": TEXTEXT_NS,
        "svg": SVG_NS,
        "xlink": XLINK_NS,
    }

    # Keys for meta data
    KEY_VERSION = "version"
    KEY_TEXCONVERTER = "texconverter"
    KEY_PDFCONVERTER = "pdfconverter"
    KEY_TEXT = "text"
    KEY_PREAMBLE = "preamble"
    KEY_SCALE = "scale"
    KEY_FONTSIZE_PT = "fontsize_pt"
    KEY_ALIGNMENT = "alignment"
    KEY_JACOBIAN_SQRT = "jacobian_sqrt"
    KEY_STROKE2PATH = "stroke-to-path"
    KEY_INKSCAPE_VERSION = "inkscapeversion"
    KEY_INKEX_VERSION = "inkexversion"

    def __init__(self, source_svg_filename: str, target_document_unit: str):
        """
        :param source_svg_filename: The name of the file containing the svg-snippet
        :param target_document_unit: String specifying the unit of the document into
                                     which the node is going to be placed ("mm", "pt", ...).
                                     This is needed to ensure that the snippet is properly
                                     scaled later.
        """
        super().__init__()
        self._svg_to_textext_node(source_svg_filename, target_document_unit)
        self.transform = inkex.Transform()

    def set_meta_data(self, meta_data: TexTextEleMetaData):
        """ Writes the meta data as attributes into the svg node

        :param (TexTextEleMetaData) meta_data: The meta data set in the node

        """
        self.set_meta(self.KEY_VERSION, meta_data.textext_version)
        self.set_meta(self.KEY_TEXCONVERTER, meta_data.tex_command)
        self.set_meta(self.KEY_PDFCONVERTER, "inkscape")
        self.set_meta_text(meta_data.text)
        self.set_meta(self.KEY_PREAMBLE, meta_data.preamble)
        self.set_meta(self.KEY_SCALE, str(meta_data.scale_factor))
        self.set_meta(self.KEY_ALIGNMENT, str(meta_data.alignment))
        self.set_meta(self.KEY_STROKE2PATH, str(int(meta_data.stroke_to_path)))
        self.set_meta(self.KEY_INKSCAPE_VERSION, str(meta_data.inkscape_version))
        self.set_meta(self.KEY_INKEX_VERSION, str(meta_data.inkex_version))

    def get_meta_data(self, **kwargs) -> TexTextEleMetaData:
        """ Reads all TexText relevant attributes as metadata from the svg.

        :raises: AttributeNotFound if no text and no preamble attribute is found.

        :return: TexTextEleMetaData

        """
        meta_data = TexTextEleMetaData()
        meta_data.text = self.get_meta_text()
        meta_data.preamble = self.get_meta(self.KEY_PREAMBLE)
        meta_data.scale_factor = self.get_meta(self.KEY_SCALE,
                                               data_type=float,
                                               default=TexTextEleMetaData.DEFAULT_SCALE)
        meta_data.alignment = self.get_meta(self.KEY_ALIGNMENT,
                                            data_type=str,
                                            default=TexTextEleMetaData.DEFAULT_ALIGNMENT)
        meta_data.tex_command = self.get_meta(self.KEY_TEXCONVERTER,
                                              data_type=str,
                                              default=TexTextEleMetaData.DEFAULT_TEXCMD)
        meta_data.stroke_to_path = bool(self.get_meta(self.KEY_STROKE2PATH,
                                                      data_type=int,
                                                      default=TexTextEleMetaData.DEFAULT_STROKE_TO_PATH))
        meta_data.font_size_pt = self.get_meta(self.KEY_FONTSIZE_PT,
                                               data_type=int,
                                               default=TexTextEleMetaData.DEFAULT_FONTSIZE_PT)
        meta_data.jacobian_sqrt = self.get_meta(self.KEY_JACOBIAN_SQRT,
                                                data_type=float,
                                                default=TexTextEleMetaData.DEFAULT_JACOBIAN_SQRT)
        meta_data.textext_version = self.get_meta(self.KEY_VERSION,
                                                  data_type=str,
                                                  default=TexTextEleMetaData.DEFAULT_TEXTEXT_VERSION)
        meta_data.inkscape_version = self.get_meta(self.KEY_INKSCAPE_VERSION,
                                                   data_type=str,
                                                   default=TexTextEleMetaData.DEFAULT_INKSCAPE_VERSION)
        meta_data.inkex_version = self.get_meta(self.KEY_INKEX_VERSION,
                                                data_type=str,
                                                default=TexTextEleMetaData.DEFAULT_INKEX_VERSION)

        return meta_data

    def align_to_node(self, ref_node, alignment: str, relative_scale: float):
        """ Aligns the node represented by self to a reference node according to the metadata

        :param ref_node: Reference node of type TexTextSvgEle to which self is going to be aligned
        :type: TexTextSvgEle
        :param alignment: A 2-element string list defining the alignment
        :param relative_scale: Scaling of the new node relative to the scale of the reference node

        ToDo: add type hint for ref_node when Python 3.11 is minimal inkex requirement
        """
        scale_transform = inkex.Transform(f"scale({relative_scale})")

        old_transform = inkex.Transform(ref_node.transform)

        # Account for vertical flipping of nodes created via pstoedit in TexText <= 0.11.x
        revert_flip = inkex.Transform("scale(1)")
        if ref_node.get_meta("pdfconverter", "pstoedit") == "pstoedit":
            revert_flip = inkex.Transform(matrix=((1, 0, 0), (0, -1, 0)))  # vertical reflection

        composition = scale_transform * old_transform * revert_flip

        # keep alignment point of drawing intact, calculate required shift
        self.transform = composition

        ref_bb = ref_node.bounding_box()
        old_x, old_y, old_w, old_h = ref_bb.left, ref_bb.top, ref_bb.width, ref_bb.height
        bbox = self.bounding_box()
        new_x, new_y, new_w, new_h = bbox.left,  bbox.top, bbox.width, bbox.height

        p_old = self._get_pos(old_x, old_y, old_w, old_h, alignment)
        p_new = self._get_pos(new_x, new_y, new_w, new_h, alignment)

        d_x = p_old[0] - p_new[0]
        d_y = p_old[1] - p_new[1]

        composition = inkex.Transform(translate=(d_x, d_y)) * composition

        self.transform = composition
        self.set_meta(self.KEY_JACOBIAN_SQRT, str(self.get_jacobian_sqrt()))

    def set_none_strokes_to_0pt(self):
        """
        Iterates over all elements of the node. For each element which has the style attribute
        "stroke" set to "none" a style attribute "stroke-width" with value "0" is added. This
        ensures that when colorizing the node later in inkscape by setting the node and
        stroke colors letters do not become bold (letters have "stroke" set to "none" but e.g.
        horizontal lines in fraction bars and square roots are only affected by stroke colors
        so for full colorization of a node you need to set the fill as well as the stroke color!).
        """
        for ele in self.iter():
            if ele.style.get("stroke", "").lower() == "none":
                ele.style["stroke-width"] = "0"

    def is_colorized(self) -> bool:
        """ Returns true if at least one element of the managed node contains a non-black fill or stroke color """
        return self._has_colorized_attribute() or self._has_colorized_style()

    def _svg_to_textext_node(self, source_svg_filename: str, target_document_unit: str):
        """ Takes content of a svg file and saves it as svg element in self

        :param source_svg_filename: The absolute path of the file from which the content
                                    is read
        :param target_document_unit: The unit used in the target document.
        """
        doc = etree.parse(source_svg_filename, parser=inkex.SVG_PARSER)

        root = doc.getroot()

        TexTextSvgEle._expand_defs(root)

        shape_elements = [el for el in root if isinstance(el, (inkex.ShapeElement, inkex.Defs))]
        root.append(self)

        for ele in shape_elements:
            self.append(ele)

        self._make_ids_unique()

        # Ensure that snippet is correctly scaled according to the units of the document
        # We scale it here such that its size is correct in the document units
        # (Usually pt returned from poppler to mm in the main document)
        self.transform.add_scale(root.uutounit(f"1{root.unit}", target_document_unit))

    @staticmethod
    def _expand_defs(root: etree.ElementTree):
        """ Replace all references to glyph definitions by the definitions itself in a given element

        :param root: The root element of the svg element. Its content is modified by this method.
        """
        for ele in root:
            if isinstance(ele, inkex.Use):
                # <group> element will replace <use> node
                group = inkex.Group()

                # add all objects from symbol node
                for obj in ele.href:
                    group.append(deepcopy(obj))

                # translate group
                group.transform = inkex.Transform(translate=(float(ele.attrib["x"]), float(ele.attrib["y"])))

                # replace use node with group node
                parent = ele.getparent()
                parent.remove(ele)
                parent.add(group)

                ele = group  # required for recursive defs

            # expand children defs
            TexTextSvgEle._expand_defs(ele)

    def _make_ids_unique(self):
        """
        PDF->SVG converters tend to use same ids.
        To avoid confusion between objects with same id from two or more TexText objects we replace auto-generated
        ids with random unique values
        """
        rename_map = {}

        # replace all ids with unique random uuid
        for ele in self.iterfind('.//*[@id]'):
            old_id = ele.attrib["id"]
            new_id = 'id-' + str(uuid.uuid4())
            ele.attrib["id"] = new_id
            rename_map[old_id] = new_id

        # find usages of old ids and replace them
        def replace_old_id(match):
            old_name = match.group(1)
            try:
                replacement = rename_map[old_name]
            except KeyError:
                replacement = old_name
            return f"url(#{replacement})"
        regex = re.compile(r"url\(#([^)(]*)\)")

        for ele in self.iter():
            for name, value in ele.items():
                new_value = regex.sub(replace_old_id, value)
                ele.attrib[name] = new_value

    def get_jacobian_sqrt(self) -> float:
        """ Calculates the square root of the determinant of the transformation matrix
        """
        # pylint: disable=invalid-name
        (a, b, _), (d, e, _) = inkex.Transform(self.transform).matrix
        det = a * e - d * b
        assert det != 0
        return math.sqrt(math.fabs(det))

    def set_meta(self, key: str, value: str):
        """ Sets a key (xml-attribute) to a value in the TEXTEXT_NS namespace

        Use _set_meta_text to set the value of the key KEY_TEXT.

        :param key: The key of the value to be set
        :param value: The value to be set
        """
        ns_key = f"{{{self.TEXTEXT_NS}}}{key}"
        self.set(ns_key, value)
        assert self.get_meta(key) == value, (self.get_meta(key), value)

    def set_meta_text(self, value: str):
        """ Sets the value of the key KEY_TEXT

        It is ensured that the text is properly encoded.

        :param value: The text
        """
        encoded_value = value.encode('unicode_escape').decode('utf-8')
        self.set_meta(self.KEY_TEXT, encoded_value)

    def get_meta_text(self) -> str:
        """ Returns the content of KEY_TEXT.

        It is ensured that it is properly decoded.
        """
        node_version = self.get_meta(self.KEY_VERSION, default=TexTextEleMetaData.DEFAULT_TEXTEXT_VERSION)
        encoded_text = self.get_meta(self.KEY_TEXT)

        if node_version != "1.2.0":
            # Fix for TexText 1.2.0 bug
            return encoded_text.encode("utf-8").decode("unicode_escape")
        return encoded_text

    def get_meta(self, key: str, data_type: Callable[[str], Any] = str, default: Any = None) -> Any:
        """ Access the value of a metadata key.

        :param key: The key of the value one wants to have
        :param data_type: The datatype the value should be converted to. Set to None if the
                          value should be returned as a string.
        :param default: The default value which is returned if the key does not exist
        :raises: AttributeError if key does not exist and no default value has been specified,
                 ValueError if value cannot be converted
        :return: The value of the key (or its default value)
        """
        try:
            ns_key = f'{{{self.TEXTEXT_NS}}}{key}'
            value = self.get(ns_key)
            if value is None:
                raise AttributeError(f'{self} has no attribute `{key}`')
            return value if data_type is str else data_type(value)
        except (AttributeError, ValueError) as attr_error:
            if default is not None:
                return default
            raise attr_error

    @staticmethod
    def _get_pos(x: float, y: float, w: float, h: float, alignment: str) -> List[float]:
        """ Returns the alignment point of a frame according to the required alignment

        :param x, y, w, h: Position of top left corner, width and height of the frame
        :param alignment: String describing the required alignment, e.g. "top left", "middle right", etc.
        """
        v_alignment, h_alignment = alignment.split(" ")
        if v_alignment == "top":
            ypos = y
        elif v_alignment == "middle":
            ypos = y + h / 2
        elif v_alignment == "bottom":
            ypos = y + h
        else:
            # fallback -> middle
            ypos = y + h / 2

        if h_alignment == "left":
            xpos = x
        elif h_alignment == "center":
            xpos = x + w / 2
        elif h_alignment == "right":
            xpos = x + w
        else:
            # fallback -> center
            xpos = x + w / 2
        return [xpos, ypos]

    def _has_colorized_attribute(self) -> bool:
        """ Returns true if at least one element of self contains a non-black fill or stroke attribute
        """
        for it_node in self.iter():
            for attrib in ["stroke", "fill"]:
                if attrib in it_node.attrib and it_node.attrib[attrib].lower().replace(" ", "") not in \
                        ["rgb(0%,0%,0%)", "black", "none", "#000000"]:
                    return True
        return False

    def _has_colorized_style(self) -> bool:
        """ Returns true if at least one element of node contains a non-black fill or stroke style
        """
        for it_node in self.iter():
            style = it_node.style  # type: inkex.Style
            for style_attrib in ["stroke", "fill"]:
                if style_attrib in style and \
                        style[style_attrib].lower().replace(" ", "") not in ["rgb(0%,0%,0%)",
                                                                             "black",
                                                                             "none",
                                                                             "#000000"]:
                    return True
        return False

    def _import_group_color_style(self, src_svg_ele):
        """
        Extracts the color relevant style attributes of src_svg_ele (of class TexTextElement) and
        applies them to all items  of self. Ensures that non color relevant style
        attributes are not overwritten.

        ToDo: Type annotation "Self" for src_svg_ele when Python 3.11 is inkex requirement
        """

        # Take the top level style information which is set when coloring the group in Inkscape
        style = src_svg_ele.style  # type: inkex.Style

        # If a style attribute exists we can copy the style, if not, there is nothing to do here
        if len(style):
            # Fetch the part of the source dict which is interesting for colorization
            color_style_dict = {key: value for key, value in style.items() if
                                key.lower() in ["fill", "stroke", "opacity", "stroke-opacity",
                                                "fill-opacity"] and value.lower() != "none"}

            for ele in self.iter():
                # Update style
                ele.style.update(color_style_dict)

                # Ensure that simple strokes are also colored if the the group has a fill color
                # ToDo: Check if this really can be put outside of the loop
                if "stroke" in ele.style and "fill" in color_style_dict:
                    ele.style["stroke"] = color_style_dict["fill"]

                # Remove style-duplicating attributes
                for prop in ("stroke", "fill"):
                    if prop in style:
                        ele.pop(prop)

                # Avoid unintentional bolded letters
                if "stroke-width" not in ele.style:
                    ele.style["stroke-width"] = "0"
