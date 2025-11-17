"""Main CLI entrypoint for regulation data ingestor."""

import argparse
import sys
from pathlib import Path
from typing import Optional

from .config import Config
from .sources.fallback import Scraper
from .processors.normalizer import Normalizer
from .processors.extractor import Extractor
from .processors.validator import Regulation
from .writers.output import OutputWriter


def update_regulation(config: Config, region_id: str, regulation_id: str, dry_run: bool = False, verbose: bool = False):
    """
    Update a single regulation.
    
    Args:
        config: Application configuration
        region_id: Region identifier
        regulation_id: Regulation identifier
        dry_run: If True, validate without writing files
        verbose: If True, print detailed output
    """
    if verbose:
        print(f"Updating {region_id}/{regulation_id}...")
    
    # Get regulation configuration
    regulation_config = config.get_regulation(region_id, regulation_id)
    if not regulation_config:
        print(f"Error: Regulation {region_id}/{regulation_id} not found in regions.json")
        return False
    
    region = config.get_region(region_id)
    if not region:
        print(f"Error: Region {region_id} not found in regions.json")
        return False
    
    if not regulation_config.sources:
        print(f"Warning: No sources configured for {region_id}/{regulation_id}")
        return False
    
    try:
        # Step 1: Scrape content
        if verbose:
            print(f"  Scraping from {len(regulation_config.sources)} source(s)...")
        scraper = Scraper()
        raw_text = scraper.scrape(region_id, regulation_id, regulation_config.sources)
        
        if verbose:
            print(f"  Extracted {len(raw_text)} characters")
        
        # Step 2: Normalize text
        if verbose:
            print("  Normalizing text...")
        normalizer = Normalizer()
        normalized_text = normalizer.normalize(raw_text)
        
        # Step 3: Extract structured content
        if verbose:
            print("  Extracting structured content...")
        extractor = Extractor()
        articles = extractor.extract_articles(normalized_text)
        summary = extractor.extract_summary(normalized_text)
        developer_guidance = extractor.extract_developer_guidance(normalized_text)
        
        if verbose:
            print(f"  Extracted {len(articles)} articles")
        
        # Step 4: Create regulation object
        regulation = Regulation(
            id=regulation_id,
            name=_get_regulation_name(regulation_id),
            region=region.name,
            risk_category="high",  # Default, can be overridden
            summary=summary,
            articles=articles,
            developer_guidance=developer_guidance
        )
        
        # Step 5: Validate
        if verbose:
            print("  Validating schema...")
        # Validation happens automatically via Pydantic
        
        # Step 6: Write output
        if not dry_run:
            if verbose:
                print("  Writing files...")
            writer = OutputWriter(config.data_dir)
            versioned_path, active_path = writer.write_regulation(regulation, region_id)
            print(f"✓ Saved versioned file: {versioned_path}")
            print(f"✓ Updated active file: {active_path}")
        else:
            print("✓ Validation passed (dry-run mode)")
        
        return True
        
    except Exception as e:
        print(f"✗ Error processing {region_id}/{regulation_id}: {e}")
        if verbose:
            import traceback
            traceback.print_exc()
        return False


def update_all(config: Config, dry_run: bool = False, verbose: bool = False):
    """
    Update all regulations.
    
    Args:
        config: Application configuration
        dry_run: If True, validate without writing files
        verbose: If True, print detailed output
    """
    regions_config = config.load_regions()
    
    total = 0
    success = 0
    
    for region in regions_config.regions:
        for regulation in region.regulations:
            total += 1
            if update_regulation(config, region.id, regulation.id, dry_run, verbose):
                success += 1
            print()  # Blank line between regulations
    
    print(f"Completed: {success}/{total} regulations updated successfully")


def init_regions(config: Config):
    """
    Initialize regions.json file with default structure.
    
    Args:
        config: Application configuration
    """
    from .processors.validator import RegionsConfig, Region, RegulationSource
    
    # Create default regions configuration
    regions_config = RegionsConfig(
        regions=[
            Region(
                id="eu",
                name="European Union",
                regulations=[
                    RegulationSource(
                        id="gdpr",
                        sources=["https://eur-lex.europa.eu/eli/reg/2016/679/oj"]
                    ),
                    RegulationSource(
                        id="dora",
                        sources=["https://eur-lex.europa.eu/eli/reg/2022/2554/oj"]
                    )
                ]
            ),
            Region(
                id="usa",
                name="United States",
                regulations=[
                    RegulationSource(
                        id="hipaa",
                        sources=[
                            "https://www.hhs.gov/hipaa/for-professionals/privacy/index.html",
                            "https://www.hhs.gov/sites/default/files/ocr/privacy/hipaa/administrative/privacyrule/pr.pdf"
                        ]
                    ),
                    RegulationSource(
                        id="ccpa",
                        sources=[
                            "https://oag.ca.gov/privacy/ccpa",
                            "https://leginfo.legislature.ca.gov/faces/codes_displayText.xhtml?division=3.&part=4.&chapter=1.&lawCode=CIV"
                        ]
                    ),
                    RegulationSource(
                        id="glba",
                        sources=[
                            "https://www.ftc.gov/legal-library/browse/statutes/gramm-leach-bliley-act",
                            "https://www.govinfo.gov/content/pkg/PLAW-106publ102/pdf/PLAW-106publ102.pdf"
                        ]
                    )
                ]
            ),
            Region(
                id="brazil",
                name="Brazil",
                regulations=[
                    RegulationSource(
                        id="lgpd",
                        sources=[
                            "https://www.gov.br/anpd/pt-br/assuntos/lei-geral-de-protecao-de-dados-lgpd",
                            "https://www.planalto.gov.br/ccivil_03/_ato2015-2018/2018/lei/l13709.htm"
                        ]
                    )
                ]
            )
        ]
    )
    
    # Ensure data directory exists
    config.ensure_data_dir()
    
    # Write regions.json
    writer = OutputWriter(config.data_dir)
    regions_path = writer.write_regions_json(regions_config)
    
    print(f"✓ Initialized regions.json at {regions_path}")
    print(f"✓ Created directory structure at {config.data_dir}")


def _get_regulation_name(regulation_id: str) -> str:
    """Get full name for a regulation ID."""
    names = {
        "gdpr": "General Data Protection Regulation",
        "dora": "Digital Operational Resilience Act",
        "hipaa": "Health Insurance Portability and Accountability Act",
        "ccpa": "California Consumer Privacy Act",
        "glba": "Gramm-Leach-Bliley Act",
        "lgpd": "Lei Geral de Proteção de Dados",
    }
    return names.get(regulation_id, regulation_id.upper())


def main():
    """Main CLI entrypoint."""
    parser = argparse.ArgumentParser(
        description="Regulation Data Ingestor - Scrape and process regulatory data"
    )
    
    subparsers = parser.add_subparsers(dest="command", help="Command to execute")
    
    # Update command
    update_parser = subparsers.add_parser("update", help="Update regulation(s)")
    update_parser.add_argument(
        "target",
        nargs="?",
        choices=["all"],
        help="Update all regulations (or specify region and regulation)"
    )
    update_parser.add_argument(
        "region_id",
        nargs="?",
        help="Region identifier (e.g., 'eu', 'usa')"
    )
    update_parser.add_argument(
        "regulation_id",
        nargs="?",
        help="Regulation identifier (e.g., 'gdpr', 'hipaa')"
    )
    update_parser.add_argument(
        "--data-dir",
        help="Override REGULATION_DATA_DIR environment variable"
    )
    update_parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Validate without writing files"
    )
    update_parser.add_argument(
        "--verbose", "-v",
        action="store_true",
        help="Print detailed output"
    )
    
    # Init command
    init_parser = subparsers.add_parser("init", help="Initialize regions.json")
    init_parser.add_argument(
        "--data-dir",
        help="Override REGULATION_DATA_DIR environment variable"
    )
    
    args = parser.parse_args()
    
    if not args.command:
        parser.print_help()
        sys.exit(1)
    
    # Initialize configuration
    config = Config(data_dir=args.data_dir)
    
    if args.command == "init":
        init_regions(config)
    
    elif args.command == "update":
        if args.target == "all":
            update_all(config, dry_run=args.dry_run, verbose=args.verbose)
        elif args.region_id and args.regulation_id:
            update_regulation(
                config,
                args.region_id,
                args.regulation_id,
                dry_run=args.dry_run,
                verbose=args.verbose
            )
        else:
            update_parser.print_help()
            sys.exit(1)


if __name__ == "__main__":
    main()


