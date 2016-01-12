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

import rosidl_parser
from rosidl_cmake import convert_camel_case_to_lower_case_underscore
from rosidl_cmake import expand_template
from rosidl_cmake import extract_message_types
from rosidl_cmake import get_newest_modification_time
from rosidl_parser import parse_message_file
from rosidl_parser import parse_service_file
from rosidl_parser import validate_field_types


def generate_typesupport_freertps_cpp(args):
    template_dir = args['template_dir']
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

    pkg_name = args['package_name']
    known_msg_types = extract_message_types(
        pkg_name, args['ros_interface_files'], args.get('ros_interface_dependencies', []))

    functions = {
        'get_header_filename_from_msg_name': convert_camel_case_to_lower_case_underscore,
        'enforce_alignment': enforce_alignment,
        'enforce_read_alignment': enforce_read_alignment,
        'serialize_field': serialize_field,
        'deserialize_field': deserialize_field,
    }
    # generate_dds_freertps_cpp() and therefore the make target depend on the additional files
    # therefore they must be listed here even if the generated type support files are independent
    latest_target_timestamp = get_newest_modification_time(
        args['target_dependencies'] + args.get('additional_files', []))

    for idl_file in args['ros_interface_files']:
        extension = os.path.splitext(idl_file)[1]
        if extension == '.msg':
            spec = parse_message_file(pkg_name, idl_file)
            validate_field_types(spec, known_msg_types)
            subfolder = os.path.basename(os.path.dirname(idl_file))
            for template_file, generated_filename in mapping_msgs.items():
                generated_file = os.path.join(
                    args['output_dir'], subfolder, 'dds_freertps', generated_filename %
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
                    args['output_dir'], 'srv', 'dds_freertps', generated_filename %
                    convert_camel_case_to_lower_case_underscore(spec.srv_name))

                data = {'spec': spec}
                data.update(functions)
                expand_template(
                    template_file, data, generated_file,
                    minimum_timestamp=latest_target_timestamp)

    return 0


def enforce_alignment(cur_alignment, required_alignment, indent=2):
    output = ""
    if required_alignment > cur_alignment:
        output += "{0}if ((uintptr_t)_p & {1})\n".format(" " * indent, required_alignment - 1)
        output += "{0}  _p += {1} - ((uintptr_t)_p & {2});\n".format(
            " " * indent, required_alignment, required_alignment - 1)
    return output


def enforce_read_alignment(cur_alignment, required_alignment, indent=2):
    output = ""
    if required_alignment > cur_alignment:
        spaces = " " * indent
        output += "{0}if ((uintptr_t)*_p & {1})\n".format(spaces, required_alignment - 1)
        output += "{0}{{\n".format(spaces)
        output += "{0}  _len -= {1} - ((uintptr_t)*_p & {2});\n".format(
            spaces, required_alignment, required_alignment - 1)
        output += "{0}  *_p += {1} - ((uintptr_t)*_p & {2});\n".format(
            spaces, required_alignment, required_alignment - 1)
        output += "{0}}}\n".format(spaces)
    return output


class PrimitiveType(object):
    def __init__(self, type_name, align):
        self.name = type_name
        self.align = align

    def serialize(self, name, cur_alignment):
        raise RuntimeError("serialization of {0} not implemented!".format(self.name))

    def deserialize(self, name, cur_alignment):
        raise RuntimeError("deserialization of {0} not implemented!".format(self.name))


class BooleanType(PrimitiveType):
    def __init__(self):
        super(BooleanType, self).__init__('bool', 1)

    def serialize(self, field_name, cur_alignment):
        return "  *_p = _s->{0} ? 1 : 0;\n  _p++;\n".format(field_name)

    def serialize_fixed_array(self, field_name, cur_alignment, array_size):
        # this could be improved a lot
        output = "  for (int _{0}_idx = 0; _{0}_idx < {1}; _{0}_idx++)\n".format(
            field_name, array_size)
        output += "  {\n"
        output += "    *_p = _s->{0}[_{0}_idx];\n".format(field_name)
        output += "    _p++;\n"
        output += "  }\n"
        return output

    def deserialize_fixed_array(self, field_name, cur_alignment, array_size):
        output = "  for (int _{0}_idx = 0; _{0}_idx < {1}; _{0}_idx++)\n".format(
            field_name, array_size)
        output += "  {\n"
        output += "    _s->{0}[_{0}_idx] = *_p;\n".format(field_name)
        output += "    _p++;\n"
        output += "  }\n"
        return output

    def serialize_variable_array(self, field_name, cur_alignment):
        output = enforce_alignment(cur_alignment, 4)  # align for the sequence count
        size_var = "_s->{0}.size()".format(field_name)
        output += "  *((uint32_t *)_p) = {0};\n".format(size_var)
        output += "  _p += 4;\n"
        # std::vector<bool> is a space-efficient non-contiguous specialization so we can't memcpy
        output += "  for (auto entry : _s->{0})\n".format(field_name)
        output += "  {\n"
        output += "    *_p = entry ? 1 : 0;\n"
        output += "    _p++;\n"
        output += "  }\n"
        return output

    def deserialize_variable_array(self, field_name, cur_alignment):
        # Read size from first 4 bytes and stuff data from _p into _s
        output = "  uint32_t _{0}_len = *((uint32_t *)_p);\n".format(field_name)
        output += "  _p += 4;\n"
        output += "  if (_s->{0}.size() != _{0}_len)\n".format(field_name)
        output += "  {\n"
        output += "    _s->{0}.resize(_{0}_len);\n".format(field_name)
        output += "  }\n"
        output += "  for (uint32_t _{0}_idx = 0; _{0}_idx < _{0}_len; _{0}_idx++)\n".format(
            field_name)
        output += "  {\n"
        output += "    _s->{0}[_{0}_idx] = *_p ? 1 : 0;\n".format(field_name)
        output += "    _p++;\n"
        output += "  }\n"

        return output

    def deserialize(self, field_name, cur_alignment):
        output = "  _s->{0} = (**_p != 0);\n".format(field_name)
        output += "  *_p += 1;\n"
        output += "  _len--;\n"
        return output


class NumericType(PrimitiveType):
    def __init__(self, c_name, align):
        super(NumericType, self).__init__(c_name, align)

    def serialize(self, field_name, cur_alignment):
        output = enforce_alignment(cur_alignment, self.align)
        output += "  *(({0} *)_p) = _s->{1};\n".format(self.name, field_name)
        output += "  _p += sizeof({0});\n".format(self.name)
        return output

    def serialize_fixed_array(self, field_name, cur_alignment, array_size):
        # this could be improved a lot
        output = enforce_alignment(cur_alignment, self.align)
        output += "  for (uint32_t _{0}_idx = 0; _{0}_idx < {1}; _{0}_idx++)\n".format(
            field_name, array_size)
        output += "  {\n"
        output += "    *(({0} *)_p) = _s->{1}[_{1}_idx];\n".format(self.name, field_name)
        output += "    _p += sizeof({0});\n".format(self.name)
        output += "  }\n"
        return output

    def serialize_variable_array(self, field_name, cur_alignment):
        output = enforce_alignment(cur_alignment, 4)  # align for the sequence count
        size_var = "_s->{0}.size()".format(field_name)
        output += "  *((uint32_t *)_p) = {0};\n".format(size_var)
        output += "  _p += 4;\n"
        output += "  memcpy(_p, _s->{0}.data(), {1} * sizeof({2}));\n".format(
            field_name, size_var, self.name)
        output += "  _p += {0} * sizeof({1});\n".format(size_var, self.name)
        return output

    def deserialize(self, field_name, cur_alignment):
        output = "  if (*_len < sizeof({0}))\n    return false;\n".format(self.name)
        output += "  _s->{0} = *(({1} *)*_p);\n".format(field_name, self.name)
        output += "  *_p += sizeof({0});\n".format(self.name)
        output += "  *_len -= sizeof({0});\n".format(self.name)
        return output

    def deserialize_fixed_array(self, field_name, cur_alignment, array_size):
        # this could be improved a lot
        output = "  for (uint32_t _{0}_idx = 0; _{0}_idx < {1}; _{0}_idx++)\n".format(
            field_name, array_size)
        output += "  {\n"
        output += "    _s->{1}[_{1}_idx] = *(({0} *)*_p);\n".format(self.name, field_name)
        output += "    *_p += sizeof({0});\n".format(self.name)
        output += "  }\n"
        return output

    def deserialize_variable_array(self, field_name, cur_alignment):
        output = "  uint32_t _{0}_len = *((uint32_t *)_p);\n".format(field_name)
        output += "  _p += 4;\n"
        output += "  if (_s->{0}.size() != _{0}_len)\n".format(field_name)
        output += "  {\n"
        output += "    _s->{0}.resize(_{0}_len);\n".format(field_name)
        output += "  }\n"

        output += "  for (uint32_t _{0}_idx = 0; _{0}_idx < _{0}_len; _{0}_idx++)\n".format(
            field_name)
        output += "  {\n"
        output += "    _s->{0}[_{0}_idx] = *(({1} *)*_p);\n".format(field_name, self.name)
        output += "    *_p += sizeof({0});\n".format(self.name)
        output += "  }\n"
        return output


class StringType(PrimitiveType):
    def __init__(self):
        super(StringType, self).__init__('string', 1)

    def serialize(self, field_name, cur_alignment):
        output = "  uint32_t _{0}_len = (uint32_t)_s->{0}.length() + 1;\n".format(field_name)
        output += "  *((uint32_t *)_p) = _{0}_len;\n".format(field_name)
        output += "  _p += 4;\n"
        output += "  memcpy(_p, _s->{0}.data(), _{0}_len);\n".format(field_name)
        output += "  _p += _{0}_len;\n".format(field_name)
        return output

    def deserialize(self, field_name, cur_alignment):
        # Read the first 4 bytes to get the length of the string, then copy _p into _s
        output = "  uint32_t _{0}_len = *((uint32_t *)_p);\n".format(field_name)
        output += "  _p+= 4;\n"
        output += "  _s->{0}.assign((char*) *_p, _{0}_len);\n".format(field_name)
        output += "  _p+= _{0}_len;\n".format(field_name)
        return output

    def serialize_fixed_array(self, field_name, cur_alignment, array_size):
        # this could be improved a lot
        output = enforce_alignment(cur_alignment, self.align)
        output += "  for (uint32_t _{0}_idx = 0; _{0}_idx < {1}; _{0}_idx++)\n".format(
            field_name, array_size)
        output += "  {\n"
        string_size = "_s->{0}[_{0}_idx].size()".format(field_name)
        output += "    *((uint32_t *)_p) = {0};\n".format(string_size)
        output += "    _p += 4;\n"
        output += "    memcpy(_p, _s->{0}[_{0}_idx].data(), {1});\n".format(
            field_name, string_size)
        output += "    _p += {0};\n".format(string_size)
        output += "  }\n"
        return output

    def deserialize_fixed_array(self, field_name, cur_alignment, array_size):
        output = enforce_alignment(cur_alignment, self.align)
        output += "  for (uint32_t _{0}_idx = 0; _{0}_idx < {1}; _{0}_idx++)\n".format(
            field_name, array_size)
        output += "  {\n"
        output += "    uint32_t str_len = *((uint32_t *)_p);\n"
        output += "    _p += 4;\n"
        output += "    _s->{0}[_{0}_idx].assign((char*) _p, str_len);\n".format(field_name)
        output += "    _p += str_len;\n"
        output += "  }\n"
        return output

    def serialize_variable_array(self, field_name, cur_alignment):
        output = enforce_alignment(cur_alignment, 4)  # align for the sequence count
        size_var = "_s->{0}.size()".format(field_name)
        output += "  *((uint32_t *)_p) = {0};\n".format(size_var)
        output += "  _p += 4;\n"
        output += "  for (uint32_t _{0}_idx = 0; _{0}_idx < {1}; _{0}_idx++)\n".format(
            field_name, size_var)
        output += "  {\n"
        output += enforce_alignment(cur_alignment, 4, indent=4)
        output += "    *((uint32_t *)_p) = (_s->{0}[_{0}_idx]).length() + 1;\n".format(field_name)
        output += "    size_t len_tmp = *((uint32_t *)_p);\n"
        output += "    _p += 4;\n"
        output += "    memcpy(_p, _s->{0}[_{0}_idx].data(), len_tmp);\n".format(field_name)
        output += "    _p += len_tmp;\n".format(field_name)
        output += "  }\n"
        return output

    def deserialize_variable_array(self, field_name, cur_alignment):
        output = "  size_t _{0}_len = *((uint32_t *)_p);\n".format(field_name)
        output += "  _p += 4;\n"
        output += "  for (uint32_t _{0}_idx = 0; _{0}_idx < _{0}_len; _{0}_idx++)\n".format(
            field_name)
        output += "  {\n"
        output += "    size_t len_tmp = *((uint32_t *)_p);\n".format(field_name)
        output += "    _p += 4;\n"
        output += "    _s->{0}[_{0}_idx].assign((char*) _p, len_tmp);\n".format(field_name)
        output += "    _p += len_tmp;\n"
        output += "  }\n"
        return output


primitive_types = {}
primitive_types['bool'] = BooleanType()
primitive_types['byte'] = NumericType('uint8_t', 1)
primitive_types['uint8'] = NumericType('uint8_t', 1)
primitive_types['char'] = NumericType('int8_t', 1)
primitive_types['int8'] = NumericType('int8_t', 1)
primitive_types['uint16'] = NumericType('uint16_t', 2)
primitive_types['int16'] = NumericType('int16_t', 2)
primitive_types['uint32'] = NumericType('uint32_t', 4)
primitive_types['int32'] = NumericType('int32_t', 4)
primitive_types['uint64'] = NumericType('uint64_t', 8)
primitive_types['int64'] = NumericType('int64_t', 8)
primitive_types['float32'] = NumericType('float', 4)
primitive_types['float64'] = NumericType('double', 8)
primitive_types['string'] = StringType()


def uncamelcase(camelcase):
    lower = ""
    upper_run_len = 0
    for idx in range(0, len(camelcase)):
        #print(camelcase[idx])
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
    print("%s -> %s" % (c, uncamelcase(c)))


def c_includes(msg_spec):
    types = []
    for field in msg_spec.fields:
        if not field.type.type in primitive_types:
            lcase_type = uncamelcase(field.type.type)
            include = "%s/%s.h" % (field.type.pkg_name, lcase_type)
            if not include in types:
                types.append(include)
    return types


def serialize_field(field, align):
    output = ""
    typename = field.type.type
    if typename in primitive_types:
        if not field.type.is_array:
            output += primitive_types[typename].serialize(field.name, align)
            align = primitive_types[typename].align
        elif field.type.array_size:
            output += primitive_types[typename].serialize_fixed_array(
                field.name, align, field.type.array_size)
            # re-compute where we stand now in alignment, to save unnecessary if()
            align = primitive_types[typename].align * field.type.array_size
            if align % 8 == 0:
                align = 8
            elif align % 4 == 0:
                align = 4
            elif align % 2 == 0:
                align = 2
            else:
                align = 1
        else:
            output += primitive_types[typename].serialize_variable_array(field.name, align)
            align = primitive_types[typename].align
    else:
        if not field.type.is_array:
            output += "    _p += {0}::msg::typesupport_freertps_cpp".format(field.type.pkg_name)
            output += "::serialize_ros_msg(_s->{1}".format(field.type.pkg_name, field.name)
            output += ", _p, _buf_size - (_p - _buf));\n"
        elif field.type.array_size:
            output += "    for (uint32_t _{0}_idx = 0;".format(field.name)
            output += " _{0}_idx < {1}; _{0}_idx++)\n".format(field.name, field.type.array_size)
            output += "      _p += {0}::msg::typesupport_freertps_cpp".format(field.type.pkg_name)
            output += "::serialize_ros_msg(_s->{0}[_{0}_idx], ".format(field.name)
            output += "_p, _buf_size - (_p - _buf));\n"
        else:  # variable-length array of structs.
            # Serialize the sequence length first.
            output += "    *((uint32_t *)_p) = _s->{0}.size();\n".format(field.name)
            output += "    _p += 4;"
            output += "    for (uint32_t _{0}_idx = 0;".format(field.name)
            output += " _{0}_idx < _s->{0}.size(); _{0}_idx++)\n".format(field.name)
            output += "      _p += {0}::msg::typesupport_freertps_cpp".format(field.type.pkg_name)
            output += "::serialize_ros_msg(_s->{0}[_{0}_idx], _p,".format(field.name)
            output += " _buf_size - (_p - _buf));\n"
        align = 1
    return align, output


def deserialize_field(field, align):
    typename = field.type.type
    output = ""
    if typename in primitive_types:
        if not field.type.is_array:
            output += primitive_types[typename].deserialize(field.name, align)
            align = primitive_types[typename].align
        elif field.type.array_size:
            output += primitive_types[typename].deserialize_fixed_array(
                field.name, align, field.type.array_size)
            # re-compute where we stand now in alignment, to save unnecessary if()
            align = primitive_types[typename].align * field.type.array_size
            if align % 8 == 0:
                align = 8
            elif align % 4 == 0:
                align = 4
            elif align % 2 == 0:
                align = 2
            else:
                align = 1
        else:
            output += primitive_types[typename].deserialize_variable_array(field.name, align)
            align = primitive_types[typename].align
    else:
        if not field.type.is_array:
            output += "    if (!{0}::msg::typesupport_freertps_cpp::".format(field.type.pkg_name)
            output += "deserialize_ros_msg(_p, _s->{0}, _len))\n".format(field.name)
            output += "      return false;\n"
        elif field.type.array_size:
            output += "    for (uint32_t _{0}_idx = 0; _{0}_idx < {1}; _{0}_idx++)\n".format(
                field.name, field.type.array_size)
            output += "    if (!{0}::msg::typesupport_freertps_cpp::".format(field.type.pkg_name)
            output += "deserialize_ros_msg(_p, _s->{0}[_{0}_idx], _len))\n".format(field.name)
            output += "        return false;\n"
        else:  # variable-length array of structs.
            output += "    uint32_t _{0}_len = *((uint32_t *)_p);\n".format(field.name)
            output += "    for (uint32_t _{0}_idx = 0; _{0}_idx < _{0}_len;".format(field.name)
            output += " _{0}_idx++)\n".format(field.name)
            output += "    {\n"
            output += "    if (!{0}::msg::typesupport_freertps_cpp::".format(field.type.pkg_name)
            output += "deserialize_ros_msg(_p, _s->{0}[_{0}_idx], _len))\n".format(field.name)
            output += "        return false;\n"
            output += "    }\n"
        align = 1
    return align, output


def generate_header(pkg_name, msg_name, msg_spec):
    """
    Generate serialization/deserialization header from a msg_spec
    """
    # TODO: pkg_name, msg_name
    struct_type = "%s__%s" % (pkg_name, uncamelcase(msg_name))
    output = ""
    output += "typedef struct %s\n{\n" % (struct_type)
    for field in msg_spec.fields:
        print("        " + field.type.type + " " + field.name)
        c_typename = ""
        #if not field.type.is_array:

        if field.type.type in primitive_types:
            c_typename = primitive_types[field.type.type].name
        else:
            c_typename = "struct {0}__{1}".format(
                field.type.pkg_name, uncamelcase(field.type.type)).lower()

        if field.type.is_array and not field.type.array_size:
            if field.type.type in primitive_types:
                output += "    struct freertps__{0}__array {1};\n".format(
                    field.type.type, field.name)
            else:
                output += "    struct freertps__{0}__{1}__array {2};\n".format(
                    field.type.pkg_name, uncamelcase(field.type.type), field.name).lower()
        elif field.type.is_array:
            output += "    {0} {1}[{2}];\n".format(c_typename, field.name, field.type.array_size)
        else:
            output += "    {0} {1};\n".format(c_typename, field.name)

    output += "} %s_t;\n\n" % struct_type
    type_obj_name = "%s__%s__type" % (pkg_name, uncamelcase(msg_name))
    output += "extern const struct freertps_type {0};\n\n".format(type_obj_name)
    output += "uint32_t serialize_{0}(".format(struct_type)
    output += "void *_msg, uint8_t *_buf, uint32_t _buf_size);\n"
    for field in msg_spec.fields[1:]:
        output += "uint32_t serialize_{0}__until_{1}(".format(struct_type, field.name)
        output += "void *_msg, uint8_t *_buf, uint32_t _buf_size);\n"
    output += "bool deserialize_{0}(".format(struct_type)
    output += "uint8_t **_p, uint32_t *_len, void *_msg);\n"
    output += "\nFREERTPS_ARRAY({0}, {0}_t);\n".format(struct_type)
    return output


def generate_source(pkg_name, msg_name, msg_spec):
    """
    Generate serialization/deserialization header from a msg_spec
    """
    struct_type = "%s__%s" % (pkg_name, uncamelcase(msg_name))
    output = "uint32_t serialize_%s(void *_msg, uint8_t *_buf, uint32_t _buf_size)\n" % struct_type
    output += "{\n"
    output += "    struct {0} *_s = (struct {1} *)_msg;\n".format(struct_type, struct_type)
    output += "    uint8_t *_p = _buf;\n"
    output += enforce_alignment(1, 4)
    align = 4
    for field in msg_spec.fields:
        align, substring = serialize_field(field, align)
        output += substring
    output += "    return _p - _buf;\n"
    output += "}\n\n"

    ### emit the whole-enchilada deserialization function
    output += "bool deserialize_%s(uint8_t **_p, uint32_t *_len, void *_msg)\n{\n" % struct_type
    output += "    struct {0} *_s = (struct {0} *)_msg;\n".format(struct_type)
    output += enforce_read_alignment(1, 4)
    align = 4
    for field in msg_spec.fields:
        align, substring = deserialize_field(field, align)
        output += substring
    output += "    return true;\n"
    output += "}\n\n"

    type_obj_name = "%s__%s__type" % (pkg_name, uncamelcase(msg_name))
    output += "const struct freertps_type {0} =\n".format(type_obj_name)
    output += "{\n"
    output += "    .rtps_typename = \"{0}::msg::dds_::{1}_\",\n".format(pkg_name, msg_name)
    output += "    .serialize = serialize_{0}\n".format(struct_type)
    output += "};\n"
    return output


def write_generated_code_to_file(pkg_name, pkg_share_path, pkg_output_path, f):
    """
        Given a file of message names, generate serialization/deserialization code and write the
        headers and source files to separate locations
    """
    for line in f:
        extension = line.rstrip().split('.')[-1]
        if extension == 'srv':
            continue
        msg_filename = os.path.join(pkg_share_path, 'msg', line.rstrip())
        msg_spec = rosidl_parser.parse_message_file(pkg_name, msg_filename)
        msg_name = '.'.join(line.rstrip().split('.')[0:-1])
        struct_type = "%s__%s" % (pkg_name, uncamelcase(msg_name))
        print("    %s/%s" % (pkg_name, msg_name))
        header_fn = uncamelcase(msg_name) + '.h'
        header_path = os.path.join(pkg_output_path, header_fn)
        hf = open(header_path, 'w')
        include_guard = ("R2_%s__%s" % (pkg_name, uncamelcase(msg_name))).upper()
        hf.write("#ifndef %s\n" % include_guard)
        hf.write("#define %s\n\n" % include_guard)
        hf.write("#include <stdint.h>\n")
        hf.write("#include <stdbool.h>\n")
        hf.write("#include \"freertps/type.h\"\n")
        includes = c_includes(msg_spec)
        if includes:
            for include in includes:
                hf.write("#include \"%s\"\n" % include)
        hf.write("\n")

        header_string = generate_header(pkg_name, msg_name, msg_spec)
        hf.write(header_string)

        #source_fn = os.path.join(msg_tree_root, 'src', struct_type) + '.c'
        source_fn = os.path.join(pkg_output_path, struct_type) + '.c'
        sf = open(source_fn, 'w')
        sf.write("#include \"freertps/type.h\"\n")
        sf.write("#include <string.h>\n")
        sf.write("#include \"%s\"\n\n" % os.path.join(pkg_name, header_fn))
        ### first, emit the whole-enchilada serialization function
        source_string = generate_source(pkg_name, msg_name, msg_spec)
        sf.write(source_string)
