#!/usr/bin/env python3
"""
Generate formatted reports from skill analysis data
"""

import json
import sys
from datetime import datetime


def generate_markdown_report(metrics: dict) -> str:
    """Generate a comprehensive markdown report"""
    report = []
    
    # Header
    report.append("# Skill Performance Analysis Report")
    report.append(f"\n*Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}*\n")
    
    # Executive Summary
    summary = metrics.get('summary', {})
    report.append("## Executive Summary\n")
    report.append(f"- **Skills Analyzed**: {summary.get('total_skills_used', 0)}")
    report.append(f"- **Total Invocations**: {summary.get('total_invocations', 0)}")
    report.append(f"- **Total Token Consumption**: {summary.get('total_tokens_consumed', 0):,}")
    report.append(f"- **Average Tokens per Invocation**: {summary.get('average_tokens_per_invocation', 0):.0f}")
    report.append(f"- **Most Frequently Used**: `{summary.get('most_used_skill', 'N/A')}`")
    report.append(f"- **Heaviest (Avg Tokens)**: `{summary.get('heaviest_skill', 'N/A')}`")
    report.append(f"- **Lightest (Avg Tokens)**: `{summary.get('lightest_skill', 'N/A')}`\n")
    
    # Skills by Category
    skills = metrics.get('skills', {})
    categories = {'Lightweight': [], 'Medium': [], 'Heavy': [], 'Very Heavy': []}
    
    for skill, data in skills.items():
        categories[data['category']].append((skill, data))
    
    report.append("## Skills by Weight Category\n")
    for category in ['Very Heavy', 'Heavy', 'Medium', 'Lightweight']:
        if categories[category]:
            report.append(f"### {category} ({len(categories[category])} skills)\n")
            for skill, data in sorted(categories[category], 
                                     key=lambda x: x[1]['average_tokens'], 
                                     reverse=True):
                report.append(f"**`{skill}`**")
                report.append(f"- Invocations: {data['invocation_count']}")
                report.append(f"- Average tokens: {data['average_tokens']:.0f}")
                report.append(f"- Total tokens: {data['total_tokens']:,}")
                report.append(f"- Token range: {data['min_tokens']:.0f} - {data['max_tokens']:.0f}\n")
    
    # Most Used Skills
    report.append("## Top 10 Most Frequently Invoked Skills\n")
    top_skills = sorted(skills.items(), 
                       key=lambda x: x[1]['invocation_count'], 
                       reverse=True)[:10]
    
    for i, (skill, data) in enumerate(top_skills, 1):
        report.append(f"{i}. **`{skill}`** - {data['invocation_count']} invocations "
                     f"({data['total_tokens']:,} total tokens)")
    report.append("")
    
    # Token Efficiency Analysis
    report.append("## Token Efficiency Rankings\n")
    report.append("### Most Efficient (Lowest Avg Tokens)\n")
    efficient = sorted(skills.items(), 
                      key=lambda x: x[1]['average_tokens'])[:5]
    for i, (skill, data) in enumerate(efficient, 1):
        report.append(f"{i}. **`{skill}`** - {data['average_tokens']:.0f} avg tokens")
    
    report.append("\n### Least Efficient (Highest Avg Tokens)\n")
    inefficient = sorted(skills.items(), 
                        key=lambda x: x[1]['average_tokens'], 
                        reverse=True)[:5]
    for i, (skill, data) in enumerate(inefficient, 1):
        report.append(f"{i}. **`{skill}`** - {data['average_tokens']:.0f} avg tokens")
    report.append("")
    
    # Consolidation Opportunities
    opportunities = metrics.get('consolidation_opportunities', [])
    if opportunities:
        report.append("## Consolidation Opportunities\n")
        report.append("Skills frequently used together may benefit from consolidation:\n")
        for opp in opportunities:
            skills_str = " + ".join(f"`{s}`" for s in opp['skills'])
            report.append(f"- {skills_str}")
            report.append(f"  - Co-occurrence: {opp['cooccurrence_count']} times "
                         f"({opp['cooccurrence_rate']}% rate)")
            report.append(f"  - {opp['recommendation']}\n")
    else:
        report.append("## Consolidation Opportunities\n")
        report.append("No significant consolidation opportunities detected.\n")
    
    # Co-occurrence Patterns
    report.append("## Skill Co-occurrence Patterns\n")
    report.append("Skills most frequently used together in conversations:\n")
    
    # Get skills with co-occurrences
    skills_with_cooccur = [(s, d) for s, d in skills.items() 
                           if d.get('cooccurs_with')]
    skills_with_cooccur.sort(key=lambda x: sum(x[1]['cooccurs_with'].values()), 
                            reverse=True)
    
    for skill, data in skills_with_cooccur[:10]:
        if data.get('cooccurs_with'):
            report.append(f"**`{skill}`** frequently appears with:")
            for partner, count in list(data['cooccurs_with'].items())[:3]:
                report.append(f"  - `{partner}` ({count} times)")
            report.append("")
    
    return "\n".join(report)


def generate_csv_export(metrics: dict) -> str:
    """Generate CSV export of skill metrics"""
    lines = []
    lines.append("Skill,Invocations,Total Tokens,Average Tokens,Min Tokens,Max Tokens,Category,First Used,Last Used")
    
    for skill, data in sorted(metrics.get('skills', {}).items()):
        lines.append(f"{skill},{data['invocation_count']},{data['total_tokens']},"
                    f"{data['average_tokens']:.2f},{data['min_tokens']:.0f},"
                    f"{data['max_tokens']:.0f},{data['category']},"
                    f"{data['first_used']},{data['last_used']}")
    
    return "\n".join(lines)


def main():
    """Generate reports from analysis results"""
    if len(sys.argv) < 2:
        print("Usage: python generate_report.py <analysis_json_file> [format]")
        print("Formats: markdown (default), csv, both")
        sys.exit(1)
    
    input_file = sys.argv[1]
    format_type = sys.argv[2] if len(sys.argv) > 2 else "markdown"
    
    # Load analysis data
    try:
        with open(input_file, 'r') as f:
            metrics = json.load(f)
    except Exception as e:
        print(f"Error loading file: {e}")
        sys.exit(1)
    
    # Generate reports
    base_name = input_file.replace('_analysis.json', '').replace('.json', '')
    
    if format_type in ['markdown', 'both']:
        markdown = generate_markdown_report(metrics)
        md_file = f"{base_name}_report.md"
        with open(md_file, 'w') as f:
            f.write(markdown)
        print(f"✅ Markdown report: {md_file}")
    
    if format_type in ['csv', 'both']:
        csv = generate_csv_export(metrics)
        csv_file = f"{base_name}_export.csv"
        with open(csv_file, 'w') as f:
            f.write(csv)
        print(f"✅ CSV export: {csv_file}")


if __name__ == '__main__':
    main()
