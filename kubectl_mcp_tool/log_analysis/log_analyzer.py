#!/usr/bin/env python3
"""
Log analyzer module for Kubernetes logs.
"""

import json
import logging
import os
import re
import subprocess
from typing import Dict, Any, List, Optional

# Configure logging
logging.basicConfig(
    level=logging.DEBUG,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    filename="log_analyzer.log"
)
logger = logging.getLogger("log-analyzer")

class LogAnalyzer:
    """Class for analyzing Kubernetes logs."""
    
    def __init__(self):
        """Initialize the LogAnalyzer class."""
        self.patterns = self._load_patterns()
        self.error_explanations = self._load_error_explanations()
        logger.info("LogAnalyzer initialized")
    
    def _load_patterns(self) -> Dict[str, str]:
        """Load patterns for log analysis."""
        return {
            # Memory-related issues
            "memory_leak": r"memory\s+usage\s+exceeded|memory\s+leak|out\s+of\s+memory",
            "memory_pressure": r"memory\s+pressure|high\s+memory\s+usage",
            
            # Connection issues
            "connection_timeout": r"connection\s+timed?\s*out|timeout\s+connecting",
            "connection_refused": r"connection\s+refused|could\s+not\s+connect",
            
            # Permission issues
            "permission_denied": r"permission\s+denied|unauthorized|access\s+denied|forbidden",
            
            # Resource issues
            "resource_exhaustion": r"resource\s+quota\s+exceeded|out\s+of\s+(memory|disk|cpu)|resource\s+limit",
            
            # Kubernetes-specific issues
            "pod_evicted": r"pod\s+evicted|eviction\s+manager",
            "image_pull_error": r"failed\s+to\s+pull\s+image|imagepullerror|imagepullbackoff",
            "probe_failure": r"liveness\s+probe\s+failed|readiness\s+probe\s+failed",
            
            # General errors
            "exception": r"exception|error|failure|failed|fatal|panic|crash",
            "warning": r"warning|warn",
        }
    
    def _load_error_explanations(self) -> Dict[str, str]:
        """Load error explanations for common error patterns."""
        return {
            "memory_leak": "The application is using more memory than expected, possibly due to memory leaks.",
            "memory_pressure": "The system or container is experiencing high memory usage.",
            "connection_timeout": "The application failed to establish a connection within the expected time limit.",
            "connection_refused": "The target service actively refused the connection.",
            "permission_denied": "The application doesn't have the necessary permissions to perform the requested action.",
            "resource_exhaustion": "The application has reached or exceeded its allocated resource limits.",
            "pod_evicted": "The pod was evicted from its node due to resource pressure or policy decisions.",
            "image_pull_error": "Kubernetes failed to pull the container image.",
            "probe_failure": "The pod's liveness or readiness probe failed.",
            "exception": "The application encountered an error or exception.",
            "warning": "The application logged a warning message."
        }
    
    def analyze_logs(self, pod_name: str, namespace: str = "default", 
                    container: Optional[str] = None, tail: int = 100) -> Dict[str, Any]:
        """Analyze logs from a pod."""
        logs = self._get_logs(pod_name, namespace, container, tail)
        
        if not logs.get("success", False):
            return logs
        
        log_content = logs.get("result", "")
        
        # Analyze log content
        analysis = {
            "code_smells": self._detect_code_smells(log_content),
            "errors": self._detect_errors(log_content),
            "summary": self._generate_summary(log_content),
            "recommendations": self._generate_recommendations(log_content),
        }
        
        return {
            "success": True,
            "command": logs.get("command", ""),
            "result": analysis,
        }
    
    def _get_logs(self, pod_name: str, namespace: str = "default", 
                 container: Optional[str] = None, tail: int = 100) -> Dict[str, Any]:
        """Get logs from a pod."""
        try:
            cmd = ["kubectl", "logs", f"--namespace={namespace}", f"--tail={tail}"]
            
            if container:
                cmd.extend(["-c", container])
            
            cmd.append(pod_name)
            
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                check=False
            )
            
            if result.returncode == 0:
                return {
                    "success": True,
                    "command": " ".join(cmd),
                    "result": result.stdout,
                }
            else:
                return {
                    "success": False,
                    "error": result.stderr,
                }
        except Exception as e:
            logger.error(f"Error getting logs: {e}")
            return {
                "success": False,
                "error": str(e),
            }
    
    def _detect_code_smells(self, log_content: str) -> List[Dict[str, str]]:
        """Detect code smells in log content."""
        code_smells = []
        
        # Check for memory leaks
        if re.search(self.patterns["memory_leak"], log_content, re.IGNORECASE):
            code_smells.append({
                "type": "memory_leak",
                "description": "Possible memory leak detected. The application is using more memory than expected.",
                "recommendation": "Check for memory leaks in the application code. Look for objects that are not being garbage collected.",
            })
        
        # Check for connection timeouts
        if re.search(self.patterns["connection_timeout"], log_content, re.IGNORECASE):
            code_smells.append({
                "type": "connection_timeout",
                "description": "Connection timeouts detected. The application is having trouble connecting to external services.",
                "recommendation": "Check network connectivity and ensure that external services are available.",
            })
        
        # Check for resource exhaustion
        if re.search(self.patterns["resource_exhaustion"], log_content, re.IGNORECASE):
            code_smells.append({
                "type": "resource_exhaustion",
                "description": "Resource exhaustion detected. The application is running out of resources.",
                "recommendation": "Review resource requests and limits in the pod specification.",
            })
        
        return code_smells
    
    def _detect_errors(self, log_content: str) -> List[Dict[str, str]]:
        """Detect errors in log content."""
        errors = []
        
        # Split log content into lines
        lines = log_content.split("\n")
        
        for line in lines:
            # Skip empty lines
            if not line.strip():
                continue
            
            # Check for error patterns
            for pattern_name, pattern in self.patterns.items():
                if re.search(pattern, line, re.IGNORECASE):
                    # Skip warning pattern if the line contains an error pattern
                    if pattern_name == "warning" and re.search(self.patterns["exception"], line, re.IGNORECASE):
                        continue
                    
                    errors.append({
                        "type": pattern_name,
                        "line": line,
                        "explanation": self._explain_error(pattern_name, line),
                    })
                    
                    # Only match one pattern per line
                    break
        
        return errors
        
    def detect_error_patterns(self, log_content: str) -> List[Dict[str, str]]:
        """
        Detect error patterns in log content.
        
        Args:
            log_content: Log content to analyze
            
        Returns:
            List of detected error patterns
        """
        return self._detect_errors(log_content)
    
    def _explain_error(self, error_type: str, error_line: str) -> str:
        """Explain an error in plain English."""
        # Use pre-defined explanations if available
        if error_type in self.error_explanations:
            return self.error_explanations[error_type]
        
        # Default explanation
        return "This is a technical error that requires investigation."
    
    def _generate_summary(self, log_content: str) -> str:
        """Generate a summary of log content."""
        # Count error and warning lines
        error_count = len(re.findall(r"(?i)error|exception|fail|fatal", log_content))
        warning_count = len(re.findall(r"(?i)warn|warning", log_content))
        
        # Generate summary
        return f"Log analysis summary: {error_count} errors, {warning_count} warnings."
    
    def _generate_recommendations(self, log_content: str) -> List[str]:
        """Generate recommendations based on log content."""
        recommendations = []
        
        # Add general recommendations
        recommendations.append("Ensure that the application has sufficient resources (CPU, memory, disk).")
        recommendations.append("Check network connectivity between application components.")
        
        # Add specific recommendations based on detected patterns
        if re.search(self.patterns["memory_leak"], log_content, re.IGNORECASE):
            recommendations.append("Investigate potential memory leaks in the application.")
        
        if re.search(self.patterns["connection_timeout"], log_content, re.IGNORECASE):
            recommendations.append("Check network connectivity and service availability.")
        
        if re.search(self.patterns["permission_denied"], log_content, re.IGNORECASE):
            recommendations.append("Review RBAC settings and service account permissions.")
        
        return recommendations
