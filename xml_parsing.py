import xml.etree.ElementTree as ET
from copy import deepcopy
import os
from string_utils import analyze_string, find_linked_path
from tree_utils import LaunchTree
from launch_node_utils import parse_node_tag
from typing import List, Optional


def check_if_run(tag: ET.Element, base_name: dict, context: dict, local_context: dict):
    """Many tag has a if and unless attribute, this function checks if the tag should be run or not."""
    if tag.get("if"):
        if_value = analyze_string(tag.get("if"), context, local_context, base_name)
        if_value = if_value.lower() == "true"
        if not if_value:
            return False
    if tag.get("unless"):
        unless_value = analyze_string(
            tag.get("unless"), context, local_context, base_name
        )
        unless_value = unless_value.lower() == "true"
        if unless_value:
            return False
    return True


def process_include_tag(
    include_tag: ET.Element,
    context: dict,
    local_context: dict,
    base_namespace: str,
    group_base_namespace: Optional[str] = None,
):
    """Process the include tag, which includes another XML file.

    include_tag: The include XML node tag to process
    context: The arugments and variables context of the current XML file, which is defined by the arg tag and will be passed to the included file
    local_context: The local variable context of the current XML file, which is defined by the let tag
    base_namespace: The current namespace of the XML file
    group_base_namespace: The namespace of the current group tag (affect the namespace of the included file)
    """
    if group_base_namespace is None:
        group_base_namespace = base_namespace
    included_file = include_tag.get("file")
    included_file = analyze_string(
        included_file, context, local_context, base_namespace
    )
    included_file = find_linked_path(included_file)

    argument_dict = dict()
    # temp_context = dict()
    for child in include_tag:
        if child.tag == "arg":
            value = analyze_string(
                child.get("value"), context, local_context, base_namespace
            )
            name = analyze_string(
                os.path.join(group_base_namespace, child.get("name")),
                context,
                local_context,
                base_namespace,
            )
            if name == "config_file":
                print("we get config_file", child.get("value"))
            print(name, value)
            argument_dict[name] = value
    temp_context = deepcopy(context)
    temp_context.update(argument_dict)
    if included_file:
        print(f"Reading included file: {included_file}")
        if included_file.endswith(".launch.xml"):
            print(temp_context)
            return parse_xml(included_file, group_base_namespace, temp_context)
    return context


def parse_argument_tag(
    argument_tag: ET.Element, base_namespace: str, context: dict, local_context: dict
):
    argument_name = os.path.join(base_namespace, argument_tag.get("name"))
    if argument_tag.get("default"):
        if argument_name not in context:
            if argument_name == "launch_driver":
                print(
                    "-------------------------we get launch_driver",
                    argument_tag.get("default"),
                )
            context[argument_name] = analyze_string(
                argument_tag.get("default"), context, local_context, base_namespace
            )
    return context


def parse_let_tag(
    let_tag: ET.Element, base_namespace: str, context: dict, local_context: dict
):
    argument_name = let_tag.get("name")
    if let_tag.get("value"):
        local_context[argument_name] = analyze_string(
            let_tag.get("value"), context, local_context, base_namespace
        )
    return context


def parse_group_tag(
    group_tag: ET.Element,
    base_namespace: str,
    context: dict,
    local_context: dict,
    parent_file_space: Optional[str] = None,
):
    if parent_file_space is None:
        parent_file_space = base_namespace
    # find the push-ros-namespace tag inside the children
    group_base_namespace = deepcopy(base_namespace)
    for child in group_tag:
        if child.tag == "push-ros-namespace":
            if child.get("namespace").strip() == "/":
                continue
            group_base_namespace = (
                f"{base_namespace}/{child.get('namespace').strip('/')}"
            )
            print(f"Setting ROS namespace to {group_base_namespace} inside group")

    ## find all other children
    for child in group_tag:
        process_tag(
            child,
            base_namespace,
            context,
            local_context,
            group_base_namespace=group_base_namespace,
        )

    if group_base_namespace != base_namespace:
        print(f"Exiting group with namespace {group_base_namespace}")
    return context


def process_tag(
    tag: ET.Element,
    base_namespace: str,
    context: dict,
    local_context: dict,
    group_base_namespace: Optional[str] = None,
):
    if group_base_namespace is None:
        group_base_namespace = base_namespace
    if not check_if_run(tag, base_namespace, context, local_context):
        return context

    if tag.tag == "arg":
        context = parse_argument_tag(tag, base_namespace, context, local_context)
    elif tag.tag == "let":
        context = parse_let_tag(tag, base_namespace, context, local_context)
    elif tag.tag == "group":
        context = parse_group_tag(tag, base_namespace, context, local_context)
    elif tag.tag == "include":
        context = process_include_tag(
            tag, context, local_context, base_namespace, group_base_namespace
        )
    elif tag.tag == "node":
        context = parse_node_tag(tag, base_namespace, context, local_context)
    return context


def parse_xml(file_path: str, namespace: str = "", context: dict = {}):
    """Recursively parse XML files, handling <include> tags. For each file, the namespace should be the same"""
    full_path = os.path.join(file_path)
    tree = ET.parse(full_path)
    root = tree.getroot()

    # Process each node in the XML
    local_context = dict()
    for tag in root:
        process_tag(tag, namespace, context, local_context)
    return context


if __name__ == "__main__":
    # Start parsing from the main XML file
    main_file = "/home/ukenryu/autoware/src/launcher/autoware_launch/autoware_launch/launch/logging_simulator.launch.xml"  # Update this path to your main XML file
    context_tree = LaunchTree()
    context = dict()
    context["__tree__"] = context_tree

    ## arguments
    context["vehicle_model"] = "sample_vehicle"
    context["sensor_model"] = "sample_sensor_kit"
    context = parse_xml(main_file, context=context)
    print(context)
