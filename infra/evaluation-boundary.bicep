// Lab32: inspect explicitly owned existing inputs; no judge/index provisioning.
param searchGroup string
param searchName string
param inferenceGroup string
param inferenceName string
resource search 'Microsoft.Search/searchServices@2023-11-01' existing = {
  name: searchName
  scope: resourceGroup(searchGroup)
}
resource inference 'Microsoft.CognitiveServices/accounts@2023-05-01' existing = {
  name: inferenceName
  scope: resourceGroup(inferenceGroup)
}
output searchId string = search.id
output searchLocalAuthDisabled bool = search.properties.disableLocalAuth
output searchPublicNetwork string = search.properties.publicNetworkAccess
output inferenceId string = inference.id
output inferenceKind string = inference.kind
output inferenceLocalAuthDisabled bool = inference.properties.disableLocalAuth
output inferencePublicNetwork string = inference.properties.publicNetworkAccess
// Actual private connectivity, data role scope, deployment/API compatibility,
// dataset rights and budget are independent readback/admission requirements.
