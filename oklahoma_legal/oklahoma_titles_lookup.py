#!/usr/bin/env python3
"""
Oklahoma Statutes - Title Names Lookup Table
Complete list of all 85 Oklahoma Statute Titles
"""

OKLAHOMA_TITLES = {
    # Based on Oklahoma Statutes Citationized - Title Names
    "1": "Civil Procedure",
    "2": "Corporations",
    "3": "Domestic Relations",
    "4": "Evidence",
    "5": "Infants and Incompetents",
    "6": "Limitations",
    "7": "Liens",
    "8": "Motions and Petitions",
    "9": "Notaries Public",
    "10": "Children",
    "10A": "Children and Juvenile Code",
    "11": "Cities and Towns",
    "12": "Civil Procedure",
    "13": "Commerce and Industry",
    "14": "Conservancy and Conservation Districts",
    "15": "Contracts",
    "16": "Conveyances",
    "17": "Corporations",
    "18": "Counties and County Officers",
    "19": "Courts",
    "20": "Decedents' Estates",
    "21": "Crimes and Punishments",
    "22": "Criminal Procedure",
    "23": "Damages",
    "24": "Drainage and Levees",
    "25": "Elections",
    "26": "Eminent Domain",
    "27": "Environmental Quality Code",
    "27A": "Environment and Natural Resources",
    "28": "Escheats",
    "29": "Executions",
    "30": "Guardian and Ward",
    "31": "Habeas Corpus",
    "32": "Homesteads and Exemptions",
    "33": "Husband and Wife",
    "34": "Initiative and Referendum",
    "35": "Injunctions",
    "36": "Insurance",
    "37": "Intoxicating Liquors",
    "38": "Jails and Jailers",
    "39": "Judgments",
    "40": "Jurors and Juries",
    "41": "Landlord and Tenant",
    "42": "Legislature",
    "43": "Libraries",
    "43A": "Oklahoma Library Code",
    "44": "Mandamus",
    "45": "Marriage",
    "46": "Mentally Ill",
    "47": "Motor Vehicles",
    "48": "Municipal Corporations",
    "49": "Navigation",
    "50": "Oaths and Affirmations",
    "51": "Officers",
    "52": "Oil and Gas",
    "53": "Partnership",
    "54": "Pensions and Retirement",
    "55": "Perpetuities and Accumulations",
    "56": "Pleading",
    "57": "Probate Procedure",
    "58": "Probate of Wills",
    "59": "Public Lands",
    "60": "Public Monies and Public Printing",
    "61": "Public Officers and Employees",
    "62": "Public Roads, Bridges and Ferries",
    "63": "Public Health and Safety",
    "64": "Public Revenues and Public Debt",
    "65": "Public Trusts",
    "66": "Quieting Title",
    "67": "Railroad and Transportation Companies",
    "68": "Revenue and Taxation",
    "69": "Schools",
    "70": "Schools",
    "71": "State Government",
    "72": "State Institutions",
    "73": "State Lands - Surveyors",
    "74": "State Government",
    "75": "Statutes and Reports",
    "76": "Streams and Streamways",
    "78": "Taxation - Exemptions",
    "79": "Torts",
    "80": "Towns",
    "81": "Townships",
    "82": "Trade-marks and Trade-names",
    "83": "Treason and Insurrection",
    "84": "Trusts",
    "85": "Waters and Water Rights"
}

# Constitution mapping
OKLAHOMA_CONSTITUTION = {
    "CONST": "Oklahoma Constitution"
}

def get_title_name(title_number: str) -> str:
    """Get title name from title number"""
    title_num = str(title_number).strip()

    # Check if it's the Constitution
    if title_num.upper() in ["CONST", "CONSTITUTION"]:
        return "Oklahoma Constitution"

    # Look up statute title
    return OKLAHOMA_TITLES.get(title_num, None)

def get_all_titles():
    """Get all title mappings including Constitution"""
    all_titles = OKLAHOMA_TITLES.copy()
    all_titles.update(OKLAHOMA_CONSTITUTION)
    return all_titles

if __name__ == "__main__":
    # Test the lookup
    print("Oklahoma Statutes Title Lookup")
    print("="*60)
    print(f"Total Titles: {len(OKLAHOMA_TITLES)}")
    print(f"\nSample lookups:")
    print(f"  Title 10: {get_title_name('10')}")
    print(f"  Title 10A: {get_title_name('10A')}")
    print(f"  Title 21: {get_title_name('21')}")
    print(f"  Title 70: {get_title_name('70')}")
    print(f"  Constitution: {get_title_name('CONST')}")

    print(f"\nAll Titles:")
    for num, name in sorted(OKLAHOMA_TITLES.items(), key=lambda x: (len(x[0]), x[0])):
        print(f"  {num:>4}. {name}")
