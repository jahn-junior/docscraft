The extension
=============

This is roughly how I'd imagine the extension would output the documentation.

Input
-----

Imagining an input something like:

.. code-block:: restructuredtext

    ``docscraft.yaml`` for docs that are docs
    ==========================================

    .. autopydantic:: main.Docscraft

       This file describes how Docscraft will build your documentation.
       Because I've provided some text here, we don't use the docstring
       of the base model, instead using this!

This should result in a page that looks something like the below:

Output
------

``docscraft.yaml`` for docs that are docs
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

This file describes how Docscraft will build your documentation.
Because I've provided some text here, we don't use the docstring of the
base model, instead using this!


``name``
^^^^^^^^

The name of this docscraft project.

This text shows up on the documentation page.

Examples
........

.. code-block:: yaml

   name: snapcraft

.. code-block:: yaml

   name: charmcraft

.. code-block:: yaml

   name: rockcraft


``type``
^^^^^^^^

The type of documentation in this project.

``VALUES``
..........

.. list-table::
   :header-rows: 1

   * - Value
     - Description
   * - ``end-user``
     - End user documentation.

       This is documentation for people who are using the product. For example, the end
       user of snapcraft's documentation is someone who's building or maintaining a
       snap.
   * - ``developer``
     - Developer documentation.

       This is documentation for someone who wants to contribute to the product's
       source code. It will often contain things like how to set up your development
       environment and linting rules.
   * - ``documenter``
     - Documenter documentation.

       This is documentation aimed at someone who wants to work on the documentation for
       a product. It should contain things like how to set up a documentation environment,
       a style guide, etc. Examples include:

       - `The Ubuntu style guide <https://docs.ubuntu.com/styleguide/en/>`_
       - https://canonical-documentation-with-sphinx-and-readthedocscom.readthedocs-hosted.com/
