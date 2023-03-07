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
    
TAP = "tap"
SWIPE = "swipe"
FLEX = "flex"
TIP = "tip"
MIDDLE = "middle"
BASE = "base"
UP = "up"
DOWN = "down"
MICROGESTURES = [TAP, SWIPE, FLEX]
TAP_CHARACTERISTICS = [TIP, MIDDLE, BASE]
SWIPE_CHARACTERISTICS = [UP, DOWN]
FLEX_CHARACTERISTICS = [UP, DOWN]
MICROGESTURE_CHARACTERISTICS = { TAP : TAP_CHARACTERISTICS,
                                 SWIPE : SWIPE_CHARACTERISTICS,
                                 FLEX : FLEX_CHARACTERISTICS}

ACTUATOR="actuator"
RECEIVER="receiver"
TRAJECTORY="trajectory"
ELEMENTS = [ACTUATOR, RECEIVER, TRAJECTORY]
TAP_ELEMENTS = [TRAJECTORY, ACTUATOR, RECEIVER]
SWIPE_ELEMENTS = [TRAJECTORY, ACTUATOR]
FLEX_ELEMENTS = [TRAJECTORY]
MG_ELEMENTS = { TAP : TAP_ELEMENTS,
                SWIPE : SWIPE_ELEMENTS,
                FLEX : FLEX_ELEMENTS}
PUNCTUAL = "punctual"
PATH = "path"
ELEMENT_SVG_TYPE_CORRESPONDANCE = { ACTUATOR : PUNCTUAL,
                                    RECEIVER : PUNCTUAL,
                                    TRAJECTORY : PATH}
TRAJ_START="traj-start"
TRAJ_END="traj-end"
MARKER_TYPES_CORRESPONDANCE = { TAP : [TRAJ_START, TRAJ_END, ACTUATOR, RECEIVER],
                                SWIPE : [TRAJ_START, TRAJ_END, ACTUATOR],
                                FLEX : [TRAJ_START, TRAJ_END]}
MARKER_TYPES=[TRAJ_START, TRAJ_END, ACTUATOR, RECEIVER]

COORDINATES = "coordinates"
CIRCLE_RADIUS = "r"

PNG="png"
JPG="jpg"
PDF="pdf"
SVG="svg"

DESIGN="design"
TRACE="trace"
TRACE_START_BOUND="trace-start-bound"
TRACE_END_BOUND="trace-end-bound"
COMMAND="command"
START_COMMAND="start-command"
END_COMMAND="end-command"
PATH_BASED_TYPES = [DESIGN, TRACE]
CIRCLE_BASED_TYPES = [TRACE_START_BOUND, TRACE_END_BOUND, COMMAND, START_COMMAND, END_COMMAND]

NAME = "name"
MAPPING = "mapping"

START = 'start'
END = 'end'
CONTROL_1 = 'control1'
CONTROL_2 = 'control2'

STROKE = "stroke"
FILL = "fill"
COLOR_BASED_STYLES = [FILL, STROKE]
RED = 'red'
BLUE = 'blue'
GREEN = 'green'
COLORS = { RED : "#FF0000",
           BLUE : "#0000FF",
           GREEN : "#00FF00"}

STROKE_WIDTH = "stroke-width"
PATH_SCALE = "path-scale"
THIN = "thin"
MEDIUM = "medium"
THICK = "thick"
SIZES = { THIN : 0.75,
          MEDIUM : 1,
          THICK : 1.5}

STYLES = COLOR_BASED_STYLES + [STROKE_WIDTH]
STYLE_CHARACTERISTICS = { STROKE : COLORS,
                          FILL : COLORS,
                          STROKE_WIDTH : SIZES}


BANANA = "banana"
PINEAPPLE = "pineapple"
CHERRY = "cherry"
KIWI = "kiwi"
BLACKBERRY = "blackberry"
PLUM = "plum"
WATERMELON = "watermelon"
COMMANDS = [BANANA, PINEAPPLE, CHERRY, KIWI, BLACKBERRY, PLUM, WATERMELON]

LEFT = "left"
RIGHT = "right"
BELOW = "below"
START = "start"
CENTER = "center"
END = "end"
TEXT_ALIGNS = {RIGHT : START, LEFT : END, BELOW : CENTER}

MIDDLE = "middle"
TEXT_ANCHORS = {RIGHT : START, LEFT : END, BELOW : MIDDLE}

#######################################################################################################################

def get_microgestures_with_charac(combinations) :
    """
    Return the (microgestures, characteristic) unique tuples from the given combinations
    """
    mg_characs = []
    for combination in combinations :
        for mg_charac in combination :
            if mg_charac not in mg_characs :
                mg_characs.append(mg_charac)
    return mg_characs