.. _proving-grounds:

Prototype proving grounds
=========================


``include-key`` output
----------------------

.. include-key:: main.Docscraft name
    :hide-examples:
    :hide-type:
    :name-prepend: <before>
    :name-append: <after>

.. include-key:: main.Docscraft testKey


``include-model`` output
------------------------

.. include-model:: main.Docscraft
    :deprecated: testKey

    This is a custom description. If you don't add this to the directive,
    it will grab the pydantic model's docstring.

