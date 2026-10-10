// Lab18: two separate groups are the owner deployment scopes, not security proof.
targetScope = 'subscription'
param location string
param groupA string
param groupB string
param suffix string
param privateEndpointSubnetId string
param privateDnsZoneId string
param costCenter string
resource a 'Microsoft.Resources/resourceGroups@2024-03-01' = { name: groupA, location: location, tags: { environment: 'course-lab', 'cost-center': costCenter } }
resource b 'Microsoft.Resources/resourceGroups@2024-03-01' = { name: groupB, location: location, tags: { environment: 'course-lab', 'cost-center': costCenter } }
module ca './context.bicep' = {
  name: 'context-a'
  scope: a
  params: { accountName: 'course-a-${suffix}', identityName: 'identity-a', location: location, privateEndpointSubnetId: privateEndpointSubnetId, privateDnsZoneId: privateDnsZoneId, ownerTags: { environment: 'course-lab', domain: 'a', 'cost-center': costCenter } }
}
module cb './context.bicep' = {
  name: 'context-b'
  scope: b
  params: { accountName: 'course-b-${suffix}', identityName: 'identity-b', location: location, privateEndpointSubnetId: privateEndpointSubnetId, privateDnsZoneId: privateDnsZoneId, ownerTags: { environment: 'course-lab', domain: 'b', 'cost-center': costCenter } }
}
output endpointA string = ca.outputs.endpoint
output endpointB string = cb.outputs.endpoint
output clientA string = ca.outputs.clientId
output clientB string = cb.outputs.clientId
