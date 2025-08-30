import argparse
import sys

from . import __version__
from .core import ChangeProcessor
from .handlers import CliInteractionHandler, AutoInteractionHandler

def main():
    """Main function for the command-line interface."""
    parser = argparse.ArgumentParser(
        description="Merge changes from a LaTeX file using the 'changes' package."
    )

    parser.add_argument(
        "-v", "--version",
        action="version",
        version=f"%(prog)s {__version__}"
    )
    parser.add_argument("infile", help="Input LaTeX file")
    parser.add_argument("outfile", help="Output file path")
    parser.add_argument("-a", "--accept-all", action="store_true", help="Accept all changes automatically.")
    parser.add_argument("-r", "--reject-all", action="store_true", help="Reject all changes automatically.")
    parser.add_argument("-rh", "--remove-highlights", action="store_true", help="Remove all highlights and comments automatically.")
    
    args = parser.parse_args()

    try:
        with open(args.infile, 'r', encoding='utf-8') as f:
            content = f.read()
    except FileNotFoundError:
        print(f"Error: Input file not found at '{args.infile}'", file=sys.stderr)
        sys.exit(1)
    except Exception as e:
        print(f"Error reading input file: {e}", file=sys.stderr)
        sys.exit(1)

    # Choose the appropriate handler based on CLI arguments
    if args.accept_all or args.reject_all or args.remove_highlights:
        handler = AutoInteractionHandler(
            accept_all=args.accept_all,
            reject_all=args.reject_all,
            remove_highlights=args.remove_highlights
        )
    else:
        handler = CliInteractionHandler()
    
    # Initialize and run the processor
    processor = ChangeProcessor(handler)
    processed_content = processor.process(content)

    try:
        with open(args.outfile, 'w', encoding='utf-8') as f:
            f.write(processed_content)
        print(f"Successfully processed file and saved result to '{args.outfile}'")
    except Exception as e:
        print(f"Error writing to output file: {e}", file=sys.stderr)
        sys.exit(1)

if __name__ == '__main__':
    main()
