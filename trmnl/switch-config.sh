#!/bin/bash
# Switch between small and large family configurations for testing

SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
cd "$SCRIPT_DIR"

case "$1" in
  small)
    echo "Switching to SMALL FAMILY (11 children, single column with spouses)..."
    cp .trmnlp.small-family.yml .trmnlp.yml
    echo "✓ Configuration switched to small family"
    ;;
  large)
    echo "Switching to LARGE FAMILY (20 children, two-column layout)..."
    cp .trmnlp.large-family.yml .trmnlp.yml
    echo "✓ Configuration switched to large family"
    ;;
  *)
    echo "Usage: ./switch-config.sh [small|large]"
    echo ""
    echo "  small  - 11 children with spouses (single column)"
    echo "  large  - 20 children only (two-column layout)"
    echo ""
    echo "Current config:"
    CHILD_COUNT=$(grep -c "child: true" .trmnlp.yml)
    echo "  Children count: $CHILD_COUNT"
    exit 1
    ;;
esac

echo ""
echo "Live reload should trigger automatically. If not, refresh http://localhost:4567/full"
