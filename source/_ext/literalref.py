# This file is part of sphinx-ext-template.
#
# Copyright 2025 Canonical Ltd.
#
# This program is free software: you can redistribute it and/or modify it under the
# terms of the GNU Lesser General Public License version 3, as published by the Free
# Software Foundation.
#
# This program is distributed in the hope that it will be useful, but WITHOUT ANY
# WARRANTY; without even the implied warranties of MERCHANTABILITY, SATISFACTORY
# QUALITY, or FITNESS FOR A PARTICULAR PURPOSE. See the GNU Lesser General Public
# License for more details.
#
# You should have received a copy of the GNU Lesser General Public License along with
# this program.  If not, see <http://www.gnu.org/licenses/>.
"""Add a custom domain to support monospaced internal links."""

from docutils import nodes
from sphinx import addnodes
from sphinx.builders import Builder
from sphinx.domains.std import StandardDomain
from sphinx.environment import BuildEnvironment
from sphinx.util.docutils import ReferenceRole
from typing import cast, override

from sphinx.util.typing import ExtensionMetadata
from sphinx.application import Sphinx


class LiteralrefDomain(StandardDomain):
    """Custom domain for the :literalref: role."""

    name: str = "lrd"

    @override
    def resolve_xref(
        self,
        env: BuildEnvironment,
        fromdocname: str,
        builder: Builder,
        typ: str,
        target: str,
        node: addnodes.pending_xref,
        contnode: nodes.Element,
    ) -> nodes.reference | None:
        """Replace the resolved node's child with the children assigned to the pending reference node.

        By default, Sphinx's standard domain
        disregards the type of the pending node's children and places their
        contents into an inline node.
        """
        resolved_node = super().resolve_xref(
            env, fromdocname, builder, typ, target, node, contnode
        )  # resolve the reference using the standard domain

        if (
            resolved_node
            and hasattr(resolved_node, "children")
            and hasattr(node, "children")
        ):  # replace the child node from ``std`` with the original children
            resolved_node.children = node.children

        return cast(nodes.reference, resolved_node)


class LiteralrefRole(ReferenceRole):
    """Define the literalref role's behavior."""

    def run(self) -> tuple[list[nodes.Node], list[nodes.system_message]]:
        """Create a cross-reference with monospaced text."""
        node: nodes.reference | addnodes.pending_xref

        # Create an external reference
        if self.target.startswith("http://") or self.target.startswith("https://"):
            node = nodes.reference("", "", internal=False, refuri=self.target)
        else:  # Create an internal reference
            node = addnodes.pending_xref(
                "",
                refdomain="lrd",  # use custom domain
                reftype="ref",
                reftarget=self.target,
                refexplicit=True,
                refwarning=True,
            )

        #  append the link text
        node.append(nodes.literal(text=self.title))

        return [node], []

def setup(app: Sphinx) -> ExtensionMetadata:
    """Add the extension's roles to Sphinx.

    :returns: ExtensionMetadata
    """
    app.add_domain(LiteralrefDomain)
    app.add_role("literalref", LiteralrefRole())

    return {
        "version": "9000",
        "parallel_read_safe": True,
        "parallel_write_safe": True,
    }