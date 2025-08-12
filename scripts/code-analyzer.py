#!/usr/bin/env python3
"""
Comprehensive Code Analyzer for ReAgent Sydney V03
Executes various code quality, security, and performance checks
"""

import os
import sys
import json
import subprocess
from pathlib import Path
from typing import Dict, List, Optional
from dataclasses import dataclass
from datetime import datetime

@dataclass
class AnalysisResult:
    """Holds results from a single analysis check"""
    check_name: str
    severity: str
    issues_found: int
    details: List[str]
    recommendations: List[str]

class CodeAnalyzer:
    """Main analyzer class for comprehensive code analysis"""
    
    def __init__(self, target_path: str = ".", focus: str = "all", depth: str = "deep"):
        self.target_path = Path(target_path)
        self.focus = focus
        self.depth = depth
        self.results: List[AnalysisResult] = []
        
    def analyze(self) -> Dict:
        """Run all analysis checks based on focus area"""
        print(f"🔍 Starting code analysis...")
        print(f"   Target: {self.target_path}")
        print(f"   Focus: {self.focus}")
        print(f"   Depth: {self.depth}\n")
        
        if self.focus in ["all", "quality"]:
            self.check_code_quality()
            
        if self.focus in ["all", "security"]:
            self.check_security()
            
        if self.focus in ["all", "performance"]:
            self.check_performance()
            
        if self.focus in ["all", "architecture"]:
            self.check_architecture()
            
        return self.generate_report()
    
    def check_code_quality(self):
        """Check code quality issues"""
        print("📊 Analyzing code quality...")
        
        # Check for test files in wrong location
        test_files_in_root = []
        if self.target_path.name == "backend" or self.target_path == Path("."):
            backend_path = self.target_path / "backend" if self.target_path == Path(".") else self.target_path
            for file in backend_path.glob("test_*.py"):
                test_files_in_root.append(str(file))
        
        # Check for debug statements
        debug_patterns = self.search_patterns([
            r'print\s*\(',
            r'console\.log',
            r'DEBUG',
            r'TODO|FIXME|HACK|XXX'
        ])
        
        # Check for duplicate files
        duplicate_patterns = self.find_duplicate_names()
        
        result = AnalysisResult(
            check_name="Code Quality",
            severity="MEDIUM" if test_files_in_root or debug_patterns > 50 else "LOW",
            issues_found=len(test_files_in_root) + debug_patterns + len(duplicate_patterns),
            details=[
                f"Test files in root: {len(test_files_in_root)}",
                f"Debug statements: {debug_patterns}",
                f"Duplicate implementations: {len(duplicate_patterns)}"
            ],
            recommendations=[
                "Move test files to tests/ directory",
                "Replace print() with proper logging",
                "Consolidate duplicate implementations"
            ]
        )
        self.results.append(result)
    
    def check_security(self):
        """Check security vulnerabilities"""
        print("🔒 Analyzing security...")
        
        # Check for hardcoded credentials
        credential_patterns = self.search_patterns([
            r'(api[_-]?key|secret|token|password|credential)\s*=\s*["\']',
            r'sk-[a-zA-Z0-9]+',
            r'(Bearer|Basic)\s+[a-zA-Z0-9+/=]+',
        ])
        
        # Check for SQL injection risks
        sql_patterns = self.search_patterns([
            r'f["\']{.*SELECT.*WHERE',
            r'\.format\(.*SELECT.*WHERE',
            r'\+.*SELECT.*WHERE'
        ])
        
        # Check authentication
        auth_issues = self.check_authentication()
        
        result = AnalysisResult(
            check_name="Security",
            severity="CRITICAL" if credential_patterns > 10 or sql_patterns > 0 else "HIGH",
            issues_found=credential_patterns + sql_patterns + auth_issues,
            details=[
                f"Potential credentials: {credential_patterns}",
                f"SQL injection risks: {sql_patterns}",
                f"Authentication issues: {auth_issues}"
            ],
            recommendations=[
                "Use environment variables for all credentials",
                "Implement parameterized queries",
                "Enable authentication by default",
                "Add rate limiting and CSRF protection"
            ]
        )
        self.results.append(result)
    
    def check_performance(self):
        """Check performance issues"""
        print("⚡ Analyzing performance...")
        
        # Check for blocking operations
        blocking_patterns = self.search_patterns([
            r'loop\.run_until_complete',
            r'time\.sleep\(',
            r'requests\.',  # Sync requests in async code
        ])
        
        # Check for missing async
        sync_in_async = self.search_patterns([
            r'def\s+(?!async)[a-z_]+.*async',
            r'open\(',  # Sync file operations
        ])
        
        result = AnalysisResult(
            check_name="Performance",
            severity="HIGH" if blocking_patterns > 5 else "MEDIUM",
            issues_found=blocking_patterns + sync_in_async,
            details=[
                f"Blocking operations: {blocking_patterns}",
                f"Sync in async context: {sync_in_async}"
            ],
            recommendations=[
                "Replace blocking operations with async equivalents",
                "Implement connection pooling",
                "Add caching for expensive operations",
                "Use asyncio.gather() for parallel operations"
            ]
        )
        self.results.append(result)
    
    def check_architecture(self):
        """Check architecture and design patterns"""
        print("🏗️ Analyzing architecture...")
        
        # Check file organization
        org_score = self.check_organization()
        
        # Check for circular imports
        circular_imports = self.check_circular_imports()
        
        # Check coupling
        coupling_score = self.check_coupling()
        
        result = AnalysisResult(
            check_name="Architecture",
            severity="MEDIUM" if org_score < 60 else "LOW",
            issues_found=circular_imports + (100 - org_score),
            details=[
                f"Organization score: {org_score}/100",
                f"Circular imports: {circular_imports}",
                f"Coupling score: {coupling_score}/100"
            ],
            recommendations=[
                "Implement clean architecture principles",
                "Separate concerns by domain",
                "Use dependency injection",
                "Create clear module boundaries"
            ]
        )
        self.results.append(result)
    
    def search_patterns(self, patterns: List[str]) -> int:
        """Search for patterns in code files"""
        count = 0
        extensions = ['.py', '.js', '.ts', '.jsx', '.tsx']
        
        for ext in extensions:
            for file_path in self.target_path.rglob(f'*{ext}'):
                if 'node_modules' in str(file_path) or '.git' in str(file_path):
                    continue
                    
                try:
                    with open(file_path, 'r', encoding='utf-8') as f:
                        content = f.read()
                        for pattern in patterns:
                            import re
                            matches = re.findall(pattern, content, re.IGNORECASE)
                            count += len(matches)
                except:
                    pass
                    
        return count
    
    def find_duplicate_names(self) -> List[str]:
        """Find files with similar names suggesting duplication"""
        duplicates = []
        file_names = {}
        
        for file_path in self.target_path.rglob('*.py'):
            base_name = file_path.stem
            if base_name in file_names:
                duplicates.append(f"{base_name}: {file_names[base_name]} vs {file_path}")
            else:
                file_names[base_name] = file_path
                
        return duplicates
    
    def check_authentication(self) -> int:
        """Check for authentication issues"""
        issues = 0
        
        # Check if auth is disabled by default
        config_file = self.target_path / "backend" / "config.py"
        if config_file.exists():
            with open(config_file, 'r') as f:
                if 'REQUIRE_API_KEY: bool = False' in f.read():
                    issues += 1
                    
        # Check for weak auth patterns
        weak_patterns = self.search_patterns([
            r'if.*==.*API_KEY',  # Direct comparison
            r'password\s*==',     # Direct password comparison
        ])
        
        return issues + weak_patterns
    
    def check_organization(self) -> int:
        """Score the code organization (0-100)"""
        score = 100
        
        # Check for test files in wrong place
        if list(Path("backend").glob("test_*.py")):
            score -= 20
            
        # Check for proper directory structure
        expected_dirs = ["api", "services", "models", "tests", "utils"]
        backend_path = self.target_path / "backend"
        for dir_name in expected_dirs:
            if not (backend_path / dir_name).exists():
                score -= 10
                
        return max(0, score)
    
    def check_circular_imports(self) -> int:
        """Detect potential circular imports"""
        # Simplified check - count cross-references between modules
        cross_refs = 0
        
        for file_path in (self.target_path / "backend").rglob("*.py"):
            try:
                with open(file_path, 'r') as f:
                    content = f.read()
                    # Check for imports from parent directories
                    if 'from ..' in content:
                        cross_refs += 1
            except:
                pass
                
        return cross_refs
    
    def check_coupling(self) -> int:
        """Score the coupling (0-100, higher is better)"""
        score = 100
        
        # Check for direct service imports
        direct_imports = self.search_patterns([
            r'from services\.[a-z_]+\s+import\s+[A-Z]',
            r'from api\.[a-z_]+\s+import\s+[A-Z]',
        ])
        
        score -= min(50, direct_imports * 2)
        return max(0, score)
    
    def generate_report(self) -> Dict:
        """Generate final analysis report"""
        total_issues = sum(r.issues_found for r in self.results)
        critical_issues = sum(1 for r in self.results if r.severity == "CRITICAL")
        high_issues = sum(1 for r in self.results if r.severity == "HIGH")
        
        # Calculate overall score
        severity_weights = {"CRITICAL": 25, "HIGH": 15, "MEDIUM": 10, "LOW": 5}
        total_weight = sum(severity_weights.get(r.severity, 0) for r in self.results)
        max_weight = len(self.results) * 25
        overall_score = max(0, 100 - (total_weight / max_weight * 100)) if max_weight > 0 else 100
        
        report = {
            "timestamp": datetime.now().isoformat(),
            "target": str(self.target_path),
            "focus": self.focus,
            "depth": self.depth,
            "overall_score": round(overall_score),
            "total_issues": total_issues,
            "critical_issues": critical_issues,
            "high_issues": high_issues,
            "results": [
                {
                    "check": r.check_name,
                    "severity": r.severity,
                    "issues": r.issues_found,
                    "details": r.details,
                    "recommendations": r.recommendations
                }
                for r in self.results
            ]
        }
        
        return report

def print_report(report: Dict, format: str = "text"):
    """Print analysis report in specified format"""
    
    if format == "json":
        print(json.dumps(report, indent=2))
        return
        
    # Text format
    print("\n" + "="*60)
    print("📋 CODE ANALYSIS REPORT")
    print("="*60)
    print(f"📅 Timestamp: {report['timestamp']}")
    print(f"📁 Target: {report['target']}")
    print(f"🎯 Focus: {report['focus']}")
    print(f"🔍 Depth: {report['depth']}")
    print()
    
    # Overall score with color
    score = report['overall_score']
    grade = "A" if score >= 90 else "B" if score >= 80 else "C" if score >= 70 else "D" if score >= 60 else "F"
    print(f"📊 OVERALL SCORE: {score}/100 (Grade: {grade})")
    print(f"⚠️  Total Issues: {report['total_issues']}")
    print(f"🔴 Critical: {report['critical_issues']}")
    print(f"🟠 High: {report['high_issues']}")
    print()
    
    # Detailed results
    print("📌 DETAILED FINDINGS:")
    print("-"*60)
    
    for result in report['results']:
        severity_icon = "🔴" if result['severity'] == "CRITICAL" else "🟠" if result['severity'] == "HIGH" else "🟡" if result['severity'] == "MEDIUM" else "🟢"
        print(f"\n{severity_icon} {result['check']} ({result['severity']})")
        print(f"   Issues Found: {result['issues']}")
        
        print("   Details:")
        for detail in result['details']:
            print(f"   • {detail}")
            
        print("   Recommendations:")
        for rec in result['recommendations'][:3]:  # Top 3 recommendations
            print(f"   → {rec}")
    
    print("\n" + "="*60)
    print("✅ Analysis Complete!")
    print("="*60)

def main():
    """Main entry point"""
    import argparse
    
    parser = argparse.ArgumentParser(description="Comprehensive Code Analyzer")
    parser.add_argument("target", nargs="?", default=".", help="Target directory to analyze")
    parser.add_argument("--focus", choices=["all", "quality", "security", "performance", "architecture"], 
                       default="all", help="Analysis focus area")
    parser.add_argument("--depth", choices=["quick", "deep"], default="deep", 
                       help="Analysis depth")
    parser.add_argument("--format", choices=["text", "json", "report"], default="text",
                       help="Output format")
    
    args = parser.parse_args()
    
    # Run analysis
    analyzer = CodeAnalyzer(args.target, args.focus, args.depth)
    report = analyzer.analyze()
    
    # Output results
    if args.format == "report":
        # Save detailed report to file
        with open("CODE_ANALYSIS_REPORT.json", "w") as f:
            json.dump(report, f, indent=2)
        print(f"✅ Report saved to CODE_ANALYSIS_REPORT.json")
        print_report(report, "text")
    else:
        print_report(report, args.format)
    
    # Exit with appropriate code
    sys.exit(0 if report['overall_score'] >= 70 else 1)

if __name__ == "__main__":
    main()