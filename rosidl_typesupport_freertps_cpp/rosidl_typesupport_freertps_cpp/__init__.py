# Copyright 2014-2015 Open Source Robotics Foundation, Inc.
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


import os, sys, re

try:
  import rosidl_parser
except ImportError:
  print("\n\033[93mUnable to import the rosidl_parser module. Perhaps you haven't yet sourced the \ninstall/setup.bash file in your ros2 workspace?\033[0m\n\n")
  sys.exit(1)

def enforce_alignment(cur_alignment, required_alignment, indent=2):
  composed_str = ""
  if required_alignment > cur_alignment:
    composed_str += "{0}if ((uintptr_t)_p & {1})\n".format(" "*indent, required_alignment-1)
    composed_str += "{0}  _p += {1} - ((uintptr_t)_p & {2});\n".format(" "*indent, required_alignment, required_alignment-1)
  return composed_str

def enforce_read_alignment(cur_alignment, required_alignment, indent=2):
  composed_str = ""
  if required_alignment > cur_alignment:
    spaces = " "*indent
    composed_str += "{0}if ((uintptr_t)*_p & {1})\n".format(spaces, required_alignment-1)
    composed_str += "{0}{{\n".format(spaces)
    composed_str += "{0}  _len -= {1} - ((uintptr_t)*_p & {2});\n".format(spaces, required_alignment, required_alignment-1)
    composed_str += "{0}  *_p += {1} - ((uintptr_t)*_p & {2});\n".format(spaces, required_alignment, required_alignment-1)
    composed_str += "{0}}}\n".format(spaces)
  return composed_str

class PrimitiveType(object):
  def __init__(self, type_name, align):
    self.name = type_name
    self.align = align

  def serialize(self, name, cur_alignment):
    raise RuntimeError("serialization of {0} not implemented!".format(self.name))

  def deserialize(self, name, cur_alignment):
    composed_str = ""
    composed_str += "  printf(\"serialization of %s not yet implemented.\");\n" % name
    composed_str += "  return false;\n"
    return composed_str

class BooleanType(PrimitiveType):
  def __init__(self):
    super(BooleanType, self).__init__('bool', 1)

  def serialize(self, field_name, cur_alignment):
    composed_str = ""
    composed_str += "  *_p = _s->{0} ? 1 : 0;\n".format(field_name)
    composed_str += "  _p++;\n"
    return composed_str

  def serialize_fixed_array(self, field_name, cur_alignment, array_size):
    # this could be improved a lot
    composed_str = ""
    composed_str += "  for (int _{0}_idx = 0; _{0}_idx < {1}; _{0}_idx++)\n".format(field_name, array_size)
    composed_str += "  {\n"
    composed_str += "    *_p = _s->{0}[_{0}_idx];\n".format(field_name)
    composed_str += "    _p++;\n"
    composed_str += "  }\n"
    return composed_str

  def deserialize(self, field_name, cur_alignment):
    composed_str = ""
    composed_str += "  _s->{0} = (**_p != 0);\n".format(field_name)
    composed_str += "  *_p += 1;\n" #(*_p)++;\n")
    composed_str += "  _len--;\n"
    return composed_str

class NumericType(PrimitiveType):
  def __init__(self, c_name, align):
    super(NumericType, self).__init__(c_name, align)

  def serialize(self, field_name, cur_alignment):
    composed_str = ""
    composed_str += enforce_alignment(cur_alignment, self.align)
    composed_str += "  *(({0} *)_p) = _s->{1};\n".format(self.name, field_name)
    composed_str += "  _p += sizeof({0});\n".format(self.name)
    return composed_str

  def serialize_fixed_array(self, field_name, cur_alignment, array_size):
    # this could be improved a lot
    composed_str = ""
    composed_str += enforce_alignment(cur_alignment, self.align)
    composed_str += "  for (uint32_t _{0}_idx = 0; _{0}_idx < {1}; _{0}_idx++)\n".format(field_name, array_size)
    composed_str += "  {\n"
    composed_str += "    *(({0} *)_p) = _s->{1}[_{1}_idx];\n".format(self.name, field_name)
    composed_str += "    _p += sizeof({0});\n".format(self.name)
    composed_str += "  }\n"
    return composed_str

  def serialize_variable_array(self, field_name, cur_alignment):
    composed_str = ""
    composed_str += enforce_alignment(cur_alignment, 4) # align for the sequence count
    size_var = "_s->{0}.size".format(field_name)
    composed_str += "  *((uint32_t *)_p) = {0};\n".format(size_var)
    composed_str += "  _p += 4;\n"
    composed_str += "  memcpy(_p, _s->{0}.data, {1} * sizeof({1}));\n".format(field_name, size_var, self.name)
    composed_str += "  _p += {0} * sizeof({1});\n".format(size_var, self.name)
    return composed_str

  def deserialize(self, field_name, cur_alignment):
    composed_str = ""
    composed_str += "  if (*_len < sizeof({0}))\n    return false;\n".format(self.name)
    composed_str += "  _s->{0} = *(({1} *)*_p);\n".format(field_name, self.name)
    composed_str += "  *_p += sizeof({0});\n".format(self.name)
    composed_str += "  *_len -= sizeof({0});\n".format(self.name)
    return composed_str

  def deserialize_fixed_array(self, field_name, cur_alignment, array_size):
    composed_str = ""
    # this could be improved a lot
    composed_str += enforce_read_alignment(cur_alignment, self.align, composed_str)
    composed_str += "  for (uint32_t _{0}_idx = 0; _{0}_idx < {1}; _{0}_idx++)\n".format(field_name, array_size)
    composed_str += "  {\n"
    composed_str += "    _s->{1}[_{1}_idx] = *(({0} *)*_p);\n".format(self.name, field_name)
    composed_str += "    *_p += sizeof({0});\n".format(self.name)
    composed_str += "  }\n"
    return composed_str

  def deserialize_variable_array(self, field_name, cur_alignment):
    composed_str = ""
    composed_str += "  printf(\"this is not yet complete.\");\n"
    composed_str += "  return false;\n"
    #f.write("  if (*_len < sizeof({0}))\n    return false;\n".format(self.name))
    #f.write("  _s->{0} = *(({1} *)_p);\n".format(field_name, self.name))
    #f.write("  **_p += sizeof({0});\n".format(self.name))
    #f.write("  *_len -= sizeof({0});\n".format(self.name))
    return composed_str

class StringType(PrimitiveType):
  def __init__(self):
    super(StringType, self).__init__('char *', 1)

  def serialize(self, field_name, cur_alignment):
    composed_str = ""
    composed_str += "  uint32_t _{0}_len = (uint32_t)strlen(_s->{0}) + 1;\n".format(field_name)
    composed_str += "  *((uint32_t *)_p) = _{0}_len;\n".format(field_name)
    composed_str += "  _p += 4;\n"
    composed_str += "  memcpy(_p, _s->{0}, _{0}_len);\n".format(field_name)
    composed_str += "  _p += _{0}_len;\n".format(field_name)
    return composed_str

  def serialize_variable_array(self, field_name, cur_alignment):
    composed_str = ""
    composed_str += enforce_alignment(cur_alignment, 4) # align for the sequence count
    size_var = "_s->{0}.size".format(field_name)
    composed_str += "  *((uint32_t *)_p) = {0};\n".format(size_var)
    composed_str += "  _p += 4;\n"
    composed_str += "  for (uint32_t _{0}_idx = 0; _{0}_idx < {1}; _{0}_idx++)\n".format(field_name, size_var)
    composed_str += "  {\n"
    composed_str += enforce_alignment(cur_alignment, 4, indent=4)
    composed_str += "    size_t len = strlen(_s->{0}[_{0}_idx].data) + 1;\n".format(field_name)
    composed_str += "    _p += 4;\n"
    composed_str += "    memcpy(_p, _s->{0}[_{0}_idx], len);\n".format(field_name)
    composed_str += "    _p += len;\n".format(field_name)
    composed_str += "  }\n"
    return composed_str

  def deserialize_variable_array(self, field_name, cur_alignment):
    composed_str = ""
    composed_str += "  printf(\"deserialization of variable-length string arrays not implemented!\n\");"
    composed_str += "  exit(1);\n"
    return composed_str


primitive_types = { }
primitive_types['bool']    = BooleanType()
primitive_types['byte']    = NumericType('uint8_t' , 1)
primitive_types['uint8']   = NumericType('uint8_t' , 1)
primitive_types['char']    = NumericType('int8_t'  , 1)
primitive_types['int8']    = NumericType('int8_t'  , 1)
primitive_types['uint16']  = NumericType('uint16_t', 2)
primitive_types['int16']   = NumericType('int16_t' , 2)
primitive_types['uint32']  = NumericType('uint32_t', 4)
primitive_types['int32']   = NumericType('int32_t' , 4)
primitive_types['uint64']  = NumericType('uint64_t', 8)
primitive_types['int64']   = NumericType('int64_t' , 8)
primitive_types['float32'] = NumericType('float'   , 4)
primitive_types['float64'] = NumericType('double'  , 8)
primitive_types['string']  = StringType()

def uncamelcase(camelcase):
  lower = ""
  upper_run_len = 0
  for idx in xrange(0, len(camelcase)):
    #print(camelcase[idx])
    if (camelcase[idx].isupper()):
      next_lower = idx < len(camelcase)-1 and camelcase[idx+1].islower()
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

# TODO move this to a test package
def camelcase_to_lower_samples():
  print_uncamelcase("String")
  print_uncamelcase("UInt32")
  print_uncamelcase("UInt32MultiArray")
  print_uncamelcase("MultiArrayLayout")
  print_uncamelcase("NavSatStatus")
  print_uncamelcase("MultiDOFJointState")
  print_uncamelcase("RegionOfInterest")
  print_uncamelcase("PointCloud2")
  print_uncamelcase("PointField")
  print_uncamelcase("MultiEchoLaserScan")

  #if rosidl_type.pkg_name:
  #  print "   context for %s = %s" % (rosidl_type.type, rosidl_type.pkg_name)
  #return "ahhhh___%s" % rosidl_type.type

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
  composed_str = ""
  typename = field.type.type
  if typename in primitive_types:
    if not field.type.is_array:
      composed_str += primitive_types[typename].serialize(field.name, align)
      align = primitive_types[typename].align
    elif field.type.array_size:
      composed_str += primitive_types[typename].serialize_fixed_array(field.name, align, field.type.array_size)
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
      composed_str += primitive_types[typename].serialize_variable_array(field.name, align)
      align = primitive_types[typename].align
  else:
    field_c_struct_name = "{0}__{1}".format(field.type.pkg_name, uncamelcase(field.type.type)).lower()
    if not field.type.is_array:
      composed_str += "  _p += serialize_{0}(&_s->{1}, _p, _buf_size - (_p - _buf));\n".format(field_c_struct_name, field.name)
    elif field.type.array_size:
      composed_str += "  for (uint32_t _{0}_idx = 0; _{0}_idx < {1}; _{0}_idx++)\n".format(field.name, field.type.array_size)
      composed_str += "    _p += serialize_{0}(&_s->{1}[_{1}_idx], _p, _buf_size - (_p - _buf));\n".format(field_c_struct_name, field.name)
    else: # variable-length array of structs.
      # todo: i think the sequence length needs to be serialized first...
      composed_str += "  for (uint32_t _{0}_idx = 0; _{0}_idx < _s->{0}.size; _{0}_idx++)\n".format(field.name)
      composed_str += "    _p += serialize_{0}(&_s->{1}.data[_{1}_idx], _p, _buf_size - (_p - _buf));\n".format(field_c_struct_name, field.name)
    align = 1
  return align, composed_str

def deserialize_field(field, align):
  typename = field.type.type
  composed_str = ""
  if typename in primitive_types:
    if not field.type.is_array:
      composed_str += primitive_types[typename].deserialize(field.name, align)
      align = primitive_types[typename].align
    elif field.type.array_size:
      composed_str += primitive_types[typename].deserialize_fixed_array(field.name, align, field.type.array_size)
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
      composed_str += primitive_types[typename].deserialize_variable_array(field.name, align)
      align = primitive_types[typename].align
  else:
    field_c_struct_name = "{0}__{1}".format(field.type.pkg_name, uncamelcase(field.type.type)).lower()
    if not field.type.is_array:
      composed_str += "  if (!deserialize_{0}(_p, _len, &_s->{1}))\n    return false;\n".format(field_c_struct_name, field.name)
    elif field.type.array_size:
      composed_str += "  for (uint32_t _{0}_idx = 0; _{0}_idx < {1}; _{0}_idx++)\n".format(field.name, field.type.array_size)
      composed_str += "    if (!deserialize_{0}(_p, _len, &_s->{1}[_{1}_idx]))\n    return false;\n".format(field_c_struct_name, field.name)
    else: # variable-length array of structs.
      composed_str += "  printf(\"hmm... not sure how to deserialize dynamic arrays just yet.\");\n;  exit(1);\n"
      #sf.write("  for (uint32_t _{0}_idx = 0; _{0}_idx < _s->_{0}_size; _{0}_idx++)\n".format(field.name))
      #sf.write("    if (!deserialize_{0}(&_s->{1}[_{1}_idx], _p, _buf_size - (_p - _buf)))\n    return false;\n".format(field_c_struct_name, field.name))
    align = 1
  return align, composed_str

"""
Generate serialization/deserialization header from a msg_spec (parsed from rosidl_parser.parse_message_file)
"""
def generate_header(pkg_name, msg_name, msg_spec):
  # TODO: pkg_name, msg_name
  struct_type = "%s__%s" % (pkg_name, uncamelcase(msg_name))
  composed_str = ""
  composed_str += "typedef struct %s\n{\n" % (struct_type)
  for field in msg_spec.fields:
    print("    " + field.type.type + " " + field.name)
    c_typename = ""
    #if not field.type.is_array:

    if field.type.type in primitive_types:
      c_typename = primitive_types[field.type.type].name
    else:
      c_typename = "struct {0}__{1}".format(field.type.pkg_name, uncamelcase(field.type.type)).lower()

    if field.type.is_array and not field.type.array_size:
      if field.type.type in primitive_types:
        composed_str += "  struct freertps__{0}__array {1};\n".format(field.type.type, field.name)
      else:
        composed_str += "  struct freertps__{0}__{1}__array {2};\n".format(field.type.pkg_name, uncamelcase(field.type.type), field.name).lower()
    elif field.type.is_array:
      composed_str += "  {0} {1}[{2}];\n".format(c_typename, field.name, field.type.array_size)
    else:
      composed_str += "  {0} {1};\n".format(c_typename, field.name)

  composed_str += "} %s_t;\n\n" % struct_type
  type_obj_name = "%s__%s__type" % (pkg_name, uncamelcase(msg_name))
  composed_str += "extern const struct freertps_type {0};\n\n".format(type_obj_name)
  composed_str += "uint32_t serialize_{0}(void *_msg, uint8_t *_buf, uint32_t _buf_size);\n".format(struct_type)
  for field in msg_spec.fields[1:]:
    composed_str += "uint32_t serialize_{0}__until_{1}(void *_msg, uint8_t *_buf, uint32_t _buf_size);\n".format(struct_type, field.name)
  composed_str += "bool deserialize_{0}(uint8_t **_p, uint32_t *_len, void *_msg);\n".format(struct_type)
  #for field in msg_spec.fields[1:]:
  #  hf.write("bool deserialize_{0}__until_{1}(void *_msg, uint8_t *_buf, uint32_t _buf_size);\n".format(struct_type, field.name))
  composed_str += "\nFREERTPS_ARRAY({0}, {0}_t);\n".format(struct_type)
  return composed_str

"""
Generate serialization/deserialization header from a msg_spec (parsed from rosidl_parser.parse_message_file)
"""
def generate_source(pkg_name, msg_name, msg_spec):
  struct_type = "%s__%s" % (pkg_name, uncamelcase(msg_name))
  composed_str = ""
  ### first, emit the whole-enchilada serialization function
  composed_str += "uint32_t serialize_%s(void *_msg, uint8_t *_buf, uint32_t _buf_size)\n{\n" % (struct_type)
  composed_str += "  struct {0} *_s = (struct {1} *)_msg;\n".format(struct_type, struct_type)
  composed_str += "  uint8_t *_p = _buf;\n"
  composed_str += enforce_alignment(1, 4)
  align = 4
  for field in msg_spec.fields:
    align, substring = serialize_field(field, align)
    composed_str += substring
  composed_str += "  return _p - _buf;\n"
  composed_str += "}\n\n"
  ### now, emit the partial serialization functions
  for until_field in msg_spec.fields[1:]:
    composed_str += "uint32_t serialize_{0}__until_{1}(void *_msg, uint8_t *_buf, uint32_t _buf_size)\n{{\n".format(struct_type, until_field.name)
    composed_str += "  struct {0} *_s = (struct {0} *)_msg;\n".format(struct_type)
    composed_str += "  uint8_t *_p = _buf;\n"
    composed_str += enforce_alignment(1, 4)
    align = 4
    for field in msg_spec.fields:
      if field == until_field:
        break
      align, substring = serialize_field(field, align)
      composed_str += substring
    composed_str += "  return _p - _buf;\n"
    composed_str += "}\n\n"

  ### emit the whole-enchilada deserialization function
  composed_str += "bool deserialize_%s(uint8_t **_p, uint32_t *_len, void *_msg)\n{\n" % struct_type
  composed_str += "  struct {0} *_s = (struct {0} *)_msg;\n".format(struct_type)
  #sf.write("  uint8_t *_p = _buf;\n")
  composed_str += enforce_read_alignment(1, 4)
  align = 4
  for field in msg_spec.fields:
    align, substring = deserialize_field(field, align)
    composed_str += substring
  composed_str += "  return true;\n" #_rpos - _buf;\n")
  composed_str += "}\n\n"
  '''
  ### now, emit the partial serialization functions
  for until_field in msg_spec.fields[1:]:
    sf.write("bool deserialize_{0}__until_{1}(void *_msg, uint8_t *_buf, uint32_t _buf_size)\n{{\n".format(struct_type, until_field.name))
    sf.write("  struct {0} *_s = (struct {0} *)_msg;\n".format(struct_type))
    sf.write("  uint8_t *_p = _buf;\n")
    enforce_alignment(1, 4, sf)
    align = 4
    for field in msg_spec.fields:
      if field == until_field:
        break
      align = deserialize_field(field, align, sf) sf.write("  return true;\n") #return _wpos - _buf;\n")
    sf.write("}\n\n")
  '''

  type_obj_name = "%s__%s__type" % (pkg_name, uncamelcase(msg_name))
  composed_str += "const struct freertps_type {0} =\n".format(type_obj_name)
  composed_str += "{\n"
  composed_str += "  .rtps_typename = \"{0}::msg::dds_::{1}_\",\n".format(pkg_name, msg_name)
  composed_str += "  .serialize = serialize_{0}\n".format(struct_type)
  composed_str += "};\n"
  return composed_str


"""
  Given a file of message names, generate serialization/deserialization code and write the
  headers and source files to separate locations
"""
def write_generated_code_to_file(pkg_name, pkg_share_path, pkg_output_path, f):
  for line in f:
    extension = line.rstrip().split('.')[-1]
    if extension == 'srv':
      continue
    msg_filename = os.path.join(pkg_share_path, 'msg', line.rstrip())
    msg_spec = rosidl_parser.parse_message_file(pkg_name, msg_filename)
    msg_name = '.'.join(line.rstrip().split('.')[0:-1])
    struct_type = "%s__%s" % (pkg_name, uncamelcase(msg_name))
    print("  %s/%s" % (pkg_name, msg_name))
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

