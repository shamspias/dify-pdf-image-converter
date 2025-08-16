from typing import Any

from dify_plugin import ToolProvider
from dify_plugin.errors.tool import ToolProviderCredentialValidationError


class Pdf2imageProvider(ToolProvider):
    def _validate_credentials(self, credentials: dict[str, Any]) -> None:
        try:
            # No credentials needed for this tool
            pass
        except Exception as e:
            raise ToolProviderCredentialValidationError(str(e))
