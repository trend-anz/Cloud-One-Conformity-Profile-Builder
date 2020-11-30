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
    def __init__(self):
        """Create filters and output constants"""
        # Pipe these to produce desired filter
        self.__f_included = ".included[]"
        # Will match all others from compliance to disable
        self.__f_remove_comp = lambda c : f'( .attributes.compliances | contains(["{c}"]) | not )'
        self.__f_non_multi = f'(.attributes."multi-risk-level" != true and .attributes.organisation != true)'
        self.__f_multi = f'(.attributes."multi-risk-level" == true and .attributes.organisation != true)'
        self.__f_remove_prov = lambda p : f'(.attributes.provider != "{p}")'

        self.__f_r_comp = lambda c : f'{self.__f_included} | select ({self.__f_remove_comp(c)} and {self.__f_non_multi})'
        self.__f_r_comp_multi = lambda c : f'{self.__f_included} | select ({self.__f_remove_comp(c)} and {self.__f_multi})'
        self.__f_r_comp_or_prov = lambda c, p : f'{self.__f_included} | select ( ({self.__f_remove_comp(c)} or {self.__f_remove_prov(p)}) and {self.__f_non_multi})'
        self.__f_r_comp_multi_or_prov = lambda c, p : f'{self.__f_included} | select ( ({self.__f_remove_comp(c)} or {self.__f_remove_prov(p)}) and {self.__f_multi})'
        ## Outputs
        self.__o_dis_inc = '{"type": .type, "id": .id, "attributes": {"enabled": false, "riskLevel": .attributes."risk-level", "provider": .attributes.provider} }'
        self.__o_dis_inc_multi = '{"type": .type, "id": .id, "attributes": {"enabled": false, "provider": .attributes.provider} }'
        self.__o_data = '{"type": .type, "id": .id }'
        ## Outputs - local non API
        self.__ol_dis_inc = '{"id": .id, "enabled": false, "provider": .attributes.provider, "riskLevel": .attributes."risk-level" }'
        self.__ol_dis_inc_multi = '{"id": .id, "enabled": false, "provider": .attributes.provider }'

    @staticmethod
    def __jq_filter_resp(expression: str):
        """Filter response"""
        return pyjq.all(expression, jsonresponse)

    def online(self, local=False, provider_filter:str = None):
        # Create Profiles via API
        api = os.environ.get("apiKey")
        for compliance in compliancesunique:
            if not provider_filter:
                di_filter = self.__f_r_comp(compliance)
                dim_filter = self.__f_r_comp_multi(compliance)
            else:
                di_filter = self.__f_r_comp_or_prov(compliance, provider_filter)
                dim_filter = self.__f_r_comp_multi_or_prov(compliance, provider_filter)

            data_filter = di_filter
            datam_filter = dim_filter

            disabledincluded = self.__jq_filter_resp(f'{di_filter} | {self.__o_dis_inc}')
            disabledmulti = self.__jq_filter_resp(f'{dim_filter} | {self.__o_dis_inc_multi}')
            data = self.__jq_filter_resp(f'{data_filter} | {self.__o_data}')
            datamulti = self.__jq_filter_resp(f'{datam_filter} | {self.__o_data}')

            name = compliance
            description = compliance
            if provider_filter:
                name += f" {provider_filter} only"
                description += f" rules only for {provider_filter}"
            buildjson = {
                "included": disabledincluded + disabledmulti,
                "data": {
                    "type": "profiles",
                    "attributes": {"name": name, "description": description},
                    "relationships": {"ruleSettings": {"data": data + datamulti}},
                },
            }
            mergedjson = json.dumps(buildjson, indent=2, sort_keys=True)
            suffix = provider_filter if provider_filter is not None else ""
            if local:
                print(f"Creating profile file {compliance}.profile4api{suffix}.json")
                f = open(f"{compliance}.profile4api{suffix}.json", "w")
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
            disabledincluded = self.__jq_filter_resp(f'{self.__f_r_comp(compliance)} | {self.__ol_dis_inc}')
            disabledmulti = self.__jq_filter_resp(f'{self.__f_r_comp_multi(compliance)} | {self.__ol_dis_inc_multi}')
            buildjson = {
                "schema": "https://cloudconformity.com/external/profile.schema.json",
                "version": "1.1",
                "name": compliance,
                "description": compliance,
                "ruleSettings": disabledincluded + disabledmulti,
            }
            mergedjson = json.dumps(buildjson, indent=4)
            print(f"Creating profile file {compliance}.profile.json")
            f = open(f"{compliance}.profile.json", "w")
            f.write(mergedjson)


def main():
    acceptable_args = ["online", "local", "local4api"]
    args = sys.argv
    ccprofiles = CPB()

    if len(sys.argv) < 2:
        sys.exit(
            'Error: No argument specified, please rerun with either "online" or "local" argument'
        )

    arg = sys.argv[1].lower()
    prov_filter = None
    if len(sys.argv) == 3:
        prov_filter = sys.argv[2]

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
        ccprofiles.online(provider_filter=prov_filter)

    elif arg == "local":
        ccprofiles.local()

    elif arg == "local4api":
        ccprofiles.online(local=True, provider_filter=prov_filter)

if __name__ == "__main__":
    main()
