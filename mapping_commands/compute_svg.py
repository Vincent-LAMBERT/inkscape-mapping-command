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
from svgutils.compose import *
from mapping_commands import CommandExport

from utils import *
from ref_and_specs import *
from configuration_file import *
from mg_maths import *

#######################################################################################################################

def get_command_names(mappings, logit):
    """
    Get all commands in mappings
    Each mapping has the form 
    """
    command_names = list()
    for mapping in mappings :
        for command in get_mapping_commands(mapping, logit) :
            if command not in command_names :
                command_names.append(command)
    return command_names

def add_command_to_layer(layer_ref, new_command, logit):
    """
    Add a command to a layer
    """
    # Find child of layer with 'mgrep-path-element' with 
    # the value of 'start-command', 'end-command' or 'command'
    start_command = layer_ref.source.find(f".//*[@mgrep-path-element='start-command']")
    end_command = layer_ref.source.find(f".//*[@mgrep-path-element='end-command']")
    command = layer_ref.source.find(f".//*[@mgrep-path-element='command']")
    
    commands = [start_command, end_command, command]
    
    for cmd in commands :
        if cmd is not None :
            # Insert the new command before the current command
            parent_cmd = cmd.getparent()
            parent_cmd.insert(parent_cmd.index(cmd), new_command)
        
    # The text origin and transform matrix is 
    # overwritten by the insertion. 
    # Thus we have to use markers and move each 
    # text to the corresponding location after 
    # the template insertion
    text_marker_pairs = get_text_marker_pairs(new_command, logit)
    logit(f"Text marker pairs : {text_marker_pairs}")
    for text, marker in text_marker_pairs :
        move_text_to_marker(text, marker, logit)
        
def get_text_marker_pairs(command, logit):
    """
    Get a list of text and marker pairs
    """
    text_marker_pairs = list()
    for text in command.xpath(".//svg:text", namespaces=inkex.NSS) :
        if 'mgrep-command' in text.attrib :
            text_type =  text.attrib['mgrep-command'].split(",")[1]
            for marker in command.xpath(".//svg:circle", namespaces=inkex.NSS) :
                if 'mgrep-command' in marker.attrib :
                    marker_type =  marker.attrib['mgrep-command'].split(",")[1]
                    if text_type == marker_type :
                        text_marker_pairs.append((text, marker))
    return text_marker_pairs

def move_text_to_marker(text, marker, logit):
    """
    Move a text to a marker position
    """    
    marker_position = np.array([float(marker.get('cx')), float(marker.get('cy'))])
    # Get the transform matrix of the text
    TS_matrix = get_transform_matrix(text, logit)
    # Change the translation part of the matrix
    # to match the marker position
    TS_matrix[:,2] = marker_position
    # Set the new transform matrix
    set_transform_matrix(text, TS_matrix)
    
    # Adjust the text-align style
    text_style = text.get('style')
    text_type =  text.attrib['mgrep-command'].split(",")[1].replace(" ", "")
    text_align = TEXT_ALIGNS[text_type]
    new_style = compute_new_style(text_style, {'text-align' : text_align}, logit)
    text.set('style', new_style)
    
def get_transform_matrix(element, logit):
    """
    Get the transform matrix of an element
    """
    # Get the transform attribute
    transform = element.get('transform')
    # Get the transform matrix
    TS_matrix = np.array(inkex.transforms.Transform(transform).matrix)
    return TS_matrix

def set_transform_matrix(element, TS_matrix):
    """
    Set the transform matrix of an element
    """
    transform = inkex.transforms.Transform()
    matrix = [[x for x in row] for row in TS_matrix]
    transform._set_matrix(matrix)
    # Set the new transform matrix
    element.set('transform', transform)

def reset_commands(layer_ref):
    """
    Reset the commands of a layer
    """
    # Remove all elements with the attribute 'mgrep-command' set to 'template'
    for cmd in layer_ref.source.xpath(f".//*[@mgrep-command='template']") :
        cmd.getparent().remove(cmd)
        
def compute_new_style(original_style, style_combination, logit) :
    """
    Compute the new style of the element
    """
    new_style = ""
    for style in original_style.split(";") :
        if style != "" :
            key, value = style.split(":")
            if key in style_combination and value!='none' and value!='None':
                new_style += f"{key}:{style_combination[key]};"
            else :
                new_style += f"{key}:{value};"
    return new_style

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
        layer_refs = self.get_document_layer_refs(logit)
        self.mg_layer_refs = get_mg_layer_refs(layer_refs, logit)
        
        # Get a dictionnary of the wanted diversified styles with their characteristics
        mappings = get_mappings(self.export.options.config, logit)
        # Get all commands in mappings
        command_names = get_command_names(mappings, logit)
        # Add the command icons to the svg
        self.command_template_ref = self.get_svg_layers_ref("./Icon.svg", logit)[0]
        self.icon_SVG_refs = self.get_icon_SVGs_refs(self.export.options.icon, command_names, logit)
        
        for mapping in mappings :
            self.change_mapping(mapping, logit)
            # Actually do the export into the destination path.
            logit(f"Exporting {get_mapping_name(mapping)}_{self.svg_name}")
            self.export.export(f"{get_mapping_name(mapping)}_{self.svg_name}", logit)
            self.reset_mapping()
    
    def change_mapping(self, mapping, logit) :
        """
        Change the mapping of the svg according to the mapping dictionnary
        and the command icons
        """
        for mg_charac, command in mapping :
           command_icon = self.create_command(command, logit)
           mg, charac = mg_charac
           for layer_ref in self.mg_layer_refs[mg][charac] :
                add_command_to_layer(layer_ref, command_icon, logit)
                
    def reset_mapping(self) :
        """
        Reset the mapping of the svg
        """
        for mg_layer_refs in self.mg_layer_refs.values() :
            for charac_layer_refs in mg_layer_refs.values() :
                for layer_ref in charac_layer_refs :
                    reset_commands(layer_ref)
    
    def create_command(self, command, logit) :
        """
        Create a command icon
        """
        # Copy the template
        new_command_document = etree.fromstring(etree.tostring(self.command_template_ref.source))
        # Replace the command texts by the command name
        for text in new_command_document.xpath('//svg:text', namespaces=inkex.NSS) :
            text.text = command
        
        # Hide the left and right texts
        left = new_command_document.xpath('//svg:text[@mgrep-command="text, left"]', namespaces=inkex.NSS)[0]
        right = new_command_document.xpath('//svg:text[@mgrep-command="text, right"]', namespaces=inkex.NSS)[0]
        
        # left.set("style", "display:none")
        # right.set("style", "display:none")
        
        # Get the centroid of the command icon template
        template = new_command_document.xpath('//svg:circle[@mgrep-icon="template"]', namespaces=inkex.NSS)[0]
        
        # Get all layers of the command icon
        icon = etree.fromstring(etree.tostring(self.icon_SVG_refs[command].source))
        # Get the centroid of the command icon
        icon_centroid = icon.xpath('//svg:circle[@mgrep-icon="centroid"]', namespaces=inkex.NSS)[0]
        
        # Get xml of the layer with the attribute 'mgrep-icon' = 'command'
        icon_xml = icon.xpath('//svg:g[@mgrep-icon="command"]', namespaces=inkex.NSS)[0]
        
        # Get translation to apply to the command icon to match the centroid of the command icon template
        template_point = np.array([float(template.get('cx')), float(template.get('cy'))])
        icon_centroid_point = np.array([float(icon_centroid.get('cx')), float(icon_centroid.get('cy'))])
        
        T_matrix = get_translation_matrix(icon_centroid_point, template_point)
        
        for xml in icon_xml.findall(".//{*}path") :
            parsed_path = svg.path.parse_path(xml.get("d"))
            parsed_path = apply_matrix_to_path(parsed_path, [], T_matrix, logit)
            xml.set('d', parsed_path.d())
        for xml in icon_xml.findall(".//{*}circle") :
            path_cx = xml.get("cx")
            path_cy = xml.get("cy")
            circle = compute_point_transformation(convert_to_complex(path_cx, path_cy), [], T_matrix, logit)
            xml.set("cx", str(circle.real))
            xml.set("cy", str(circle.imag))
            
        # Add child to the parent of the template layer
        # The +1 is to insert the icon above the template
        #element to make our icon visible
        parent = template.getparent()
        parent.insert(parent.index(template)+1, icon_xml)
        
        # Get the layer with the attribute 'mgrep-command' = 'template'
        # to be inserted in the svg
        new_command = new_command_document.xpath('//svg:g[@mgrep-command="template"]', namespaces=inkex.NSS)[0]
        
        return new_command
    
    def get_icon_SVGs_refs(self, icon_folder_path, command_names, logit):
        """
        Returns the command icon SVG template and the command icons
        """
        # Get the command icon SVG template
        commands = dict()
        
        for command in command_names :
            icon_SVG = self.get_svg_layers_ref(f"{icon_folder_path}/{command}.svg", logit)[0]
            commands[command] = icon_SVG
            
        return commands
    
    def get_document_layer_refs(self, logit) -> list:
        """
        Return the layers in the SVG
        """
        svg_layers = self.export.document.xpath('//svg:g[@inkscape:groupmode="layer"]', namespaces=inkex.NSS)
        return self.get_layer_refs(svg_layers) 

    def get_svg_layers_ref(self, file, logit) -> list:
        """
        Return the layers in the SVG
        """
        document = etree.parse(file)
        svg_layers = document.xpath('//svg:g[@inkscape:groupmode="layer"]', namespaces=inkex.NSS)
        return self.get_layer_refs(svg_layers)
        
    def get_layer_refs(self, svg_layers) -> list:
        """
        Return the layers in the SVG
        """
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