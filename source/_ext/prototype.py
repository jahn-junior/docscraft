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

    key_node = nodes.section(ids=[self.arguments[1]])

    title = nodes.title()
    title += nodes.Text(self.arguments[1])
    key_node += title

    field_params = pydantic_class.__fields__[self.arguments[1]]

    # grab type and enum data if applicable
    if issubclass(field_params.annotation, enum.Enum):
      enum_values = get_values_node(field_params.annotation)
      basic_type = 'enum'
    else:
      enum_values = None
      basic_type = format_type_string(f'{field_params.annotation}')

    key_node += create_basic_node('Type', basic_type)

    # grab docstring for type annotation from the class AST
    description_str = get_annotation_docstring(pydantic_class, self.arguments[1])
    if description_str is None:
      description_str = field_params.description

    if description_str is not None:
      key_node += create_basic_node('Description', description_str)

    if enum_values is not None:
      values_header = nodes.paragraph()
      values_header += nodes.strong(text='Values')
      values_header += nodes.line()
      key_node += values_header
      key_node += create_table(enum_values)

    if field_params.examples is not None:
      key_node += create_basic_node('Examples', field_params.examples)

    return [key_node]

def create_basic_node(heading_str, content):
  node = nodes.paragraph()
  node += nodes.strong(text=heading_str)
  node += nodes.line()
  node += nodes.Text(content)

  return node

def create_table(values):
  header = ['Values', 'Description']
  table = nodes.table()
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
  
  return table

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

def get_values_node(enum_class: str):
  enum_docstrings = []

  for attr, enum in enum_class.__dict__.items():
    if not attr.startswith('_'):
      docstring = enum.__doc__
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