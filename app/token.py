import argparse

from app.auth import create_access_token


def main() -> None:
    parser = argparse.ArgumentParser(description="Create a short-lived API access token")
    parser.add_argument("--subject", required=True, help="Token subject, e.g. a user ID")
    parser.add_argument("--minutes", type=int, default=None, help="Token lifetime")
    args = parser.parse_args()
    from datetime import timedelta

    lifetime = timedelta(minutes=args.minutes) if args.minutes else None
    print(create_access_token(args.subject, lifetime))


if __name__ == "__main__":
    main()
