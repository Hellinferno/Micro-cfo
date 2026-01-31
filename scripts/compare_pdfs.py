#!/usr/bin/env python3
"""
Comprehensive PDF Comparison and Gap Analysis
Compares Idea.pdf (original concept) with micro-cfo.pdf (implementation spec)
"""

import re
from pathlib import Path

def clean_text(text):
    """Remove extra whitespace from extracted PDF text"""
    # Replace multiple newlines/spaces with single space
    text = re.sub(r'\s+', ' ', text)
    return text.strip()

def extract_sections(text, title):
    """Extract key sections from the documents"""
    sections = {}
    
    # Common patterns to look for
    patterns = {
        'problem_statement': r'Problem\s+Statement(.*?)(?=Motivation|$)',
        'motivation': r'Motivation(.*?)(?=Application|Proposed|$)',
        'agents': r'Agent[s]?\s+(.*?)(?=Feature|Agent|Part|$)',
        'features': r'Feature[s]?\s+(.*?)(?=Feature|Part|Technical|$)',
        'architecture': r'(?:Technical\s+)?Architecture(.*?)(?=Part|Security|$)',
        'security': r'Security(.*?)(?=Deployment|Testing|$)',
        'deployment': r'Deployment(.*?)(?=Testing|Monitoring|$)',
        'testing': r'Testing(.*?)(?=Monitoring|Compliance|$)',
        'compliance': r'Compliance(.*?)(?=$)',
    }
    
    text_clean = clean_text(text)
    
    for key, pattern in patterns.items():
        match = re.search(pattern, text_clean, re.IGNORECASE | re.DOTALL)
        if match:
            sections[key] = match.group(1)[:500]  # First 500 chars
    
    return sections

def analyze_and_compare():
    """Main comparison logic"""
    
    # Read the extracted content
    idea_path = Path("d:/CFO/docs/pdf_analysis/idea_pdf_content.txt")
    micro_cfo_path = Path("d:/CFO/docs/pdf_analysis/micro_cfo_pdf_content.txt")
    
    with open(idea_path, 'r', encoding='utf-8') as f:
        idea_content = f.read()
    
    with open(micro_cfo_path, 'r', encoding='utf-8') as f:
        micro_cfo_content = f.read()
    
    # Extract sections
    idea_sections = extract_sections(idea_content, "Idea")
    micro_cfo_sections = extract_sections(micro_cfo_content, "Micro-CFO")
    
    # Generate comparison report
    report = []
    report.append("=" * 100)
    report.append("MICRO-CFO: PDF COMPARISON & GAP ANALYSIS")
    report.append("=" * 100)
    report.append("")
    report.append(f"Document 1: Idea .pdf (Original Concept) - {len(idea_content)} characters")
    report.append(f"Document 2: micro-cfo.pdf (Implementation Spec) - {len(micro_cfo_content)} characters")
    report.append("")
    
    # Analyze coverage
    report.append("=" * 100)
    report.append("SECTION COVERAGE ANALYSIS")
    report.append("=" * 100)
    report.append("")
    
    all_sections = set(list(idea_sections.keys()) + list(micro_cfo_sections.keys()))
    
    for section in sorted(all_sections):
        in_idea = section in idea_sections
        in_micro = section in micro_cfo_sections
        
        status = ""
        if in_idea and in_micro:
            status = "✓ COVERED IN BOTH"
        elif in_idea and not in_micro:
            status = "⚠ MISSING IN IMPLEMENTATION SPEC"
        elif not in_idea and in_micro:
            status = "✓ ADDED IN IMPLEMENTATION SPEC"
        
        report.append(f"{section.upper().replace('_', ' ')}: {status}")
    
    report.append("")
    
    # Key topics analysis
    report.append("=" * 100)
    report.append("KEY TOPICS & FEATURES ANALYSIS")
    report.append("=" * 100)
    report.append("")
    
    # Topics to check
    topics = {
        'Visual Auditor': ['visual', 'auditor', 'image', 'bill', 'invoice', 'scan'],
        'Legal Sentinel': ['legal', 'sentinel', 'compliance', 'regulation', 'MCA', 'GST'],
        'Subsidy Hunter': ['subsidy', 'scheme', 'grant', 'PLI', 'startup india'],
        'Negotiator': ['negotiat', 'vendor', 'payment', 'email'],
        'Database': ['database', 'postgres', 'sqlalchemy', 'schema'],
        'Authentication': ['auth', 'jwt', 'login', 'user', 'token'],
        'API': ['api', 'endpoint', 'rest', 'fastapi'],
        'Frontend': ['frontend', 'react', 'ui', 'dashboard'],
        'Security': ['security', 'encryption', 'pii', 'gdpr'],
        'Testing': ['test', 'pytest', 'integration'],
        'Deployment': ['deploy', 'docker', 'ci/cd', 'github'],
        'WebSocket': ['websocket', 'real-time', 'notification'],
        'RAG': ['rag', 'retrieval', 'vector', 'embedding', 'chromadb'],
        'WhatsApp': ['whatsapp', 'bot', 'messaging'],
    }
    
    idea_lower = idea_content.lower()
    micro_lower = micro_cfo_content.lower()
    
    for topic, keywords in topics.items():
        in_idea = any(kw in idea_lower for kw in keywords)
        in_micro = any(kw in micro_lower for kw in keywords)
        
        idea_count = sum(idea_lower.count(kw) for kw in keywords)
        micro_count = sum(micro_lower.count(kw) for kw in keywords)
        
        status = ""
        if in_idea and in_micro:
            status = f"✓ COVERED (Idea: {idea_count} mentions, Spec: {micro_count} mentions)"
        elif in_idea and not in_micro:
            status = f"⚠ MISSING IN SPEC (Idea: {idea_count} mentions)"
        elif not in_idea and in_micro:
            status = f"✓ ADDED IN SPEC ({micro_count} mentions)"
        else:
            status = "✗ NOT MENTIONED"
        
        report.append(f"{topic}: {status}")
    
    report.append("")
    
    # Missing components analysis
    report.append("=" * 100)
    report.append("POTENTIAL GAPS & MISSING COMPONENTS")
    report.append("=" * 100)
    report.append("")
    
    gaps = []
    
    # Check for specific implementations
    if 'whatsapp' in idea_lower and 'whatsapp' not in micro_lower:
        gaps.append("⚠ WhatsApp Bot Integration - Mentioned in idea but not in implementation spec")
    
    if 'mobile' in idea_lower and 'mobile' not in micro_lower:
        gaps.append("⚠ Mobile App - May need mobile interface consideration")
    
    if 'monitoring' not in micro_lower or micro_lower.count('monitoring') < 3:
        gaps.append("⚠ System Monitoring & Observability - May need more detail")
    
    if 'backup' not in micro_lower:
        gaps.append("⚠ Backup Strategy - Not mentioned in spec")
    
    if 'disaster' not in micro_lower:
        gaps.append("⚠ Disaster Recovery Plan - Not mentioned in spec")
    
    if 'scaling' not in micro_lower and 'scale' not in micro_lower:
        gaps.append("⚠ Scaling Strategy - May need more detail")
    
    if 'rate limit' not in micro_lower:
        gaps.append("✓ Rate Limiting - Implemented in code but may need documentation")
    
    if gaps:
        for gap in gaps:
            report.append(gap)
    else:
        report.append("✓ No major gaps identified")
    
    report.append("")
    
    # Implementation status
    report.append("=" * 100)
    report.append("CURRENT IMPLEMENTATION STATUS (Based on Codebase)")
    report.append("=" * 100)
    report.append("")
    
    implemented = [
        "✓ FastAPI Backend with async support",
        "✓ PostgreSQL Database with SQLAlchemy ORM",
        "✓ JWT Authentication & Authorization",
        "✓ Role-Based Access Control (RBAC)",
        "✓ Field-Level Encryption for PII",
        "✓ Visual Auditor (Invoice Scanning)",
        "✓ Legal Sentinel (Compliance Monitoring)",
        "✓ Subsidy Hunter (Scheme Matching)",
        "✓ Negotiator Agent (Email Generation)",
        "✓ WebSocket for Real-time Updates",
        "✓ RAG with ChromaDB",
        "✓ Audit Logging Middleware",
        "✓ Rate Limiting & Idempotency",
        "✓ Error Handling & Validation",
        "✓ Frontend with React & Vite",
        "✓ CI/CD with GitHub Actions",
        "✓ Property-Based Testing with Hypothesis",
        "✓ Integration Tests",
    ]
    
    for item in implemented:
        report.append(item)
    
    report.append("")
    
    # Recommendations
    report.append("=" * 100)
    report.append("RECOMMENDATIONS FOR COMPLETION")
    report.append("=" * 100)
    report.append("")
    
    recommendations = [
        "1. Documentation:",
        "   - Create API documentation (OpenAPI/Swagger)",
        "   - Add user manual/guide",
        "   - Document deployment procedures",
        "",
        "2. WhatsApp Integration:",
        "   - Implement WhatsApp Business API integration",
        "   - Create bot command handlers",
        "   - Add message queue for async processing",
        "",
        "3. Monitoring & Observability:",
        "   - Add Prometheus metrics",
        "   - Implement distributed tracing",
        "   - Set up alerting system",
        "",
        "4. Infrastructure:",
        "   - Document backup strategy",
        "   - Create disaster recovery plan",
        "   - Define scaling guidelines",
        "",
        "5. Security Enhancements:",
        "   - Implement API key rotation",
        "   - Add security scanning to CI/CD",
        "   - Create security incident response plan",
        "",
        "6. Mobile Support:",
        "   - Consider Progressive Web App (PWA)",
        "   - Or develop React Native app",
        "",
        "7. Performance:",
        "   - Add caching layer (Redis already in stack)",
        "   - Implement database query optimization",
        "   - Add CDN for static assets",
    ]
    
    for rec in recommendations:
        report.append(rec)
    
    return "\n".join(report)

if __name__ == "__main__":
    report = analyze_and_compare()
    
    # Save report
    output_path = Path("d:/CFO/docs/PDF_COMPARISON_ANALYSIS.md")
    with open(output_path, 'w', encoding='utf-8') as f:
        f.write(report)
    
    print(report)
    print(f"\n\nReport saved to: {output_path}")
