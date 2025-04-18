import sys
import logging
import argparse
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from src.scraper.pinterest import PinterestScraper
from src.export.excel import ExcelExporter
from src.export.json import JsonExporter


def configure_logging():
    """Configure logging for the application."""
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(levelname)s - %(name)s - %(message)s',
        handlers=[
            logging.FileHandler('pinterest_scraper.log'),
            logging.StreamHandler()
        ]
    )
    
    # Reduce verbosity for external libraries
    for logger_name in ["webdriver_manager", "websockets", "selenium", "urllib3"]:
        logging.getLogger(logger_name).setLevel(logging.WARNING)


def parse_arguments():
    """Parse command line arguments."""
    parser = argparse.ArgumentParser(description='Pinterest Pin Scraper')
    
    parser.add_argument(
        'keywords',
        nargs='*',
        help='Keywords to search for pins (if none provided, will prompt)'
    )
    
    parser.add_argument(
        '-n', '--max-pins',
        type=int,
        default=100,
        help='Maximum number of pins to scrape (default: 100)'
    )
    
    parser.add_argument(
        '-c', '--cookie-path',
        default='data/cookies/pin.json',
        help='Path to cookie file for authentication'
    )
    
    parser.add_argument(
        '-o', '--output-dir',
        default='data/output',
        help='Directory to save output files'
    )
    
    parser.add_argument(
        '-f', '--format',
        choices=['excel', 'json', 'both'],
        default='excel',
        help='Output format (default: excel)'
    )
    
    return parser.parse_args()


def main():
    """Main function to run the Pinterest scraper."""
    # Configure logging
    configure_logging()
    logger = logging.getLogger(__name__)
    
    # Parse command line arguments
    args = parse_arguments()
    
    # Create exporters based on the specified format
    exporters = []
    if args.format in ['excel', 'both']:
        exporters.append(ExcelExporter(args.output_dir))
    if args.format in ['json', 'both']:
        exporters.append(JsonExporter(args.output_dir))
    
    # Initialize the scraper
    scraper = PinterestScraper(args.cookie_path)
    
    try:
        # Get keywords from command line or prompt
        keywords = args.keywords
        if not keywords:
            keyword = input("Enter search keyword: ")
            keywords = [keyword]
        
        # Process each keyword
        for keyword in keywords:
            logger.info(f"Processing keyword: {keyword}")
            
            # Search for pins
            pins = scraper.search_pins(keyword, args.max_pins)
            
            if not pins:
                logger.warning(f"No pins found for keyword: {keyword}")
                continue
            
            # Export results
            for exporter in exporters:
                filepath = exporter.export(pins, keyword)
                if filepath:
                    print(f"Exported {len(pins)} pins to {filepath}")
    
    except KeyboardInterrupt:
        logger.info("Operation cancelled by user")
    except Exception as e:
        logger.exception(f"Error during scraping: {e}")
    finally:
        scraper.close()
        logger.info("Pinterest scraper completed")

if __name__ == "__main__":
    main()