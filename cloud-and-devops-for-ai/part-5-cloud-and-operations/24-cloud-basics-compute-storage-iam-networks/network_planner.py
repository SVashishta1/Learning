"""network_planner.py: plan a cloud network on paper before you click anything.

It does two jobs, using only Python's standard library (no cloud account needed):
  1. Splits a VPC address range (the "building") into public and private subnets
     (the "floors"), spread over several availability zones (separate buildings).
  2. Plays "door guard": checks which visitors the security groups let in.

Run:  python network_planner.py
      python network_planner.py --cidr 10.20.0.0/16 --azs 3
"""

import argparse
import ipaddress

# AWS keeps 5 addresses in every subnet for itself (network, router, DNS, future, broadcast).
# GCP keeps 4 and Azure keeps 5. We use 5 to be safe.
RESERVED_PER_SUBNET = 5

# Security groups: one "door guard" per kind of room. Each rule says
# "let in traffic on this port, if it comes FROM here". Anything not listed is refused.
# A source is either an address range (like "0.0.0.0/0" = anyone on the internet)
# or the name of another security group (= "anyone wearing that group's badge").
SECURITY_GROUPS = {
    "web-sg": [  # the load balancer at the front door
        {"port": 443, "source": "0.0.0.0/0", "why": "HTTPS from anyone on the internet"},
        {"port": 80, "source": "0.0.0.0/0", "why": "HTTP (we redirect it to HTTPS)"},
    ],
    "app-sg": [  # the servers running your AI API
        {"port": 8000, "source": "web-sg", "why": "only the load balancer may call the API"},
        {"port": 22, "source": "203.0.113.7/32", "why": "SSH only from the office IP"},
    ],
    "db-sg": [  # the database
        {"port": 5432, "source": "app-sg", "why": "only the API servers may talk to Postgres"},
    ],
}

# Visitors we want to test: (description, where they come from, which group they knock on, port)
# "from" is either an IP address or the security group the caller belongs to.
VISITORS = [
    ("A customer's browser opens the website", "198.51.100.25", "web-sg", 443),
    ("The load balancer forwards a request to the API", "web-sg", "app-sg", 8000),
    ("A stranger tries to call the API directly", "198.51.100.25", "app-sg", 8000),
    ("The API reads from the database", "app-sg", "db-sg", 5432),
    ("A stranger tries to reach the database", "198.51.100.25", "db-sg", 5432),
    ("You SSH in from the office", "203.0.113.7", "app-sg", 22),
    ("You SSH in from a cafe", "192.0.2.50", "app-sg", 22),
]


def plan_subnets(vpc_cidr: str, azs: int, new_prefix: int = 24) -> list[dict]:
    """Cut the VPC range into equal /24 blocks: public ones first, private ones from block 10 on."""
    try:
        vpc = ipaddress.ip_network(vpc_cidr)
    except ValueError as error:  # e.g. "10.0.0.5/16": the part after the last dot must be 0 here
        raise SystemExit(f"Not a valid network range: {error}")
    blocks = list(vpc.subnets(new_prefix=new_prefix))  # every possible /24 inside the VPC
    if len(blocks) < 10 + azs:
        raise SystemExit(f"{vpc_cidr} is too small: use a bigger range such as 10.0.0.0/16")
    zone_letters = "abcdefgh"
    plan = []
    for i in range(azs):
        zone = f"zone-{zone_letters[i]}"
        plan.append({"name": f"public-{zone_letters[i]}", "zone": zone, "cidr": blocks[i], "public": True})
        # Private subnets start at block 10 (10.0.10.0/24...), so the numbers are easy to tell apart.
        plan.append({"name": f"private-{zone_letters[i]}", "zone": zone, "cidr": blocks[10 + i], "public": False})
    return plan


def is_allowed(source: str, group: str, port: int) -> tuple[bool, str]:
    """Return (allowed?, reason) for one visitor knocking on one security group."""
    for rule in SECURITY_GROUPS[group]:
        if rule["port"] != port:
            continue
        if rule["source"] in SECURITY_GROUPS:  # the rule names another group (a "badge")
            if source == rule["source"]:
                return True, rule["why"]
        elif source not in SECURITY_GROUPS:  # the rule is an address range and the visitor is an IP
            if ipaddress.ip_address(source) in ipaddress.ip_network(rule["source"]):
                return True, rule["why"]
    return False, "no rule matches, so the guard says no (default deny)"


def main() -> None:
    parser = argparse.ArgumentParser(description="Plan subnets and test security-group rules.")
    parser.add_argument("--cidr", default="10.0.0.0/16", help="the VPC address range (default 10.0.0.0/16)")
    parser.add_argument("--azs", type=int, default=2, choices=range(1, 9), help="availability zones (1-8)")
    args = parser.parse_args()

    plan = plan_subnets(args.cidr, args.azs)  # check the range first, before printing anything
    vpc = ipaddress.ip_network(args.cidr)
    print(f"🏢 VPC {vpc}  ->  {vpc.num_addresses:,} addresses in total")
    print(f"   first address {vpc[0]}, last address {vpc[-1]}\n")

    print(f"{'subnet':<11}{'zone':<8}{'range':<16}{'usable':>7}  door to the street?")
    for s in plan:
        usable = s["cidr"].num_addresses - RESERVED_PER_SUBNET
        door = "yes (route to internet gateway)" if s["public"] else "no (outbound only, via NAT)"
        print(f"{s['name']:<11}{s['zone']:<8}{str(s['cidr']):<16}{usable:>7}  {door}")

    print("\n🛂 Security-group check (default deny: anything not allowed is refused)")
    for description, source, group, port in VISITORS:
        allowed, reason = is_allowed(source, group, port)
        mark = "✅ ALLOW" if allowed else "❌ DENY "
        print(f"{mark}  {description}\n          {source} -> {group}:{port}  ({reason})")


if __name__ == "__main__":
    main()
