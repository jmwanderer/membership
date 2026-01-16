import datetime
from dataclasses import dataclass, field

import docs
import memberdata
import keys

# TODO: add some type of handling of multiple attestations for same household


@dataclass
class AccountAttest:
    account_num: str
    web_view_links: list[str] = field(default_factory=lambda: [])
    people: list[docs.AttestEntry] = field(default_factory=lambda: [])


account_attest_map: dict[str, AccountAttest] = {}


def record_attestation(
    membership: memberdata.Membership, attestation: docs.Attestation
) -> None:
    primary_name = attestation.adult().name
    account = membership.get_account_by_fullname(primary_name)
    if account is None:
        print(f"Failed to find account for {primary_name}")
        print(f"doc: {attestation.web_view_link}")
        return

    account_attest = account_attest_map.get(account.account_num)
    if account_attest is None:
        account_attest = AccountAttest(account.account_num)
        account_attest_map[account.account_num] = account_attest

    account_attest.web_view_links.append(attestation.web_view_link)
    for entry in attestation.adults:
        account_attest.people.append(entry)
    for entry in attestation.minors:
        account_attest.people.append(entry)


