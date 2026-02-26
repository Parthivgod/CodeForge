def generate_report(labeled_clusters):
    md = "# Monolith Decomposition Report\n\n"
    md += "## Executive Summary\n"
    md += f"Found {len(labeled_clusters)} potential microservices.\n\n"
    
    for c in labeled_clusters:
        md += f"### {c['name']}\n"
        md += f"- **Risk Level**: {c['risk'].upper()}\n"
        md += f"- **Estimated LOC**: {c['loc_count']}\n"
        md += f"- **Description**: {c['description']}\n\n"
        
    return md
