import yaml
import xml.etree.ElementTree as ET
from string_utils import analyze_string, find_linked_path

def read_ros_yaml(file_path):
    """Read and return the contents of a YAML file."""
    with open(file_path, 'r') as file:
        # Using safe_load() to avoid potential security risks
        data = yaml.safe_load(file)
    return data['/**']['ros__parameters']

def parse_node_param_tag(node_param_tag, base_namespace, context):
    if node_param_tag.get('name') is None:
        return context

def parse_node_tag(node_tag, base_namespace, context, local_context):
    pkg = analyze_string(node_tag.get('pkg'), context, local_context, base_namespace)
    exec = analyze_string(node_tag.get('exec'), context, local_context, base_namespace)
    local_parameters = {}
    local_parameters["__param_files"] = []
    # print(context, base_namespace)
    for child in node_tag:
        if child.tag == 'param':
            if child.get('name') is not None:
                local_parameters[child.get('name')] = \
                    analyze_string(child.get('value'), context, local_context, base_namespace)
            if child.get('from') is not None:
                path = analyze_string(child.get('from'), context, local_context, base_namespace)
                path = find_linked_path(path)
                if path.endswith('_empty.param.yaml'):
                    continue
                print(path, child.get('from'))
                local_parameters["__param_files"].append(path)
                local_parameters.update(read_ros_yaml(path))
    # except Exception as e:
    #     print(e)
    #     print(context['sensor_launch_pkg'], base_namespace, pkg, exec)
    #     print(context.keys(), base_namespace)
    #     exit()
    print(f"Launching node: {pkg} {exec}")
    # print(local_parameters)
    