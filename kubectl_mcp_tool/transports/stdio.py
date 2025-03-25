"""
Stdio transport implementation for MCP.
"""

import sys
import json
import logging
from typing import Any, Dict, Optional

logger = logging.getLogger(__name__)

class StdioTransport:
    """Transport implementation for stdio communication."""
    
    def __init__(self, stdin=sys.stdin, stdout=sys.stdout):
        """Initialize the stdio transport."""
        self.stdin = stdin
        self.stdout = stdout
    
    def send(self, message: Dict[str, Any]) -> None:
        """Send a message over stdio."""
        try:
            json_str = json.dumps(message) + "\n"
            self.stdout.write(json_str)
            self.stdout.flush()
        except Exception as e:
            logger.error(f"Error sending message: {e}")
            raise
    
    def receive(self) -> Optional[Dict[str, Any]]:
        """Receive a message from stdio."""
        try:
            line = self.stdin.readline()
            if not line:
                return None
            return json.loads(line)
        except Exception as e:
            logger.error(f"Error receiving message: {e}")
            raise
