param environmentName string
param appName string
param location string = resourceGroup().location
@description('Immutable approved image, preferably registry/repository@sha256:digest')
param image string
param identityId string
param clientId string
param principalId string
param cosmosEndpoint string
param namespaceName string
param privateEndpointSubnetId string
param serviceBusPrivateDnsZoneId string
param tenantScope string
param ownerTags object

resource environment 'Microsoft.App/managedEnvironments@2025-01-01' existing = { name: environmentName }
resource bus 'Microsoft.ServiceBus/namespaces@2024-01-01' = {
  name: namespaceName
  location: location
  tags: ownerTags
  sku: { name: 'Premium', tier: 'Premium', capacity: 1 }
  properties: { publicNetworkAccess: 'Disabled', disableLocalAuth: true, minimumTlsVersion: '1.2' }
}
resource queue 'Microsoft.ServiceBus/namespaces/queues@2024-01-01' = {
  parent: bus
  name: 'tasks'
  properties: {
    lockDuration: 'PT1M'
    requiresDuplicateDetection: true
    duplicateDetectionHistoryTimeWindow: 'PT10M'
    maxDeliveryCount: 3
    defaultMessageTimeToLive: 'PT30M'
    deadLetteringOnMessageExpiration: true
  }
}
resource receiver 'Microsoft.Authorization/roleAssignments@2022-04-01' = {
  name: guid(queue.id, identityId, 'receive')
  scope: queue
  properties: {
    principalId: principalId
    principalType: 'ServicePrincipal'
    roleDefinitionId: subscriptionResourceId('Microsoft.Authorization/roleDefinitions', '4f6d3b9b-027b-4f4c-9142-0e5a2a2247e0')
  }
}
resource pe 'Microsoft.Network/privateEndpoints@2024-05-01' = {
  name: '${namespaceName}-pe'
  location: location
  tags: ownerTags
  properties: {
    subnet: { id: privateEndpointSubnetId }
    privateLinkServiceConnections: [{ name: 'servicebus', properties: { privateLinkServiceId: bus.id, groupIds: ['namespace'] } }]
  }
}
resource dns 'Microsoft.Network/privateEndpoints/privateDnsZoneGroups@2024-05-01' = {
  parent: pe
  name: 'default'
  properties: { privateDnsZoneConfigs: [{ name: 'bus', properties: { privateDnsZoneId: serviceBusPrivateDnsZoneId } }] }
}
resource dapr 'Microsoft.App/managedEnvironments/daprComponents@2025-01-01' = {
  parent: environment
  name: '${appName}-state'
  properties: {
    componentType: 'state.azure.cosmosdb'
    version: 'v1'
    scopes: [appName]
    initTimeout: '5m'
    metadata: [
      { name: 'url', value: cosmosEndpoint }
      { name: 'database', value: 'orders' }
      { name: 'collection', value: 'daprstate' }
      { name: 'azureClientId', value: clientId }
    ]
  }
}
resource app 'Microsoft.App/containerApps@2025-01-01' = {
  name: appName
  location: location
  tags: ownerTags
  identity: { type: 'UserAssigned', userAssignedIdentities: { '${identityId}': {} } }
  properties: {
    managedEnvironmentId: environment.id
    configuration: { activeRevisionsMode: 'Single', dapr: { enabled: true, appId: appName } }
    template: {
      containers: [{
        name: 'worker'
        image: image
        command: ['python', '-m', 'azure_course.dapr_worker']
        resources: { cpu: json('0.25'), memory: '0.5Gi' }
        env: [
          { name: 'AZURE_CLIENT_ID', value: clientId }
          { name: 'AZURE_COURSE_EFFECTS', value: 'approved-disposable-lab' }
          { name: 'SERVICEBUS_FQDN', value: '${namespaceName}.servicebus.windows.net' }
          { name: 'SERVICEBUS_QUEUE', value: 'tasks' }
          { name: 'COSMOS_ENDPOINT', value: cosmosEndpoint }
          { name: 'COURSE_TENANT', value: tenantScope }
          { name: 'DAPR_STATE_STORE', value: '${appName}-state' }
        ]
      }]
      scale: {
        minReplicas: 0
        maxReplicas: 3
        rules: [{ name: 'task-depth', custom: {
          type: 'azure-servicebus'
          identity: identityId
          metadata: { queueName: 'tasks', namespace: namespaceName, messageCount: '5' }
        } }]
      }
    }
  }
  dependsOn: [receiver, dapr, dns]
}
output appId string = app.id
output queueId string = queue.id
