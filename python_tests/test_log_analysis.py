#!/usr/bin/env python3
"""
Test script for log analysis features.
"""

import logging
import sys
from rich.console import Console
from rich.panel import Panel
from rich.table import Table
from rich.text import Text

# Configure logging
logging.basicConfig(
    level=logging.DEBUG,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    filename="test_log_analysis.log"
)
logger = logging.getLogger("test-log-analysis")

# Add console handler for important messages
console_handler = logging.StreamHandler()
console_handler.setLevel(logging.INFO)
console_formatter = logging.Formatter('%(levelname)s: %(message)s')
console_handler.setFormatter(console_formatter)
logger.addHandler(console_handler)

def test_log_analyzer():
    """Test the log analyzer functionality."""
    print("\n=== Testing Log Analyzer ===")
    
    try:
        # Import the log analyzer
        from kubectl_mcp_tool.log_analysis.log_analyzer import LogAnalyzer
        
        # Create a log analyzer
        analyzer = LogAnalyzer()
        
        # Create a console
        console = Console()
        
        # Test sample log content
        sample_log = """
2025-03-24T10:15:30.123Z ERROR Failed to connect to database: connection timed out
2025-03-24T10:15:35.456Z WARN  High memory usage detected: 85% of available memory in use
2025-03-24T10:15:40.789Z ERROR Exception in thread "main" java.lang.OutOfMemoryError: Java heap space
2025-03-24T10:15:45.012Z INFO  Pod nginx-5869d7778c-glw6b started successfully
2025-03-24T10:15:50.345Z ERROR Permission denied: cannot access /var/log/kubernetes
2025-03-24T10:15:55.678Z WARN  Resource quota exceeded for namespace: default
2025-03-24T10:16:00.901Z ERROR Pod evicted due to node memory pressure
"""
        
        # Analyze the log content
        errors = analyzer.detect_error_patterns(sample_log)
        
        # Create a table for errors
        error_table = Table(title="Detected Errors", show_header=True, header_style="bold red")
        error_table.add_column("Type", style="cyan")
        error_table.add_column("Line", style="yellow")
        error_table.add_column("Explanation", style="green")
        
        # Add rows
        for error in errors:
            error_table.add_row(
                error["type"],
                error["line"],
                error["explanation"]
            )
        
        # Print the table
        console.print(error_table)
        
        # Create a panel for summary
        summary = analyzer._generate_summary(sample_log)
        summary_panel = Panel(
            Text(summary, style="green"),
            title="Log Analysis Summary",
            border_style="green"
        )
        
        # Print the summary
        console.print(summary_panel)
        
        # Create a table for recommendations
        recommendations = analyzer._generate_recommendations(sample_log)
        recommendation_table = Table(title="Recommendations", show_header=True, header_style="bold blue")
        recommendation_table.add_column("Recommendation", style="green")
        
        # Add rows
        for recommendation in recommendations:
            recommendation_table.add_row(recommendation)
        
        # Print the table
        console.print(recommendation_table)
        
        return True
    except Exception as e:
        print(f"Error testing log analyzer: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_code_smell_detection():
    """Test the code smell detection functionality."""
    print("\n=== Testing Code Smell Detection ===")
    
    try:
        # Import the log analyzer
        from kubectl_mcp_tool.log_analysis.log_analyzer import LogAnalyzer
        
        # Create a log analyzer
        analyzer = LogAnalyzer()
        
        # Create a console
        console = Console()
        
        # Test sample log content
        sample_log = """
2025-03-24T10:15:30.123Z ERROR Failed to connect to database: connection timed out
2025-03-24T10:15:35.456Z WARN  High memory usage detected: 85% of available memory in use
2025-03-24T10:15:40.789Z ERROR Exception in thread "main" java.lang.OutOfMemoryError: Java heap space
2025-03-24T10:15:45.012Z INFO  Pod nginx-5869d7778c-glw6b started successfully
2025-03-24T10:15:50.345Z ERROR Permission denied: cannot access /var/log/kubernetes
2025-03-24T10:15:55.678Z WARN  Resource quota exceeded for namespace: default
2025-03-24T10:16:00.901Z ERROR Pod evicted due to node memory pressure
2025-03-24T10:16:05.234Z ERROR Memory leak detected in container: nginx
"""
        
        # Detect code smells
        code_smells = analyzer._detect_code_smells(sample_log)
        
        # Create a table for code smells
        code_smell_table = Table(title="Detected Code Smells", show_header=True, header_style="bold magenta")
        code_smell_table.add_column("Type", style="cyan")
        code_smell_table.add_column("Description", style="yellow")
        code_smell_table.add_column("Recommendation", style="green")
        
        # Add rows
        for smell in code_smells:
            code_smell_table.add_row(
                smell["type"],
                smell["description"],
                smell["recommendation"]
            )
        
        # Print the table
        console.print(code_smell_table)
        
        return True
    except Exception as e:
        print(f"Error testing code smell detection: {e}")
        import traceback
        traceback.print_exc()
        return False

def main():
    """Run the log analysis tests."""
    try:
        # Test log analyzer
        analyzer_success = test_log_analyzer()
        
        # Test code smell detection
        code_smell_success = test_code_smell_detection()
        
        # Print summary
        print("\n=== Test Summary ===")
        print(f"Log Analyzer: {'PASS' if analyzer_success else 'FAIL'}")
        print(f"Code Smell Detection: {'PASS' if code_smell_success else 'FAIL'}")
        
        # Return overall success
        return 0 if analyzer_success and code_smell_success else 1
    except Exception as e:
        print(f"Error in test: {e}")
        import traceback
        traceback.print_exc()
        return 1

if __name__ == "__main__":
    sys.exit(main())
