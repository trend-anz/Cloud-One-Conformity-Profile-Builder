import requests
import json
import os
import pyjq
import sys

region = os.environ.get("apiRegion", "us-west-2")
servicesurl = "https://" + region + ".cloudconformity.com/v1/services"
profilesapi = "https://" + region + "-api.cloudconformity.com/v1/profiles"
response = requests.get(servicesurl)
jsonresponse = json.loads(response.text)
compliancesunique = pyjq.all(
    ".included | map(.attributes.compliances[]) | unique[]",
    jsonresponse,
)


class CPB:
    def online(self):
        # Create Profiles via API
        api = os.environ.get("apiKey")
        for compliance in compliancesunique:
            disabledincluded = pyjq.all(
                '.included[] | select ((.attributes.compliances| index("'
                + compliance
                + '")|not) and (.attributes."multi-risk-level" != true and .attributes.organisation != true)) | {"type": .type, "id": .id, "attributes":{"enabled": false, "riskLevel": .attributes."risk-level", "provider": .attributes.provider}}',
                jsonresponse,
            )
            disabledmulti = pyjq.all(
                '.included[] | select ((.attributes.compliances| index("'
                + compliance
                + '")|not) and (.attributes."multi-risk-level" == true and .attributes.organisation != true)) | {"type": .type, "id": .id, "attributes":{"enabled": false, "provider": .attributes.provider}}',
                jsonresponse,
            )
            data = pyjq.all(
                '.included[] | select ((.attributes.compliances| index("'
                + compliance
                + '")|not) and (.attributes."multi-risk-level" != true and .attributes.organisation != true)) | {"type": .type, "id": .id}',
                jsonresponse,
            )
            datamulti = pyjq.all(
                '.included[] | select ((.attributes.compliances| index("'
                + compliance
                + '")|not) and (.attributes."multi-risk-level" == true and .attributes.organisation != true)) | {"type": .type, "id": .id}',
                jsonresponse,
            )
            buildjson = {
                "included": disabledincluded + disabledmulti,
                "data": {
                    "type": "profiles",
                    "attributes": {"name": compliance, "description": compliance},
                    "relationships": {"ruleSettings": {"data": data + datamulti}},
                },
            }
            mergedjson = json.dumps(buildjson)
            headers = {
                "Content-Type": "application/vnd.api+json",
                "Authorization": "ApiKey " + api,
            }
            cc = requests.post(profilesapi, headers=headers, data=mergedjson)
            if cc.status_code == 200:
                print("Successfuly created {} profile!".format(compliance))
            else:
                print(
                    "Warning: Received the following status code when trying to create profile {}:".format(
                        compliance
                    ),
                    cc.status_code,
                )
                print(json.dumps(cc.json(), indent=4, sortcompliancekeys=True))

    def local(self):
        for compliance in compliancesunique:
            disabledincluded = pyjq.all(
                '.included[] | select ((.attributes.compliances| index("'
                + compliance
                + '")|not) and (.attributes."multi-risk-level" != true and .attributes.organisation != true)) | {"id": .id, "enabled": false, "provider": .attributes.provider, "riskLevel": .attributes."risk-level"}',
                jsonresponse,
            )
            disabledmulti = pyjq.all(
                '.included[] | select ((.attributes.compliances| index("'
                + compliance
                + '")|not) and (.attributes."multi-risk-level" == true and .attributes.organisation != true)) | {"id": .id, "enabled": false, "provider": .attributes.provider}',
                jsonresponse,
            )
            buildjson = {
                "schema": "https://cloudconformity.com/external/profile.schema.json",
                "version": "1.1",
                "name": compliance,
                "description": compliance,
                "ruleSettings": disabledincluded + disabledmulti,
            }
            mergedjson = json.dumps(buildjson, indent=4)
            print("Creating profile file {}.profile.json".format(compliance))
            f = open("{}.profile.json".format(compliance), "w")
            f.write(mergedjson)


def main():
    acceptablecomplianceargs = ["online", "local"]
    args = sys.argv
    ccprofiles = CPB()

    if len(sys.argv) < 2:
        sys.exit(
            'Error: No argument specified, please rerun with either "online" or "local" argument'
        )

    arg = sys.argv[1].lower()

    if arg not in acceptablecomplianceargs:
        sys.exit(
            'Error: Specified argument is not valid, please run again with either "online" or "local" argument'
        )

    elif arg == "online":
        try:
            os.environ["apiKey"]
        except KeyError:
            sys.exit(
                'Error: Environment variable "apiKey" not set, please set this and try again'
            )
        try:
            os.environ["apiRegion"]
        except KeyError:
            sys.exit(
                'Error: Environment variable "apiRegion" not set, please set this and try again'
            )
        ccprofiles.online()

    elif arg == "local":
        ccprofiles.local()


if __name__ == "__main__":
    main()
