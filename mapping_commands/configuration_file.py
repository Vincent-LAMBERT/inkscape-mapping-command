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

import itertools
import csv
import os
import sys

from utils import *

#######################################################################################################################

def compute_wanted_mappings() :
    """
    Return the wanted mappings.
    By default, returns every command that
    can be done with a microgesture in an dictionnary with the form
    [((microgesture1, characteristic1), command1), ((microgesture2, characteristic2), command2), ...]
    """
    wanted_mappings = []
    
    for microgesture in MICROGESTURES :
        for characteristic in MICROGESTURE_CHARACTERISTICS[microgesture] :
            for command in COMMANDS :
                wanted_mappings.append(((microgesture, characteristic), command))
    
    return wanted_mappings

def compute_all_mappings(mappings) :
    """
    Return all the command mappings corresponding to the given list
    """
    mg_characs = []
    commands = []
    for mg_charac, command in mappings:
        if mg_charac not in mg_characs:
            mg_characs.append(mg_charac)
        if command not in commands:
            commands.append(command)
            
    return [list(zip(mg_characs, p)) for p in itertools.permutations(commands)]

def get_mapping_name(mapping) :
    """
    Return a name to describe the given mapping
    of the form [((microgesture1, characteristic1), command1), 
    (microgesture2, characteristic2), command2), ...]}
    """
    name = ""
    for mg_charac, command in mapping:
        name += f"{mg_charac[0]}_{mg_charac[1]}-{command}_"
    return name[:-1]


def compute_default_mappings() :
    """
    Return the command mappings corresponding to the default configuration
    """
    return [["tap_tip-banana", "tap_middle-watermelon", "tap_base-blackberry", "swipe_up-kiwi", "swipe_down-plum", "flex_up-cherry", "flex_down-pineapple"], ["tap_tip-pineapple", "tap_middle-blackberry", "tap_base-cherry", "swipe_up-plum", "swipe_down-banana", "flex_up-kiwi", "flex_down-watermelon"], ["tap_tip-cherry", "tap_middle-pineapple", "tap_base-blackberry", "swipe_up-watermelon", "swipe_down-kiwi", "flex_up-plum", "flex_down-banana"], ["tap_tip-kiwi", "tap_middle-cherry", "tap_base-watermelon", "swipe_up-banana", "swipe_down-plum", "flex_up-pineapple", "flex_down-blackberry"], ["tap_tip-blackberry", "tap_middle-watermelon", "tap_base-plum", "swipe_up-pineapple", "swipe_down-kiwi", "flex_up-banana", "flex_down-cherry"], ["tap_tip-plum", "tap_middle-blackberry", "tap_base-banana", "swipe_up-watermelon", "swipe_down-cherry", "flex_up-kiwi", "flex_down-pineapple"], ["tap_tip-watermelon", "tap_middle-plum", "tap_base-blackberry", "swipe_up-kiwi", "swipe_down-cherry", "flex_up-pineapple", "flex_down-banana"]]

def get_mappings(file_path, logit) :
    """
    Return the command mappings corresponding to the given configuration file if it exists and is valid
    """
    logit(f"The given file is {file_path}")
    if file_path[-4:] != ".csv" :
        logit(f"ERROR: The configuration file must be a csv file. The given file is {file_path}")
        return compute_default_mappings()
    else :
        logit(f"Loading the configuration file {file_path}")
        return get_mappings_from_file(file_path)

def get_mappings_from_file(file_path) :
    """
    Return the command mappings corresponding to the given configuration file
    """
    mappings = []
    with open(file_path, 'r') as csvfile:
        reader = csv.reader(csvfile, delimiter=',')
        for row in reader:
            combination = []
            for mg_command in row:
                mg_charac, command = mg_command.split('-')
                mg, charac = mg_charac.split('_')
                combination.append(((mg, charac), command))
            mappings.append(combination)
    return mappings

#######################################################################################################################

def create_configuration_file(mappings, file_path="./configuration/config_export_mapping_rep.csv") :
    """
    Creates the configuration file for the mappings
    """
    output_path = os.path.expanduser(file_path)
    output_path = os.path.dirname(output_path)
    if not os.path.exists(os.path.join(output_path)):
        os.makedirs(os.path.join(output_path))     
    with open(file_path, 'w', newline='') as csvfile:
        writer = csv.writer(csvfile, delimiter=',')
        for combination in mappings:
            row = ["{0}_{1}-{2}".format(mg_charac[0], mg_charac[1], command) for mg_charac ,command in combination]
            print(row)
            writer.writerow(row)

#######################################################################################################################

def _main():
    mappings = compute_default_mappings()
    if len(sys.argv) > 1 :
        create_configuration_file(mappings, sys.argv[1])
    else :
        create_configuration_file(mappings)

if __name__ == "__main__":
    _main()

#######################################################################################################################