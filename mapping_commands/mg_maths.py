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
import inkex.bezier
import numpy as np
import svg.path

from utils import *
from shapely.geometry import Point, Polygon

#######################################################################################################################
        

def convert_to_complex(x, y) :
    """
    Convert a pair of floats to a complex number
    """
    return np.array([x, y]).astype(float).view(np.complex128)[0]

def convert_from_complex(p) :
    """
    Convert a complex number to a pair of floats
    """
    return np.array([p.real, p.imag]).astype(float)

def vector(p1, p2) :
    """
    Computes the vector resulting from the given points
    """
    return np.array([p2[0] - p1[0], p2[1] - p1[1]])
    
def get_scaling_matrix(vec1, vec2) :
    """
    Compute the scaling matrix from vec1 to vec2
    
    CAUTION : is it is intended to be used with a 
    translation matrix, the scaling matrix
    has a 3x3 dimension
    """
    scaling_factor = np.linalg.norm(vec2) / np.linalg.norm(vec1)
    return np.array([[scaling_factor, 0, 0],
                     [0, scaling_factor, 0],
                     [0, 0, 1]])

def get_translation_matrix(vec1, vec2) :
    """
    Compute the translation matrix from vec1 to vec2   
    """
    if isinstance(vec1, list) :
        vec1 = np.array(vec1)
    if isinstance(vec2, list) :
        vec2 = np.array(vec2)
    translation_vector = vec2 - vec1
    return np.array([[1, 0, translation_vector[0]],
                     [0, 1, translation_vector[1]],
                     [0, 0, 1]])

def get_translation_matrix_from_vector(translation_vector) :
    """
    Compute the translation matrix from vec1 to vec2   
    """
    return np.array([[1, 0, translation_vector[0]],
                     [0, 1, translation_vector[1]],
                     [0, 0, 1]])
    
def get_rotation_matrix(vec1, vec2) :
    """
    Compute the rotation matrix from vec1 to vec2 
    with the signed angle computed with arctan
    
    CAUTION : is it is intended to be used with a 
    translation matrix, the scaling matrix
    has a 3x3 dimension
    """
    theta = np.arctan2(vec2[1], vec2[0]) - np.arctan2(vec1[1], vec1[0])
    return np.array([[np.cos(theta), -np.sin(theta), 0],
                     [np.sin(theta), np.cos(theta), 0],
                     [0, 0, 1]])
    
def apply_matrix_to_path(parsed_path, bound_zones, TRS_matrix, logit) :
    """
    Apply the TRS_matrix to the given path
    """
    # Make a copy of the path
    parsed_path_copy = svg.path.parse_path(parsed_path.d())
    for path_segment in parsed_path_copy :
        path_segment.start = compute_point_transformation(path_segment.start, bound_zones, TRS_matrix, logit)
        path_segment.end = compute_point_transformation(path_segment.end, bound_zones, TRS_matrix, logit)
        if hasattr(path_segment, CONTROL_1):
            path_segment.control1 = compute_point_transformation(path_segment.control1, bound_zones, TRS_matrix, logit)
        if hasattr(path_segment, CONTROL_2):
            path_segment.control2 = compute_point_transformation(path_segment.control2, bound_zones, TRS_matrix, logit)
    return parsed_path_copy
    
def apply_matrix_to_circle(parsed_circle, bound_zones, TRS_matrix, logit) :
    """
    Apply the TRS_matrix to the given circle
    """
    # Make a copy of the circle
    parsed_circle_copy = parsed_circle.copy()
    parsed_circle_copy[COORDINATES] = compute_point_transformation(parsed_circle_copy[COORDINATES], bound_zones, TRS_matrix, logit)
    return parsed_circle_copy

def apply_matrix_to_point(point, bound_zones, TRS_matrix, logit) :
    """
    Apply the TRS_matrix to the given point
    """
    return compute_point_transformation(point, bound_zones, TRS_matrix, logit)

def point_in_bound_zones(point, bound_zones) :
    """
    Check if the given point is in the given bound zones
    """
    for bound_zone in bound_zones :
        if point_in_bound_zone(point, bound_zone) :
            return True
    return False

def point_in_bound_zone(point, bound_zone) :
    """
    Check if the given point is in the given bound zone
    """
    # The bound zone is a circle of center bound_zone[COORDINATES] and radius bound_zone[CIRCLE_RADIUS]
    center = convert_from_complex(bound_zone[COORDINATES])
    radius = float(bound_zone[CIRCLE_RADIUS])
    # Check if the point is in the circle
    if np.linalg.norm(vector(center, point)) <= radius :
        return True
    return False

def compute_point_transformation(point, bound_zones, TRS_matrix, logit) :
    """
    Apply the TRS_matrix to the given point
    Correct the transformation by a back-to-origin translation
    based on the centroid of the TTRT zone the point is in if it is in a TTRT zone
    """
    if point is not None :
        converted_point = convert_from_complex(point)
        old_point = np.array([converted_point[0], converted_point[1], 1]).T

        # Bound zones handling
        if point_in_bound_zones(converted_point, bound_zones) :
            for bound_zone in bound_zones :
                if point_in_bound_zone(converted_point, bound_zone) :
                    center_bound_zone = convert_from_complex(bound_zone[COORDINATES])
                    translation_vector = center_bound_zone - converted_point
                    center_bound_zone = np.array([center_bound_zone[0], center_bound_zone[1], 1]).T
                    fixed_distance = np.linalg.norm(translation_vector)
                    
                    # Apply the matrix to the points
                    center_bound_zone = (TRS_matrix @ center_bound_zone).T  
                    new_point = (TRS_matrix @ old_point).T
                    
                    # # Adjust the new point to be at the same distance from the center of the bound zone
                    new_translation_vector = new_point - center_bound_zone
                    new_distance = np.linalg.norm(new_translation_vector)
                    if new_distance != 0 :
                        new_translation_vector = new_translation_vector / np.linalg.norm(new_translation_vector) * fixed_distance
                        new_point = center_bound_zone + new_translation_vector   
                    break
        else :
            # Apply the matrix to the point
            new_point = (TRS_matrix @ old_point).T
            
        # Convert the point back to a complex number
        new_point = convert_to_complex(new_point[0], new_point[1])
        return new_point
    return None

def compute_translation(parsed_path, new_position, logit) :
    """
    Move the parsed path so that its centroid matches the new_centroid_position
    """
    parsed_path_centroid = path_centroid(parsed_path)
    translation_matrix = get_translation_matrix(parsed_path_centroid, new_position)
    return apply_matrix_to_path(parsed_path, {}, translation_matrix, logit)

def get_TRS_matrix(path, reference_vector, start_position, logit) :
    """
    Compute the matrixes to apply to the path to match the reference_vector
    and the start_position
    """
    # Copy the path given to not alterate it
    # svg.path.parse_path does not integrate a copy method
    # so we have to parse the path.d() string
    reference_path = svg.path.parse_path(path.d())
    ## Translate to the origin before scaling and rotating
    # Actualize the starting point position
    start_point = convert_from_complex(reference_path[0].start)
    # Translate each position
    translation_matrix_to_origin = get_translation_matrix(start_point, [0, 0])
    # Apply the matrix to the reference_path
    reference_path = apply_matrix_to_path(reference_path, {}, translation_matrix_to_origin, logit)
    
    ## Scale and rotate the reference_path
    # Compute the initial reference_path vector from actualized start and end positions
    start_point = convert_from_complex(reference_path[0].start)
    end_point = convert_from_complex(reference_path[-1].end)
    initial_path_vector = vector(start_point, end_point)
    # Compute the scaling matrix
    scaling_matrix = get_scaling_matrix(initial_path_vector, reference_vector)
        
    # Compute the rotation matrix
    rotation_matrix = get_rotation_matrix(initial_path_vector, reference_vector)
    # Apply the matrixes to the reference_path
    reference_path = apply_matrix_to_path(reference_path, {}, rotation_matrix @ scaling_matrix, logit)
    
    # ## Translate to the final position
    # # Actualize the starting point position
    start_point = convert_from_complex(reference_path[0].start)
    # Compute the translation matrix
    translation_matrix = get_translation_matrix(start_point, start_position)
    # Compute the final matrix
    TRS_matrix = translation_matrix @ rotation_matrix @ scaling_matrix @ translation_matrix_to_origin
    return TRS_matrix

def compute_transformation(parsed_paths, parsed_circles, reference_vector, start_position, logit, trace_path=False, trace_end_path=False) :
    """
    Move the parsed_paths so that the first parsed_path 
    ends match the reference_vector
    """
    # If no trace_path is given, use the design path as a reference
    # CAUTION: It MUST be a stroke path (as any trace) to work
    if trace_path==False :
        trace_path = parsed_paths[DESIGN]
    
    TRS_matrix = get_TRS_matrix(trace_path, reference_vector, start_position, logit)
    
    # The design points being in the bounds of a trace do not scale. 
    # Instead, they are translated and rotated according to the 
    # center of the bound zone
    bound_zones = []
    if TRACE_START_BOUND in parsed_circles.keys() :
        bound_zones.append(parsed_circles[TRACE_START_BOUND])
    if TRACE_END_BOUND in parsed_circles.keys() :
        bound_zones.append(parsed_circles[TRACE_END_BOUND])    
    
    transformed_paths = {}
    transformed_circles = {}
    
    for path_name in parsed_paths.keys() :
        transformed_paths[path_name] = apply_matrix_to_path(parsed_paths[path_name], bound_zones, TRS_matrix, logit)
    
    for circle_name in parsed_circles :
        transformed_circles[circle_name] = apply_matrix_to_circle(parsed_circles[circle_name], bound_zones, TRS_matrix, logit)
    
    return transformed_paths, transformed_circles
    
#######################################################################################################################

def path_centroid(parsed_path):
    """
    Retrieve the points of the path and compute the centroid of the polygon they form
    """
    segment_ends = [convert_from_complex(seg.end) for seg in parsed_path]
    if len(segment_ends) > 1 :
        polygon = Polygon([Point(seg) for seg in segment_ends])
        centroid = [polygon.centroid.coords[0][0], polygon.centroid.coords[0][1]]
    else :
        centroid = segment_ends[0]
    return centroid
    