from ament_index_python.packages import get_package_share_directory
import re
import os

patterns = {
    'var': r'\$\((var) ([^\)]+)\)',
    'env': r'\$\((env) ([^\s]+)(?:\s+([^\)]+))?\)', 
    'eval': '\$\((eval) ([^\)]+)\)',
    'find-pkg-share': r'\$\((find-pkg-share) ([^\)]+)\)',
}

def clean_eval_variables(string):
    return string.replace('"', "").replace("'", "").strip()

def analyze_string(input_string, context, local_context, base_namespace):
    """Resolve substitutions recursively in a given string."""
    
    def replace_match(match):
        # Determine type and execute corresponding logic
        if match.group(1) == 'var':
            variable_name = analyze_string(match.group(2), context, local_context, base_namespace)
            var_value = local_context.get(variable_name, None)
            if var_value is None:
                var_value = context.get(os.path.join(base_namespace, variable_name))
            return var_value
        elif match.group(1) == 'env':
            var_name = analyze_string(match.group(2), context, local_context, base_namespace)
            default_value = analyze_string(
                match.group(3) if match.group(3) is not None else '', context, local_context, base_namespace)
            return os.getenv(var_name, default_value)
        elif match.group(1) == 'eval':
            expression = analyze_string(match.group(2), context, local_context, base_namespace)
            # deal with "=="
            variables = expression.split("==")
            if len(variables) == 2:
                return str(clean_eval_variables(variables[0]) == clean_eval_variables(variables[1]) )
            variables = expression.split(">=")
            if len(variables) == 2:
                return str(clean_eval_variables(variables[0]) >= clean_eval_variables(variables[1]) )
            variables = expression.split("+")
            if len(variables) == 2:
                return str(clean_eval_variables(variables[0]) + clean_eval_variables(variables[1]))

        elif match.group(1) == 'find-pkg-share':
            package_name = analyze_string(match.group(2), context, local_context, base_namespace)  # Recursively resolve inner substitutions
            package_dir = get_package_share_directory(package_name)
            return package_dir
        
        return ''

    # Loop to ensure all substitutions are resolved
    for key, pattern in patterns.items():
        while True:
            old_string = input_string
            input_string = re.sub(pattern, replace_match, input_string)
            # Stop if no more changes are made
            if input_string == old_string:
                break

    return input_string


def find_linked_path(path):
    if os.path.islink(path):
        linked_path = os.readlink(path)
        return linked_path
    else:
        return path