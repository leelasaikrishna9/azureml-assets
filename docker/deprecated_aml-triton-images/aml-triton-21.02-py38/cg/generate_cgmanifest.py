import re
import sys
import json


def main(input_json):
    with open(input_json, 'r') as f:
        data = json.load(f)

        output = {'Version': 1, 'Registrations': []}
        for d in data:
            # Only handling Ubuntu Linux components for now
            assert d['Component']['Linux']
            version = d['Component']['Linux']['Version']
            version = re.sub(r'^[0-9]+:', '', version)
            d['Component']['Linux']['Version'] = version
            item = {'Component': {'Type': 'Linux', 'Linux': d['Component']['Linux']}}

            assert d['Component']['Linux']['Distribution'] == 6
            item['Component']['Linux']['Distribution'] = 'Ubuntu'

            output['Registrations'].append(item)

    with open('cgmanifest.json', 'w') as f:
        json.dump(output, f, indent=2, sort_keys=True)


if __name__ == "__main__":
    main(sys.argv[1])
