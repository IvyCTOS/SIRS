# -*- coding: utf-8 -*-
"""
Output Aggregator - FIXED
Handles all severity levels and proper formatting
"""

from datetime import datetime
from typing import Dict, List, Any
from collections import defaultdict
import sys
import io

# Ensure UTF-8 encoding for console output
if sys.stdout.encoding != 'utf-8':
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')


class ConsoleOutputAggregator:
    def __init__(self):
        """Initialize aggregator with configuration"""
        self.insights = []
        
        # Define severity order (lower number = higher priority)
        self.severity_order = {
            'critical': 0,
            'high': 1,
            'medium': 2,
            'low': 3,
            'positive': 4
        }
        
        # Define label order for better grouping
        self.label_priority = {
            '🔴 High Utilization': 1,
            '🟠 Moderate Utilization': 2,
            '🟠 Missed Payments': 3,
            '🟡 Frequent Applications': 4,
            '🟡 Pending Applications': 5,
            '🟡 High Decline Rate': 6,
            '🟣 Thin Credit File': 7,
            '⚪ Short Credit History': 8,
            '⚪ Recent Enquiries': 9,
            '⚪ Trade Reference Issues': 10,
            '⚫ Legal Risk': 11,
            '🔵 Lender Concentration': 12,
            '🔵 Secured Debt Heavy': 13,
            '🟢 Positive Pattern': 14,
            '🟢 Low Utilization': 15,
            '🟢 Long Credit History': 16,
            '🟢 Low Application Rate': 17
        }
        
    def add_insight(self, insight: Dict[str, Any]) -> None:
        """Add a single insight to the collection"""
        if not isinstance(insight, dict):
            raise ValueError("Insight must be a dictionary")
        
        # Ensure required fields exist
        required_fields = {
            'label': '',
            'message': '',
            'recommendation': '',
            'severity': 'medium',
            'type': ''
        }
        
        # Update with provided values, using defaults for missing fields
        insight_data = {**required_fields, **insight}
        
        # Add metadata
        insight_data['timestamp'] = datetime.now().isoformat()
        
        self.insights.append(insight_data)

    def group_insights(self, grouping_key: str = 'label') -> Dict[str, List[Dict]]:
        """Group insights by specified key"""
        grouped = defaultdict(list)
        for insight in self.insights:
            key = insight.get(grouping_key, 'other')
            grouped[key].append(insight)
        return grouped

    def _sort_insights(self, insights: List[Dict]) -> List[Dict]:
        """Sort insights by severity and timestamp"""
        return sorted(
            insights,
            key=lambda x: (
                self.severity_order.get(x.get('severity', 'medium'), 99),
                x.get('timestamp', '')
            )
        )
    
    def _sort_labels(self, labels: List[str]) -> List[str]:
        """Sort labels by predefined priority"""
        return sorted(
            labels,
            key=lambda x: self.label_priority.get(x, 99)
        )

    def print_report(self) -> None:
        """Print formatted report to console"""
        if not self.insights:
            print("No insights to display")
            return

        print("\n" + "="*70)
        print("Credit Behavior Insight Report".center(70))
        print("="*70)
        print(f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        print(f"Total Insights: {len(self.insights)}")
        print("="*70)

        # Group and sort insights
        grouped_insights = self.group_insights()
        sorted_labels = self._sort_labels(list(grouped_insights.keys()))
        
        # Count by severity
        severity_counts = defaultdict(int)
        for insight in self.insights:
            severity_counts[insight.get('severity', 'medium')] += 1
        
        # Print severity summary
        if severity_counts:
            print("\nSummary by Severity:")
            print("-" * 70)
            if severity_counts.get('critical'):
                print(f"  ⛔ Critical: {severity_counts['critical']}")
            if severity_counts.get('high'):
                print(f"  🔴 High: {severity_counts['high']}")
            if severity_counts.get('medium'):
                print(f"  🟡 Medium: {severity_counts['medium']}")
            if severity_counts.get('low'):
                print(f"  🔵 Low: {severity_counts['low']}")
            if severity_counts.get('positive'):
                print(f"  ✅ Positive: {severity_counts['positive']}")
        
        # Print detailed insights
        for label in sorted_labels:
            insights = grouped_insights[label]
            
            print(f"\n{'='*70}")
            print(f"{label}")
            print("="*70)
            
            sorted_insights = self._sort_insights(insights)
            for idx, insight in enumerate(sorted_insights, 1):
                insight_type = insight.get('type', 'Unknown')
                message = insight.get('message', 'No message')
                recommendation = insight.get('recommendation', '')
                severity = insight.get('severity', 'medium')
                
                # Format severity indicator
                severity_icon = {
                    'critical': '⛔',
                    'high': '🔴',
                    'medium': '🟡',
                    'low': '🔵',
                    'positive': '✅'
                }.get(severity, '•')
                
                print(f"\n{idx}. {insight_type}")
                print(f"   {severity_icon} {message}")
                
                if recommendation:
                    print(f"\n   💡 Recommendation:")
                    # Wrap long recommendations
                    rec_lines = self._wrap_text(recommendation, 64)
                    for line in rec_lines:
                        print(f"      {line}")
                
                # Show additional info for debugging if needed
                if insight.get('data_source'):
                    print(f"   📊 Data Source: {insight['data_source']}")
        
        print("\n" + "="*70)
        print("End of Report".center(70))
        print("="*70 + "\n")

    def _wrap_text(self, text: str, width: int) -> List[str]:
        """Wrap text to specified width"""
        words = text.split()
        lines = []
        current_line = []
        current_length = 0
        
        for word in words:
            word_length = len(word)
            if current_length + word_length + len(current_line) > width:
                if current_line:
                    lines.append(' '.join(current_line))
                    current_line = [word]
                    current_length = word_length
                else:
                    lines.append(word)
            else:
                current_line.append(word)
                current_length += word_length
        
        if current_line:
            lines.append(' '.join(current_line))
        
        return lines

    def generate_json_report(self) -> Dict[str, Any]:
        """Generate JSON-serializable report"""
        grouped = self.group_insights()
        
        return {
            'generated_at': datetime.now().isoformat(),
            'total_insights': len(self.insights),
            'severity_counts': self._get_severity_counts(),
            'insights_by_label': {
                label: [
                    {
                        'type': i.get('type'),
                        'message': i.get('message'),
                        'recommendation': i.get('recommendation'),
                        'severity': i.get('severity')
                    }
                    for i in insights
                ]
                for label, insights in grouped.items()
            }
        }
    
    def _get_severity_counts(self) -> Dict[str, int]:
        """Count insights by severity"""
        counts = defaultdict(int)
        for insight in self.insights:
            counts[insight.get('severity', 'medium')] += 1
        return dict(counts)


def main():
    """Example usage"""
    aggregator = ConsoleOutputAggregator()
    
    # Add sample insights
    samples = [
        {
            'label': '🔴 High Utilization',
            'type': 'Revolving Credit Overuse',
            'message': 'Your Credit Card with CIMB Bank has a utilization rate of 85% – well above the recommended threshold.',
            'recommendation': 'Credit utilization above 30% can signal financial stress to lenders. Aim to pay off balances early in the billing cycle, or request a credit limit increase if your income supports it.',
            'severity': 'high',
            'data_source': 'CCRIS'
        },
        {
            'label': '🟠 Missed Payments',
            'type': 'Payment Conduct Issues',
            'message': 'Your Credit Card shows recent payment issues (code 2) in the last 12 months.',
            'recommendation': 'Payment codes 1-2 indicate missed or late payments. Contact your lender immediately to bring the account current. Set up auto-debit to prevent future delays.',
            'severity': 'high',
            'data_source': 'CCRIS'
        },
        {
            'label': '🟢 Long Credit History',
            'type': 'Established Credit',
            'message': 'Your credit history spans 21.8 years, showing established credit experience.',
            'recommendation': 'A long credit history demonstrates stability and experience managing credit. This is a strong positive factor for lenders.',
            'severity': 'positive',
            'data_source': 'CCRIS'
        }
    ]
    
    for insight in samples:
        aggregator.add_insight(insight)
    
    aggregator.print_report()


if __name__ == "__main__":
    main()