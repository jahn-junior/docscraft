from docutils import nodes
from docutils.core import publish_doctree
from docutils.parsers.rst import Directive

from sphinx.application import Sphinx
from sphinx.locale import _
from sphinx.util.docutils import SphinxDirective
from sphinx.util.typing import ExtensionMetadata

import ast
import enum
import importlib
import inspect
import json
import pydantic
import textwrap


class IncludeKeyDirective(SphinxDirective):
  required_arguments = 2
  optional_arguments = 0
  has_content = False
  final_argument_whitespace = True

  def run(self) -> list[nodes.Node]:
    module_str, class_str = self.arguments[0].rsplit('.', maxsplit=1)
    module = importlib.import_module(module_str)
    pydantic_class = getattr(module, class_str)
    
    # exit if provided field name is not present in the model
    if not self.arguments[1] in pydantic_class.__annotations__:
      return [] # this should throw an error in final product

    # grab pydantic field data (need desc and examples)
    field_params = pydantic_class.__fields__[self.arguments[1]]

    # grab type and enum data if applicable
    if issubclass(field_params.annotation, enum.Enum):
      description_str = field_params.annotation.__doc__
      enum_values = get_enum_values(field_params.annotation)
      basic_type = 'enum'
    else:
      description_str = get_annotation_docstring(pydantic_class, self.arguments[1])
      enum_values = None
      basic_type = format_type_string(f'{field_params.annotation}')

    # grab docstring for type annotation from the class AST
    if description_str is None:
      description_str = field_params.description # use JSON description value

    return [create_key_node(self.arguments[1], basic_type, description_str, enum_values, field_params.examples)]


class IncludeModelDirective(SphinxDirective):
  required_arguments = 1
  optional_arguments = 0
  has_content = True
  final_argument_whitespace = True

  def run(self) -> list[nodes.Node]:
    module_str, class_str = self.arguments[0].rsplit('.', maxsplit=1)
    module = importlib.import_module(module_str)
    pydantic_class = getattr(module, class_str)

    if not issubclass(pydantic_class, pydantic.BaseModel):
      return []

    class_node = nodes.section(ids=[pydantic_class.__name__])
    
    if self.content:
      class_node += parse_rst_description('\n'.join(self.content))
    else:
      class_node += parse_rst_description(pydantic_class.__doc__)

    for field in pydantic_class.__annotations__:
      if not field.startswith('_') and not field.startswith('model_'):
        # grab pydantic field data (need desc and examples)
        field_params = pydantic_class.__fields__[field]

        # grab type and enum data if applicable
        if issubclass(field_params.annotation, enum.Enum):
          description_str = field_params.annotation.__doc__
          enum_values = get_enum_values(field_params.annotation)
          basic_type = 'enum'
        else:
          description_str = get_annotation_docstring(pydantic_class, field)
          enum_values = None
          basic_type = format_type_string(f'{field_params.annotation}')

        # grab docstring for type annotation from the class AST
        if description_str is None:
          description_str = field_params.description # use JSON description value
        
        class_node.append(create_key_node(field, basic_type, description_str, enum_values, field_params.examples))

    return [class_node]


def create_key_node(key_name, key_type, key_desc, key_values, key_examples):
  key_node = nodes.section(ids=[key_name])
  title_node = nodes.title()
  title_node += nodes.literal(text=key_name)
  key_node += title_node
  key_node += create_basic_node('Type', key_name)
  
  if key_desc:
    desc_header = nodes.paragraph()
    desc_header += nodes.strong(text='Description')
    key_node += desc_header
    key_node += parse_rst_description(key_desc)
  
  if key_values:
    values_header = nodes.paragraph()
    values_header += nodes.strong(text='Values')
    key_node += values_header
    key_node += create_table_node(key_values)

  if key_examples:
    examples_header = nodes.paragraph()
    examples_header += nodes.strong(text='Examples')
    key_node += examples_header
    for example in key_examples:
      key_node += build_examples_block(key_name, example)

  return key_node


def build_examples_block(key_name, example):
  examples_block = nodes.literal_block()
  example_str = json.dumps(example, indent=2)
  examples_block += nodes.Text(f'{key_name}: ')
  yaml_string = example_str.replace('"', '').replace('{', '').replace('}', '').rstrip()
  examples_block += nodes.Text(yaml_string)

  return examples_block
  


def create_basic_node(heading_str, content):
  header_node = nodes.paragraph()
  header_node += nodes.strong(text=heading_str)
  content_node = nodes.paragraph()
  content_node += nodes.Text(content)

  return [header_node, content_node]


def create_table_node(values):
  div_node = nodes.container()
  table = nodes.table()
  div_node += table

  tgroup = nodes.tgroup(cols=2)
  table += tgroup

  tgroup += nodes.colspec(colwidth=1)
  tgroup += nodes.colspec(colwidth=1)

  thead = nodes.thead()
  header_row = nodes.row()

  values_entry = nodes.entry()
  values_entry += nodes.Text('Values')
  header_row += values_entry

  desc_entry = nodes.entry()
  desc_entry += nodes.Text('Description')
  header_row += desc_entry

  thead += header_row
  tgroup += thead

  tbody = nodes.tbody()
  tgroup += tbody

  for row in values:
    tbody += create_table_row(row)
  
  return div_node


def create_table_row(values):
  row = nodes.row()

  value_entry = nodes.entry()
  value_entry += nodes.literal(text=values[0])
  row += value_entry

  desc_entry = nodes.entry()
  desc_entry += parse_rst_description(values[1])
  row += desc_entry

  return row


# this is kinda gross
def get_annotation_docstring(cls, annotation_name: str) -> str:
  code = inspect.getsource(cls)
  tree = ast.parse(code)
  
  found = False
  docstring = None

  for node in ast.walk(tree):
    if isinstance(node, ast.AnnAssign):
      # ensures it doesn't skip to the next type annotation
      # in the absence of a docstring
      if found:
        return None
      if node.target.id == annotation_name:
        found = True
    elif found and isinstance(node, ast.Expr):
      docstring = node.value.value
      break

  return docstring


# also kinda gross
def get_enum_member_docstring(cls, enum_member):
  source = inspect.getsource(cls)
  tree = ast.parse(source)

  for node in tree.body:
    for i, inner_node in enumerate(node.body):
      if isinstance(inner_node, ast.Assign):
        for target in inner_node.targets:
          if isinstance(target, ast.Name) and target.id == enum_member:
            docstring_node = node.body[i + 1]
            if isinstance(docstring_node, ast.Expr):
              return docstring_node.value.value
  
  return None


def get_enum_values(enum_class: str) -> list[str]:
  enum_docstrings = []
  
  for attr, enum in enum_class.__dict__.items():
    if not attr.startswith('_'):
      docstring = get_enum_member_docstring(enum_class, attr)
      if docstring:
        enum_docstrings.append([f'{enum.value}', f'{docstring}'])

  return enum_docstrings


def parse_rst_description(rst_desc):
  desc_nodes = []
  rst_doc = publish_doctree(strip_whitespace(rst_desc))
  for node in rst_doc.children:
    desc_nodes.append(node)

  return desc_nodes


def strip_whitespace(rst_desc):
  lines = rst_desc.splitlines()
  first_line = lines[0]
  remaining_lines = lines[1:]
  dedented_remaining_lines = textwrap.dedent("\n".join(remaining_lines)).splitlines()
  return "\n".join([first_line] + dedented_remaining_lines)


def format_type_string(type_str: str) -> str:
  start = type_str.find("'") + 1
  end = type_str.rfind("'")

  if end == -1:
    return type_str

  return type_str[start:end]


def setup(app: Sphinx) -> ExtensionMetadata:
  app.add_directive('include-key', IncludeKeyDirective)
  app.add_directive('include-model', IncludeModelDirective)

  return {
    'version': '0.1',
    'env_version': 1,
    'parallel_read_safe': True,
    'parallel_write_safe': True,
  }