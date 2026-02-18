import os
import sys
import json
import argparse

# Add backend directory to path so we can import api_server
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from api_server import app  # noqa: E402


def generate_openapi(output_file: str):
    """Generate OpenAPI schema and save to file."""
    openapi_schema = app.openapi()

    with open(output_file, 'w') as f:
        json.dump(openapi_schema, f, indent=2)

    print(f"OpenAPI schema generated at: {output_file}")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Generate OpenAPI schema for MediBot API")
    parser.add_argument("--output", default="openapi.json", help="Output file path (default: openapi.json)")

    args = parser.parse_args()
    generate_openapi(args.output)
