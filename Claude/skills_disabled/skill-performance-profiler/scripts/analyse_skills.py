#!/usr/bin/env python3
"""
Skill Performance Profiler - Analyses skill usage patterns and token consumption
"""

import json
import re
from collections import defaultdict, Counter
from datetime import datetime
from typing import Dict, List, Tuple, Set
import sys


class SkillAnalyser:
    def __init__(self):
        self.skill_invocations = defaultdict(list)
        self.skill_tokens = defaultdict(list)
        self.skill_cooccurrences = defaultdict(Counter)
        self.conversation_skills = defaultdict(set)

    def estimate_tokens(self, text: str) -> int:
        """Estimate token count using rough approximation (4 chars ≈ 1 token)"""
        if not text:
            return 0
        return len(text) // 4

    def extract_skill_mentions(self, content: str) -> Set[str]:
        """Extract skill names from conversation content"""
        skills = set()

        # Pattern 1: Direct mentions like "using the docx skill"
        pattern1 = r'(?:using|use|used|invoking|invoked|calling|called|reading|read)\s+(?:the\s+)?([a-z0-9-]+)\s+skill'
        matches1 = re.findall(pattern1, content.lower())
        skills.update(matches1)

        # Pattern 2: File paths like /mnt/skills/.../skill-name/SKILL.md
        pattern2 = r'/mnt/skills/(?:public|user|examples)/([a-z0-9-]+)/SKILL\.md'
        matches2 = re.findall(pattern2, content.lower())
        skills.update(matches2)

        # Pattern 3: Tool calls to file_read with skill paths
        pattern3 = r'file_read.*?/mnt/skills/[^/]+/([a-z0-9-]+)/'
        matches3 = re.findall(pattern3, content.lower())
        skills.update(matches3)

        return skills

    def parse_conversation(self, chat_content: str, updated_at: str = None):
        """Parse a single conversation and extract skill usage"""
        # Extract timestamp
        timestamp = updated_at or datetime.now().isoformat()

        # Estimate total tokens in conversation
        total_tokens = self.estimate_tokens(chat_content)

        # Extract skills used in this conversation
        skills = self.extract_skill_mentions(chat_content)

        # Record invocations and token usage
        for skill in skills:
            self.skill_invocations[skill].append({
                'timestamp': timestamp,
                'total_conversation_tokens': total_tokens
            })

            # Estimate tokens for this skill (rough approximation)
            # Assume skill content is mentioned multiple times, allocate proportionally
            skill_token_estimate = total_tokens // max(len(skills), 1)
            self.skill_tokens[skill].append(skill_token_estimate)

        # Track co-occurrence patterns
        skills_list = list(skills)
        for i, skill1 in enumerate(skills_list):
            self.conversation_skills[timestamp].add(skill1)
            for skill2 in skills_list[i+1:]:
                self.skill_cooccurrences[skill1][skill2] += 1
                self.skill_cooccurrences[skill2][skill1] += 1

    def calculate_metrics(self) -> Dict:
        """Calculate comprehensive performance metrics"""
        metrics = {
            'skills': {},
            'summary': {},
            'consolidation_opportunities': [],
            'trends': {}
        }

        # Per-skill metrics
        for skill, invocations in self.skill_invocations.items():
            tokens = self.skill_tokens[skill]

            metrics['skills'][skill] = {
                'invocation_count': len(invocations),
                'total_tokens': sum(tokens),
                'average_tokens': sum(tokens) / len(tokens) if tokens else 0,
                'min_tokens': min(tokens) if tokens else 0,
                'max_tokens': max(tokens) if tokens else 0,
                'category': self._categorise_skill(sum(tokens) / len(tokens) if tokens else 0),
                'first_used': min(inv['timestamp'] for inv in invocations),
                'last_used': max(inv['timestamp'] for inv in invocations),
                'cooccurs_with': dict(self.skill_cooccurrences[skill].most_common(5))
            }

        # Summary statistics
        if metrics['skills']:
            all_invocations = sum(s['invocation_count'] for s in metrics['skills'].values())
            all_tokens = sum(s['total_tokens'] for s in metrics['skills'].values())

            metrics['summary'] = {
                'total_skills_used': len(metrics['skills']),
                'total_invocations': all_invocations,
                'total_tokens_consumed': all_tokens,
                'average_tokens_per_invocation': all_tokens / all_invocations if all_invocations else 0,
                'most_used_skill': max(metrics['skills'].items(),
                                      key=lambda x: x[1]['invocation_count'])[0],
                'heaviest_skill': max(metrics['skills'].items(),
                                     key=lambda x: x[1]['average_tokens'])[0],
                'lightest_skill': min(metrics['skills'].items(),
                                     key=lambda x: x[1]['average_tokens'])[0]
            }

        # Consolidation opportunities
        metrics['consolidation_opportunities'] = self._find_consolidation_opportunities()

        return metrics

    def _categorise_skill(self, avg_tokens: float) -> str:
        """Categorise skill by token weight"""
        if avg_tokens < 500:
            return "Lightweight"
        elif avg_tokens < 2000:
            return "Medium"
        elif avg_tokens < 5000:
            return "Heavy"
        else:
            return "Very Heavy"

    def _find_consolidation_opportunities(self) -> List[Dict]:
        """Identify skills that are frequently used together"""
        opportunities = []

        # Find skill pairs with high co-occurrence
        processed_pairs = set()
        for skill1, cooccurs in self.skill_cooccurrences.items():
            for skill2, count in cooccurs.most_common():
                pair = tuple(sorted([skill1, skill2]))
                if pair in processed_pairs or count < 2:
                    continue

                processed_pairs.add(pair)

                # Calculate co-occurrence rate
                skill1_total = len(self.skill_invocations[skill1])
                skill2_total = len(self.skill_invocations[skill2])
                cooccurrence_rate = count / min(skill1_total, skill2_total)

                if cooccurrence_rate >= 0.5:  # Used together in 50%+ of cases
                    opportunities.append({
                        'skills': list(pair),
                        'cooccurrence_count': count,
                        'cooccurrence_rate': round(cooccurrence_rate * 100, 1),
                        'recommendation': f"Consider consolidating {pair[0]} and {pair[1]} - used together {cooccurrence_rate*100:.0f}% of the time"
                    })

        return sorted(opportunities, key=lambda x: x['cooccurrence_rate'], reverse=True)


def main():
    """Main analysis function"""
    if len(sys.argv) < 2:
        print("Usage: python analyse_skills.py <conversations_json_file>")
        print("\nExpected JSON format:")
        print('''{
  "conversations": [
    {
      "content": "conversation text with skill mentions...",
      "updated_at": "2025-10-22T10:30:00Z"
    }
  ]
}''')
        sys.exit(1)

    input_file = sys.argv[1]

    # Load conversation data
    try:
        with open(input_file, 'r') as f:
            data = json.load(f)
    except Exception as e:
        print(f"Error loading file: {e}")
        sys.exit(1)

    # Initialize analyser
    analyser = SkillAnalyser()

    # Process conversations
    conversations = data.get('conversations', [])
    print(f"Processing {len(conversations)} conversations...")

    for conv in conversations:
        content = conv.get('content', '')
        updated_at = conv.get('updated_at')
        analyser.parse_conversation(content, updated_at)

    # Calculate metrics
    metrics = analyser.calculate_metrics()

    # Output results
    output_file = input_file.replace('.json', '_analysis.json')
    with open(output_file, 'w') as f:
        json.dump(metrics, f, indent=2)

    print(f"\n✅ Analysis complete!")
    print(f"   Results saved to: {output_file}")
    print(f"\n📊 Summary:")
    print(f"   Skills analysed: {metrics['summary'].get('total_skills_used', 0)}")
    print(f"   Total invocations: {metrics['summary'].get('total_invocations', 0)}")
    print(f"   Total tokens: {metrics['summary'].get('total_tokens_consumed', 0):,}")

    if metrics['consolidation_opportunities']:
        print(f"\n💡 Consolidation opportunities found: {len(metrics['consolidation_opportunities'])}")


if __name__ == '__main__':
    main()
