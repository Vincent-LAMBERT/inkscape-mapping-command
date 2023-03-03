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

import sys
sys.path.append('/usr/share/inkscape/extensions')
import inkex

import copy
import logging
import os
import tempfile
import subprocess

from compute_svg import *

#######################################################################################################################

class CommandExport(inkex.Effect):
    """
    The core logic of exporting combinations of layers as images.
    """

    def __init__(self):
        super().__init__()
        self.arg_parser.add_argument("--path", type=str, dest="path", default="~/", help="The directory to export into")
        self.arg_parser.add_argument('-f', '--filetype', type=str, dest='filetype', default='png', 
                                     help='Exported file type. One of [png|jpeg|pdf]')
        self.arg_parser.add_argument("--dpi", type=float, dest="dpi", default=90.0, help="DPI of exported image")
        self.arg_parser.add_argument("--temp", type=inkex.Boolean, dest="temp", default=True, help="SVG files used to export are temporary")
        self.arg_parser.add_argument("--config", type=str, dest="config", default="~/", help="Configuration file used to export (Optional)")
        self.arg_parser.add_argument("--debug", type=inkex.Boolean, dest="debug", default=False, help="Debug mode (verbose logging)")
    
    def effect(self):
        """
        Execute the effect in the ComputeSVG class to keep the code clean and structured.
        """
        compute = ComputeSVG(self)
        compute.compute()
    
 ### Export functions ###
            
    def export(self, label, logit):
        """
        Export the representation
        """
        output_path = os.path.expanduser(self.options.path)
        if not os.path.exists(os.path.join(output_path)):
            logit(f"Creating directory path {output_path} because it does not exist")
            os.makedirs(os.path.join(output_path))            
            
        with CustomNamedTemporaryFile(suffix=".{SVG}") as fp_svg:
            if self.options.temp:
                # logit(f"Writing SVG to temporary location {svg_path}")
                svg_path = fp_svg.name
            else :
                svg_path = os.path.join(output_path, f"{label}.{SVG}")
            
            # Export to SVG
            doc = copy.deepcopy(self.document)
            doc.write(svg_path)
            
            # Export to filetype            
            if self.options.filetype == PNG or self.options.filetype == PDF :
                filetype_path = os.path.join(output_path, f"{label}.{self.options.filetype}")
                command = f"inkscape --export-type=\"{self.options.filetype}\" -d {self.options.dpi} --export-filename=\"{filetype_path}\" \"{svg_path}\""
                if os.name == "nt":
                    p = subprocess.Popen(command, shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
                else :
                    p = subprocess.Popen(command.encode("utf-8"), shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
                p.wait()
            
            if self.options.filetype == JPG :
                with CustomNamedTemporaryFile(suffix=".{PNG}") as png_temp_file:
                    command = f"inkscape --export-type=\"{PNG}\" -d {self.options.dpi} --export-filename=\"{png_temp_file.name}\" \"{svg_path}\""
                    jpg_path = os.path.join(output_path, f"{label}.{JPG}")
                    command = f"convert \"{png_temp_file.name}\" \"{jpg_path}\""
                    if os.name == "nt":
                        p = subprocess.Popen(command, shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
                    else :
                        p = subprocess.Popen(command.encode("utf-8"), shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
                    p.wait()
            

######################################################################################################################
    

class CustomNamedTemporaryFile: 
    """
    MODIFIED FROM : https://stackoverflow.com/questions/23212435/permission-denied-to-write-to-my-temporary-file
    This custom implementation is needed because of the following limitation of tempfile.NamedTemporaryFile:

    > Whether the name can be used to open the file a second time, while the named temporary file is still open,
    > varies across platforms (it can be so used on Unix; it cannot on Windows NT or later).
    """
    def __init__(self, mode='wb', suffix="", delete=True):
        self._mode = mode
        self._delete = delete
        self.suffix = suffix

    def __enter__(self):
        # If OS is Windows, use a the CustomNamedTemporaryFile.
        if os.name == "nt":
            file_name = os.path.join(tempfile.gettempdir(), os.urandom(24).hex())+self.suffix
            # Ensure the file is created
            open(file_name, "x").close()
            # Open the file in the given mode
            self._tempFile = open(file_name, self._mode)
        else : # Otherwise, use the standard NamedTemporaryFile.
            self._tempFile = tempfile.NamedTemporaryFile(suf)
        return self._tempFile

    def __exit__(self, exc_type, exc_val, exc_tb):
        self._tempFile.close()
        if self._delete:
            os.remove(self._tempFile.name)
    
    def close(self):
        self._tempFile.close()
        if self._delete:
            os.remove(self._tempFile.name)
    

#######################################################################################################################

def _main():
    logging.warning(f"Running Python interpreter: {sys.executable}")
    effect = DiversifyExport()
    effect.run()
    exit()

if __name__ == "__main__":
    _main()

#######################################################################################################################