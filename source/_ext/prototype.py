from docutils import nodes
from docutils.parsers.rst import Directive

from sphinx.application import Sphinx
from sphinx.locale import _
from sphinx.util.docutils import SphinxDirective
from sphinx.util.typing import ExtensionMetadata

import ast
import enum
import importlib
import inspect
import pydantic


class IncludeKeyDirective(SphinxDirective):
  required_arguments = 2

  def run(self) -> list[nodes.Node]:
    module_str, class_str = self.arguments[0].rsplit('.', maxsplit=1)
    module = importlib.import_module(module_str)
    pydantic_class = getattr(module, class_str)
    
    # exit if provided field name is not present in the model
    if not self.arguments[1] in pydantic_class.__annotations__:
      return [] # this should throw an error in final product

    field_params = pydantic_class.__fields__[self.arguments[1]]

    # grab type and enum data if applicable
    if issubclass(field_params.annotation, enum.Enum):
      enum_values = get_enum_values(field_params.annotation)
      basic_type = 'enum'
    else:
      enum_values = None
      basic_type = format_type_string(f'{field_params.annotation}')

    # grab docstring for type annotation from the class AST
    description_str = get_annotation_docstring(pydantic_class, self.arguments[1])
    if description_str is None:
      description_str = field_params.description

    return create_key_node(self.arguments[1], basic_type, description_str, enum_values, field_params.examples)

def create_key_node(key_title, key_type, key_desc, key_values, key_examples):
  key_node = nodes.section(ids=[key_title])
  title_node = nodes.title()
  title_node += nodes.literal(text=key_title)
  key_node += title_node
  key_node += create_basic_node('Type', key_type)
  
  if key_desc is not None:
    key_node += create_basic_node('Description', key_desc)
  
  if key_values is not None:
    values_header = nodes.paragraph()
    values_header += nodes.strong(text='Values')
    key_node += values_header
    key_node += create_table_node(key_values)

  if key_examples is not None:
    examples_header = nodes.paragraph()
    examples_header += nodes.strong(text='Examples')
    key_node += examples_header
    for example in key_examples:
      examples_block = nodes.literal_block()
      examples_block += nodes.Text(example)
      key_node += examples_block

  return [key_node]

def create_basic_node(heading_str, content):
  header_node = nodes.paragraph()
  header_node += nodes.strong(text=heading_str)
  content_node = nodes.paragraph()
  content_node += nodes.Text(content)

  return [header_node, content_node]

def create_table_node(values):
  header = ['Values', 'Description']

  div_node = nodes.container()
  div_node['classes'].append('table-wrapper docutils container')
  table = nodes.table()
  div_node += table

  tgroup = nodes.tgroup(cols=2)
  table += tgroup

  tgroup += nodes.colspec(colwidth=1)
  tgroup += nodes.colspec(colwidth=1)

  thead = nodes.thead()
  thead += create_table_row(header)

  tbody = nodes.tbody()
  tgroup += tbody

  for row in values:
    tbody += create_table_row(row)
  
  return div_node

def create_table_row(values):
  row = nodes.row()
  for cell in values:
      entry = nodes.entry()
      row += entry
      entry += nodes.paragraph(text=cell)
  return row

# This is kinda gross
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

# oops i did it again
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

def format_type_string(type_str: str) -> str:
  start = type_str.find("'") + 1
  end = type_str.rfind("'")

  if end == -1:
    return type_str

  return type_str[start:end]

def setup(app: Sphinx) -> ExtensionMetadata:
  app.add_directive('include-key', IncludeKeyDirective)

  return {
    'version': '0.1',
    'env_version': 1,
    'parallel_read_safe': True,
    'parallel_write_safe': True,
  }