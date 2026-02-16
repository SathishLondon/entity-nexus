# Neo4j Schema Definitions - Enterprise Grade

# Node Labels
LABEL_LEGAL_ENTITY = "LegalEntity"
LABEL_BRANCH = "Branch"
LABEL_TRADING_COUNTERPARTY = "TradingCounterparty"
LABEL_PERSON = "Person"

# Edge Relationships
REL_OWNS = "OWNS" # Ownership with %
REL_PARENT_OF = "PARENT_OF" # Legal Hierarchy
REL_HAS_BRANCH = "HAS_BRANCH"
REL_TRADES_WITH = "TRADES_WITH"

# Edge Properties
PROP_OWNERSHIP_PCT = "ownership_percentage"
PROP_VOTING_POWER = "voting_power"
PROP_EFFECTIVE_FROM = "effective_from"
PROP_EFFECTIVE_TO = "effective_to"
PROP_SOURCE = "source" # Lineage on the edge itself
