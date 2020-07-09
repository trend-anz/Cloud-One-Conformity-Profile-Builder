import requests
import json
import os
import pyjq
region=os.environ.get('apiRegion')
api=os.environ.get('apiKey')
servicesurl='https://' + region + '.cloudconformity.com/v1/services'
profilesapi='https://' + region + '-api.cloudconformity.com/v1/profiles'
response=requests.get(servicesurl)
json_data=json.loads(response.text)
compliancesjq=pyjq.all('.included[].attributes | select (.compliances[] != null) | .compliances[]', json_data)
compliancesunique=pyjq.all('unique', compliancesjq)
#Create Profiles via API
#comment out this section if you only want to create the profiles locally
for compliance in compliancesunique:
    for c in compliance:
        disabledincluded=pyjq.all('.included[] | select ((.attributes.compliances| index("' + c + '")|not) and (.attributes."multi-risk-level" != true and .attributes.organisation != true)) | {"type": .type, "id": .id, "attributes":{"enabled": false, "riskLevel": .attributes."risk-level"}}', json_data)
        disabledmulti=pyjq.all('.included[] | select ((.attributes.compliances| index("' + c + '")|not) and (.attributes."multi-risk-level" == true and .attributes.organisation != true)) | {"type": .type, "id": .id, "attributes":{"enabled": false}}', json_data)
        data=pyjq.all('.included[] | select ((.attributes.compliances| index("' + c + '")|not) and (.attributes."multi-risk-level" != true and .attributes.organisation != true)) | {"type": .type, "id": .id}', json_data)
        datamulti=pyjq.all('.included[] | select ((.attributes.compliances| index("' + c + '")|not) and (.attributes."multi-risk-level" == true and .attributes.organisation != true)) | {"type": .type, "id": .id}', json_data)
        buildjson = {"included": disabledincluded + disabledmulti, "data": {"type": "profiles", "attributes": {"name": c, "description": c},"relationships": { "ruleSettings": { "data": data + datamulti}}}}
        mergedjson = json.dumps(buildjson)
        headers={
            'Content-Type': 'application/vnd.api+json',
            'Authorization': 'ApiKey ' + api
        }
        cc=requests.post(profilesapi, headers=headers,data=mergedjson)
        print(json.dumps(cc.json(), indent=4, sort_keys=True))

#Create profile files locally
for compliance in compliancesunique:
    for c in compliance:
        disabledincluded=pyjq.all('.included[] | select ((.attributes.compliances| index("' + c + '")|not) and (.attributes."multi-risk-level" != true and .attributes.organisation != true)) | {"id": .id, "enabled": false, "provider": .attributes.provider, "riskLevel": .attributes."risk-level"}', json_data)
        disabledmulti=pyjq.all('.included[] | select ((.attributes.compliances| index("' + c + '")|not) and (.attributes."multi-risk-level" == true and .attributes.organisation != true)) | {"id": .id, "enabled": false, "provider": .attributes.provider}', json_data)
        buildjson = {"schema": "https://cloudconformity.com/external/profile.schema.json", "version": "1.1", "name": c, "description": c, "ruleSettings": disabledincluded + disabledmulti}
        mergedjson = json.dumps(buildjson, indent=4)
        print('Creating profile file {}.profile.json'.format(c))
        f=open('{}.profile.json'.format(c),'w')
        f.write(mergedjson)
