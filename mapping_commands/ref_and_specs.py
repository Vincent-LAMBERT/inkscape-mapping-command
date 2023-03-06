#! /usr/bin/env python3
#######################################################################################################################
#  Copyright (c) 2023 Vincent LAMBERT
#  License: MIT
#
#  Permission is hereby granted, free of charge, to any person obtaining a copy
#  of this software and associated documentation files (the "Software"), to deal
#  in the Software without restriction, including without limitation the rights
#  to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
#  copies of the Software, and to permit persons to whom the Software is
#  furnished to do so, subject to the following conditions:
# 
#  The above copyright notice and this permission notice shall be included in all
#  copies or substantial portions of the Software.
# 
#  THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
#  IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
#  FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
#  AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
#  LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
#  OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
#  SOFTWARE.
#
#######################################################################################################################
# NOTES
#
# Developing extensions:
#   SEE: https://inkscape.org/develop/extensions/
#   SEE: https://wiki.inkscape.org/wiki/Python_modules_for_extensions
#   SEE: https://wiki.inkscape.org/wiki/Using_the_Command_Line
#
# Implementation References:
#   SEE: https://github.com/nshkurkin/inkscape-export-layer-combos

import inkex
import numpy as np

from utils import *
from lxml import etree


#######################################################################################################################
    
def get_mg_layer_refs(layer_refs, logit) :
    """
    Retrieve the microgesture layers
    """
    count=0
    mg_layer_refs = dict()
    # Figure out the family layers.
    for layer_ref in layer_refs:
        if not layer_ref.has_valid_mg_export_spec():
            continue
        
        for export in layer_ref.mg_export_specs :
            if export.microgesture not in mg_layer_refs :
                mg_layer_refs[export.microgesture] = dict()
            if export.characteristic not in mg_layer_refs[export.microgesture] :
                mg_layer_refs[export.microgesture][export.characteristic] = list()
            count+=1
            mg_layer_refs[export.microgesture][export.characteristic].append(layer_ref)

    logit(f"Found {count} valid layers for {len(mg_layer_refs)} types of microgestures")
    return mg_layer_refs

#######################################################################################################################

class LayerRef(object):
    """
    A wrapper around an Inkscape XML layer object plus some helper data for doing combination exports.
    """

    def __init__(self, source: etree.Element):
        self.source = source
        self.id = source.attrib["id"]
        label_attrib_name = LayerRef.get_layer_attrib_name(source)
        self.label = source.attrib[label_attrib_name]
        self.children = list()
        self.non_layer_children_style = dict()
        self.non_layer_children_initial_path = dict()
        self.parent = None

        self.export_specs = list()
        self.request_hidden_state = False
        self.requested_hidden = False
        self.sibling_ids = list()

        self.mg_export_specs = MicrogestureExportSpec.create_specs(self)
        self.described_mg = source.attrib["mgrep-microgesture-layer"] if "mgrep-microgesture-layer" in source.attrib else None

    @staticmethod
    def get_layer_attrib_name(layer: etree.Element) -> str:
        return "{%s}label" % layer.nsmap['inkscape']
    
    def has_valid_mg_export_spec(self):
        return len(self.mg_export_specs) > 0
    
#######################################################################################################################

class MicrogestureExportSpec(object):
    """
    A description of how to export a family layer.
    """

    ATTR_ID = "mgrep-microgesture-layer"

    def __init__(self, spec: str, layer: object, microgesture: str, characteristic: str):
        self.spec = spec
        self.layer = layer
        self.microgesture = microgesture
        self.characteristic = characteristic

    @staticmethod
    def create_specs(layer) -> list:
        """Extracts '[microgesture],[characteristic]' from the layer's ATTR_ID attribute and returns either an empty list or a list of FamilyExportSpec element. A RuntimeError is raised if it is incorrectly formatted.
        """
        result = list()
        if MicrogestureExportSpec.ATTR_ID not in layer.source.attrib:
            return result
        
        spec = layer.source.attrib[MicrogestureExportSpec.ATTR_ID]
        
        g_split = spec.split(",")

        if len(g_split) != 2 :
            raise RuntimeError(f"layer '{layer.label}'(#{layer.id}) has an invalid value '{spec}'. " +
                                f"Expected value is of the form '[microgesture],[characteristic]'")
        
        microgesture = g_split[0].replace(" ", "")
        charac = g_split[1].replace(" ", "")
        
        if microgesture not in MICROGESTURES :
            raise RuntimeError(f"layer '{layer.label}'(#{layer.id}) has an invalid value '{microgesture}'. " +
                                f"Expected value is one of {list(MICROGESTURES.keys())}")
        if charac not in MICROGESTURE_CHARACTERISTICS[microgesture] :
            raise RuntimeError(f"layer '{layer.label}'(#{layer.id}) has an invalid value '{charac}'. " +
                                f"Expected value is one of {list(MICROGESTURE_CHARACTERISTICS[microgesture].keys())}")
            
        result.append(MicrogestureExportSpec(spec, layer, microgesture, charac))
        return result
