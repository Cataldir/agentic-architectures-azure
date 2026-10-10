// Original teaching module. API versions are pinned; deployment not executed.
param accountName string
param location string = resourceGroup().location
param privateEndpointSubnetId string
param privateDnsZoneId string
param identityName string
param ownerTags object

resource identity 'Microsoft.ManagedIdentity/userAssignedIdentities@2023-01-31' = {
  name: identityName
  location: location
  tags: ownerTags
}
resource account 'Microsoft.DocumentDB/databaseAccounts@2024-05-15' = {
  name: accountName
  location: location
  kind: 'GlobalDocumentDB'
  tags: ownerTags
  properties: {
    databaseAccountOfferType: 'Standard'
    publicNetworkAccess: 'Disabled'
    disableLocalAuth: true
    consistencyPolicy: { defaultConsistencyLevel: 'Session' }
    locations: [{ locationName: location, failoverPriority: 0 }]
    backupPolicy: { type: 'Continuous', continuousModeProperties: { tier: 'Continuous7Days' } }
  }
}
resource db 'Microsoft.DocumentDB/databaseAccounts/sqlDatabases@2024-05-15' = {
  parent: account
  name: 'orders'
  properties: { resource: { id: 'orders' } }
}
resource state 'Microsoft.DocumentDB/databaseAccounts/sqlDatabases/containers@2024-05-15' = {
  parent: db
  name: 'state'
  properties: {
    resource: { id: 'state', partitionKey: { paths: ['/id'], kind: 'Hash', version: 2 } }
    options: { throughput: 400 }
  }
}
resource daprState 'Microsoft.DocumentDB/databaseAccounts/sqlDatabases/containers@2024-05-15' = {
  parent: db
  name: 'daprstate'
  properties: {
    resource: { id: 'daprstate', partitionKey: { paths: ['/partitionKey'], kind: 'Hash', version: 2 } }
    options: { throughput: 400 }
  }
}
resource role 'Microsoft.DocumentDB/databaseAccounts/sqlRoleAssignments@2024-05-15' = {
  parent: account
  name: guid(account.id, identity.id, 'orders-data')
  properties: {
    principalId: identity.properties.principalId
    roleDefinitionId: '${account.id}/sqlRoleDefinitions/00000000-0000-0000-0000-000000000002'
    scope: '${account.id}/dbs/orders'
  }
}
resource pe 'Microsoft.Network/privateEndpoints@2024-05-01' = {
  name: '${accountName}-pe'
  location: location
  tags: ownerTags
  properties: {
    subnet: { id: privateEndpointSubnetId }
    privateLinkServiceConnections: [{
      name: 'cosmos-sql'
      properties: { privateLinkServiceId: account.id, groupIds: ['Sql'] }
    }]
  }
}
resource dns 'Microsoft.Network/privateEndpoints/privateDnsZoneGroups@2024-05-01' = {
  parent: pe
  name: 'default'
  properties: { privateDnsZoneConfigs: [{ name: 'cosmos', properties: { privateDnsZoneId: privateDnsZoneId } }] }
}
output endpoint string = account.properties.documentEndpoint
output accountId string = account.id
output identityId string = identity.id
output clientId string = identity.properties.clientId
output principalId string = identity.properties.principalId
