"""
Check that family waivers are complete.
"""

import memberdata
import memberwaiver


def main():
    # Read membership data
    membership = memberdata.Membership()
    membership.read_csv_files()

    # Read waibers
    waivers: list[memberwaiver.MemberWaiver] = memberwaiver.read_csv()

    # Review waiver entries and update status
    for waiver in waivers:
        # Get account number
        if len(waiver.signatures) < 1:
            continue
        name = waiver.signatures[0].name
        account = membership.get_account_by_fullname(name)
        if account is None:
            print(f"Warning: no account for name '{name}'")
            continue

        # Count number of minor children
        minors = 0
        for member in membership.get_members_for_account_num(account.account_num):
            if member.is_minor():
                minors += 1
        waiver.set_complete(minors == 0 or minors == len(waiver.minors))

    # Write waiver entries
    memberwaiver.write_csv(waivers)


if __name__ == "__main__":
    main()
