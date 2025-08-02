"""
Master control file for member waiver process
"""

import sys

import docs
import csvfile
import memberdata
import keys
import extract_attest
import extract_members
import gen_waiver_groups
import waiverrec
import waiver_calcs

def main(command: str):
    membership = memberdata.Membership()
    membership.read_csv_files()
    member_keys = keys.gen_member_key_map(membership)

    # Get new waiver files
    extract_members.main()
    extract_attest.main()

    # Create new groups
    waiver_groups = gen_waiver_groups.generate_groups(membership)

    # Read latest attestations and member waivers
    attestations = docs.Attestation.read_csv()
    member_waivers = docs.MemberWaiver.read_csv()

    waiver_calcs.review_and_update_waivers(membership, waiver_groups, member_waivers, attestations)
    waiver_calcs.update_waiver_status(waiver_groups, member_waivers, attestations)
    waiver_calcs.report_waiver_stats(membership, waiver_groups, member_waivers, attestations, member_keys)

    # Generate and save member records
    waiver_calcs.generate_member_records(waiver_groups, member_keys)
    waiverrec.MemberWaiverGroups.write_csv_files(waiver_groups)
    docs.MemberWaiver.write_csv(member_waivers)
    docs.Attestation.write_csv(attestations)


if __name__ == "__main__":
    # TODO: pass in step
    main("")