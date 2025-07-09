from docutils import nodes
from sphinx import addnodes
from sphinx.util.docutils import ReferenceRole
from sphinx.util.typing import ExtensionMetadata
from sphinx.application import Sphinx


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
                refdomain="std",
                reftype="ref",
                reftarget=self.target,
            )
            node["refexplicit"] = True

        node.append(nodes.literal(text=self.title))

        return [node], []
        

def setup(app: Sphinx) -> ExtensionMetadata:
    """Add the extension's directive to Sphinx.

    :returns: ExtensionMetadata
    """
    app.add_role("literalref", LiteralrefRole())

    return {
        "version": "0.0.1",
        "parallel_read_safe": True,
        "parallel_write_safe": True,
    }
