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

import copy
import logging
import numpy as np
import inkex
from representation_with_commands import CommandExport

from utils import *
from ref_and_specs import *
from configuration_file import *

#######################################################################################################################

class ComputeSVG():
    def __init__(self, export: CommandExport):
        self.export = export
        # Get the name of the svg file
        self.svg_name = self.export.svg.name.split(".")[0]
        
    def compute(self):
        """
        This is the core of the extension
        It gathers all layers, puts all families elements in a Nx4 matrix
        and compute the representations  for each one of them 
        according to the markers types and position  
        """
        logit = logging.warning if self.export.options.debug else logging.info
        logit(f"Options: {str(self.export.options)}")
        
        # Get a dictionnary of each exported family with their
        # element layers also put in a dictionnary corresponding 
        # to the element considered
        layer_refs = self.get_layer_refs()
        mg_layer_refs = get_mg_layer_refs(layer_refs, logit)
        
        # Add the command icons to the svg
        command_layers = add_command_icons(mg_layer_refs, logit)
        
        # Get a dictionnary of the wanted diversified styles with their characteristics
        mappings = get_mappings(self.export.options.config, logit)
        for mapping in mappings :
            change_mapping(command_layers, mapping, mg_layer_refs, logit)
            # Actually do the export into the destination path.
            logit(f"Exporting {get_mapping_name(mapping)}_{self.svg_name}")
            self.export.export(f"{get_mapping_name(mapping)}_{self.svg_name}", logit)
            reset_mapping(command_layers)
 
    def get_layer_refs(self) -> list:
        """
        Return the layers in the SVG
        """
        svg_layers = self.export.document.xpath('//svg:g[@inkscape:groupmode="layer"]', namespaces=inkex.NSS)
        layer_refs = []

        # Find all of our "valid" layers.
        for layer in svg_layers:
            label_attrib_name = LayerRef.get_layer_attrib_name(layer)
            if label_attrib_name not in layer.attrib:
                continue
            layer_refs.append(LayerRef(layer))

        # Create the layer hierarchy (children and parents).
        for layer in layer_refs:
            for other in layer_refs:
                for child in layer.source.getchildren():
                    if child is other.source:
                        layer.children.append(other)
                if layer.source.getparent() is other.source:
                    layer.parent = other

        return layer_refs
        
    
