# Copyright 2015-2016 Open Source Robotics Foundation, Inc.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.


import os

from rosidl_cmake import convert_camel_case_to_lower_case_underscore
from rosidl_cmake import expand_template
from rosidl_cmake import extract_message_types
from rosidl_cmake import get_newest_modification_time
from rosidl_parser import parse_message_file
from rosidl_parser import parse_service_file
from rosidl_parser import validate_field_types

from rosidl_generator_cpp import MSG_TYPE_TO_CPP


def generate_typesupport_freertps_cpp(template_dir, pkg_name, ros_interface_files,
                                      ros_interface_dependencies, target_dependencies,
                                      additional_files, output_dir):
    mapping_msgs = {
        os.path.join(template_dir, 'msg__type_support.hpp.template'): '%s__type_support.hpp',
        os.path.join(template_dir, 'msg__type_support.cpp.template'): '%s__type_support.cpp',
    }

    mapping_srvs = {
        os.path.join(template_dir, 'srv__type_support.cpp.template'):
        '%s__type_support.cpp',
    }

    for template_file in mapping_msgs.keys():
        assert os.path.exists(template_file), 'Could not find template: ' + template_file

    for template_file in mapping_srvs.keys():
        assert os.path.exists(template_file), 'Could not find template: ' + template_file

    known_msg_types = extract_message_types(
        pkg_name, ros_interface_files, ros_interface_dependencies)

    functions = {
        'get_header_filename_from_msg_name': convert_camel_case_to_lower_case_underscore,
        'enforce_alignment': enforce_alignment,
        'enforce_read_alignment': enforce_read_alignment,
        'enforce_alignment_buffer_size': enforce_alignment_buffer_size,
        'get_alignment': get_alignment,
        'msg_type_to_cpp': msg_type_to_cpp,
    }
    # generate_dds_freertps_cpp() and therefore the make target depend on the additional files
    # therefore they must be listed here even if the generated type support files are independent
    latest_target_timestamp = get_newest_modification_time(
        target_dependencies + additional_files)

    for idl_file in ros_interface_files:
        extension = os.path.splitext(idl_file)[1]
        if extension == '.msg':
            spec = parse_message_file(pkg_name, idl_file)
            validate_field_types(spec, known_msg_types)
            subfolder = os.path.basename(os.path.dirname(idl_file))
            for template_file, generated_filename in mapping_msgs.items():
                generated_file = os.path.join(
                    output_dir, subfolder, 'freertps', generated_filename %
                    convert_camel_case_to_lower_case_underscore(spec.base_type.type))

                data = {'spec': spec, 'subfolder': subfolder}
                data.update(functions)
                expand_template(
                    template_file, data, generated_file,
                    minimum_timestamp=latest_target_timestamp)

        elif extension == '.srv':
            spec = parse_service_file(pkg_name, idl_file)
            validate_field_types(spec, known_msg_types)
            for template_file, generated_filename in mapping_srvs.items():
                generated_file = os.path.join(
                    output_dir, 'srv', 'freertps', generated_filename %
                    convert_camel_case_to_lower_case_underscore(spec.srv_name))

                data = {'spec': spec}
                data.update(functions)
                expand_template(
                    template_file, data, generated_file,
                    minimum_timestamp=latest_target_timestamp)

    return 0


# TODO(jacquelinekay) use bit shifting/& instead of mod/multiplication!!!
def enforce_alignment(required_alignment, indent=2):
    print("""{0}if ((_p - _buf) % {1} != 0) {{
{0}  _p += (static_cast<uint32_t>(floor((_p - _buf) / {1}) + 1)) * {1} - (_p - _buf);
{0}}}""".format(' ' * indent, required_alignment))


def enforce_read_alignment(required_alignment, indent=2):
    print("""{0}if ((*_p - initial_p) % {1} != 0) {{
{0}  uint8_t pad = (static_cast<uint32_t>(
{0}      floor((*_p - initial_p) / {1})) + 1) * {1} - (*_p - initial_p);
{0}  if (*_len < pad) {{
{0}    return false;
{0}  }}
{0}  *_p += pad;
{0}  *_len -= pad;
{0}}}""".format(' ' * indent, required_alignment))


def enforce_alignment_buffer_size(required_alignment, indent=2):
    print("""{0}if (_len % {1} != 0) {{
{0}  _len += (static_cast<uint32_t>(floor(_len / {1})) + 1) * {1} - _len;
{0}}}""".format(' ' * indent, required_alignment))


primitive_type_alignment = {}
primitive_type_alignment['bool'] = 1
primitive_type_alignment['byte'] = 1
primitive_type_alignment['uint8'] = 1
primitive_type_alignment['char'] = 1
primitive_type_alignment['int8'] = 1
primitive_type_alignment['uint16'] = 2
primitive_type_alignment['int16'] = 2
primitive_type_alignment['uint32'] = 4
primitive_type_alignment['int32'] = 4
primitive_type_alignment['uint64'] = 8
primitive_type_alignment['int64'] = 8
primitive_type_alignment['float32'] = 4
primitive_type_alignment['float64'] = 8


def get_alignment(field_str):
    return primitive_type_alignment[field_str]


def msg_type_to_cpp(msg_type):
    return MSG_TYPE_TO_CPP[msg_type]


def uncamelcase(camelcase):
    lower = ''
    upper_run_len = 0
    for idx in range(0, len(camelcase)):
        if (camelcase[idx].isupper()):
            next_lower = idx < len(camelcase) - 1 and camelcase[idx + 1].islower()
            if (idx > 0 and upper_run_len == 0) or (idx > 1 and next_lower):
                lower += '_'
            lower += camelcase[idx].lower()
            upper_run_len += 1
        else:
            lower += camelcase[idx]
            upper_run_len = 0
    return lower


def print_uncamelcase(c):
    print('%s -> %s' % (c, uncamelcase(c)))
