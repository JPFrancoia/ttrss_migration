from custom_logging import init_logging
from migration import config


def main():
    print("Hello from ttrss-migration!")


if __name__ == "__main__":
    init_logging(config.LOGGING_CONFIG)
    main()
