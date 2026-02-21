#!/usr/bin/env python3
"""
Agent Creation Script - Creates a new agent from TEMPLATE.

Usage:
    python scripts/create_agent.py --name=max --role=wordpress-dev
    python scripts/create_agent.py --name=frontend --role=frontend-dev --specialization=react
    
This will create:
    agents/max/
    ├── soul.md
    ├── rules.md
    ├── knowledge.md
    ├── config.yaml
    └── memories/
        ├── systems/
        ├── links/
        └── lessons/
"""

import argparse
import shutil
import sys
from pathlib import Path
from datetime import datetime
from typing import Optional


def create_agent(
    name: str,
    role: str,
    specialization: Optional[str] = None,
    communication_style: str = "professionell, freundlich",
    strengths: str = "Schnelle Problemlösung, Code-Qualität",
    primary_tasks: str = "Web-Entwicklung und Wartung",
    tech_stack: Optional[str] = None,
) -> Path:
    """
    Create a new agent from template.
    
    Args:
        name: Agent name (used for directory and ID)
        role: Agent role (e.g., "wordpress-dev", "frontend-dev")
        specialization: Specific technology focus
        communication_style: How the agent communicates
        strengths: Agent strengths
        primary_tasks: What the agent helps with
        tech_stack: Technical stack description
        
    Returns:
        Path to created agent directory
    """
    
    base_path = Path("agents")
    template_path = base_path / "TEMPLATE"
    agent_path = base_path / name
    
    # Check if template exists
    if not template_path.exists():
        print(f"❌ Error: Template not found at {template_path}")
        print("   Make sure you're running from the project root.")
        sys.exit(1)
    
    # Check if agent already exists
    if agent_path.exists():
        print(f"❌ Error: Agent '{name}' already exists at {agent_path}")
        print("   Use a different name or delete the existing agent.")
        sys.exit(1)
    
    print(f"🚀 Creating agent '{name}'...")
    
    # Create directory structure
    agent_path.mkdir(parents=True)
    (agent_path / "memories" / "systems").mkdir(parents=True)
    (agent_path / "memories" / "links").mkdir(parents=True)
    (agent_path / "memories" / "lessons").mkdir(parents=True)
    
    print(f"   📁 Created directories")
    
    # Template variables
    vars_dict = {
        "agent_name": name.capitalize(),
        "agent_id": name.lower(),
        "role": role,
        "specialization": specialization or role,
        "communication_style": communication_style,
        "strengths": strengths,
        "primary_tasks": primary_tasks,
        "created_at": datetime.now().isoformat(),
        "languages": "[python, javascript, php]",
        "frameworks": "[fastapi, react, shopware]",
        "tools": "[docker, git, ddev]",
        "tech_stack": tech_stack or "Standard Web Stack",
    }
    
    # Add role-specific defaults
    role_defaults = get_role_defaults(role)
    vars_dict.update(role_defaults)
    
    # Override with provided values
    if tech_stack:
        vars_dict["tech_stack"] = tech_stack
    
    # Process template files
    process_template(template_path / "soul.md.template", agent_path / "soul.md", vars_dict)
    process_template(template_path / "rules.md.template", agent_path / "rules.md", vars_dict)
    process_template(template_path / "knowledge.md.template", agent_path / "knowledge.md", vars_dict)
    process_template(template_path / "config.yaml.template", agent_path / "config.yaml", vars_dict)
    
    print(f"   📝 Created configuration files")
    
    # Create default memory files
    create_default_memories(agent_path, vars_dict)
    
    print(f"   🧠 Created memory structure")
    
    print(f"\n✅ Agent '{name}' created successfully!")
    print(f"\n📂 Location: {agent_path.absolute()}")
    print(f"\n📝 Next steps:")
    print(f"   1. Edit {agent_path}/soul.md to customize personality")
    print(f"   2. Edit {agent_path}/knowledge.md to add domain knowledge")
    print(f"   3. Add system docs to {agent_path}/memories/systems/")
    print(f"   4. Update config.yaml with specific capabilities")
    print(f"\n🚀 To use the agent:")
    print(f"   python agent_worker.py --agent={name}")
    
    return agent_path


def get_role_defaults(role: str) -> dict:
    """Get default values for specific roles."""
    
    defaults = {
        "wordpress-dev": {
            "languages": "[php, javascript]",
            "frameworks": "[wordpress, woocommerce]",
            "tools": "[docker, git, wp-cli]",
            "capabilities": "  - wordpress_development\n  - plugin_development\n  - theme_customization\n  - woocommerce",
            "specific_rules": "- WordPress Coding Standards befolgen\n- Plugins immer über WP-CLI oder Composer installieren\n- Child-Themes für Customizations nutzen",
            "agent_specific_knowledge": "## WordPress Best Practices\n- Child-Themes nutzen\n- wp_enqueue für Assets\n- Nonces für Security\n- Transients für Caching",
            "troubleshooting": "### WP-CLI\n```bash\nwp plugin list\nwp theme activate <theme>\nwp db export backup.sql\n```",
        },
        "frontend-dev": {
            "languages": "[javascript, typescript, html, css]",
            "frameworks": "[react, vue, angular]",
            "tools": "[npm, webpack, vite]",
            "capabilities": "  - frontend_development\n  - responsive_design\n  - api_integration\n  - performance_optimization",
            "specific_rules": "- Mobile-first Responsive Design\n- Semantic HTML\n- CSS-Variablen für Theming\n- Lazy Loading für Bilder",
            "agent_specific_knowledge": "## Frontend Best Practices\n- Komponenten wiederverwendbar gestalten\n- Accessibility (ARIA-Labels)\n- Performance: Bildoptimierung, Code-Splitting\n- TypeScript für type-safety",
            "troubleshooting": "### NPM/Yarn\n```bash\nnpm install\nnpm run build\nnpm run test\n```",
        },
        "php-dev": {
            "languages": "[php, javascript]",
            "frameworks": "[symfony, laravel, shopware]",
            "tools": "[docker, git, composer]",
            "capabilities": "  - php_development\n  - api_development\n  - database_design\n  - testing",
            "specific_rules": "- PSR-12 Coding Standards\n- Dependency Injection nutzen\n- Unit-Tests für Services\n- PHP 8+ Features verwenden",
            "agent_specific_knowledge": "## PHP Best Practices\n- Typed properties\n- Union Types\n- Attributes für Metadata\n- Composer Autoloading",
            "troubleshooting": "### Composer\n```bash\ncomposer install\ncomposer update\ncomposer dump-autoload\n```",
        },
        "python-dev": {
            "languages": "[python, sql]",
            "frameworks": "[fastapi, django, flask]",
            "tools": "[docker, git, pytest]",
            "capabilities": "  - python_development\n  - api_development\n  - data_processing\n  - automation",
            "specific_rules": "- PEP 8 Style Guide\n- Type Hints verwenden\n- Docstrings für alle Funktionen\n- pytest für Testing",
            "agent_specific_knowledge": "## Python Best Practices\n- Virtual Environments\n- requirements.txt / pyproject.toml\n- Black für Formatting\n- Pydantic für Validation",
            "troubleshooting": "### Python Environment\n```bash\npython -m venv venv\nsource venv/bin/activate\npip install -r requirements.txt\npytest\n```",
        },
    }
    
    return defaults.get(role.lower(), {
        "languages": "[python, javascript, php]",
        "frameworks": "[fastapi, react, shopware]",
        "tools": "[docker, git, ddev]",
        "capabilities": "  - code_generation\n  - file_operations\n  - git_operations",
        "specific_rules": "- Code-Qualität priorisieren\n- Tests schreiben\n- Dokumentation pflegen",
        "agent_specific_knowledge": "## Allgemeine Best Practices\n- Clean Code Prinzipien\n- DRY (Don't Repeat Yourself)\n- KISS (Keep It Simple)",
        "troubleshooting": "### Allgemein\n- Logs prüfen\n- Dokumentation lesen\n- Inkrementell vorgehen",
    })


def process_template(template_path: Path, output_path: Path, vars_dict: dict):
    """Process a template file and write output."""
    
    if not template_path.exists():
        print(f"   ⚠️  Template not found: {template_path}")
        return
    
    content = template_path.read_text(encoding="utf-8")
    
    # Replace template variables
    for key, value in vars_dict.items():
        content = content.replace(f"{{{key}}}", str(value))
    
    output_path.write_text(content, encoding="utf-8")


def create_default_memories(agent_path: Path, vars_dict: dict):
    """Create default memory files for the agent."""
    
    # Links template
    links_content = f"""# Wichtige Links & Ressourcen für {vars_dict['agent_name']}

## Entwicklungs-Links

### {vars_dict['role']} Ressourcen
- **Offizielle Docs**: (hier einfügen)
- **Best Practices**: (hier einfügen)
- **Tutorials**: (hier einfügen)

### Tools
| Tool | URL | Beschreibung |
|------|-----|--------------|
| Tool 1 | https://... | Beschreibung |
| Tool 2 | https://... | Beschreibung |

### Cheatsheets
- **Commands**: (hier einfügen)
- **Shortcuts**: (hier einfügen)

## Projekt-Spezifisch

### Aktive Projekte
| Projekt | Repo | Tech-Stack |
|---------|------|------------|
| Projekt 1 | (url) | {vars_dict['tech_stack']} |

## Troubleshooting

### Häufige Fehler
1. **Fehler**: Lösung
2. **Fehler**: Lösung
"""
    
    (agent_path / "memories" / "links" / "resources.md").write_text(
        links_content, encoding="utf-8"
    )
    
    # Lessons template
    lessons_content = f"""# Gelernte Lektionen für {vars_dict['agent_name']}

## Projekt-Erfahrungen

### Lektion 1
**Datum**: YYYY-MM-DD
**Kontext**: Projekt XYZ
**Was gelernt**: Beschreibung
**Ergebnis**: Positive/Negative Erfahrung

### Lektion 2
**Datum**: YYYY-MM-DD
**Kontext**: Projekt ABC
**Was gelernt**: Beschreibung
**Ergebnis**: Positive/Negative Erfahrung

## Technische Insights

### Best Practices
1. Punkt 1
2. Punkt 2

### Zu Vermeiden
1. Anti-Pattern 1
2. Anti-Pattern 2

## Kunden-Spezifisch

### Kunde A
- Besonderheit 1
- Besonderheit 2
"""
    
    (agent_path / "memories" / "lessons" / "learned.md").write_text(
        lessons_content, encoding="utf-8"
    )
    
    # Systems placeholder
    systems_readme = f"""# System-Dokumentation für {vars_dict['agent_name']}

Hier kommen Dokumentationen über:
- Verwendete Frameworks
- Build-Prozesse
- Deployment-Workflows
- System-Architekturen
"""
    
    (agent_path / "memories" / "systems" / "README.md").write_text(
        systems_readme, encoding="utf-8"
    )


def main():
    """Main entry point."""
    
    parser = argparse.ArgumentParser(
        description="Create a new agent from TEMPLATE",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Create a WordPress developer agent
  python scripts/create_agent.py --name=max --role=wordpress-dev
  
  # Create a frontend developer agent
  python scripts/create_agent.py --name=lisa --role=frontend-dev --specialization=vue
  
  # Create a custom agent with specific tech stack
  python scripts/create_agent.py --name=thorsten --role=python-dev \\
      --tech-stack="Python, FastAPI, PostgreSQL"
        """
    )
    
    parser.add_argument(
        "--name", "-n",
        required=True,
        help="Agent name (used for directory and ID)"
    )
    
    parser.add_argument(
        "--role", "-r",
        required=True,
        choices=[
            "wordpress-dev",
            "frontend-dev", 
            "php-dev",
            "python-dev",
            "developer"
        ],
        help="Agent role/category"
    )
    
    parser.add_argument(
        "--specialization", "-s",
        help="Specific technology focus (e.g., 'react', 'shopware', 'laravel')"
    )
    
    parser.add_argument(
        "--communication-style",
        default="professionell, freundlich",
        help="How the agent communicates (default: 'professionell, freundlich')"
    )
    
    parser.add_argument(
        "--strengths",
        default="Schnelle Problemlösung, Code-Qualität",
        help="Agent strengths (default: 'Schnelle Problemlösung, Code-Qualität')"
    )
    
    parser.add_argument(
        "--primary-tasks",
        default="Web-Entwicklung und Wartung",
        help="What the agent helps with (default: 'Web-Entwicklung und Wartung')"
    )
    
    parser.add_argument(
        "--tech-stack",
        help="Technical stack description (overrides role defaults)"
    )
    
    args = parser.parse_args()
    
    # Validate name
    if not args.name.replace("-", "").replace("_", "").isalnum():
        print("❌ Error: Agent name must be alphanumeric (with optional - or _)")
        sys.exit(1)
    
    # Create agent
    create_agent(
        name=args.name.lower(),
        role=args.role,
        specialization=args.specialization,
        communication_style=args.communication_style,
        strengths=args.strengths,
        primary_tasks=args.primary_tasks,
        tech_stack=args.tech_stack,
    )


if __name__ == "__main__":
    main()
