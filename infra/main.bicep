// Workload deployment into one authorized disposable RG/private landing-zone.
// The owner supplies an existing private ACA environment/subnet/DNS bindings.
param environmentName string
param privateEndpointSubnetId string
param cosmosPrivateDnsZoneId string
param serviceBusPrivateDnsZoneId string
param image string
param suffix string
param tenantScope string = 'learnera'
param costCenter string
param location string = resourceGroup().location
var tags = { environment: 'course-lab', 'agent-system': 'orders-course', 'agent-role': 'worker', 'tenant-scope': tenantScope, 'cost-center': costCenter }
module context './context.bicep' = {
  name: 'orders-context'
  params: {
    accountName: 'course-orders-${suffix}'
    identityName: 'course-orders-${suffix}'
    location: location
    ownerTags: tags
    privateEndpointSubnetId: privateEndpointSubnetId
    privateDnsZoneId: cosmosPrivateDnsZoneId
  }
}
module worker './worker.bicep' = {
  name: 'orders-worker'
  params: {
    environmentName: environmentName
    appName: 'course-worker-${suffix}'
    image: image
    location: location
    identityId: context.outputs.identityId
    clientId: context.outputs.clientId
    principalId: context.outputs.principalId
    cosmosEndpoint: context.outputs.endpoint
    namespaceName: 'course-bus-${suffix}'
    privateEndpointSubnetId: privateEndpointSubnetId
    serviceBusPrivateDnsZoneId: serviceBusPrivateDnsZoneId
    tenantScope: tenantScope
    ownerTags: tags
  }
}
output AZURE_CONTAINER_APP_NAME string = 'course-worker-${suffix}'
output COSMOS_ENDPOINT string = context.outputs.endpoint
output AZURE_CLIENT_ID string = context.outputs.clientId
