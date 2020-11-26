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
    @staticmethod
    def __jq_filter_resp(expression: str):
        """Filter response"""
        return pyjq.all(expression, jsonresponse)

    def online(self, local=False):
        # Create Profiles via API
        api = os.environ.get("apiKey")
        for compliance in compliancesunique:
            disabledincluded = self.__jq_filter_resp(
                '.included[] | select ((.attributes.compliances| index("'
                + compliance
                + '")|not) and (.attributes."multi-risk-level" != true and .attributes.organisation != true)) | {"type": .type, "id": .id, "attributes":{"enabled": false, "riskLevel": .attributes."risk-level", "provider": .attributes.provider}}',
            )
            disabledmulti = self.__jq_filter_resp(
                '.included[] | select ((.attributes.compliances| index("'
                + compliance
                + '")|not) and (.attributes."multi-risk-level" == true and .attributes.organisation != true)) | {"type": .type, "id": .id, "attributes":{"enabled": false, "provider": .attributes.provider}}',
            )
            data = self.__jq_filter_resp(
                '.included[] | select ((.attributes.compliances| index("'
                + compliance
                + '")|not) and (.attributes."multi-risk-level" != true and .attributes.organisation != true)) | {"type": .type, "id": .id}',
            )
            datamulti = self.__jq_filter_resp(
                '.included[] | select ((.attributes.compliances| index("'
                + compliance
                + '")|not) and (.attributes."multi-risk-level" == true and .attributes.organisation != true)) | {"type": .type, "id": .id}',
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
            if local:
                print("Creating profile file {}.profile4api.json".format(compliance))
                f = open("{}.profile4api.json".format(compliance), "w")
                f.write(mergedjson)
            else:
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
            disabledincluded = self.__jq_filter_resp(
                '.included[] | select ((.attributes.compliances| index("'
                + compliance
                + '")|not) and (.attributes."multi-risk-level" != true and .attributes.organisation != true)) | {"id": .id, "enabled": false, "provider": .attributes.provider, "riskLevel": .attributes."risk-level"}',
            )
            disabledmulti = self.__jq_filter_resp(
                '.included[] | select ((.attributes.compliances| index("'
                + compliance
                + '")|not) and (.attributes."multi-risk-level" == true and .attributes.organisation != true)) | {"id": .id, "enabled": false, "provider": .attributes.provider}',
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

    def local4api(self):
        """
        Create Profiles for API, store locally
        """
        # https://github.com/cloudconformity/documentation-api/blob/master/Profiles.md#parameters-3
        self.online(local=True)

def main():
    acceptable_args = ["online", "local", "local4api"]
    args = sys.argv
    ccprofiles = CPB()

    if len(sys.argv) < 2:
        sys.exit(
            'Error: No argument specified, please rerun with either "online" or "local" argument'
        )

    arg = sys.argv[1].lower()

    if arg not in acceptable_args:
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

    elif arg == "local4api":
        ccprofiles.local4api()

if __name__ == "__main__":
    main()
