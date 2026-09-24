import argparse
import logging


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("path")
    parser.add_argument("--dry-run", action="store_true")
    args = parser.parse_args()
    logging.basicConfig(level=logging.INFO)
    logging.info("processing %s", args.path)


if __name__ == "__main__":
    main()
